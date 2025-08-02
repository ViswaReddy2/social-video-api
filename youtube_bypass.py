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
        """Get yt-dlp options optimized for bypass"""
        opts = {
            'quiet': True,
            'no_warnings': True,
            'socket_timeout': 45,
            'retries': 2,
            'fragment_retries': 2,
            'extractor_retries': 3,
            'http_headers': {
                'User-Agent': random.choice(self.user_agents),
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Cache-Control': 'max-age=0'
            },
            'sleep_interval': random.uniform(1, 3),
            'max_sleep_interval': 5,
            'sleep_interval_requests': random.uniform(0.5, 2),
            'age_limit': 99,
            'extract_flat': False,
            'youtube_include_dash_manifest': False,
            'ignoreerrors': False,
            # Bypass YouTube's newer restrictions
            'extractor_args': {
                'youtube': {
                    'skip': ['dash', 'hls'] if strategy == "simple" else [],
                    'player_client': ['android', 'web'],
                    'player_skip': ['webpage'],
                }
            }
        }
        
        # Format selection based strategy
        if strategy == "high_quality":
            opts['format'] = 'best[height<=1080]/best'
        elif strategy == "medium_quality":
            opts['format'] = 'best[height<=720]/best'
        elif strategy == "low_quality":
            opts['format'] = 'best[height<=480]/best'
        elif strategy == "audio_only":
            opts['format'] = 'bestaudio/best'
        else:  # standard
            opts['format'] = 'best[height<=720]/best'
        
        if proxy:
            opts['proxy'] = proxy
            
        return opts
    
    async def extract_with_retry(self, url: str, proxy: Optional[str] = None, max_attempts: int = 3) -> Optional[Dict[str, Any]]:
        """Extract video info with multiple retry strategies"""
        strategies = ["standard", "medium_quality", "low_quality", "simple"]
        
        for attempt in range(max_attempts):
            for strategy in strategies:
                try:
                    logger.info(f"🎯 Attempt {attempt + 1}, Strategy: {strategy}")
                    
                    # Random delay to avoid rate limiting
                    if attempt > 0:
                        await asyncio.sleep(random.uniform(2, 5))
                    
                    opts = self.get_bypass_options(proxy, strategy)
                    
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