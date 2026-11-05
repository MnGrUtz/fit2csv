# fit2csv - Convert Garmin FIT Files to CSV

A simple tool to convert Garmin FIT files (from MyWhoosh, Garmin, or other cycling apps) into easy-to-read CSV files for analysis in Excel, Google Sheets, or any data analysis tool.

## 🚀 Quick Start

### 1. Install Python

You need **Python 3.10 or higher** installed on your computer.

- **Windows/Mac**: Download from [python.org](https://www.python.org/downloads/)
- **Linux**: Usually pre-installed, or use `sudo apt install python3`

### 2. Install the Required Package

Open a terminal/command prompt and run:

```bash
pip install fitdecode
```

### 3. Download fit2csv

Download the `fit2csv.py` file from this repository and save it to a folder on your computer.

### 4. Convert Your FIT File

Run this command (replace the file names with your own):

```bash
python fit2csv.py YourActivity.fit -o output_folder
```

This will create several CSV files in the `output_folder`:
- `YourActivity_records.csv` - Detailed second-by-second data
- `YourActivity_laps.csv` - Lap summaries
- `YourActivity_session.json` - Activity overview
- `YourActivity_events.csv` - Event markers

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

### Common Questions

**Q: What is a FIT file?**
A: FIT is Garmin's file format for storing activity data (power, heart rate, GPS, etc.). It's like a CSV but binary (smaller file size).

**Q: Where do I get FIT files?**
A: From your Garmin device, MyWhoosh app, Strava (export), or other cycling apps.

**Q: Why are some values empty?**
A: Not all activities record all data. If your sensor didn't measure temperature, those cells will be empty.

**Q: Can I use this for running?**
A: Yes! It works with any FIT file, including running, cycling, swimming, etc.

## 📧 Support

If you have any issues:
1. Make sure you have Python 3.10+
2. Make sure you installed fitdecode: `pip install fitdecode`
3. Check that your FIT file is not corrupted

For bugs or questions, please open an issue on GitHub.

---

**Happy analyzing! 🚴‍♂️**
