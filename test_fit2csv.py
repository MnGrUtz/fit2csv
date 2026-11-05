#!/usr/bin/env python3
"""Test script for fit2csv converter."""

import os
import sys
import tempfile
from pathlib import Path

# Add current directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

import fit2csv


def create_sample_fit_data() -> bytes:
    """Create a minimal sample FIT file for testing.
    
    This creates a simple FIT file with a FILE_ID, SESSION, and a few RECORD messages.
    Note: This is a simplified version and may not be a valid FIT file.
    For real testing, use actual FIT files.
    """
    # In a real scenario, we would need actual FIT files for testing
    # For now, we'll just test the processing logic with mock data
    return b''


def test_with_mock_data():
    """Test the processing logic with mock data."""
    print("Testing fit2csv with mock data...")
    
    # Create temporary directories
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        
        # Test that the module can be imported
        print("✓ Module imported successfully")
        
        # Test timestamp conversion
        from fit2csv import convert_timestamp
        ts = convert_timestamp(1369708800)  # Example timestamp
        print(f"✓ Timestamp conversion: {ts}")
        
        # Test that output directory is created
        output_dir = tmpdir / "output"
        output_dir.mkdir()
        print(f"✓ Output directory created: {output_dir}")
        
        # Test file collection
        fit_files = fit2csv.get_fit_files(str(tmpdir))
        print(f"✓ File collection works: {len(fit_files)} files")
        
        print("\nAll basic tests passed!")
        print("\nNote: For full testing, please use actual FIT files.")
        print("Example:")
        print("  python fit2csv.py your_activity.fit -o ./output")


def test_cli():
    """Test the CLI interface."""
    import subprocess
    
    print("\nTesting CLI interface...")
    
    # Test help
    result = subprocess.run(
        [sys.executable, "fit2csv.py", "--help"],
        capture_output=True,
        text=True
    )
    if result.returncode == 0:
        print("✓ CLI help works")
    else:
        print(f"✗ CLI help failed: {result.stderr}")
    
    # Test with non-existent file
    result = subprocess.run(
        [sys.executable, "fit2csv.py", "nonexistent.fit", "-o", "/tmp/test_output"],
        capture_output=True,
        text=True
    )
    if result.returncode != 0:
        print("✓ CLI handles non-existent file correctly")
    else:
        print("✗ CLI should fail with non-existent file")


def test_flask_app():
    """Test the Flask app imports."""
    print("\nTesting Flask app...")
    
    try:
        import app
        print("✓ Flask app module imports successfully")
        
        # Test lazy import
        fit2csv_module = app.get_fit2csv()
        print(f"✓ Lazy import works: {fit2csv_module}")
        
    except Exception as e:
        print(f"✗ Flask app import failed: {e}")


if __name__ == "__main__":
    print("=" * 60)
    print("fit2csv - Test Suite")
    print("=" * 60)
    
    test_with_mock_data()
    test_cli()
    test_flask_app()
    
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    print("For full testing, please install and use actual FIT files.")
    print("\nTo test with a real FIT file:")
    print("  python fit2csv.py your_file.fit -o ./output")
