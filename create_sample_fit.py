#!/usr/bin/env python3
"""Create a sample FIT file for testing."""

import sys
from datetime import datetime, timezone
from pathlib import Path

# Install fitdecode if not available
try:
    import fitdecode
    from fitdecode import FitFile, FitMessage, FitField
    print("fitdecode is available")
except ImportError:
    print("fitdecode not found, installing...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "fitdecode"])
    import fitdecode
    from fitdecode import FitFile, FitMessage, FitField


def create_sample_fit(output_path: str = "sample.fit") -> None:
    """Create a minimal sample FIT file."""
    
    # Create a FitFile
    fit_file = FitFile()
    
    # Add FILE_ID message
    file_id = FitMessage(0)  # FILE_ID message number
    file_id.add_field(FitField(0, 1))  # type = activity
    file_id.add_field(FitField(1, 12345))  # manufacturer
    file_id.add_field(FitField(2, 1))  # product
    file_id.add_field(FitField(3, 100))  # serial_number
    file_id.add_field(FitField(4, 1))  # time_created
    fit_file.messages.append(file_id)
    
    # Add SESSION message
    session = FitMessage(18)  # SESSION message number
    session.add_field(FitField(0, 1))  # event = start
    session.add_field(FitField(1, 1))  # event_type = start
    session.add_field(FitField(2, 3600))  # start_time (seconds since FIT epoch)
    session.add_field(FitField(3, 3600))  # total_elapsed_time = 1 hour
    session.add_field(FitField(4, 3600))  # total_timer_time = 1 hour
    session.add_field(FitField(5, 1))  # sport = cycling
    session.add_field(FitField(6, 0))  # sub_sport = generic
    session.add_field(FitField(7, 200))  # avg_power = 200W
    session.add_field(FitField(8, 300))  # max_power = 300W
    session.add_field(FitField(9, 150))  # avg_heart_rate = 150 bpm
    session.add_field(FitField(10, 180))  # max_heart_rate = 180 bpm
    session.add_field(FitField(11, 36000))  # total_distance = 36 km in half-meters
    fit_file.messages.append(session)
    
    # Add some RECORD messages (10 seconds of data)
    start_time = 3600
    for i in range(10):
        record = FitMessage(20)  # RECORD message number
        record.add_field(FitField(0, start_time + i))  # timestamp
        record.add_field(FitField(1, 0))  # position_lat
        record.add_field(FitField(2, 0))  # position_long
        record.add_field(FitField(3, 200 + i * 10))  # power = 200-290W
        record.add_field(FitField(4, 150 + i))  # heart_rate = 150-159 bpm
        record.add_field(FitField(5, 90 + i))  # cadence = 90-99 rpm
        record.add_field(FitField(6, 10000 + i * 100))  # speed = ~10-11 m/s in mm/s
        record.add_field(FitField(7, 18000 + i * 100))  # distance in half-meters
        record.add_field(FitField(8, 100 + i))  # altitude in meters
        record.add_field(FitField(9, 50 + i))  # grade in 1/100 percent
        record.add_field(FitField(10, 2000 + i * 10))  # temperature in 0.01°C
        fit_file.messages.append(record)
    
    # Write to file
    with open(output_path, 'wb') as f:
        fit_file.write(f)
    
    print(f"Sample FIT file created: {output_path}")


if __name__ == "__main__":
    output_path = "sample.fit"
    if len(sys.argv) > 1:
        output_path = sys.argv[1]
    
    create_sample_fit(output_path)
