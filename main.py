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
    

@app.get("/ping")
def ping():
    return {"message":"pong"}
    
@app.post("/api/download")
def handleDownload(url: RequestedUrl):
    try:
        # ydl_opts = {
        #     'quiet': True,
        #     'skip_download': True,
        #     'extract_flat': False,
        #     'cookiefile': 'cookies.txt'
        # }
        ydl_opts = {
            # --- Download Behavior ---
            'quiet': True,
            'no_warnings': True,
            'ignoreerrors': True,
            'noplaylist': True,  
            'skip_download': False,
            'cookiefile': 'cookies.txt', 
            'http_headers': {
                'User-Agent': (
                    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                    'AppleWebKit/537.36 (KHTML, like Gecko) '
                    'Chrome/113.0.0.0 Safari/537.36'
                ),
                'Accept-Language': 'en-US,en;q=0.9',
            },
            'source_address': '0.0.0.0', 
            'socket_timeout': 15,
            'retries': 10,
            'fragment_retries': 10,
            'concurrent_fragment_downloads': 5,
            'throttled_rate': None, 
            'geo_bypass': True,
            'geo_bypass_country': 'IN',
            'allow_multiple_video_streams': True,
            'allow_multiple_audio_streams': True,
            'age_limit': 99,
            'extract_flat': False,
            'force_keyframes_at_cuts': True,
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
    
    
