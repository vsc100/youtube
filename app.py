from flask import Flask, request, render_template, send_file, redirect, url_for, jsonify, send_from_directory
from downloader import download_video_or_audio, get_video_formats
import os
import tempfile
import zipfile
import io
import uuid
import threading

app = Flask(__name__)
# Use a temporary directory for downloads
DOWNLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'downloads')

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        url = request.form.get('url')
        mode = request.form.get('mode', 'video')
        quality = request.form.get('quality')
        is_playlist = request.form.get('is_playlist') == 'true'
        progress_id = str(uuid.uuid4())
        try:
            # Start download in a background thread
            def run_download():
                try:
                    filename = download_video_or_audio(url, mode, DOWNLOAD_FOLDER, quality, is_playlist, progress_id)
                    with open(os.path.join(DOWNLOAD_FOLDER, f'{progress_id}.result'), 'w') as f:
                        if isinstance(filename, list):
                            f.write(','.join(filename))
                        else:
                            f.write(filename)
                except Exception as e:
                    # Write error to a .error file
                    with open(os.path.join(DOWNLOAD_FOLDER, f'{progress_id}.error'), 'w') as ef:
                        ef.write(str(e))
            t = threading.Thread(target=run_download)
            t.start()
            return render_template('progress.html', progress_id=progress_id)
        except Exception as e:
            return render_template('index.html', error=str(e))
    return render_template('index.html')

@app.route('/get_formats', methods=['POST'])
def get_formats():
    url = request.json.get('url')
    if not url:
        return jsonify({'error': 'No URL provided'}), 400
    try:
        result = get_video_formats(url)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/progress/<progress_id>')
def progress(progress_id):
    from downloader import get_progress
    percent = get_progress(progress_id)
    result_file = os.path.join(DOWNLOAD_FOLDER, f'{progress_id}.result')
    error_file = os.path.join(DOWNLOAD_FOLDER, f'{progress_id}.error')
    filenames = None
    error_msg = None
    # Check for error file first
    if os.path.exists(error_file):
        with open(error_file) as ef:
            error_msg = ef.read().strip()
        os.remove(error_file)
        return jsonify({'progress': percent, 'error': error_msg})
    # Only return filenames if the file(s) exist on disk
    if percent == 100 and os.path.exists(result_file):
        with open(result_file) as f:
            filenames = f.read().strip()
        all_exist = True
        if filenames:
            file_list = filenames.split(',')
            for fname in file_list:
                if not os.path.exists(os.path.join(DOWNLOAD_FOLDER, fname)):
                    all_exist = False
                    break
        if all_exist:
            os.remove(result_file)
            # If it's a playlist (more than one file), return playlist_files
            if filenames and ',' in filenames:
                return jsonify({'progress': percent, 'playlist_files': filenames})
        else:
            filenames = None  # Wait until all files are present
    return jsonify({'progress': percent, 'filenames': filenames})

@app.route('/downloaded/<filename>')
def downloaded(filename):
    # If filename is a comma-separated list, it's a playlist
    if ',' in filename:
        files = filename.split(',')
        return render_template('downloaded.html', filenames=files, is_playlist=True)
    return render_template('downloaded.html', filename=filename, is_playlist=False)

@app.route('/download/playlist')
def download_playlist():
    files = request.args.get('files')
    if not files:
        return 'No files specified', 400
    file_list = files.split(',')
    memory_file = io.BytesIO()
    with zipfile.ZipFile(memory_file, 'w') as zf:
        for fname in file_list:
            fpath = os.path.join(DOWNLOAD_FOLDER, fname)
            if os.path.exists(fpath):
                zf.write(fpath, arcname=fname)
    memory_file.seek(0)
    # Remove files after zipping
    from downloader import cleanup_downloaded_files
    cleanup_downloaded_files(file_list, DOWNLOAD_FOLDER)
    return send_file(memory_file, download_name='playlist.zip', as_attachment=True, mimetype='application/zip')

@app.route('/download/<filename>')
def download(filename):
    file_path = os.path.join(DOWNLOAD_FOLDER, filename)
    if not os.path.exists(file_path):
        return 'File not found', 404
    response = send_file(file_path, as_attachment=True, mimetype='video/mp4')
    # Remove file after sending
    try:
        os.remove(file_path)
    except Exception:
        pass
    return response

if __name__ == '__main__':
    if not os.path.exists(DOWNLOAD_FOLDER):
        os.makedirs(DOWNLOAD_FOLDER)
    app.run(debug=True)
