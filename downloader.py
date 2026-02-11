import aiofiles, uuid, aiohttp
async def download(url: str) -> str:
    tmp = f"/tmp/{uuid.uuid4().hex}.mp4"
    async with aiohttp.ClientSession() as s, s.get(url) as resp, aiofiles.open(tmp, "wb") as f:
        async for chunk in resp.content.iter_chunked(1024*64):
            await f.write(chunk)
    return tmp
