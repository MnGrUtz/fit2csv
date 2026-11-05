#!/usr/bin/env python3
"""fit2csv - Convert Garmin FIT files to CSV/JSON format for analysis.

Usage:
    python fit2csv.py <input.fit> -o <outdir> [--verify]
    python fit2csv.py <input_dir> -o <outdir> [--verify]
"""

import argparse
import csv
import importlib
import json
import os
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, TYPE_CHECKING

# Lazy import for fitdecode
_fitdecode_module = None


def get_fitdecode():
    """Lazy import of fitdecode module."""
    global _fitdecode_module
    if _fitdecode_module is None:
        _fitdecode_module = importlib.import_module('fitdecode')
    return _fitdecode_module


def decode_fit_data(fit_data: bytes) -> List[Any]:
    """Decode FIT data using the appropriate API for the installed version."""
    fitdecode_module = get_fitdecode()
    
    # Try new API (FitReader) first (version 0.11.0+)
    if hasattr(fitdecode_module, 'FitReader'):
        messages = []
        import io
        with fitdecode_module.FitReader(io.BytesIO(fit_data)) as fit:
            for frame in fit:
                if frame.frame_type == fitdecode_module.FIT_FRAME_DATA:
                    messages.append(frame)
        return messages
    else:
        # Fall back to old API (decode function)
        return list(fitdecode_module.decode(fit_data))


# Constants for FIT field scaling
DISTANCE_SCALE = 0.5  # FIT stores distance in half-meters
TEMPERATURE_SCALE = 0.01  # FIT stores temperature in 0.01°C units
SPEED_SCALE = 1000 / 3600  # FIT stores speed in mm/s, convert to m/s

# Required column names for output files
RECORDS_COLUMNS = [
    "elapsed_s",
    "timestamp_iso8601",
    "power_w",
    "heart_rate_bpm",
    "cadence_rpm",
    "speed_mps",
    "distance_m",
    "altitude_m",
    "grade_percent",
    "temperature_c",
]

LAPS_COLUMNS = [
    "message_index",
    "start_iso8601",
    "elapsed_time_s",
    "total_timer_time_s",
    "avg_power_w",
    "max_power_w",
    "avg_heart_rate_bpm",
    "max_heart_rate_bpm",
    "avg_cadence_rpm",
    "total_distance_m",
    "lap_name",
]

EVENTS_COLUMNS = ["timestamp_iso8601", "event_type", "event", "name", "data"]


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Convert Garmin FIT files to CSV/JSON format"
    )
    parser.add_argument(
        "input",
        type=str,
        help="Input FIT file or directory containing FIT files",
    )
    parser.add_argument(
        "-o", "--output",
        type=str,
        required=True,
        help="Output directory",
    )
    parser.add_argument(
        "--verify",
        action="store_true",
        help="Verify FIT checksum",
    )
    return parser.parse_args()


def get_fit_files(input_path: str) -> List[Path]:
    """Get list of FIT files from input path."""
    path = Path(input_path)
    if path.is_file() and path.suffix.lower() == ".fit":
        return [path]
    elif path.is_dir():
        return sorted(path.glob("*.fit"))
    else:
        print(f"Error: {input_path} is not a valid FIT file or directory", file=sys.stderr)
        sys.exit(1)


def convert_timestamp(ts: Optional[Any]) -> str:
    """Convert FIT timestamp to ISO 8601.
    
    Handles both float timestamps (seconds since FIT epoch) and datetime objects.
    """
    if ts is None:
        return ""
    # If already a datetime object
    if hasattr(ts, 'strftime'):
        return ts.strftime("%Y-%m-%dT%H:%M:%SZ")
    # FIT timestamp is seconds since 1989-12-31 00:00:00 UTC
    fit_epoch = datetime(1989, 12, 31, tzinfo=timezone.utc)
    dt = fit_epoch + timedelta(seconds=ts)
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def get_field_value(message: Any, field_name: str) -> Any:
    """Get field value from FIT message, handling None and scaling.
    
    Supports both old API (dict-like messages) and new API (FitDataMessage with fields).
    """
    # New API: message has 'fields' attribute
    if hasattr(message, 'fields'):
        for field in message.fields:
            if field.name == field_name:
                return field.value
        return None
    # Old API: message is dict-like
    elif hasattr(message, '__getitem__'):
        if field_name in message:
            return message[field_name]
        return None
    return None


