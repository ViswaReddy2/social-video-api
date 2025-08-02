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

import os

# Environment detection
IS_CLOUD = bool(os.getenv('RENDER') or os.getenv('VERCEL') or os.getenv('HEROKU') or os.getenv('RAILWAY') or os.getenv('FLY_APP_NAME'))

@app.get("/get-video-url-simple")
async def get_video_url_simple(video_url: str):
    """Simple endpoint for testing - minimal processing"""
    video_url = urllib.parse.unquote(video_url)
    
    try:
        logging.info("🚀 Simple extraction attempt...")
        opts = {
            'format': 'best[height<=720]/best',
            'quiet': True,
            'no_warnings': True,
            'socket_timeout': 15,
            'retries': 1,
            'extractor_args': {
                'youtube': {
                    'player_client': ['android_embedded'],
                }
            }
        }
        
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(video_url, download=False)
            download_url = extract_video_url(info)
            if download_url:
                logging.info("✅ Simple extraction success!")
                return format_response(info, download_url)
                
    except Exception as e:
        logging.error(f"❌ Simple extraction failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Simple extraction failed: {str(e)[:100]}")

@app.get("/get-video-url")
async def get_video_url(video_url: str):
    video_url = urllib.parse.unquote(video_url)
    
    if IS_CLOUD:
        # Cloud platform - force proxy usage
        logging.info("🌐 Cloud platform detected - using proxy-first strategy")
        
        # Try with multiple proxies first
        for attempt in range(5):
            proxy = await get_proxy_quickly()
            if proxy:
                logging.info(f"🔄 Cloud attempt {attempt + 1} with proxy")
                info = await youtube_bypass.extract_with_retry(video_url, proxy=proxy, max_attempts=1)
                
                if info:
                    download_url = extract_video_url(info)
                    if download_url:
                        logging.info("✅ Success with proxy on cloud!")
                        return format_response(info, download_url)
            else:
                logging.info("⏳ No proxy available, waiting...")
                await asyncio.sleep(2)
                
        # Fallback without proxy for cloud
        logging.info("🔄 Cloud fallback without proxy...")
        info = await youtube_bypass.extract_with_retry(video_url, proxy=None, max_attempts=1)
        if info:
            download_url = extract_video_url(info)
            if download_url:
                return format_response(info, download_url)
                
    else:
        # Local development - try without proxy first (much faster)
        logging.info("🏠 Local environment - trying without proxy first")
        
        try:
            # Quick attempt without proxy
            info = await youtube_bypass.extract_with_retry(video_url, proxy=None, max_attempts=1)
            if info:
                download_url = extract_video_url(info)
                if download_url:
                    logging.info("✅ Success without proxy (local)!")
                    return format_response(info, download_url)
        except Exception as e:
            logging.info(f"⚠️ Local no-proxy failed: {str(e)[:50]}...")
        
        # Try with proxy only if no-proxy failed
        logging.info("🔄 Local fallback with proxy...")
        for attempt in range(2):  # Only 2 attempts for local
            proxy = await get_proxy_quickly()
            if proxy:
                logging.info(f"🌐 Local proxy attempt {attempt + 1}")
                info = await youtube_bypass.extract_with_retry(video_url, proxy=proxy, max_attempts=1)
                
                if info:
                    download_url = extract_video_url(info)
                    if download_url:
                        logging.info("✅ Success with proxy (local)!")
                        return format_response(info, download_url)
            else:
                break  # Don't wait for proxies in local development
    
    # Final fallback for both environments
    try:
        logging.info("🔄 Final basic fallback...")
        opts = {
            'format': 'worst/best',
            'quiet': True,
            'no_warnings': True,
            'socket_timeout': 30 if IS_CLOUD else 15,
            'retries': 2 if IS_CLOUD else 1,
            'extractor_args': {
                'youtube': {
                    'player_client': ['android_embedded'],
                }
            }
        }
        
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(video_url, download=False)
            download_url = extract_video_url(info)
            if download_url:
                logging.info("✅ Basic fallback success!")
                return format_response(info, download_url)
    except Exception as e:
        logging.error(f"❌ Final fallback failed: {str(e)[:100]}")
    
    error_msg = "Video extraction failed."
    if IS_CLOUD:
        error_msg += " Cloud platform IPs are often blocked by YouTube."
    else:
        error_msg += " Video may be geo-blocked or require authentication."
    
    raise HTTPException(status_code=503, detail=error_msg)

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
    env_type = "Cloud Platform" if IS_CLOUD else "Local Development"
    return {
        "message": "Social Media Video API",
        "environment": env_type,
        "endpoints": {
            "get_video": "/get-video-url?video_url=YOUR_URL",
            "get_video_simple": "/get-video-url-simple?video_url=YOUR_URL (faster, basic extraction)"
        },
        "active_proxies": len(proxy_manager.working_proxies) if 'proxy_manager' in globals() else 0
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)