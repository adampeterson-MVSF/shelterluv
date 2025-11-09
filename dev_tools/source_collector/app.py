"""
Source Code Collector Flask Application.
Clean separation of concerns with modular design.
"""

import os
from pathlib import Path
from flask import Flask, render_template, request, jsonify, send_file
from werkzeug.utils import secure_filename
import tempfile
import io

from scanner import scan_directory

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/scan', methods=['POST'])
def scan():
    data = request.get_json()
    directory = data.get('directory', '')

    if not directory or not Path(directory).exists():
        return jsonify({'error': 'Directory not found'}), 404

    try:
        scanned_files = scan_directory(directory)
        return jsonify({'files': scanned_files})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/combine', methods=['POST'])
def combine():
    data = request.get_json()
    selected_files = data.get('selectedFiles', [])
    include_structure = data.get('includeStructure', True)
    include_metadata = data.get('includeMetadata', True)

    if not selected_files:
        return jsonify({'error': 'No files selected'}), 400

    try:
        # Get the directory from the first file path
        first_file = selected_files[0]
        base_dir = None
        for root, dirs, files_in_dir in os.walk('.'):
            for file in files_in_dir:
                if first_file in os.path.join(root, file):
                    base_dir = root
                    break
            if base_dir:
                break

        if not base_dir:
            return jsonify({'error': 'Could not determine base directory'}), 500

        output = ''

        # Add structure overview
        if include_structure:
            output += 'PROJECT STRUCTURE:\n'
            output += '==================\n\n'

            structure = {}
            for file_path in selected_files:
                full_path = Path(base_dir) / file_path
                if full_path.exists():
                    try:
                        content = full_path.read_text(encoding='utf-8', errors='ignore')
                        lines = len(content.split('\n'))
                        size = full_path.stat().st_size

                        parts = file_path.split('/')
                        current = structure
                        for i, part in enumerate(parts):
                            if part not in current:
                                current[part] = {}
                            if i == len(parts) - 1:
                                current[part] = {'__file': True, 'size': size, 'lines': lines}
                            else:
                                current = current[part]
                    except Exception:
                        continue

            def print_structure(obj, prefix='', is_last=True):
                keys = [k for k in obj.keys() if not k.startswith('__')]
                keys.sort()
                lines = []
                for i, key in enumerate(keys):
                    val = obj[key]
                    last = i == len(keys) - 1
                    connector = '└── ' if last else '├── '

                    if isinstance(val, dict) and val.get('__file'):
                        size_kb = (val['size'] / 1024)
                        lines.append(f"{prefix}{connector}{key} ({size_kb:.1f} KB, {val['lines']} lines)")
                    else:
                        lines.append(f"{prefix}{connector}{key}/")
                        new_prefix = prefix + ('    ' if last else '│   ')
                        lines.extend(print_structure(val, new_prefix, last))
                return lines

            output += '\n'.join(print_structure(structure)) + '\n\n'

        # Process each file
        for file_path in selected_files:
            full_path = Path(base_dir) / file_path
            if full_path.exists():
                try:
                    content = full_path.read_text(encoding='utf-8', errors='ignore')
                    lines = len(content.split('\n'))
                    size = full_path.stat().st_size

                    output += f"\n{'='*60}\n"
                    output += f"FILE: {file_path}\n"
                    if include_metadata:
                        output += f"SIZE: {(size / 1024):.1f} KB | LINES: {lines}\n"
                    output += f"{'='*60}\n\n"
                    output += content + '\n'
                except Exception as e:
                    output += f"\n{'='*60}\n"
                    output += f"FILE: {file_path}\n"
                    output += f"ERROR: Could not read file - {e}\n"
                    output += f"{'='*60}\n\n"

        # Return as downloadable file
        return send_file(
            io.BytesIO(output.encode('utf-8')),
            mimetype='text/plain',
            as_attachment=True,
            download_name='source-code-collection.txt'
        )

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("Source Code Collector - Python Version")
    print("Starting web server on http://localhost:5000")
    print("Open your browser and navigate to the URL above")
    app.run(debug=True, host='0.0.0.0', port=5000)