def process_fit_file(
    fit_path: Path, output_dir: Path, verify: bool = False
) -> Tuple[bool, str]:
    """Process a single FIT file and generate output files.
    
    Returns:
        Tuple of (success, summary_message)
    """
    stem = fit_path.stem
    
    try:
        # Read and decode FIT file
        with open(fit_path, "rb") as f:
            fit_data = f.read()
        
        # Verify checksum if requested
        fitdecode_module = get_fitdecode()
        if verify:
            try:
                if hasattr(fitdecode_module, 'checksum'):
                    fitdecode_module.checksum.verify_checksum(fit_data)
                else:
                    # New API: use FitReader with check_crc parameter
                    import io
                    with fitdecode_module.FitReader(
                        io.BytesIO(fit_data), 
                        check_crc=fitdecode_module.CrcCheck.RAISE
                    ) as fit:
                        for frame in fit:
                            pass  # Just iterate to trigger verification
            except Exception as e:
                print(f"Warning: Checksum verification failed for {fit_path.name}: {e}", file=sys.stderr)
        
        # Decode all messages
        messages = decode_fit_data(fit_data)
        
    except Exception as e:
        print(f"Error reading {fit_path.name}: {e}", file=sys.stderr)
        return False, ""
    
    # Collect messages by type
    records: List[Any] = []
    laps: List[Any] = []
    sessions: List[Any] = []
    events: List[Any] = []
    file_ids: List[Any] = []
    
    for msg in messages:
        # New API: msg is a FitDataMessage with a 'name' attribute
        msg_name = getattr(msg, 'name', None)
        if msg_name == 'record':
            records.append(msg)
        elif msg_name == 'lap':
            laps.append(msg)
        elif msg_name == 'session':
            sessions.append(msg)
        elif msg_name == 'event':
            events.append(msg)
        elif msg_name == 'file_id':
            file_ids.append(msg)
    
    # Get start timestamp for elapsed time calculation
    first_record_ts = None
    if records:
        first_record = records[0]
        ts = get_field_value(first_record, "timestamp")
        if ts is not None:
            # Convert to FIT timestamp format (seconds since 1989-12-31)
            if hasattr(ts, 'timestamp'):
                # It's a datetime object, convert to FIT timestamp
                dt = ts
                fit_epoch = datetime(1989, 12, 31, tzinfo=timezone.utc)
                first_record_ts = (dt - fit_epoch).total_seconds()
            else:
                first_record_ts = ts
    
    # Process records
    records_data = process_records(records, first_record_ts)
    
    # Process laps
    laps_data = process_laps(laps)
    
    # Process session and file_id for JSON
    session_data = process_session(sessions, file_ids)
    
    # Process events
    events_data = process_events(events)
    
    # Write output files
    output_dir.mkdir(parents=True, exist_ok=True)
    
    records_path = output_dir / f"{stem}_records.csv"
    laps_path = output_dir / f"{stem}_laps.csv"
    session_path = output_dir / f"{stem}_session.json"
    events_path = output_dir / f"{stem}_events.csv"
    
    write_csv(records_path, RECORDS_COLUMNS, records_data)
    write_csv(laps_path, LAPS_COLUMNS, laps_data)
    write_json(session_path, session_data)
    write_csv(events_path, EVENTS_COLUMNS, events_data)
    
    # Perform validation
    validation_warnings = validate_data(
        records_data, laps_data, session_data, sessions, records
    )
    for warning in validation_warnings:
        print(f"Warning for {fit_path.name}: {warning}", file=sys.stderr)
    
    # Generate summary
    summary = generate_summary(records_data, session_data)
    
    return True, summary


