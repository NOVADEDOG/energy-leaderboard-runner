"""Main CLI entrypoint for the energy-leaderboard-runner."""

import atexit
import json
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

# Handle both module import and direct script execution
if __name__ == "__main__" and __package__ is None:
    # Add parent directory to path for direct script execution
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from src.config import config
    from src.energy_meter.integrator import get_platform_meter
    from src.llm_integrations.ollama_client import OllamaClient
    from src.llm_integrations.openai_client import OpenAIClient
    from src.utils.result_exporter import export_results
    from src.utils.device_info import get_device_info
else:
    from .config import config
    from .energy_meter.integrator import get_platform_meter
    from .llm_integrations.ollama_client import OllamaClient
    from .llm_integrations.openai_client import OpenAIClient
    from .utils.result_exporter import export_results
    from .utils.device_info import get_device_info

app = typer.Typer(
    name="energy-leaderboard-runner",
    help="Benchmark local LLM energy consumption",
)
console = Console()


def resolve_testset_path(testset_name: str) -> Path:
    """Resolve a user-supplied testset name to an on-disk JSON file."""
    testset_dir = Path(__file__).parent / "data" / "testsets"
    normalized = testset_name.lower().rstrip(".json")
    candidates = []

    # Allow inputs like "easy", "testset_easy", and explicit filenames.
    suffix_candidates = [normalized]
    if not normalized.startswith("testset_"):
        suffix_candidates.append(f"testset_{normalized}")

    for suffix in suffix_candidates:
        candidates.append(testset_dir / f"{suffix}.json")

    for candidate in candidates:
        if candidate.exists():
            return candidate

    raise FileNotFoundError(
        f"Testset '{testset_name}' not found in {testset_dir}. "
        "Available files: "
        f"{', '.join(sorted(p.stem for p in testset_dir.glob('*.json')))}"
    )


def load_testset(testset_name: str) -> tuple[Dict[str, str], List[Dict[str, str]]]:
    """
    Load a structured testset definition.

    Returns:
        (metadata, questions) where metadata contains the top-level fields
        from the JSON (id, name, goal, notes, etc.) and questions is a list of
        dictionaries with at minimum a "prompt" key.
    """
    testset_path = resolve_testset_path(testset_name)

    try:
        with open(testset_path, "r") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in testset file '{testset_path}': {e}")

    if isinstance(data, dict) and "questions" in data:
        questions = data["questions"]
        metadata = {k: v for k, v in data.items() if k != "questions"}
    elif isinstance(data, list):
        # Backwards compatibility with legacy flat lists
        questions = data
        metadata = {"id": testset_name, "name": testset_name}
    else:
        raise ValueError(
            "Testset file must be either a list of prompts or an object "
            "containing a 'questions' array"
        )

    if not isinstance(questions, list) or not questions:
        raise ValueError("Testset contains no questions")

    for question in questions:
        if "prompt" not in question:
            raise ValueError("Each question must include a 'prompt' field")

    return metadata, questions


def get_available_testsets() -> List[str]:
    """Scan the testsets directory and return user-friendly testset names."""
    testset_dir = Path(__file__).parent / "data" / "testsets"
    names: set[str] = set()
    for file in testset_dir.glob("*.json"):
        stem = file.stem
        display = stem.replace("testset_", "", 1)
        names.add(display)
    return sorted(names)


