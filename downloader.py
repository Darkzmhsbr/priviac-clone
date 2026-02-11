import aiofiles, uuid, aiohttp, os

async def download(url: str) -> str:
    # Cria pasta /tmp se não existir (segurança)
    if not os.path.exists("/tmp"):
        os.makedirs("/tmp")

    name = f"{uuid.uuid4().hex}.mp4"
    path = os.path.join("/tmp", name)
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    async with aiohttp.ClientSession(headers=headers) as session:
        async with session.get(url) as resp:
            if resp.status == 200:
                async with aiofiles.open(path, "wb") as f:
                    async for chunk in resp.content.iter_chunked(1024*64):
                        await f.write(chunk)
                return path
            else:
                print(f"Erro ao baixar mídia: {resp.status}")
                return ""