def process_records(
    records: List[Any], first_timestamp: Optional[float]
) -> List[Dict[str, Any]]:
    """Process RECORD messages into CSV rows."""
    rows = []
    for i, record in enumerate(records):
        row = {}
        
        # Get timestamp
        ts = get_field_value(record, "timestamp")
        
        # Calculate elapsed time
        if first_timestamp is not None and ts is not None:
            # Handle datetime objects from new API
            if hasattr(ts, 'timestamp'):
                ts_float = ts.timestamp()
                # Convert to FIT timestamp (seconds since 1989-12-31)
                fit_epoch = datetime(1989, 12, 31, tzinfo=timezone.utc)
                ts_float = (ts - fit_epoch).total_seconds()
                elapsed = ts_float - first_timestamp
            else:
                elapsed = ts - first_timestamp
            row["elapsed_s"] = int(elapsed)
        else:
            row["elapsed_s"] = ""
        
        # Timestamp
        ts_raw = get_field_value(record, "timestamp")
        # Handle datetime objects from new API
        if hasattr(ts_raw, 'timestamp'):
            dt = ts_raw
        else:
            dt = convert_timestamp(ts_raw)
        row["timestamp_iso8601"] = dt
        
        # Power
        power = get_field_value(record, "power")
        row["power_w"] = power if power is not None else ""
        
        # Heart rate
        hr = get_field_value(record, "heart_rate")
        row["heart_rate_bpm"] = hr if hr is not None else ""
        
        # Cadence
        cadence = get_field_value(record, "cadence")
        row["cadence_rpm"] = cadence if cadence is not None else ""
        
        # Speed (convert from mm/s to m/s)
        speed = get_field_value(record, "speed")
        if speed is not None:
            row["speed_mps"] = round(speed * SPEED_SCALE, 6)
        else:
            row["speed_mps"] = ""
        
        # Distance (convert from half-meters to meters)
        distance = get_field_value(record, "distance")
        if distance is not None:
            row["distance_m"] = distance * DISTANCE_SCALE
        else:
            row["distance_m"] = ""
        
        # Altitude
        altitude = get_field_value(record, "altitude")
        row["altitude_m"] = altitude if altitude is not None else ""
        
        # Grade (percentage)
        grade = get_field_value(record, "grade")
        if grade is not None:
            row["grade_percent"] = grade * 100  # Convert from fraction to percentage
        else:
            row["grade_percent"] = ""
        
        # Temperature (convert from 0.01°C to °C)
        temp = get_field_value(record, "temperature")
        if temp is not None:
            row["temperature_c"] = temp * TEMPERATURE_SCALE
        else:
            row["temperature_c"] = ""
        
        rows.append(row)
    
    return rows


def process_laps(laps: List[Any]) -> List[Dict[str, Any]]:
    """Process LAP messages into CSV rows."""
    rows = []
    for i, lap in enumerate(laps):
        row = {}
        
        row["message_index"] = i
        
        # Start time
        start_time_raw = get_field_value(lap, "start_time")
        # Handle datetime objects
        if hasattr(start_time_raw, 'strftime'):
            row["start_iso8601"] = start_time_raw.strftime("%Y-%m-%dT%H:%M:%SZ")
        else:
            row["start_iso8601"] = convert_timestamp(start_time_raw)
        
        # Elapsed time
        elapsed = get_field_value(lap, "elapsed_time")
        row["elapsed_time_s"] = elapsed if elapsed is not None else ""
        
        # Total timer time
        total_timer = get_field_value(lap, "total_timer_time")
        row["total_timer_time_s"] = total_timer if total_timer is not None else ""
        
        # Power stats
        avg_power = get_field_value(lap, "avg_power")
        row["avg_power_w"] = avg_power if avg_power is not None else ""
        
        max_power = get_field_value(lap, "max_power")
        row["max_power_w"] = max_power if max_power is not None else ""
        
        # Heart rate stats
        avg_hr = get_field_value(lap, "avg_heart_rate")
        row["avg_heart_rate_bpm"] = avg_hr if avg_hr is not None else ""
        
        max_hr = get_field_value(lap, "max_heart_rate")
        row["max_heart_rate_bpm"] = max_hr if max_hr is not None else ""
        
        # Cadence
        avg_cadence = get_field_value(lap, "avg_cadence")
        row["avg_cadence_rpm"] = avg_cadence if avg_cadence is not None else ""
        
        # Distance (convert from half-meters to meters)
        total_distance = get_field_value(lap, "total_distance")
        if total_distance is not None:
            row["total_distance_m"] = total_distance * DISTANCE_SCALE
        else:
            row["total_distance_m"] = ""
        
        # Lap name
        lap_name = get_field_value(lap, "message_index")  # Often used as lap name
        # Try to get actual lap name if available
        if hasattr(lap, 'lap_name') and lap.lap_name:
            lap_name = lap.lap_name
        row["lap_name"] = lap_name if lap_name is not None else ""
        
        rows.append(row)
    
    return rows


