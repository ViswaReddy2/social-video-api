from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import yt_dlp
import urllib.parse
import random
import logging
import asyncio

from proxy_utils import get_proxy_quickly, start_background_proxy_refresh
from youtube_bypass import youtube_bypass

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
    """Get optimized yt-dlp options with bot detection bypass"""
    opts = {
        'format': 'best[height<=720]/best',
        'quiet': True,
        'no_warnings': True,
        'socket_timeout': 30,
        'retries': 1,
        'fragment_retries': 1,
        'extractor_retries': 1,
        # Anti-detection headers
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-us,en;q=0.5',
            'Accept-Encoding': 'gzip,deflate',
            'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.7',
            'Keep-Alive': '300',
            'Connection': 'keep-alive',
        },
        # YouTube-specific bypass options
        'extract_flat': False,
        'writethumbnail': False,
        'writeinfojson': False,
        'simulate': False,
        # Additional anti-detection
        'sleep_interval': 1,
        'max_sleep_interval': 3,
        'sleep_interval_requests': 1,
        'sleep_interval_subtitles': 1,
        # Try to avoid age gate
        'age_limit': 99,
        # Use cookies if available (you can add cookie file later)
        'cookiefile': None,
        # Additional YouTube bypasses
        'youtube_include_dash_manifest': False,
        'extract_args': {
            'youtube': {
                'skip': ['hls', 'dash']
            }
        }
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
    
    # Try without proxy first using advanced bypass
    logging.info("🎯 Trying advanced bypass without proxy...")
    info = await youtube_bypass.extract_with_retry(video_url, proxy=None, max_attempts=2)
    
    if info:
        download_url = extract_video_url(info)
        if download_url:
            logging.info("✅ Success without proxy!")
            return format_response(info, download_url)
    
    # Try with proxy using advanced bypass
    logging.info("🔄 Trying with proxy using advanced bypass...")
    for attempt in range(3):
        proxy = await get_proxy_quickly()
        if proxy:
            logging.info(f"🌐 Using proxy for attempt {attempt + 1}")
            info = await youtube_bypass.extract_with_retry(video_url, proxy=proxy, max_attempts=1)
            
            if info:
                download_url = extract_video_url(info)
                if download_url:
                    logging.info("✅ Success with proxy!")
                    return format_response(info, download_url)
        else:
            logging.info("⏳ No proxy available, waiting...")
            await asyncio.sleep(2)
    
    # Final attempt with basic yt-dlp (fallback)
    try:
        logging.info("🔄 Final fallback attempt...")
        opts = {
            'format': 'worst',
            'quiet': True,
            'no_warnings': True,
            'socket_timeout': 30,
            'extractor_args': {
                'youtube': {
                    'player_client': ['android'],
                }
            }
        }
        
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(video_url, download=False)
            download_url = extract_video_url(info)
            if download_url:
                logging.info("✅ Success with fallback!")
                return format_response(info, download_url)
    except Exception as e:
        logging.error(f"❌ Fallback failed: {str(e)[:100]}")
    
    raise HTTPException(
        status_code=503, 
        detail="Video extraction failed due to anti-bot protection. The video may be geo-blocked, age-restricted, or require authentication."
    )

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