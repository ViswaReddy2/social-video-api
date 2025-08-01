from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware  # Add this import
import yt_dlp
import urllib.parse  # Added import for URL decoding

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins (change to specific like ["http://127.0.0.1:5500"] for security)
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods (GET, POST, etc.)
    allow_headers=["*"],  # Allows all headers
)

@app.get("/get-video-url")
async def get_video_url(video_url: str):
    video_url = urllib.parse.unquote(video_url)  # Added: Decode the encoded URL param
    try:
        ydl_opts = {
            'format': 'best',  # Prefer best combined video+audio format
            'quiet': True,
            'no_warnings': True,
            'cookiefile': 'cookies.txt'  # Added: Load a combined cookies file for all platforms (Instagram, Facebook, Twitter, Pinterest, etc.)
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)
            
            # Check for combined format URL
            if 'url' in info:
                download_url = info['url']
                audio_url = None  # Combined, so no separate audio
            elif 'requested_formats' in info and len(info['requested_formats']) > 1:
                # Separate video and audio detected
                video_format = next((f for f in info['requested_formats'] if f.get('vcodec') != 'none'), None)
                audio_format = next((f for f in info['requested_formats'] if f.get('acodec') != 'none'), None)
                download_url = video_format['url'] if video_format else None
                audio_url = audio_format['url'] if audio_format else None
            elif 'formats' in info and info['formats']:
                # Fallback: Select best combined format
                valid_formats = [
                    f for f in info['formats'] if 'url' in f 
                    and f.get('vcodec') != 'none' 
                    and f.get('acodec') != 'none'
                ]
                if not valid_formats:
                    # No combined; fallback to best video-only
                    valid_formats = [f for f in info['formats'] if 'url' in f and f.get('vcodec') != 'none']
                    if not valid_formats:
                        raise ValueError("No valid video formats found.")
                best_format = max(valid_formats, key=lambda f: (f.get('height') or 0, f.get('filesize') or 0))
                download_url = best_format['url']
                audio_url = None
            else:
                raise ValueError("No video formats found.")
            
            response = {
                "download_url": download_url,
                "title": info.get('title', 'Untitled')
            }
            if audio_url:
                response["audio_url"] = audio_url
                response["note"] = "Audio is separate; merge client-side with tools like FFmpeg."
            
            return response
    
    except yt_dlp.utils.DownloadError as e:
        raise HTTPException(status_code=400, detail=f"Invalid or unsupported URL: {str(e)}. Check if the video is public.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error extracting URL: {str(e)}")

@app.get("/")
async def root():
    return {"message": "Welcome to Social Media Video API! Use /get-video-url?video_url=... to extract URLs."}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)