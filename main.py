from fastapi import FastAPI,HTTPException,BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import asyncio
import os
import uuid
import subprocess
from fastapi.responses import FileResponse
import yt_dlp
from utils.file_helpers import download_file, cleanup_files
import random
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

app = FastAPI()



app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_headers=["*"],
    allow_methods=["*"]
)


class RequestedUrl(BaseModel):
    url:str
    
class MergeRequest(BaseModel):
    video_url: str
    audio_url: str
    title: str = "merged_video"
 
 

def get_youtube_headers_and_cookies():
    """
    Launch Playwright to visit YouTube and extract fresh cookies and headers.
    Returns a dict with 'User-Agent', 'Accept-Language', and 'Cookie' keys.
    """
    headers_for_ytdlp = {}
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)  # headless for production, set False for debug
            context = browser.new_context(
                geolocation={"latitude": 28.6139, "longitude": 77.2090},
                permissions=["geolocation"]
            )
            page = context.new_page()
            page.goto("https://www.youtube.com", wait_until="networkidle")

            page.wait_for_load_state("load")

            cookies = context.cookies()
            cookie_string = "; ".join(f"{c['name']}={c['value']}" for c in cookies)

            try:
                user_agent = page.evaluate("() => navigator.userAgent")
            except Exception:
                user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"

            try:
                accept_language = page.evaluate("() => navigator.language")
            except Exception:
                accept_language = "en-US,en;q=0.9"

            headers_for_ytdlp = {
                "User-Agent": user_agent,
                "Accept-Language": accept_language,
                "Cookie": cookie_string
            }
    except PlaywrightTimeoutError:
        print("Page load timed out, using default headers.")
        headers_for_ytdlp = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            "Accept-Language": "en-US,en;q=0.9",
            "Cookie": ""
        }
    except Exception as e:
        print(f"Unexpected error fetching headers: {e}")
        headers_for_ytdlp = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            "Accept-Language": "en-US,en;q=0.9",
            "Cookie": ""
        }

    return headers_for_ytdlp 
    

@app.get("/ping")
def ping():
    return {"message":"pong"}
    
@app.post("/api/download")
def handleDownload(url: RequestedUrl):
    try:
        headers = get_youtube_headers_and_cookies()

        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'ignoreerrors': True,
            'noplaylist': True,
            'skip_download': False,
            'http_headers': {
                'User-Agent': headers.get("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"),
                'Accept-Language': headers.get("Accept-Language", "en-US,en;q=0.9"),
                'Cookie': headers.get("Cookie", "")
            },
            'source_address': '0.0.0.0',
            'socket_timeout': 15,
            'retries': 10,
            'fragment_retries': 10,
            'concurrent_fragment_downloads': 5,
            'geo_bypass': True,
            'geo_bypass_country': 'IN',
            'age_limit': 99,
            'cachedir': False,
        }



        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url.url, download=False)

            response = {
                "title": info.get("title"),
                "uploader": info.get("uploader"),
                "duration": info.get("duration"),
                "thumbnail": info.get("thumbnail"),
                "video_formats": [],
                "audio_formats": [],
                "muxed_formats": [],  # formats with both audio + video
            }

            for fmt in info.get("formats", []):
                fmt_url = fmt.get("url")
                if not fmt_url:
                    continue

                # Skip chunked streaming formats (m3u8, mpd)
                if any(ext in fmt_url for ext in ['.m3u8', '.mpd']):
                    continue

                # Check if muxed (both audio and video)
                has_video = fmt.get("vcodec") != "none"
                has_audio = fmt.get("acodec") != "none"

              
                if has_video and has_audio:
                    response["muxed_formats"].append({
                        "format_id": fmt.get("format_id"),
                        "ext": fmt.get("ext"),
                        "resolution": f"{fmt.get('width')}x{fmt.get('height')}" if fmt.get("width") and fmt.get("height") else None,
                        "filesize": fmt.get("filesize"),
                        "fps": fmt.get("fps"),
                        "vcodec": fmt.get("vcodec"),
                        "acodec": fmt.get("acodec"),
                        "url": fmt_url,
                    })
                # Video-only formats
                elif has_video:
                    response["video_formats"].append({
                        "format_id": fmt.get("format_id"),
                        "ext": fmt.get("ext"),
                        "resolution": f"{fmt.get('width')}x{fmt.get('height')}" if fmt.get("width") and fmt.get("height") else None,
                        "filesize": fmt.get("filesize"),
                        "fps": fmt.get("fps"),
                        "vcodec": fmt.get("vcodec"),
                        "url": fmt_url,
                    })
                # Audio-only formats
                elif has_audio:
                    response["audio_formats"].append({
                        "format_id": fmt.get("format_id"),
                        "ext": fmt.get("ext"),
                        "filesize": fmt.get("filesize"),
                        "acodec": fmt.get("acodec"),
                        "url": fmt_url,
                    })

            return response

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to extract video: {str(e)}")
    
            

# @app.post("/api/merge_download")
# async def merge_download(request: MergeRequest, background_tasks: BackgroundTasks):
#     current_dir = os.getcwd()
#     video_file = os.path.join(current_dir, f"{uuid.uuid4()}_video.mp4")
#     audio_file = os.path.join(current_dir, f"{uuid.uuid4()}_audio.mp3")
#     output_file = os.path.join(current_dir, f"{uuid.uuid4()}_output.mp4")

#     try:
#         await asyncio.gather(
#             download_file(request.video_url, video_file),
#             download_file(request.audio_url, audio_file)
#         )

#         FFMPEG_PATH = r"C:\ffmpeg\bin\ffmpeg.exe"
#         command = [
#             FFMPEG_PATH,
#             "-i", video_file,
#             "-i", audio_file,
#             "-c:v", "copy",
#             "-c:a", "aac",
#             "-strict", "experimental",
#             "-y",
#             output_file
#         ]

#         result = subprocess.run(command, capture_output=True, text=True)
#         if result.returncode != 0:
#             raise HTTPException(status_code=500, detail=f"FFmpeg error: {result.stderr}")

#         background_tasks.add_task(cleanup_files, video_file, audio_file, output_file)

#         return FileResponse(output_file, media_type="video/mp4", filename=f"{request.title}.mp4")

#     except Exception as e:
#         cleanup_files(video_file, audio_file, output_file)
#         raise HTTPException(status_code=500, detail=str(e))
    
    
