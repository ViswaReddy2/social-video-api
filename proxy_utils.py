import aiohttp
import asyncio
import logging
from typing import List
import random

logger = logging.getLogger("proxy_utils")

class ProxyManager:
    def __init__(self):
        self.all_proxies = []
        self.working_proxies = []
        self.failed_proxies = set()
        self.is_fetching = False
        
    async def fetch_proxies_quickly(self) -> List[str]:
        """Fetch proxies from multiple sources for cloud platforms"""
        if self.is_fetching:
            return self.working_proxies
            
        self.is_fetching = True
        try:
            logger.info("🌐 Fetching proxies for cloud deployment...")
            all_proxies = set()
            
            # Multiple sources for better reliability on cloud
            sources = [
                "https://www.proxy-list.download/api/v1/get?type=http",
                "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt",
                "https://raw.githubusercontent.com/clarketm/proxy-list/master/proxy-list-raw.txt",
                "https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/http.txt"
            ]
            
            async with aiohttp.ClientSession() as session:
                for source in sources:
                    try:
                        async with session.get(source, timeout=10) as resp:
                            if resp.status == 200:
                                proxy_text = await resp.text()
                                proxies = [p.strip() for p in proxy_text.splitlines() 
                                         if p.strip() and ':' in p.strip() and not p.startswith('#')]
                                all_proxies.update(proxies)
                                logger.info(f"📥 Got {len(proxies)} proxies from source")
                    except Exception as e:
                        logger.warning(f"❌ Source failed: {str(e)}")
                        continue
            
            self.all_proxies = list(all_proxies)
            logger.info(f"📥 Total unique proxies collected: {len(self.all_proxies)}")
            return self.all_proxies
            
        except Exception as e:
            logger.warning(f"❌ Proxy fetch failed: {str(e)}")
        finally:
            self.is_fetching = False
        return []
    
    async def test_single_proxy_fast(self, proxy: str) -> bool:
        """Quick proxy test with minimal timeout"""
        if proxy in self.failed_proxies:
            return False
            
        proxy_clean = proxy.strip().replace("http://", "").replace("https://", "")
        if not proxy_clean or ':' not in proxy_clean:
            return False
            
        try:
            proxy_url = f"http://{proxy_clean}"
            timeout = aiohttp.ClientTimeout(total=5, connect=3)
            
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(
                    "http://httpbin.org/ip",  # Use HTTP instead of HTTPS for faster testing
                    proxy=proxy_url,
                    headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'},
                    ssl=False
                ) as response:
                    if response.status == 200:
                        text = await response.text()
                        if '"origin"' in text:  # Basic validation that we got a proper response
                            if proxy_clean not in self.working_proxies:
                                self.working_proxies.append(proxy_clean)
                                logger.debug(f"✅ Working proxy found: {proxy_clean}")
                            return True
        except Exception as e:
            logger.debug(f"❌ Proxy failed: {proxy_clean} - {str(e)}")
            self.failed_proxies.add(proxy)
        return False
    
    async def get_working_proxy(self) -> str:
        """Get a working proxy quickly - test on demand"""
        # If we have working proxies, return one
        if self.working_proxies:
            # Try a random working proxy first
            proxy = random.choice(self.working_proxies)
            if await self.test_single_proxy_fast(proxy):
                return f"http://{proxy}"
            else:
                # Remove failed proxy
                if proxy in self.working_proxies:
                    self.working_proxies.remove(proxy)
        
        # If no working proxies, test a few from all_proxies
        if not self.all_proxies:
            await self.fetch_proxies_quickly()
        
        # Test up to 5 random proxies quickly
        untested_proxies = [p for p in self.all_proxies if p not in self.failed_proxies and p not in self.working_proxies]
        test_proxies = random.sample(untested_proxies, min(5, len(untested_proxies))) if untested_proxies else []
        
        for proxy in test_proxies:
            if await self.test_single_proxy_fast(proxy):
                return f"http://{proxy}"
        
        # Return any working proxy we have, even if not recently tested
        if self.working_proxies:
            return f"http://{random.choice(self.working_proxies)}"
        
        return None
    
    async def background_proxy_refresh(self):
        """Background task to continuously find more working proxies"""
        while True:
            try:
                if len(self.working_proxies) < 5:  # Keep finding more if we have less than 5
                    if not self.all_proxies:
                        await self.fetch_proxies_quickly()
                    
                    # Test 20 random untested proxies for better chance of finding working ones
                    untested = [p for p in self.all_proxies if p not in self.failed_proxies and p not in self.working_proxies]
                    if untested:
                        test_batch = random.sample(untested, min(20, len(untested)))
                        logger.info(f"🧪 Testing {len(test_batch)} proxies...")
                        
                        # Test proxies with some concurrency but not too much
                        semaphore = asyncio.Semaphore(10)
                        
                        async def test_with_semaphore(proxy):
                            async with semaphore:
                                return await self.test_single_proxy_fast(proxy)
                        
                        results = await asyncio.gather(*[test_with_semaphore(proxy) for proxy in test_batch], return_exceptions=True)
                        working_count = sum(1 for r in results if r is True)
                        logger.info(f"🔍 Background check: {len(self.working_proxies)} working proxies total, found {working_count} new ones")
                
                await asyncio.sleep(30)  # Check every 30 seconds
            except Exception as e:
                logger.error(f"Background refresh error: {e}")
                await asyncio.sleep(60)

# Global proxy manager instance
proxy_manager = ProxyManager()

async def get_proxy_quickly() -> str:
    """Main function to get a working proxy fast"""
    return await proxy_manager.get_working_proxy()

async def start_background_proxy_refresh():
    """Start background proxy refresh task"""
    asyncio.create_task(proxy_manager.background_proxy_refresh())
    # Initial quick fetch
    await proxy_manager.fetch_proxies_quickly()