from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware  # Add this import
import yt_dlp
import urllib.parse  # Added import for URL decoding
import random  # Added for proxy rotation

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
    video_url = urllib.parse.unquote(video_url)  # Decode the encoded URL param
    proxies = [
    'http://72.10.160.90:3581',
    'http://123.141.181.7:5031',
    'http://218.236.166.96:8888',
    'http://34.48.171.130:33080',
    'http://14.225.240.23:8562',
    'http://155.94.241.132:3128',
    'http://171.237.95.207:1019',
    'http://114.6.27.84:8520',
    'http://123.141.181.32:5031',
    'http://67.43.228.252:21045',
    'http://8.213.151.128:3128',
    'http://42.118.2.147:16000',
    'http://67.43.236.19:3527',
    'http://190.97.238.74:8080',
    'http://79.127.54.89:3130',
    'http://123.141.181.84:5031',
    'http://197.255.126.69:80',
    'http://67.43.236.21:5423',
    'http://67.43.228.253:13271',
    'http://140.245.88.97:8118',
    'http://154.236.177.103:1977',
    'http://42.119.156.140:16000',
    'http://67.43.228.254:6535',
    'http://67.43.236.20:6231',
    'http://123.141.181.53:5031',
    'http://171.237.94.84:10007',
    'http://123.141.181.24:5031',
    'http://189.45.204.251:80',
    'http://189.180.46.175:8118',
    'http://197.243.20.178:80',
    'http://67.43.228.251:28401',
    'http://52.51.50.129:3128',
    'http://20.78.118.91:8561',
    'http://123.141.181.1:5031',
    'http://190.145.194.210:8080',
    'http://47.251.60.125:8080',
    'http://123.141.181.46:5031',
    'http://123.141.181.49:5031',
    'http://77.242.177.57:3128',
    'http://123.141.181.31:5031',
    'http://85.206.93.105:8080',
    'http://66.78.40.66:8880',
    'http://49.48.68.109:8080',
    'http://45.136.198.40:3128',
    'http://112.216.83.10:3128',
    'http://201.222.50.218:80',
    'http://190.110.226.122:80',
    'http://203.175.127.240:8080',
    'http://157.230.220.25:4857',
    'http://202.5.37.104:17382',
    'http://123.141.181.8:5031',
    'http://167.99.236.14:80',
    'http://87.95.143.37:80',
    'http://162.243.5.191:80',
    'http://37.27.6.46:80',
    'http://35.161.94.92:1080',
    'http://202.94.145.6:80',
    'http://186.65.109.21:81',
    'http://116.103.131.240:1023',
    'http://209.13.186.20:80',
    'http://87.255.196.143:80',
    'http://78.28.152.113:80',
    'http://51.159.28.39:80',
    'http://68.183.143.134:80',
    'http://194.150.110.134:80',
    'http://45.91.94.197:80',
    'http://123.141.181.23:5031',
    'http://135.148.120.6:80',
    'http://174.138.54.65:80',
    'http://62.84.120.61:80',
    'http://45.92.108.112:80',
    'http://212.32.235.131:80',
    'http://65.21.34.102:80',
    'http://122.99.125.85:80',
    'http://5.161.103.41:88',
    'http://89.23.112.143:80',
    'http://94.23.9.170:80',
    'http://62.171.146.164:80',
    'http://94.46.172.104:80',
    'http://72.10.160.94:29225',
    'http://95.129.101.73:80',
    'http://34.81.160.132:80',
    'http://147.135.128.218:80',
    'http://52.191.222.212:8080',
    'http://147.182.180.242:80',
    'http://194.87.98.70:80',
    'http://103.210.22.17:3128',
    'http://46.101.115.59:80',
    'http://43.130.52.194:8118',
    'http://35.209.198.222:80',
    'http://157.245.97.119:9090',
    'http://34.87.84.105:80',
    'http://27.71.228.47:3128',
    'http://34.81.72.31:80',
    'http://193.123.237.191:8080',
    'http://78.28.152.111:80',
    'http://31.220.78.244:80',
    'http://173.181.143.245:80',
    'http://79.174.12.190:80',
    'http://157.15.66.119:8080'
       
    ]  # List of proxies (add more for better rotation)
    max_retries = 3  # Number of retry attempts if proxy fails
    
    for attempt in range(max_retries):
        try:
            selected_proxy = random.choice(proxies)  # Randomly select a proxy
            ydl_opts = {
                'format': 'best',  # Prefer best combined video+audio format
                'quiet': True,
                'no_warnings': True,
                'proxy': selected_proxy  # Use the selected proxy
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
            if attempt == max_retries - 1:
                raise HTTPException(status_code=400, detail=f"Invalid or unsupported URL: {str(e)}. Check if the video is public.")
            # Retry with another proxy on failure

    raise HTTPException(status_code=500, detail="All proxies failed. Try later or add more proxies.")

@app.get("/")
async def root():
    return {"message": "Welcome to Social Media Video API! Use /get-video-url?video_url=... to extract URLs."}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)