def process_session(
    sessions: List[Any], 
    file_ids: List[Any]
) -> Dict[str, Any]:
    """Process SESSION and FILE_ID messages into JSON."""
    data: Dict[str, Any] = {}
    
    # Process FILE_ID if available
    if file_ids:
        file_id = file_ids[0]
        # New API: file_id has fields attribute
        if hasattr(file_id, 'fields'):
            for field in file_id.fields:
                data[f"file_{field.name}"] = field.value
        else:
            # Old API
            for field in file_id:
                data[f"file_{field}"] = file_id[field]
    
    # Process SESSION if available
    if sessions:
        session = sessions[0]
        # New API: session has fields attribute
        if hasattr(session, 'fields'):
            for field in session.fields:
                # Convert distance fields
                if field.name == "total_distance":
                    val = field.value
                    data[field.name] = val * DISTANCE_SCALE if val is not None else None
                # Convert timestamp fields
                elif field.name.endswith("_time") or field.name == "start_time":
                    val = field.value
                    if hasattr(val, 'strftime'):
                        data[field.name] = val.strftime("%Y-%m-%dT%H:%M:%SZ")
                    else:
                        data[field.name] = convert_timestamp(val) if val is not None else None
                else:
                    data[field.name] = field.value
        else:
            # Old API
            for field in session:
                if field == "total_distance":
                    val = session[field]
                    data[field] = val * DISTANCE_SCALE if val is not None else None
                elif field.endswith("_time") or field == "start_time":
                    val = session[field]
                    data[field] = convert_timestamp(val) if val is not None else None
                else:
                    data[field] = session[field]
    
    return data


def process_events(events: List[Any]) -> List[Dict[str, Any]]:
    """Process EVENT messages into CSV rows."""
    rows = []
    for event in events:
        row = {}
        
        # Timestamp
        ts_raw = get_field_value(event, "timestamp")
        if hasattr(ts_raw, 'strftime'):
            row["timestamp_iso8601"] = ts_raw.strftime("%Y-%m-%dT%H:%M:%SZ")
        else:
            row["timestamp_iso8601"] = convert_timestamp(ts_raw)
        
        # Event type
        event_type = get_field_value(event, "event_type")
        row["event_type"] = event_type if event_type is not None else ""
        
        # Event
        event_val = get_field_value(event, "event")
        row["event"] = event_val if event_val is not None else ""
        
        # Name
        name = get_field_value(event, "event_group")
        row["name"] = name if name is not None else ""
        
        # Data
        data = get_field_value(event, "data")
        row["data"] = data if data is not None else ""
        
        rows.append(row)
    
    return rows


def write_csv(path: Path, columns: List[str], data: List[Dict[str, Any]]) -> None:
    """Write data to CSV file."""
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        for row in data:
            # Convert all values to strings, handling floats
            formatted_row = {}
            for col in columns:
                val = row.get(col, "")
                if val == "":
                    formatted_row[col] = ""
                elif isinstance(val, float):
                    formatted_row[col] = f"{val:.6f}".rstrip("0").rstrip(".")
                else:
                    formatted_row[col] = str(val) if val is not None else ""
            writer.writerow(formatted_row)


def write_json(path: Path, data: Dict[str, Any]) -> None:
    """Write data to JSON file."""
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, default=str, ensure_ascii=False)


