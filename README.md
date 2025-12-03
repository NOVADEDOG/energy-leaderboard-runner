# Energy Leaderboard Runner 🌿

[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Docker](https://img.shields.io/badge/docker-ready-blue.svg)](https://www.docker.com/)

**Real-world energy benchmarks for local LLMs.**

> 🏆 **View the Live Leaderboard:** [novadedog.github.io/energy-leaderboard-runner](https://novadedog.github.io/energy-leaderboard-runner/)

This tool measures the **actual hardware energy consumption** (Wh) and CO2 emissions of Large Language Models running on your local machine. No estimates, no cloud APIs—just real data from your hardware sensors.

## 🚀 Why This Matters

As LLMs become ubiquitous, their energy footprint grows. We believe in:
1.  **Transparency**: Real measurements, not theoretical estimates.
2.  **Reproducibility**: Standardized containerized benchmarks.
3.  **Community**: Crowdsourced data from diverse hardware.

## ✨ Features

- **🔌 Real Hardware Metering**:
    - **macOS**: Apple Silicon & Intel (via `powermetrics`)
    - **Linux**: NVIDIA GPUs (NVML), AMD GPUs (ROCm), Intel/AMD CPUs (RAPL)
- **🤖 Broad Support**: Works with **Ollama**, vLLM, and OpenAI-compatible endpoints.
- **📊 Rich Metrics**: Energy (Wh), CO2 (g), Tokens/Watt, and more.
- **🐳 Docker Ready**: Consistent environments for reproducible testing.

## 🏁 Quick Start

### 1. Prerequisites
- **Python 3.10+**
- **Ollama** running locally (e.g., `ollama serve`)
- Pull a model: `ollama pull llama3`

### 2. Install
```bash
git clone https://github.com/NOVADEDOG/energy-leaderboard-runner.git
cd energy-leaderboard-runner
pip install -r requirements.txt
```

### 3. Run a Benchmark
```bash
# Run the full suite (Recommended for contributors)
python run_all_tests.py --model llama3:latest

# Or run a specific test set
python src/main.py run-test --model llama3:latest --test-set easy
```

### 4. Contribute Your Results! 🌍
Help us build the most comprehensive energy dataset.
1.  Your results are saved to `results/output_*.json`.
2.  **Move** this file to `energy-leaderboard-web/public/data/`.
3.  Submit a **Pull Request** with your new data file.

👉 **See [RUNBOOK.md](RUNBOOK.md) for detailed instructions on running benchmarks and contributing data.**

## 🛠️ Platform Support

| Platform | Meter | Status |
|----------|-------|--------|
| **macOS** | `powermetrics` | ✅ Native Support (Requires Sudo) |
| **Linux + NVIDIA** | `NVML` | ✅ Full Support |
| **Linux + AMD** | `ROCm` | ✅ Full Support |
| **Linux CPU** | `RAPL` | ✅ Full Support |
| **Windows** | - | 🚧 Docker Only (No Energy Data yet) |

## 🤝 Contributing

We love contributions! Whether it's running benchmarks on new hardware, adding support for new providers, or improving the docs.

- **Run Benchmarks**: See [RUNBOOK.md](RUNBOOK.md).
- **Develop**: See [AI_DOCS/Project_Plan.md](AI_DOCS/Project_Plan.md) for architecture details.
- **Legal**: All contributors must agree to the [CLA](CLA.md) when submitting a Pull Request.

## 📄 License

GNU GPLv3 - see [LICENSE](LICENSE) for details.
