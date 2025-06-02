import os
import yt_dlp

def ensure_download_dir(path='downloads'):
    if not os.path.exists(path):
        os.makedirs(path)

def download_video(url, output_path='downloads/%(title)s.%(ext)s'):
    ydl_opts = {
        'outtmpl': output_path,
        'format': 'bestvideo+bestaudio/best',
        'merge_output_format': 'mp4',
        'progress_hooks': [download_hook],
        'cookies': 'www.youtube.com_cookies.txt'
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

def download_hook(d):
    if d['status'] == 'downloading':
        print(f"Downloading: {d['_percent_str']} at {d['_speed_str']} ETA {d['_eta_str']}", end='\r')
    elif d['status'] == 'finished':
        print(f"\nDownload completed: {d['filename']}")

def main():
    ensure_download_dir()
    url = input('Enter YouTube video or playlist URL: ').strip()
    if not url:
        print('No URL provided.')
        return
    try:
        download_video(url)
    except Exception as e:
        print(f"Error: {e}")

if __name__ == '__main__':
    main()
