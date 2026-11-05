#!/usr/bin/env python3
"""Flask web interface for fit2csv converter.

Usage:
    python app.py [--host 0.0.0.0] [--port 5000]
"""

import argparse
import importlib
import os
import shutil
import sys
import tempfile
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, TYPE_CHECKING

from flask import Flask, render_template, request, redirect, url_for, send_from_directory, flash

# Lazy import for fit2csv module
_fit2csv_module = None


def get_fit2csv():
    """Lazy import of fit2csv module."""
    global _fit2csv_module
    if _fit2csv_module is None:
        _fit2csv_module = importlib.import_module('fit2csv')
    return _fit2csv_module


app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'fit2csv-secret-key-dev')

# Configuration
UPLOAD_FOLDER = tempfile.mkdtemp(prefix='fit2csv_uploads_')
OUTPUT_FOLDER = tempfile.mkdtemp(prefix='fit2csv_output_')
ALLOWED_EXTENSIONS = {'fit', 'FIT'}
MAX_CONTENT_LENGTH = 100 * 1024 * 1024  # 100MB

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['OUTPUT_FOLDER'] = OUTPUT_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH


def allowed_file(filename: str) -> bool:
    """Check if file has allowed extension."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def cleanup_old_files(folder: str, max_age_seconds: int = 3600) -> None:
    """Clean up old files from folder."""
    now = datetime.now().timestamp()
    for filename in os.listdir(folder):
        filepath = os.path.join(folder, filename)
        if os.path.isfile(filepath):
            file_mtime = os.path.getmtime(filepath)
            if now - file_mtime > max_age_seconds:
                try:
                    os.remove(filepath)
                except OSError:
                    pass


@app.route('/', methods=['GET', 'POST'])
def index():
    """Main page with upload form."""
    if request.method == 'POST':
        # Check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part', 'error')
            return redirect(request.url)
        
        file = request.files['file']
        
        # If user does not select file, browser also submits empty part
        if file.filename == '':
            flash('No selected file', 'error')
            return redirect(request.url)
        
        if file and allowed_file(file.filename):
            # Generate unique session ID
            session_id = str(uuid.uuid4())
            session_folder = Path(app.config['OUTPUT_FOLDER']) / session_id
            session_folder.mkdir(parents=True, exist_ok=True)
            
            # Save uploaded file
            upload_filename = f"{session_id}.fit"
            upload_path = Path(app.config['UPLOAD_FOLDER']) / upload_filename
            file.save(upload_path)
            
            # Process the file
            verify = request.form.get('verify') == 'on'
            
            try:
                # Use the existing fit2csv logic
                fit2csv_module = get_fit2csv()
                fit_files = [upload_path]
                success_count = 0
                error_count = 0
                summaries = []
                
                for fit_file in fit_files:
                    try:
                        success, summary = fit2csv_module.process_fit_file(
                            fit_file, session_folder, verify
                        )
                        if success:
                            summaries.append(summary)
                            success_count += 1
                        else:
                            error_count += 1
                    except Exception as e:
                        flash(f'Error processing file: {e}', 'error')
                        error_count += 1
                
                if success_count > 0:
                    # Get list of output files
                    output_files = []
                    for f in session_folder.glob("*"):
                        if f.is_file():
                            output_files.append(f.name)
                    
                    return render_template(
                        'results.html',
                        session_id=session_id,
                        summaries=summaries,
                        output_files=output_files,
                        verify=verify
                    )
                else:
                    flash('Failed to process file', 'error')
                    return redirect(request.url)
                    
            except Exception as e:
                flash(f'Error: {e}', 'error')
                return redirect(request.url)
        else:
            flash('File type not allowed. Please upload .fit files only.', 'error')
            return redirect(request.url)
    
    return render_template('index.html')


@app.route('/download/<session_id>/<filename>')
def download(session_id: str, filename: str):
    """Download converted file."""
    session_folder = Path(app.config['OUTPUT_FOLDER']) / session_id
    return send_from_directory(session_folder, filename, as_attachment=True)


@app.route('/download-all/<session_id>')
def download_all(session_id: str):
    """Download all converted files as zip."""
    import zipfile
    import io
    
    session_folder = Path(app.config['OUTPUT_FOLDER']) / session_id
    
    # Create zip file in memory
    memory_file = io.BytesIO()
    with zipfile.ZipFile(memory_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for f in session_folder.glob("*"):
            if f.is_file():
                zipf.write(f, f.name)
    
    memory_file.seek(0)
    return send_from_directory(
        app.config['OUTPUT_FOLDER'],
        f"{session_id}.zip",
        as_attachment=True,
        mimetype='application/zip'
    )


@app.route('/batch', methods=['GET', 'POST'])
def batch():
    """Batch processing page."""
    if request.method == 'POST':
        if 'files' not in request.files:
            flash('No files part', 'error')
            return redirect(request.url)
        
        files = request.files.getlist('files')
        
        if not files or all(f.filename == '' for f in files):
            flash('No selected files', 'error')
            return redirect(request.url)
        
        # Filter valid files
        valid_files = [f for f in files if f and allowed_file(f.filename)]
        
        if not valid_files:
            flash('No valid .fit files selected', 'error')
            return redirect(request.url)
        
        # Generate unique session ID
        session_id = str(uuid.uuid4())
        session_folder = Path(app.config['OUTPUT_FOLDER']) / session_id
        session_folder.mkdir(parents=True, exist_ok=True)
        
        verify = request.form.get('verify') == 'on'
        
        try:
            uploaded_files = []
            for file in valid_files:
                upload_filename = f"{uuid.uuid4()}.fit"
                upload_path = Path(app.config['UPLOAD_FOLDER']) / upload_filename
                file.save(upload_path)
                uploaded_files.append(upload_path)
            
            # Process all files
            fit2csv_module = get_fit2csv()
            summaries = []
            for fit_file in uploaded_files:
                try:
                    success, summary = fit2csv_module.process_fit_file(
                        fit_file, session_folder, verify
                    )
                    if success:
                        summaries.append(f"{fit_file.name}: {summary}")
                except Exception as e:
                    summaries.append(f"{fit_file.name}: Error - {e}")
            
            # Get list of output files
            output_files = []
            for f in session_folder.glob("*"):
                if f.is_file():
                    output_files.append(f.name)
            
            return render_template(
                'results.html',
                session_id=session_id,
                summaries=summaries,
                output_files=output_files,
                verify=verify,
                is_batch=True
            )
            
        except Exception as e:
            flash(f'Error: {e}', 'error')
            return redirect(request.url)
    
    return render_template('batch.html')


@app.route('/cleanup')
def cleanup():
    """Clean up old files."""
    cleanup_old_files(app.config['UPLOAD_FOLDER'], 3600)
    cleanup_old_files(app.config['OUTPUT_FOLDER'], 3600)
    flash('Old files cleaned up', 'success')
    return redirect(url_for('index'))


@app.teardown_appcontext
def teardown(exception=None):
    """Clean up on app teardown."""
    cleanup_old_files(app.config['UPLOAD_FOLDER'], 0)
    cleanup_old_files(app.config['OUTPUT_FOLDER'], 0)


def main():
    """Run the Flask application."""
    parser = argparse.ArgumentParser(description='Run fit2csv web interface')
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind to')
    parser.add_argument('--port', default=5000, type=int, help='Port to bind to')
    parser.add_argument('--debug', action='store_true', help='Run in debug mode')
    args = parser.parse_args()
    
    app.run(host=args.host, port=args.port, debug=args.debug)


if __name__ == '__main__':
    main()
