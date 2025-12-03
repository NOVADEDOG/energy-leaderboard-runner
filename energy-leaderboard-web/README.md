# Energy Leaderboard Web

A modern, static website that displays LLM energy efficiency benchmarks. Built with React, Vite, and Tailwind CSS.

🌐 **Live Site:** [https://NOVADEDOG.github.io/energy-leaderboard-runner/](https://NOVADEDOG.github.io/energy-leaderboard-runner/)

## Features

- **🌿 Eco-Friendly Design** - Clean, minimal interface with green accents
- **🌙 Dark Mode** - Automatic system detection + manual toggle
- **📊 Interactive Table** - Sort by any column, filter by device/method
- **📱 Responsive** - Optimized for desktop and mobile
- **🔍 Search** - Filter models by name
- **📈 Detail View** - Click any model for detailed stats

## Development

```bash
# Navigate to the web directory
cd energy-leaderboard-web

# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

## Adding Benchmark Results

Benchmark results are stored as JSON files in the `public/data/` directory. The website automatically discovers and loads all `.json` files from this directory at build time.

### JSON Schema

Each benchmark result file should follow this schema:

```json
{
  "model": "llama3.2:3b-instruct-q4_K_M",
  "device_name": "Apple M1 Pro Mac (MacBookPro18,3)",
  "device_type": "apple",
  "os_name": "macOS",
  "os_version": "14.2",
  "method": "measured",
  "timestamp": "2025-01-15T10:30:00Z",
  "tokens_per_second": 42.5,
  "watt_hours_per_1k_tokens": 0.0032,
  "grams_co2_per_1k_tokens": 0.0012,
  "watts_average": 12.5,
  "total_tokens": 15000,
  "total_seconds": 352.94,
  "cpu_model": "Apple M1 Pro",
  "gpu_model": "Apple M1 Pro",
  "ram_gb": 16.0,
  "chip_architecture": "arm64",
  "ollama_version": "0.6.6",
  "notes": "Optional notes about the run"
}
```

### Required Fields

| Field | Type | Description |
|-------|------|-------------|
| `model` | string | Model name (e.g., "llama3.2:3b-instruct-q4_K_M") |
| `device_name` | string | Human-readable device name |
| `device_type` | string | One of: `apple`, `nvidia`, `amd`, `intel`, `unknown` |
| `os_name` | string | Operating system (macOS, Linux, Windows) |
| `os_version` | string | OS version string |
| `method` | string | Either "measured" or "estimated" |
| `timestamp` | string | ISO 8601 timestamp |
| `tokens_per_second` | number | Generation speed |
| `watt_hours_per_1k_tokens` | number | Energy efficiency metric |
| `grams_co2_per_1k_tokens` | number | Carbon footprint metric |
| `watts_average` | number | Average power draw |
| `total_tokens` | number | Total tokens generated |
| `total_seconds` | number | Total benchmark duration |

### Optional Fields

| Field | Type | Description |
|-------|------|-------------|
| `cpu_model` | string | CPU model string |
| `gpu_model` | string | GPU model string (if applicable) |
| `ram_gb` | number | System RAM in gigabytes |
| `chip_architecture` | string | CPU architecture (arm64, x86_64) |
| `ollama_version` | string | Ollama version used |
| `notes` | string | Additional notes |

### File Naming

Use descriptive names like:
- `run_apple_m1_llama3.json`
- `run_nvidia_4090_mistral.json`
- `run_intel_i9_phi3.json`

### Contributing Benchmarks

1. Run the [Energy Leaderboard Runner](https://github.com/NOVADEDOG/energy-leaderboard-runner) on your hardware
2. The runner outputs a JSON file with the correct schema
3. Add the JSON file to `public/data/`
4. Submit a pull request

## Deployment

The site is automatically deployed to GitHub Pages when changes are pushed to `main`. The GitHub Actions workflow:

1. Builds the Vite project
2. Uploads the `dist/` folder as an artifact
3. Deploys to GitHub Pages

### Manual Deployment

```bash
# Build the site
npm run build

# The dist/ folder contains the static site
```

## Tech Stack

- **React 18** - UI framework
- **TypeScript** - Type safety
- **Vite 5** - Build tool
- **Tailwind CSS** - Styling
- **@tanstack/react-table** - Table sorting
- **Lucide React** - Icons

## Project Structure

```
energy-leaderboard-web/
├── public/
│   └── data/           # Benchmark JSON files
├── src/
│   ├── components/     # React components
│   ├── lib/            # Utilities and types
│   ├── App.tsx         # Main app component
│   ├── main.tsx        # Entry point
│   └── index.css       # Global styles
├── index.html
├── vite.config.ts
├── tailwind.config.js
└── package.json
```

## License

MIT - See the main repository LICENSE file.
