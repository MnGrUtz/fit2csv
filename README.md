# fit2csv - Convert Garmin FIT Files to CSV

A simple tool to convert Garmin FIT files (from MyWhoosh, Garmin, or other cycling apps) into easy-to-read CSV files for analysis in Excel, Google Sheets, or any data analysis tool.

## 🚀 Quick Start

### Option 1: Command Line (Recommended for most users)

#### 1. Install Python

You need **Python 3.10 or higher** installed on your computer.

- **Windows/Mac**: Download from [python.org](https://www.python.org/downloads/)
- **Linux**: Usually pre-installed, or use `sudo apt install python3`

#### 2. Install the Required Packages

Open a terminal/command prompt and run:

```bash
pip install -r requirements.txt
```

This installs both `fitdecode` (for CLI) and `Flask` (for web interface).

#### 3. Convert Your FIT File

Run this command (replace the file names with your own):

```bash
python fit2csv.py YourActivity.fit -o output_folder
```

This will create several CSV files in the `output_folder`:
- `YourActivity_records.csv` - Detailed second-by-second data
- `YourActivity_laps.csv` - Lap summaries
- `YourActivity_session.json` - Activity overview
- `YourActivity_events.csv` - Event markers

### Option 2: Web Interface (Easier for beginners)

#### 1. Install Python and dependencies (same as above)

#### 2. Start the web server

```bash
python app.py
```

#### 3. Open your browser

Go to: `http://localhost:5000`

#### 4. Upload your FIT file

- Click "Choose File" and select your `.fit` file
- Click "Convert File"
- Download the converted CSV files

You can also use `--host` and `--port` to change the server settings:

```bash
python app.py --host 0.0.0.0 --port 8080
```

## 📖 What You Get

### Records CSV (Main File)
This is the most important file. It contains **one row for every second** of your activity with:

| Column | What It Means | Unit |
|--------|---------------|------|
| `elapsed_s` | Seconds into the activity | seconds |
| `timestamp_iso8601` | Date and time | - |
| `power_w` | Power output | watts |
| `heart_rate_bpm` | Heart rate | beats per minute |
| `cadence_rpm` | Pedal cadence | revolutions per minute |
| `speed_mps` | Speed | meters per second |
| `distance_m` | Distance traveled | meters |
| `altitude_m` | Elevation | meters |
| `grade_percent` | Hill steepness | % |
| `temperature_c` | Temperature | °C |

### Laps CSV
Summary for each lap:
- Average and maximum power
- Average and maximum heart rate
- Distance per lap
- Lap name

### Session JSON
Overall activity summary:
- Total duration
- Total distance
- Average power and heart rate
- Activity type (cycling, running, etc.)

### Events CSV
Markers for events like:
- Activity start/stop
- Pauses
- Auto-pauses

## 💡 Tips

### Convert Multiple Files at Once

```bash
python fit2csv.py folder_with_fit_files/ -o output_folder/
```

This will convert ALL `.fit` files in the folder.

### Verify File Integrity

Add `--verify` to check if the FIT file is not corrupted:

```bash
python fit2csv.py YourActivity.fit -o output_folder/ --verify
```

### Open in Excel

1. Open Excel
2. Go to **Data** > **From Text/CSV**
3. Select your `*_records.csv` file
4. Click **Load**

### Convert Temperature to Fahrenheit

The CSV files use Celsius (°C). To convert to Fahrenheit:

```
°F = (°C × 9/5) + 32
```

## 📧 Common Questions

**Q: What is a FIT file?**
A: FIT is Garmin's file format for storing activity data (power, heart rate, GPS, etc.). It's like a CSV but binary (smaller file size).

**Q: Where do I get FIT files?**
A: From your Garmin device, MyWhoosh app, Strava (export), or other cycling apps.

**Q: Why are some values empty?**
A: Not all activities record all data. If your sensor didn't measure temperature, those cells will be empty.

**Q: Can I use this for running?**
A: Yes! It works with any FIT file, including running, cycling, swimming, etc.

**Q: Do I need both CLI and Web Interface?**
A: No, you can use either one. The CLI is faster for batch processing, the Web Interface is easier for single files.

## 🔄 Keeping Up to Date

The `distro` branch contains the stable, user-friendly version of fit2csv. To update:

### For Git Users:

```bash
# Navigate to your fit2csv folder
cd fit2csv

# Pull the latest changes from distro branch
git fetch origin
git checkout distro
git pull origin distro
```

### For Non-Git Users:

1. Visit: [https://github.com/MnGrUtz/fit2csv/tree/distro](https://github.com/MnGrUtz/fit2csv/tree/distro)
2. Download the files you need:
   - `fit2csv.py` (required for CLI)
   - `app.py` (required for Web Interface)
   - `templates/` folder (required for Web Interface)
   - `requirements.txt` (required)
   - `README.md` (optional)
3. Replace your old files with the new ones

### Version Compatibility:

- **Python**: 3.10 or higher
- **fitdecode**: Automatically installed via requirements.txt
- **Flask**: Automatically installed via requirements.txt (only needed for Web Interface)

After updating, reinstall dependencies:

```bash
pip install -r requirements.txt
```

## 🐛 Troubleshooting

**Problem: `python: command not found`**

Solution: Python is not installed or not in your PATH. Install Python from [python.org](https://www.python.org/downloads/) and make sure to check "Add Python to PATH" during installation.

**Problem: `pip: command not found`**

Solution: pip should come with Python 3. Try `python -m pip install fitdecode` instead.

**Problem: ModuleNotFoundError: No module named 'fitdecode'**

Solution: Run `pip install -r requirements.txt` to install all dependencies.

**Problem: The program crashes or gives errors**

Solution: Make sure you're using Python 3.10 or higher. Check with `python --version`.

## 📧 Support

If you have any issues that aren't covered above:
1. Make sure you're using the latest version from the `distro` branch
2. Make sure you have Python 3.10+
3. Make sure you installed dependencies: `pip install -r requirements.txt`
4. Check that your FIT file is not corrupted

For bugs or questions, please open an issue on GitHub.

---

**Happy analyzing! 🚴‍♂️**
