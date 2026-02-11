import os, uuid, aiofiles, redis, json
from curl_cffi.requests import AsyncSession

r = redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379"))

async def download(url: str, referer_url: str) -> str:
    # Cria pasta temp
    if not os.path.exists("/tmp"): os.makedirs("/tmp")
    
    # Nome do arquivo
    ext = "mp4" if ".mp4" in url else "jpg"
    filename = f"{uuid.uuid4().hex}.{ext}"
    path = os.path.join("/tmp", filename)
    
    # Pega cookies
    cookie_data = r.get("privacy_cookies")
    cookies = json.loads(cookie_data) if cookie_data else {}

    print(f"⬇️ Baixando: {url[:30]}... (Ref: {referer_url})")

    # Camuflagem Pesada para evitar erro 423
    async with AsyncSession(cookies=cookies, impersonate="chrome120") as s:
        s.headers.update({
            "Referer": referer_url, # O segredo está aqui!
            "Origin": "https://privacy.com.br",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "*/*",
            "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
            "Sec-Fetch-Dest": "video",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-site"
        })
        
        try:
            resp = await s.get(url, stream=True)
            
            if resp.status_code == 200:
                async with aiofiles.open(path, "wb") as f:
                    async for chunk in resp.aiter_content():
                        await f.write(chunk)
                print("✅ Download OK!")
                return path
            elif resp.status_code == 423:
                print("❌ Erro 423: O servidor trancou o arquivo (Bloqueio de Região ou IP).")
                return None
            else:
                print(f"❌ Erro Download: Status {resp.status_code}")
                return None
        except Exception as e:
            print(f"🔥 Falha crítica: {e}")
            return None