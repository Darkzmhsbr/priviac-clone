import os, uuid, aiofiles, redis, json
from curl_cffi.requests import AsyncSession

r = redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379"))

async def download(url: str, referer_url: str) -> str:
    # Prepara pasta
    if not os.path.exists("/tmp"): os.makedirs("/tmp")
    
    # Define extensão
    ext = "mp4" if ".mp4" in url else "jpg"
    filename = f"{uuid.uuid4().hex}.{ext}"
    path = os.path.join("/tmp", filename)
    
    # Recupera cookies
    cookie_data = r.get("privacy_cookies")
    cookies = json.loads(cookie_data) if cookie_data else {}

    print(f"⬇️ Bufferizando: {url[:30]}... (Modo Player)")

    # Sessão Camuflada
    async with AsyncSession(cookies=cookies, impersonate="chrome120") as s:
        # HEADERS MÁGICOS PARA VENCER O ERRO 423
        s.headers.update({
            "Referer": referer_url,
            "Origin": "https://privacy.com.br",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "*/*",
            "Accept-Encoding": "identity;q=1, *;q=0",
            "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
            "Range": "bytes=0-",  # <--- O SEGREDO! Diz que estamos "assistindo"
            "Sec-Fetch-Dest": "video",
            "Sec-Fetch-Mode": "no-cors",
            "Sec-Fetch-Site": "same-site",
            "Pragma": "no-cache",
            "Cache-Control": "no-cache"
        })
        
        try:
            # stream=True é essencial aqui
            resp = await s.get(url, stream=True)
            
            # Aceita 200 (OK) ou 206 (Partial Content - Streaming)
            if resp.status_code in [200, 206]:
                async with aiofiles.open(path, "wb") as f:
                    async for chunk in resp.aiter_content():
                        await f.write(chunk)
                print("✅ Download Concluído!")
                return path
            
            elif resp.status_code == 423:
                print("❌ ERRO 423: O IP do Railway está na lista negra (Data Center Block).")
                print("Solução: O código está perfeito, mas o servidor odeia o IP do Railway.")
                return None
            else:
                print(f"❌ Erro Status: {resp.status_code}")
                return None

        except Exception as e:
            print(f"🔥 Falha crítica: {e}")
            return None