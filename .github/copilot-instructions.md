# Copilot Instructions for Energy Leaderboard Runner

## Project Overview

This project measures real-world energy consumption of local LLMs. It has two main components:
1. **Python CLI** (`src/`) - Runs benchmarks and collects energy metrics from hardware sensors
2. **React Web App** (`energy-leaderboard-web/`) - Displays crowdsourced benchmark results

## Architecture & Key Patterns

### Energy Meter System (Plugin Architecture)
All energy meters inherit from `EnergyMeter` base class in [src/energy_meter/base.py](src/energy_meter/base.py):
- `is_available()` → Platform detection
- `start()` / `stop()` → Measurement lifecycle returning `energy_wh_raw`, `duration_s`, `sampling_ms`

Platform detection priority in [src/energy_meter/integrator.py](src/energy_meter/integrator.py):
- macOS: `powermetrics` (requires sudo)
- Linux: NVML (NVIDIA) → ROCm (AMD) → RAPL (CPU)

### LLM Integrations (Plugin Architecture)
Implement `LlmRunner` from [src/llm_integrations/base.py](src/llm_integrations/base.py):
- `check_connection()` → Validate endpoint
- `generate()` → Returns `(text, tokens_prompt, tokens_completion, response_time_s)`

Supported: Ollama (`ollama_client.py`), OpenAI-compatible (`openai_client.py`)

### Configuration
Environment-based via [src/config.py](src/config.py):
- `OLLAMA_HOST` (default: `http://localhost:11434`)
- `CO2_INTENSITY_G_KWH` (default: 350.0 - EU average)
- `SAMPLING_INTERVAL_MS` (default: 100)

## Commands & Workflows

```bash
# Install dependencies
pip install -r requirements.txt

# Run single benchmark (requires Ollama running)
python src/main.py run-test --model llama3:latest --test-set easy

# Run all test sets (easy, medium, hard, mixed) - preferred for contributions
python run_all_tests.py --model llama3:latest

# OpenAI-compatible provider
python run_all_tests.py --model gpt-4 --provider openai --base-url https://api.example.com

# Docker (Linux with GPU)
docker build -t energy-leaderboard-runner .
docker run --rm --gpus all -v $(pwd)/results:/app/results \
  -e OLLAMA_HOST=http://172.17.0.1:11434 energy-leaderboard-runner \
  run_all_tests.py --model llama3:latest
```

## Test Sets

Located in [src/data/testsets/](src/data/testsets/). Structure:
```json
{
  "id": "ts1",
  "name": "...",
  "goal": "...",
  "questions": [{ "id": "...", "prompt": "...", "difficulty": "easy" }]
}
```
Reference testset by name without prefix: `--test-set easy` (resolves to `testset_easy.json`)

## Output Schema

Results validated against [src/data/metrics_schema.json](src/data/metrics_schema.json). Key metrics:
- `energy_wh_raw` / `energy_wh_net` - Energy consumption
- `wh_per_1k_tokens` - Efficiency metric
- `g_co2` - Calculated from `CO2_INTENSITY_G_KWH`

Output files: `results/output_{model}_{testset}_{date}.json`

## Web Frontend (`energy-leaderboard-web/`)

React + Vite + Tailwind. Data lives in `public/data/*.json`.

```bash
cd energy-leaderboard-web
npm install && npm run dev    # Development
npm run build                 # Production build
```

## Contributing Benchmarks

1. Run `python run_all_tests.py --model <model>`
2. Copy `results/output_*.json` → `energy-leaderboard-web/public/data/`
3. Submit PR with new JSON files

## Code Conventions

- CLI uses Typer with Rich for console output
- Dual import pattern in main.py supports both module and direct execution
- Abstract base classes define interfaces; implementations are in same directory
- All file paths use `pathlib.Path`
