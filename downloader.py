import yt_dlp
import os
import tempfile
import threading
import time

progress_dict = {}

def get_video_formats(url):
    ydl_opts = {'quiet': True, 'skip_download': True, 'extract_flat': False}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        # Detect if it's a playlist
        is_playlist = info.get('_type') == 'playlist' or 'entries' in info
        # For playlists, get the first video entry and use its formats
        if is_playlist and 'entries' in info and info['entries']:
            first_entry = info['entries'][0]
            if 'formats' not in first_entry:
                # Need to fetch full info for the first video
                first_entry = ydl.extract_info(first_entry['url'], download=False)
            formats = []
            seen = set()
            for f in first_entry.get('formats', []):
                if f.get('vcodec') != 'none' and f.get('ext') in ['mp4', 'webm']:
                    height = f.get('height')
                    if height and height not in seen:
                        seen.add(height)
                        label = f"{f.get('format_note', height)}p"
                        formats.append({'format_id': f'bestvideo[height={height}]+bestaudio/best', 'label': label})
        elif not is_playlist:
            formats = []
            seen = set()
            for f in info.get('formats', []):
                if f.get('vcodec') != 'none' and f.get('ext') in ['mp4', 'webm']:
                    height = f.get('height')
                    if height and height not in seen:
                        seen.add(height)
                        label = f"{f.get('format_note', height)}p"
                        formats.append({'format_id': f['format_id'], 'label': label})
        else:
            # fallback: show standard options if no entries
            formats = [
                {'format_id': 'bestvideo[height=480]+bestaudio/best', 'label': '480p'},
                {'format_id': 'bestvideo[height=720]+bestaudio/best', 'label': '720p'},
                {'format_id': 'bestvideo[height=1080]+bestaudio/best', 'label': '1080p'},
            ]
        return {'formats': formats, 'is_playlist': is_playlist}

def download_video_or_audio(url, mode='video', download_dir=None, quality=None, is_playlist=False, progress_id=None):
    # Always use the current working directory for downloads
    if download_dir is None:
        download_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'downloads')
    if not os.path.exists(download_dir):
        os.makedirs(download_dir)
    # Generate a unique filename pattern based on mode and quality
    base_pattern = '%(title)s'
    if mode == 'audio':
        base_pattern += '_audio'
    elif quality:
        base_pattern += f'_q{quality}'
    outtmpl = os.path.join(download_dir, base_pattern + '.%(ext)s')
    def progress_hook(d):
        if progress_id:
            if d['status'] == 'downloading':
                total = d.get('total_bytes') or d.get('total_bytes_estimate') or 1
                downloaded = d.get('downloaded_bytes', 0)
                percent = int(downloaded / total * 100)
                progress_dict[progress_id] = percent
            elif d['status'] == 'finished':
                progress_dict[progress_id] = 100
    if mode == 'audio':
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': outtmpl,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'force_overwrite': True,
            'progress_hooks': [progress_hook],
        }
    else:
        if quality:
            # For playlist, use the bestvideo[height=...] format string
            ydl_opts = {
                'format': quality,
                'outtmpl': outtmpl,
                'merge_output_format': 'mp4',
                'force_overwrite': True,
                'progress_hooks': [progress_hook],
                'noplaylist': not is_playlist,  # Only download playlist if is_playlist is True
            }
        else:
            ydl_opts = {
                'format': 'bestvideo+bestaudio/best',
                'outtmpl': outtmpl,
                'merge_output_format': 'mp4',
                'force_overwrite': True,
                'progress_hooks': [progress_hook],
                'noplaylist': not is_playlist,
            }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        # If playlist, return a list of filenames for all videos that actually exist
        if is_playlist and 'entries' in info:
            filenames = []
            for entry in info['entries']:
                if entry:
                    fname = os.path.basename(ydl.prepare_filename(entry))
                    fpath = os.path.join(download_dir, fname)
                    if os.path.exists(fpath):
                        filenames.append(fname)
            return filenames
        filename = ydl.prepare_filename(info)
        return os.path.basename(filename)

def cleanup_downloaded_files(filenames=None, download_dir=None):
    """
    Delete all files in the download directory. Ignores filenames argument if provided.
    """
    if download_dir is None:
        download_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'downloads')
    for fname in os.listdir(download_dir):
        fpath = os.path.join(download_dir, fname)
        try:
            if os.path.isfile(fpath):
                os.remove(fpath)
        except Exception as e:
            print(f"Error deleting {fpath}: {e}")

def get_progress(progress_id):
    return progress_dict.get(progress_id, 0)