@app.command()
def run_test(
    model: str = typer.Option(
        ...,
        "--model",
        "-m",
        help="Model identifier (e.g., 'llama3:latest')",
    ),
    test_set: Optional[str] = typer.Option(
        None,
        "--test-set",
        "-t",
        help="Testset to run (e.g., 'easy', 'testset_easy')",
        case_sensitive=False,
        autocompletion=get_available_testsets,
    ),
    legacy_test_set: Optional[str] = typer.Argument(
        None,
        help="[Deprecated] Positional testset argument",
        case_sensitive=False,
        autocompletion=get_available_testsets,
        hidden=True,
    ),
    output: str = typer.Option(
        "results/output.json",
        "--output",
        "-o",
        help="Output file path for results",
    ),
    device_name: Optional[str] = typer.Option(
        None,
        "--device-name",
        "-d",
        help="Override auto-detected device name (e.g., 'My Custom PC')",
    ),
    device_type: Optional[str] = typer.Option(
        None,
        "--device-type",
        help="Override auto-detected device type (apple, nvidia, amd, intel, unknown)",
    ),
    provider: str = typer.Option(
        "ollama",
        "--provider",
        "-p",
        help="LLM provider (ollama, openai)",
    ),
    base_url: Optional[str] = typer.Option(
        None,
        "--base-url",
        help="Base URL for OpenAI-compatible provider (default: uses OLLAMA_HOST for ollama)",
    ),
    api_key: Optional[str] = typer.Option(
        "sk-no-key-required",
        "--api-key",
        help="API key for OpenAI-compatible provider",
    ),
):
    """
    Run an energy benchmark test on a local LLM.

    This command will:
    1. Connect to the LLM provider (Ollama or OpenAI-compatible)
    2. Load the specified testset
    3. Initialize the platform-appropriate energy meter
    4. Run all prompts with energy measurement
    5. Export results to JSON
    """
    console.print(
        f"[bold blue]Energy Leaderboard Runner[/bold blue]",
        style="bold",
    )
    selected_test_set = test_set or legacy_test_set or "easy"

    console.print(f"Model: {model}")
    console.print(f"Testset: {selected_test_set}")
    console.print(f"Output: {output}\n")

    # Load configuration
    ollama_host = config.get_ollama_host()
    co2_intensity = config.get_co2_intensity()
    region = config.get_region()
    sampling_ms = config.get_sampling_interval_ms()

    console.print(f"Provider: {provider}")
    if base_url:
        console.print(f"Base URL: {base_url}")
    elif provider == "ollama":
        console.print(f"Ollama Host: {ollama_host}")

    console.print(f"CO2 Intensity: {co2_intensity} g/kWh")
    console.print(f"Region: {region}")
    console.print(f"Sampling Interval: {sampling_ms}ms\n")

    # Detect device information
    console.print("[yellow]Detecting device information...[/yellow]")
    device_info = get_device_info(device_name=device_name, device_type=device_type)
    console.print(f"[green]✓[/green] Device: {device_info.device_name}")
    console.print(f"  Type: {device_info.device_type}")
    console.print(f"  OS: {device_info.os_name} {device_info.os_version}")
    if device_info.cpu_model:
        console.print(f"  CPU: {device_info.cpu_model}")
    if device_info.gpu_model:
        console.print(f"  GPU: {device_info.gpu_model}")
    if device_info.ram_gb:
        console.print(f"  RAM: {device_info.ram_gb} GB")
    console.print("")

    # Initialize LLM client
    console.print(f"[yellow]Initializing {provider} client...[/yellow]")
    
    llm_client = None
    if provider == "ollama":
        # For Ollama, we use the config host if base_url is not provided
        host = base_url if base_url else ollama_host
        llm_client = OllamaClient(host=host)
    elif provider == "openai":
        if not base_url:
            console.print("[red]✗[/red] --base-url is required for openai provider")
            sys.exit(1)
        llm_client = OpenAIClient(base_url=base_url, api_key=api_key)
    else:
        console.print(f"[red]✗[/red] Unknown provider: {provider}")
        sys.exit(1)

    # Check connection
    try:
        llm_client.check_connection()
        console.print(f"[green]✓[/green] Connected to {provider} successfully\n")
    except ConnectionError as e:
        console.print(f"[red]✗[/red] {e}")
        sys.exit(1)

    # Initialize energy meter
    console.print("[yellow]Initializing energy meter...[/yellow]")
    try:
        meter = get_platform_meter(sampling_ms=sampling_ms)
        console.print(
            f"[green]✓[/green] Using {meter.__class__.__name__}\n"
        )
    except NotImplementedError as e:
        console.print(f"[red]✗[/red] {e}")
        sys.exit(1)

    # Register cleanup handler to ensure meter is stopped
    def cleanup():
        try:
            # Attempt to stop the meter if it was initialized
            if 'meter' in locals() and meter and hasattr(meter, 'stop'):
                 try:
                     meter.stop()
                 except Exception:
                     pass
        except Exception:
            pass

    atexit.register(cleanup)

    # Pre-authenticate sudo if using macOS powermetrics
    if meter.__class__.__name__ == "MacosMeter":
        console.print(
            "[yellow]Requesting sudo access for powermetrics...[/yellow]"
        )
        try:
            subprocess.run(
                ["sudo", "-v"],
                check=True,
                capture_output=True,
                timeout=60,
            )
            console.print(
                "[green]✓[/green] Sudo access granted (credentials cached)\n"
            )
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
            console.print(
                f"[red]✗[/red] Failed to authenticate sudo: {e}\n"
            )
            sys.exit(1)

    # Load testset
    console.print(
        f"[yellow]Loading testset '{selected_test_set}'...[/yellow]"
    )
    try:
        testset_meta, questions = load_testset(selected_test_set)
        console.print(
            f"[green]✓[/green] Loaded {len(questions)} prompts from "
            f"'{testset_meta.get('name', selected_test_set)}'\n"
        )
    except (FileNotFoundError, ValueError) as e:
        console.print(f"[red]✗[/red] {e}")
        sys.exit(1)

    if not questions:
        console.print("[red]✗[/red] Testset is empty")
        sys.exit(1)

    # Run all prompts with energy measurement
    console.print(
        f"[bold yellow]Running {len(questions)} prompts with energy measurement...[/bold yellow]\n"
    )

    results: List[Dict] = []

    for idx, question in enumerate(questions, start=1):
        prompt = question["prompt"]
        console.print(
            f"[cyan]Prompt {idx}/{len(questions)} - "
            f"{question.get('id', 'no-id')}:[/cyan] {prompt[:80]}..."
        )

        try:
            # Start energy measurement
            try:
                meter.start()
            except PermissionError as e:
                console.print(f"[red]✗[/red] Permission denied: {e}")
                console.print("[yellow]Please run the script with sudo privileges.[/yellow]")
                sys.exit(1)

            # Measure total duration
            total_start = time.time()

            # Generate completion
            (
                completion_text,
                tokens_prompt,
                tokens_completion,
                response_time_s,
            ) = llm_client.generate(model=model, prompt=prompt)

            total_end = time.time()
            duration_s = total_end - total_start

            # Stop energy measurement
            energy_metrics = meter.stop()

            # Combine all metrics
            base_result = {
                "prompt": prompt,
                "completion": completion_text,
                "tokens_prompt": tokens_prompt,
                "tokens_completion": tokens_completion,
                "duration_s": round(duration_s, 3),
                "response_time_s": round(response_time_s, 3),
                "energy_wh_raw": round(energy_metrics["energy_wh_raw"], 6),
                "energy_wh_net": round(energy_metrics["energy_wh_raw"], 6),
                "provider": provider,
                "model": model,
                "region": region,
                "notice": None,
                "sampling_ms": energy_metrics["sampling_ms"],
                # Device information (mandatory)
                "device_name": device_info.device_name,
                "device_type": device_info.device_type,
                "os_name": device_info.os_name,
                "os_version": device_info.os_version,
            }
            
            # Add optional device fields
            if device_info.cpu_model:
                base_result["cpu_model"] = device_info.cpu_model
            if device_info.gpu_model:
                base_result["gpu_model"] = device_info.gpu_model
            if device_info.ram_gb:
                base_result["ram_gb"] = device_info.ram_gb
            if device_info.chip_architecture:
                base_result["chip_architecture"] = device_info.chip_architecture

            metadata_fields = {
                "testset_id": testset_meta.get("id", selected_test_set),
                "testset_name": testset_meta.get("name", selected_test_set),
                "testset_goal": testset_meta.get("goal"),
                "testset_notes": testset_meta.get("notes_for_experimenter"),
                "question_id": question.get("id"),
                "question_difficulty": question.get("difficulty"),
                "question_task_type": question.get("task_type"),
                "expected_answer_description": question.get(
                    "expected_answer_description"
                ),
                "max_output_tokens_hint": question.get(
                    "max_output_tokens_hint"
                ),
                "energy_relevance": question.get("energy_relevance"),
            }

            result = base_result.copy()
            for key, value in metadata_fields.items():
                if value is not None:
                    result[key] = value

            tags = question.get("tags")
            if tags is not None:
                result["tags"] = tags

            results.append(result)

            console.print(
                f"  [green]✓[/green] Energy: {result['energy_wh_raw']:.4f} Wh | "
                f"Tokens: {tokens_completion} | Time: {response_time_s:.2f}s\n"
            )

        except Exception as e:
            console.print(f"  [red]✗[/red] Error: {e}\n")
            # Continue with next prompt
            continue

    # Export results
    if not results:
        console.print("[red]✗[/red] No results to export")
        sys.exit(1)

    console.print(f"[yellow]Exporting results to {output}...[/yellow]")

    schema_path = Path(__file__).parent / "data" / "metrics_schema.json"

    try:
        export_results(
            results_list=results,
            output_file=output,
            co2_intensity=co2_intensity,
            schema_path=str(schema_path),
        )
        console.print(f"[green]✓[/green] Results exported successfully!")
        console.print(f"\n[bold]Summary:[/bold]")
        console.print(f"  Total prompts: {len(results)}")

        total_energy = sum(r["energy_wh_raw"] for r in results)
        total_tokens = sum(
            r["tokens_prompt"] + r["tokens_completion"] for r in results
        )

        console.print(f"  Total energy: {total_energy:.4f} Wh")
        console.print(f"  Total tokens: {total_tokens}")

    except Exception as e:
        console.print(f"[red]✗[/red] Failed to export results: {e}")
        sys.exit(1)


def main():
    """Entry point for the CLI."""
    app()


if __name__ == "__main__":
    main()
