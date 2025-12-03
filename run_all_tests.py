"""
Script to automate running all 4 test sets (easy, medium, hard, mixed).
"""

import argparse
import datetime
import subprocess
import sys
from pathlib import Path

# Define the test sets to run
TEST_SETS = ["easy", "medium", "hard", "mixed"]


def sanitize_model_name(model_name: str) -> str:
    """Sanitize model name for filename usage."""
    return model_name.replace(":", "_").replace("/", "_")


def main():
    parser = argparse.ArgumentParser(
        description="Run all energy leaderboard test sets."
    )
    parser.add_argument(
        "--model", "-m", required=True, help="Model identifier (e.g., 'llama3:latest')"
    )
    parser.add_argument(
        "--provider",
        "-p",
        default="ollama",
        choices=["ollama", "openai"],
        help="LLM provider",
    )
    parser.add_argument(
        "--base-url",
        help="Base URL for OpenAI-compatible provider",
    )
    parser.add_argument(
        "--api-key",
        default="sk-no-key-required",
        help="API key for OpenAI-compatible provider",
    )
    parser.add_argument(
        "--device-name",
        "-d",
        help="Override device name",
    )

    args = parser.parse_args()

    # Get current date for filenames
    date_str = datetime.datetime.now().strftime("%d_%m")
    sanitized_model = sanitize_model_name(args.model)

    # Ensure results directory exists
    results_dir = Path("results")
    results_dir.mkdir(exist_ok=True)

    print(f"Starting automation for model: {args.model}")
    print(f"Provider: {args.provider}")
    print(f"Date: {date_str}")
    print("-" * 50)

    for test_set in TEST_SETS:
        print(f"\n>>> Running test set: {test_set}")
        
        output_filename = f"output_{sanitized_model}_{test_set}_{date_str}.json"
        output_path = results_dir / output_filename

        cmd = [
            sys.executable,
            "src/main.py",
            "run-test",
            "--model",
            args.model,
            "--test-set",
            test_set,
            "--output",
            str(output_path),
            "--provider",
            args.provider,
        ]

        if args.base_url:
            cmd.extend(["--base-url", args.base_url])
        
        if args.api_key:
            cmd.extend(["--api-key", args.api_key])
            
        if args.device_name:
            cmd.extend(["--device-name", args.device_name])

        try:
            subprocess.run(cmd, check=True)
            print(f">>> Finished {test_set}. Results saved to {output_path}")
        except subprocess.CalledProcessError as e:
            print(f"!!! Error running {test_set}: {e}")
            continue

    print("\n" + "=" * 50)
    print("Automation complete.")


if __name__ == "__main__":
    main()
