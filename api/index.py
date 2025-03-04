from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests
import os
from typing import Optional

app = FastAPI(title="TikTok Video Downloader API")

# Add CORS middleware to allow cross-origin requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

class TikTokVideoRequest(BaseModel):
    url: str
    output_path: Optional[str] = "downloads"

def extract_tiktok_video_url(tiktok_url):
    """
    Extract the direct video URL from a TikTok share link
    """
    try:
        # Send a request to get the redirected URL
        response = requests.head(tiktok_url, allow_redirects=True)
        
        # Check if the final URL is a TikTok video
        if 'tiktok.com' not in response.url:
            raise ValueError("Invalid TikTok URL")
        
        return response.url
    except Exception as e:
        raise ValueError(f"Error extracting video URL: {str(e)}")

def download_tiktok_video(video_url, output_path):
    """
    Download TikTok video using requests
    """
    try:
        # Create output directory if it doesn't exist
        os.makedirs(output_path, exist_ok=True)
        
        # Send a GET request to download the video
        video_response = requests.get(video_url, stream=True)
        video_response.raise_for_status()
        
        # Generate filename
        filename = os.path.join(output_path, f"tiktok_video_{hash(video_url)}.mp4")
        
        # Write video content to file
        with open(filename, 'wb') as video_file:
            for chunk in video_response.iter_content(chunk_size=8192):
                video_file.write(chunk)
        
        return filename
    except Exception as e:
        raise ValueError(f"Error downloading video: {str(e)}")

@app.post("/api/download")
async def download_video(request: TikTokVideoRequest):
    try:
        # Extract the actual video URL
        resolved_url = extract_tiktok_video_url(request.url)
        
        # Download the video
        filename = download_tiktok_video(resolved_url, request.output_path)
        
        return {
            "status": "success", 
            "message": "Video downloaded successfully",
            "filename": filename
        }
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")

# Optional: Add a health check endpoint
@app.get("/api")
async def health_check():
    return {"status": "API is running"}
