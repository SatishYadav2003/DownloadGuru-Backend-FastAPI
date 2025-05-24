import os
import aiohttp
from fastapi import HTTPException

async def download_file(url: str, filepath: str):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            if resp.status != 200:
                raise HTTPException(status_code=400, detail=f"Failed to download from {url}")
            with open(filepath, 'wb') as f:
                while True:
                    chunk = await resp.content.read(1024)
                    if not chunk:
                        break
                    f.write(chunk)

def cleanup_files(*files):
    for f in files:
        if os.path.exists(f):
            os.remove(f)