def validate_data(
    records: List[Dict[str, Any]],
    laps: List[Dict[str, Any]],
    session: Dict[str, Any],
    session_msgs: List[Any],
    record_msgs: List[Any],
) -> List[str]:
    """Perform validation checks on the data."""
    warnings = []
    
    # Check record count vs total timer time
    if record_msgs and session_msgs:
        session_msg = session_msgs[0]
        total_timer_time = get_field_value(session_msg, "total_timer_time")
        if total_timer_time is not None:
            expected_records = total_timer_time  # 1 Hz = 1 record per second
            actual_records = len(record_msgs)
            
            if expected_records > 0:
                tolerance = 0.05  # 5%
                ratio = actual_records / expected_records
                if abs(ratio - 1.0) > tolerance:
                    warnings.append(
                        f"Record count {actual_records} vs expected {expected_records} "
                        f"(ratio: {ratio:.2f}, tolerance: {tolerance})"
                    )
        
        # Check power average
        session_avg_power = get_field_value(session_msg, "avg_power")
        if session_avg_power is not None and session_avg_power > 0:
                # Calculate average from records
                power_values = [
                    r["power_w"] for r in records if r["power_w"] != "" and r["power_w"] is not None
                ]
                if power_values:
                    calc_avg_power = sum(power_values) / len(power_values)
                    if calc_avg_power > 0:
                        tolerance = 0.01  # 1%
                        ratio = calc_avg_power / session_avg_power
                        if abs(ratio - 1.0) > tolerance:
                            warnings.append(
                                f"Power avg: calculated {calc_avg_power:.2f}W vs session {session_avg_power}W "
                                f"(ratio: {ratio:.2f}, tolerance: {tolerance})"
                            )
        
        # Check heart rate average
        session_avg_hr = get_field_value(session_msg, "avg_heart_rate")
        if session_avg_hr is not None and session_avg_hr > 0:
                # Calculate average from records
                hr_values = [
                    r["heart_rate_bpm"] for r in records 
                    if r["heart_rate_bpm"] != "" and r["heart_rate_bpm"] is not None
                ]
                if hr_values:
                    calc_avg_hr = sum(hr_values) / len(hr_values)
                    if calc_avg_hr > 0:
                        tolerance = 0.01  # 1%
                        ratio = calc_avg_hr / session_avg_hr
                        if abs(ratio - 1.0) > tolerance:
                            warnings.append(
                                f"HR avg: calculated {calc_avg_hr:.2f}bpm vs session {session_avg_hr}bpm "
                                f"(ratio: {ratio:.2f}, tolerance: {tolerance})"
                            )
    
    return warnings


def generate_summary(
    records: List[Dict[str, Any]], session: Dict[str, Any]
) -> str:
    """Generate a summary string for the processed file."""
    record_count = len(records)
    
    # Get duration from session or records
    duration = 0
    if records and "elapsed_s" in records[-1]:
        last_elapsed = records[-1]["elapsed_s"]
        if isinstance(last_elapsed, int):
            duration = last_elapsed
    
    # Get power stats from records
    power_values = [
        r["power_w"] for r in records 
        if r["power_w"] != "" and r["power_w"] is not None and isinstance(r["power_w"], (int, float))
    ]
    avg_power = sum(power_values) / len(power_values) if power_values else 0
    max_power = max(power_values) if power_values else 0
    
    # Get HR stats from records
    hr_values = [
        r["heart_rate_bpm"] for r in records 
        if r["heart_rate_bpm"] != "" and r["heart_rate_bpm"] is not None and isinstance(r["heart_rate_bpm"], (int, float))
    ]
    avg_hr = sum(hr_values) / len(hr_values) if hr_values else 0
    max_hr = max(hr_values) if hr_values else 0
    
    # Format duration
    hours = duration // 3600
    minutes = (duration % 3600) // 60
    seconds = duration % 60
    duration_str = f"{hours}h {minutes}m {seconds}s" if duration > 3600 else f"{minutes}m {seconds}s"
    
    return (
        f"Records: {record_count}, Duration: {duration_str}, "
        f"Avg Power: {avg_power:.0f}W, Max Power: {max_power:.0f}W, "
        f"Avg HR: {avg_hr:.0f}bpm, Max HR: {max_hr:.0f}bpm"
    )


def main() -> None:
    """Main entry point."""
    args = parse_args()
    
    input_path = Path(args.input)
    output_dir = Path(args.output)
    verify = args.verify
    
    # Get FIT files
    fit_files = get_fit_files(args.input)
    
    if not fit_files:
        print(f"Error: No FIT files found in {args.input}", file=sys.stderr)
        sys.exit(1)
    
    # Process each file
    success_count = 0
    error_count = 0
    
    for fit_file in fit_files:
        try:
            success, summary = process_fit_file(fit_file, output_dir, verify)
            if success:
                print(f"{fit_file.name}: {summary}")
                success_count += 1
            else:
                error_count += 1
        except Exception as e:
            print(f"Error processing {fit_file.name}: {e}", file=sys.stderr)
            error_count += 1
    
    # Summary
    print(f"\nProcessed {success_count} files successfully, {error_count} errors")
    
    if error_count > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
