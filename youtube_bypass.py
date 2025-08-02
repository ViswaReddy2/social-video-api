import yt_dlp
import logging
import random
import asyncio
from typing import Optional, Dict, Any

logger = logging.getLogger("youtube_bypass")

class YouTubeBypass:
    def __init__(self):
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0'
        ]
    
    def get_bypass_options(self, proxy: Optional[str] = None, strategy: str = "standard") -> Dict[str, Any]:
        """Get yt-dlp options optimized for cloud platform bypass"""
        opts = {
            'quiet': True,
            'no_warnings': True,
            'socket_timeout': 60,  # Longer timeout for cloud
            'retries': 3,
            'fragment_retries': 3,
            'extractor_retries': 5,
            'http_headers': {
                'User-Agent': random.choice(self.user_agents),
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9,es;q=0.8,fr;q=0.7',
                'Accept-Encoding': 'gzip, deflate, br',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-User': '?1',
                'Cache-Control': 'no-cache',
                'Pragma': 'no-cache'
            },
            'sleep_interval': random.uniform(2, 5),  # Longer delays for cloud
            'max_sleep_interval': 10,
            'sleep_interval_requests': random.uniform(1, 3),
            'age_limit': 99,
            'extract_flat': False,
            'youtube_include_dash_manifest': False,
            'ignoreerrors': False,
            # Enhanced bypass for cloud platforms
            'extractor_args': {
                'youtube': {
                    'skip': ['dash', 'hls'] if strategy == "simple" else [],
                    'player_client': ['android', 'android_embedded', 'android_music'],
                    'player_skip': ['webpage', 'configs'],
                    'innertube_host': 'youtubei.googleapis.com',
                    'innertube_key': None,
                }
            },
            # Additional cloud-specific options
            'http_chunk_size': 10485760,
            'prefer_insecure': False,
        }
        
        # More aggressive format selection for cloud
        if strategy == "high_quality":
            opts['format'] = 'best[height<=1080][ext=mp4]/best[ext=mp4]/best'
        elif strategy == "medium_quality":
            opts['format'] = 'best[height<=720][ext=mp4]/best[ext=mp4]/best'
        elif strategy == "low_quality":
            opts['format'] = 'best[height<=480][ext=mp4]/worst[ext=mp4]/worst'
        elif strategy == "audio_only":
            opts['format'] = 'bestaudio[ext=m4a]/bestaudio/best'
        elif strategy == "simple":
            opts['format'] = 'worst/best'
        else:  # standard
            opts['format'] = 'best[height<=720][ext=mp4]/best'
        
        if proxy:
            opts['proxy'] = proxy
            # Additional proxy-specific settings for cloud
            opts['source_address'] = None
            
        return opts
    
    async def extract_with_retry(self, url: str, proxy: Optional[str] = None, max_attempts: int = 3) -> Optional[Dict[str, Any]]:
        """Extract video info with multiple retry strategies"""
        import os
        is_cloud = bool(os.getenv('RENDER') or os.getenv('VERCEL') or os.getenv('HEROKU'))
        
        if is_cloud:
            strategies = ["standard", "medium_quality", "low_quality", "simple"]
        else:
            # Local development - simpler and faster strategies
            strategies = ["standard", "low_quality"] if max_attempts > 1 else ["standard"]
        
        for attempt in range(max_attempts):
            for strategy in strategies:
                try:
                    logger.info(f"🎯 Attempt {attempt + 1}, Strategy: {strategy}")
                    
                    # Shorter delay for local development
                    if attempt > 0:
                        delay = random.uniform(2, 5) if is_cloud else random.uniform(0.5, 1.5)
                        await asyncio.sleep(delay)
                    
                    opts = self.get_bypass_options(proxy, strategy)
                    
                    # Shorter timeout for local development
                    if not is_cloud:
                        opts['socket_timeout'] = 20
                        opts['sleep_interval'] = random.uniform(0.5, 1.5)
                        opts['sleep_interval_requests'] = random.uniform(0.2, 1)
                    
                    # Run in executor to avoid blocking
                    loop = asyncio.get_event_loop()
                    info = await loop.run_in_executor(
                        None, 
                        lambda: self._extract_sync(url, opts)
                    )
                    
                    if info:
                        logger.info(f"✅ Success with strategy: {strategy}")
                        return info
                        
                except yt_dlp.utils.DownloadError as e:
                    error_msg = str(e).lower()
                    if any(keyword in error_msg for keyword in ['sign in', 'bot', 'captcha', 'verify']):
                        logger.warning(f"🤖 Bot detection: {str(e)[:100]}")
                        continue
                    elif 'unavailable' in error_msg or 'private' in error_msg:
                        logger.error(f"📺 Video unavailable: {str(e)[:100]}")
                        return None
                    else:
                        logger.warning(f"❌ Download error: {str(e)[:100]}")
                        continue
                except Exception as e:
                    logger.warning(f"❌ Unexpected error: {str(e)[:100]}")
                    continue
        
        return None
    
    def _extract_sync(self, url: str, opts: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Synchronous extraction (to be run in executor)"""
        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                return ydl.extract_info(url, download=False)
        except Exception:
            return None

# Global instance
youtube_bypass = YouTubeBypass()