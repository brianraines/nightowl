# NightOwl

Pull sleep data from the Oura API and persist it to CSV over time.

## Features

* Consistent CLI for fetching sleep data from the Oura API
* Automatic CSV persistence with duplicate detection
* Interactive HTML dashboard generation with Plotly
* Configurable date ranges and output paths
* Simple API client abstraction ready for extension

## Prerequisites

* Python 3.9 or newer
* Access to the Oura API, including a valid Personal Access Token

## Installation

```bash
git clone https://github.com/brianraines/nightowl.git
cd nightowl
python3 -m venv .venv
. .venv/bin/activate
make install-dev  # installs runtime + dev tools
```

> For runtime dependencies only: `make install`

## Configuration

Set the Oura Personal Access Token so the CLI can authenticate:

```bash
export OURA_ACCESS_TOKEN="YOUR_ACCESS_TOKEN"
```

### Creating a Personal Access Token

To get a Personal Access Token:

1. Visit [Oura Cloud Personal Access Tokens](https://cloud.ouraring.com/personal-access-tokens)
2. Log in to your Oura account if prompted
3. Click "Create Token" or "Generate New Token"
4. Give your token a descriptive name (e.g., "NightOwl CLI")
5. Select the appropriate permissions (at minimum, you'll need access to sleep data)
6. Copy the generated token immediately (you won't be able to see it again)
7. Store it securely in your environment variables or `.envrc` file

**Important**: Keep your token secure and never commit it to version control. The `.envrc` file is already gitignored for this purpose.

### Using direnv (Recommended)

If you use [direnv](https://direnv.net/), you can store your token in `.envrc`:

```bash
export OURA_ACCESS_TOKEN="your-token-here"
```

Then run `direnv allow` in the project directory to load it automatically.

## Usage

The easiest way to run NightOwl is using the Makefile:

```bash
make run  # Fetches last 7 days of sleep data
```

Or run the script directly with custom arguments:

```bash
# Using the wrapper script directly (executable)
./nightowl.py --days 7

# Using Python explicitly
python nightowl.py --days 7

# Using the module entrypoint
python -m nightowl --days 7

# Using the installed console script
nightowl --days 7
```

### Arguments

* `-s`, `--start-date`: Start date in YYYY-MM-DD format. Defaults to `--days` days ago when omitted.
* `-e`, `--end-date`: End date in YYYY-MM-DD format. Defaults to today when omitted.
* `-d`, `--days`: Number of days to fetch if dates not specified. Defaults to `7`.
* `-o`, `--output`: Path to CSV output file. Defaults to `exports/sleep_data.csv`.
* `--overwrite`: Overwrite existing CSV file instead of appending.
* `--debug`: Enable debug logging.

### Examples

Fetch the last 7 days of sleep data:
```bash
make run
# or
./nightowl.py
```

Fetch a specific date range:
```bash
./nightowl.py --start-date 2024-01-01 --end-date 2024-01-31
```

Fetch last 30 days and save to custom location:
```bash
./nightowl.py --days 30 --output exports/my_sleep.csv
```

Overwrite existing file:
```bash
./nightowl.py --overwrite
```

## CSV Output Format

The CSV file includes the following fields (when available):

* `date` - Date of the sleep record (YYYY-MM-DD)
* `score` - Overall sleep score
* `total_sleep_duration` - Total sleep duration in seconds
* `total_sleep_time` - Total sleep time in seconds
* `time_in_bed` - Time spent in bed in seconds
* `awake_time` - Time awake in seconds
* `rem_sleep_duration` - REM sleep duration in seconds
* `deep_sleep_duration` - Deep sleep duration in seconds
* `light_sleep_duration` - Light sleep duration in seconds
* `average_breath` - Average breathing rate
* `average_heart_rate` - Average heart rate
* `average_hrv` - Average heart rate variability
* `lowest_heart_rate` - Lowest heart rate
* `highest_heart_rate` - Highest heart rate
* `contributor_*` - Various contributor scores (e.g., `contributor_total`, `contributor_efficiency`)
* `phases_count` - Number of sleep phase measurements

## Dashboard

After saving sleep data, NightOwl automatically generates an interactive HTML dashboard using Plotly. The dashboard includes:

* **Total Sleep Duration** - Time series showing sleep duration trends over time
* **Sleep Stages Breakdown** - Average distribution of deep, REM, and light sleep
* **Heart Rate Trends** - Average and lowest heart rate over time
* **Heart Rate Variability** - HRV trends
* **Breathing Rate** - Average breathing rate trends
* **Time in Bed vs Sleep** - Comparison of time in bed vs actual sleep duration

The dashboard is saved as `exports/nightowl_dashboard.html`. Open it in any web browser to explore your sleep data interactively.

**Note**: Dashboard generation requires `plotly` and `pandas`, which are included in the default installation. If these are not available, the script will continue without generating a dashboard.

## Development

* CLI entrypoint: `nightowl/cli.py`
* API client: `nightowl/api.py`
* CSV storage: `nightowl/storage.py`
* Dashboard generation: `nightowl/dashboard.py`

To add new features or extend functionality, modify the respective modules and update tests accordingly.

### Common Development Tasks

```bash
make install-dev  # Install with development dependencies
make format       # Format code with black and ruff
make lint         # Run linting checks
make test         # Run test suite
make clean        # Remove build artifacts
make run          # Run the CLI script
```

See `make help` for all available targets.

## Testing

Run tests:
```bash
make test
```

Run with coverage report:
```bash
pytest --cov=nightowl --cov-report=html
```

## Code Quality

Format code:
```bash
make format
```

Lint code:
```bash
make lint
```

Clean build artifacts:
```bash
make clean
```

## Project Structure

```
nightowl/
├── nightowl/          # Main package
│   ├── __init__.py
│   ├── cli.py         # CLI interface
│   ├── api.py         # Oura API client
│   └── storage.py     # CSV persistence
├── tests/             # Test suite
│   ├── test_api.py
│   └── test_storage.py
├── exports/                      # Exported data directory (gitignored)
│   ├── sleep_data.csv            # Sleep data CSV file
│   └── nightowl_dashboard.html   # Interactive dashboard
├── nightowl.py        # Entry point script
├── pyproject.toml     # Project configuration
├── Makefile           # Build and test tasks
└── README.md          # This file
```

## License

See LICENSE for details.

## About

A Python application for collecting and persisting Oura sleep data over time.
