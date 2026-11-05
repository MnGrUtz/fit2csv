# fit2csv - Garmin FIT to CSV/JSON Converter

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](https://opensource.org/licenses/MIT)

A command-line tool and web interface for converting Garmin FIT (Flexible and Interchange Protocol) files to tabular CSV and JSON formats for analysis.

## Features

- **Raw Data Preservation**: No smoothing, interpolation, or aggregation - outputs exact data from FIT files
- **Multiple Output Formats**:
  - `*_records.csv` - Second-by-second data (power, heart rate, speed, etc.)
  - `*_laps.csv` - Lap summary data
  - `*_session.json` - Session metadata and totals
  - `*_events.csv` - Event markers (pauses, auto-pauses, etc.)
- **Batch Processing**: Convert multiple FIT files at once
- **Data Validation**: Automatic consistency checks with warnings
- **Unit Conversion**: Correct conversion of FIT-specific units (distance, temperature, speed)
- **FIT Checksum Verification**: Optional validation of file integrity
- **Web Interface**: Flask-based GUI for easy file upload and conversion

## Installation

### Prerequisites

- Python 3.10 or higher
- pip (Python package manager)

### Install from Source

```bash
# Clone the repository
git clone https://github.com/MnGrUtz/fit2csv.git
cd fit2csv

# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Usage

### Command Line Interface

#### Single File Conversion

```bash
python fit2csv.py activity.fit -o output_directory/
```

#### Batch Processing (Directory)

```bash
python fit2csv.py /path/to/fit/files/ -o output_directory/ --verify
```

#### Options

- `-o, --output`: Output directory (required)
- `--verify`: Verify FIT checksum (optional)

#### Examples

```bash
# Convert single file
python fit2csv.py my_ride.fit -o ./output

# Convert all FIT files in a directory
python fit2csv.py ./rides/ -o ./output

# Convert with checksum verification
python fit2csv.py my_ride.fit -o ./output --verify

# Batch convert with verification
python fit2csv.py ./rides/ -o ./output --verify
```

### Web Interface

Start the Flask web application:

```bash
python app.py
```

Then open your browser to `http://localhost:5000`

#### Options

- `--host`: Host to bind to (default: 0.0.0.0)
- `--port`: Port to bind to (default: 5000)
- `--debug`: Run in debug mode

#### Examples

```bash
# Start on localhost
python app.py

# Start on specific host and port
python app.py --host 0.0.0.0 --port 8080

# Start in debug mode
python app.py --debug
```

## Output Files

### Records CSV (`*_records.csv`)

Contains second-by-second data with the following columns:

| Column | Description | Unit |
|--------|-------------|------|
| `elapsed_s` | Seconds since first record | seconds |
| `timestamp_iso8601` | UTC timestamp | ISO 8601 |
| `power_w` | Power | watts |
| `heart_rate_bpm` | Heart rate | beats per minute |
| `cadence_rpm` | Cadence | revolutions per minute |
| `speed_mps` | Speed | meters per second |
| `distance_m` | Distance | meters |
| `altitude_m` | Altitude | meters |
| `grade_percent` | Grade | percent |
| `temperature_c` | Temperature | °C |

### Laps CSV (`*_laps.csv`)

Contains lap summary data:

| Column | Description | Unit |
|--------|-------------|------|
| `message_index` | Lap message index | - |
| `start_iso8601` | Lap start time | ISO 8601 |
| `elapsed_time_s` | Elapsed time for this lap | seconds |
| `total_timer_time_s` | Total timer time | seconds |
| `avg_power_w` | Average power | watts |
| `max_power_w` | Maximum power | watts |
| `avg_heart_rate_bpm` | Average heart rate | bpm |
| `max_heart_rate_bpm` | Maximum heart rate | bpm |
| `avg_cadence_rpm` | Average cadence | rpm |
| `total_distance_m` | Total distance | meters |
| `lap_name` | Lap name | - |

### Session JSON (`*_session.json`)

Contains session metadata including:

- Start time
- Sport type
- Total duration
- Average/maximum power
- Average/maximum heart rate
- Total work
- Total distance
- File metadata from FILE_ID message

### Events CSV (`*_events.csv`)

Contains event markers:

| Column | Description | Unit |
|--------|-------------|------|
| `timestamp_iso8601` | Event timestamp | ISO 8601 |
| `event_type` | Event type | - |
| `event` | Event code | - |
| `name` | Event name | - |
| `data` | Event data | - |

## Data Validation

The tool performs automatic validation:

1. **Record Count**: Checks if the number of records is plausible compared to total timer time (±5% tolerance)
2. **Power Average**: Compares calculated average power from records with session average (±1% tolerance)
3. **Heart Rate Average**: Compares calculated average heart rate from records with session average (±1% tolerance)

Warnings are printed to stderr if any validation fails, but files are still written.

## Unit Conversion

FIT files store values in specific units that are converted to standard units:

- **Distance**: FIT stores in half-meters → converted to meters (× 0.5)
- **Temperature**: FIT stores in 0.01°C units → converted to °C (× 0.01)
- **Speed**: FIT stores in mm/s → converted to m/s (× 1000/3600)
- **Grade**: FIT stores as fraction → converted to percentage (× 100)

## Technical Details

### Lazy Imports

The tool uses lazy imports for the `fitdecode` module to optimize startup time and memory usage, especially in the Flask web interface where the module is only loaded when needed.

### Performance

- Single file conversion: < 1 second for typical 1-hour activities
- Batch processing: Linear time based on number of files
- Memory usage: Minimal, processes files sequentially

### Error Handling

- Corrupt or invalid FIT files: Clear error message on stderr, exit code 1
- Missing fields: Empty cells in output
- Unknown message types: Silently ignored
- Batch processing: Continues with other files if one fails

## Testing

The tool has been tested with:

- MyWhoosh exports (Trainer sessions with power and heart rate)
- Garmin device exports
- Various activity types (cycling, running, etc.)

### Test with Sample Data

To test with your own FIT files:

```bash
# Convert a sample file
python fit2csv.py sample.fit -o ./test_output

# Check the output
ls -la ./test_output
cat ./test_output/sample_records.csv | head -5
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [fitdecode](https://github.com/potmop/fitdecode) - Python library for decoding Garmin FIT files
- [Flask](https://flask.palletsprojects.com/) - Web framework for the GUI
- Garmin - For the FIT file format specification

## Changelog

### v1.0.0

- Initial release
- CLI and web interface
- Full FIT to CSV/JSON conversion
- Data validation
- Lazy imports for performance
