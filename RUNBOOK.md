# 📘 Energy Leaderboard Runbook

This guide explains how to run benchmarks, troubleshoot issues, and contribute your results to the global leaderboard.

## 🏃 Running Benchmarks

### 1. Setup Environment
Ensure you have Python 3.10+ and the dependencies installed:
```bash
pip install -r requirements.txt
```

### 2. Prepare Ollama
Make sure Ollama is running and you have the model you want to test:
```bash
ollama serve
ollama pull llama3:latest
```

### 3. Build Docker Image (Optional)
If you prefer running with Docker, build the image first. This is simple and only needs to be done once (or when you update the code).

```bash
# Build the image with the tag 'energy-leaderboard-runner'
docker build -t energy-leaderboard-runner .
```

### 4. Execute Tests
Run the standard test suite. We recommend running the **easy**, **medium**, and **hard** sets to get a complete picture.

#### Option A: Running with Python (Native)
Best for accurate energy measurement on macOS and Linux.

```bash
# Run a single test set
python src/main.py run-test --model llama3:latest --test-set easy

# Run ALL test sets automatically (Recommended)
python run_all_tests.py --model llama3:latest
```

#### Option B: Running with Docker
Great for reproducibility. Note that on macOS, Docker cannot measure energy (due to VM isolation), but it works perfectly for verifying the pipeline.

**Linux (with NVIDIA GPU):**
```bash
docker run --rm \
  --gpus all \
  -v $(pwd)/results:/app/results \
  -e OLLAMA_HOST=http://172.17.0.1:11434 \
  energy-leaderboard-runner \
  run_all_tests.py --model llama3:latest
```

**Windows (with NVIDIA GPU):**
```powershell
docker run --rm `
  --gpus all `
  -v ${PWD}/results:/app/results `
  -e OLLAMA_HOST=http://host.docker.internal:11434 `
  energy-leaderboard-runner `
  run_all_tests.py --model llama3:latest
```

**macOS (Pipeline Test Only):**
```bash
docker run --rm \
  -v $(pwd)/results:/app/results \
  -e OLLAMA_HOST=http://host.docker.internal:11434 \
  energy-leaderboard-runner \
  run_all_tests.py --model llama3:latest
```

### 4. Verify Results
Check the `results/` directory. You should see files like:
- `results/output_llama3_latest_testset_easy_2024-12-02.json`
- `results/output_llama3_latest_testset_medium_2024-12-02.json`

---

## 🌍 Contributing to the Leaderboard

We crowdsource data to build the most comprehensive view of LLM energy efficiency. Here is how to add your data:

### Step 1: Generate Data
Run the benchmarks as described above. Ensure your machine was not running other heavy background tasks during the test.

### Step 2: Move Data
Copy your result JSON files from the `results/` folder to the web application's data directory:

```bash
# Example
cp results/output_*.json energy-leaderboard-web/public/data/
```

### Step 3: Submit a Pull Request
1.  Commit the new JSON files in `energy-leaderboard-web/public/data/`.
2.  Push your branch to GitHub.
3.  Open a Pull Request to the `main` branch.

**PR Checklist:**
- [ ] Included JSON files in `energy-leaderboard-web/public/data/`
- [ ] Mentioned your hardware specs in the PR description (optional, as it's in the JSON)
- [ ] Verified the data looks reasonable (no 0 energy readings unless expected)

---

## 🔧 Troubleshooting

### "Permission Denied" on macOS
**Issue:** `powermetrics` requires root privileges.
**Fix:** The script will ask for your sudo password. If it fails, try running with sudo explicitly (though the script handles this internally):
```bash
sudo python src/main.py run-test ...
```

### "No Energy Meter Available"
**Issue:** Your hardware is not supported or drivers are missing.
**Fix:**
- **Mac**: Only Apple Silicon (M1/M2/M3) is fully supported. Intel Macs work but may vary.
- **Linux/NVIDIA**: Ensure `nvidia-smi` works and `pynvml` is installed.
- **Windows**: Currently not supported for direct energy measurement. Use WSL2 with caution (no hardware access usually) or wait for Windows support.

### "Ollama Connection Failed"
**Issue:** Cannot connect to `http://localhost:11434`.
**Fix:**
- Ensure `ollama serve` is running.
- If using Docker, use `host.docker.internal` or the host IP.

---

## 🧪 Advanced Usage

### Custom Test Sets
Create a JSON file in `src/data/testsets/` with your custom prompts.
```json
{
  "id": "my-custom-set",
  "questions": [
    { "id": "q1", "prompt": "Explain quantum physics", "difficulty": "hard" }
  ]
}
```
Run it with:
```bash
python src/main.py run-test --model llama3 --test-set my-custom-set
```

### OpenAI-Compatible Endpoints
Test vLLM, LM Studio, or other providers:
```bash
python src/main.py run-test \
  --provider openai \
  --base-url "http://localhost:8000/v1" \
  --model "local-model-name"
```
