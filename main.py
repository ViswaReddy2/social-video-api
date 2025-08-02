from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import yt_dlp
import urllib.parse
import random
import logging
import asyncio

from proxy_utils import get_proxy_quickly, start_background_proxy_refresh

# Logging
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s: %(message)s')

app = FastAPI()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_ydl_opts(proxy: str = None) -> dict:
    """Get optimized yt-dlp options"""
    opts = {
        'format': 'best[height<=720]/best',
        'quiet': True,
        'no_warnings': True,
        'socket_timeout': 15,
        'retries': 0,  # No retries for faster failure
        'fragment_retries': 0,
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        },
    }
    if proxy:
        opts['proxy'] = proxy
    return opts

@app.on_event("startup")
async def startup_event():
    # Start background proxy refresh - non-blocking
    asyncio.create_task(start_background_proxy_refresh())
    logging.info("🚀 API ready! Background proxy fetching started.")

@app.get("/get-video-url")
async def get_video_url(video_url: str):
    video_url = urllib.parse.unquote(video_url)
    
    # Try without proxy first (fastest)
    try:
        logging.info("🎯 Trying without proxy first...")
        with yt_dlp.YoutubeDL(get_ydl_opts()) as ydl:
            info = ydl.extract_info(video_url, download=False)
            download_url = extract_video_url(info)
            if download_url:
                logging.info("✅ Success without proxy!")
                return format_response(info, download_url)
    except Exception as e:
        logging.info(f"⚠️ No proxy failed: {str(e)[:100]}...")
    
    # Try with proxies (up to 5 attempts)
    for attempt in range(5):
        try:
            proxy = await get_proxy_quickly()
            if not proxy:
                logging.info(f"⏳ No proxy available for attempt {attempt + 1}, waiting...")
                await asyncio.sleep(1)  # Wait a bit for background task to find proxies
                continue
                
            logging.info(f"🔄 Attempt {attempt + 1} with proxy: {proxy}")
            
            with yt_dlp.YoutubeDL(get_ydl_opts(proxy)) as ydl:
                info = ydl.extract_info(video_url, download=False)
                download_url = extract_video_url(info)
                if download_url:
                    logging.info(f"✅ Success with proxy!")
                    return format_response(info, download_url)
                    
        except Exception as e:
            logging.warning(f"❌ Proxy attempt {attempt + 1} failed: {str(e)[:100]}")
            continue
    
    # Last resort: try once more without proxy with different options
    try:
        logging.info("🔄 Last resort: trying without proxy with different settings...")
        ydl_opts = get_ydl_opts()
        ydl_opts['format'] = 'worst'  # Try lower quality
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)
            download_url = extract_video_url(info)
            if download_url:
                logging.info("✅ Success with fallback!")
                return format_response(info, download_url)
    except Exception as e:
        logging.error(f"❌ Final attempt failed: {str(e)}")
    
    raise HTTPException(status_code=500, detail="Unable to extract video. The video might be geo-blocked or the URL is invalid.")

def extract_video_url(info: dict) -> str:
    """Extract video URL from yt-dlp info"""
    # Try direct URL first
    if info.get('url'):
        return info['url']
    
    # Try requested formats
    if 'requested_formats' in info:
        video_fmt = next((f for f in info['requested_formats'] if f.get('vcodec') != 'none'), None)
        if video_fmt and video_fmt.get('url'):
            return video_fmt['url']
    
    # Try formats list
    if 'formats' in info:
        valid_formats = [f for f in info['formats'] 
                        if f.get('vcodec') != 'none' and 'url' in f and f.get('height', 0) <= 1080]
        if valid_formats:
            best = max(valid_formats, key=lambda f: (f.get('height', 0), f.get('tbr', 0)))
            return best['url']
    
    return None

def format_response(info: dict, download_url: str) -> dict:
    """Format the API response"""
    return {
        "download_url": download_url,
        "title": info.get('title', 'Untitled'),
        "duration": info.get('duration'),
        "view_count": info.get('view_count'),
        "uploader": info.get('uploader'),
        "thumbnail": info.get('thumbnail')
    }

@app.get("/")
async def root():
    return {
        "message": "Social Media Video API",
        "usage": "GET /get-video-url?video_url=YOUR_VIDEO_URL"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)