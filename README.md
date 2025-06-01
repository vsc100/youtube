# YouTube Video/Audio Downloader Web App

A modern Flask web application to download YouTube videos and playlists as MP4 (video) or MP3 (audio) using [yt-dlp](https://github.com/yt-dlp/yt-dlp). Supports quality selection, real-time progress, playlist ZIP downloads, and automatic server-side cleanup.

## Features
- Download single YouTube videos or entire playlists
- Choose video quality (for both single and playlist)
- Download as MP4 (video) or MP3 (audio)
- Real-time progress bar with error handling
- Playlist downloads are zipped and offered as a single file
- Automatic cleanup of all downloaded files after download
- Modern, responsive UI

## Requirements
- Python 3.8+
- [yt-dlp](https://github.com/yt-dlp/yt-dlp)
- Flask

Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage
1. Run the Flask app:
   ```bash
   python app.py
   ```
2. Open your browser and go to `http://127.0.0.1:5000/`
3. Paste a YouTube video or playlist URL, select options, and download!

## Deployment
- You can deploy this app on any server with Python and Flask support.
- **Note:** Free PythonAnywhere accounts cannot access YouTube due to network restrictions. Use a paid account or another host (Render, Heroku, etc.) for full functionality.

## Project Structure
```
app.py              # Main Flask app
requirements.txt    # Python dependencies
/Downloads          # Temporary download folder (auto-cleaned)
downloader.py       # Download logic (yt-dlp integration)
templates/          # HTML templates (index, progress, downloaded)
```

## Security & Cleanup
- All files in the `downloads/` folder are deleted after each download completes.
- No user data is stored on the server.

## License
MIT

---
Made with ❤️ using Flask & yt-dlp.
