import os, uuid, aiofiles, redis, json
from curl_cffi.requests import AsyncSession

r = redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379"))

async def download(url: str) -> str:
    # Pasta temporária
    if not os.path.exists("/tmp"): os.makedirs("/tmp")
    filename = f"{uuid.uuid4().hex}.mp4"
    path = os.path.join("/tmp", filename)
    
    # Pega cookies
    cookie_data = r.get("privacy_cookies")
    cookies = json.loads(cookie_data) if cookie_data else {}

    print(f"⬇️ Baixando: {url[:40]}...")

    # Usa Chrome para enganar o bloqueio de download
    async with AsyncSession(cookies=cookies, impersonate="chrome120") as s:
        s.headers.update({
            "Referer": "https://privacy.com.br/",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        })
        
        try:
            resp = await s.get(url, stream=True)
            if resp.status_code == 200:
                async with aiofiles.open(path, "wb") as f:
                    async for chunk in resp.aiter_content():
                        await f.write(chunk)
                print("✅ Download OK!")
                return path
            else:
                print(f"❌ Erro Download: Status {resp.status_code}")
                return None
        except Exception as e:
            print(f"🔥 Falha: {e}")
            return None