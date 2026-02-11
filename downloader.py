import os, uuid, aiofiles, redis, json
from curl_cffi.requests import AsyncSession

# Conecta ao Redis para pegar o "crachá" (cookies)
r = redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379"))

async def download(url: str) -> str:
    # Cria pasta temporária se não existir
    if not os.path.exists("/tmp"):
        os.makedirs("/tmp")

    # Nome único para o arquivo
    filename = f"{uuid.uuid4().hex}.mp4"
    path = os.path.join("/tmp", filename)
    
    # Pega os cookies salvos
    cookie_data = r.get("privacy_cookies")
    cookies = json.loads(cookie_data) if cookie_data else {}

    print(f"⬇️ Iniciando download: {url[:30]}...")

    # Usa a sessão camuflada (Chrome) para baixar
    async with AsyncSession(cookies=cookies, impersonate="chrome120") as s:
        # Headers obrigatórios para o download não ser barrado
        s.headers.update({
            "Referer": "https://privacy.com.br/",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        })
        
        try:
            # Baixa em pedaços (stream) para não lotar a memória
            resp = await s.get(url, stream=True)
            
            if resp.status_code == 200:
                async with aiofiles.open(path, "wb") as f:
                    async for chunk in resp.aiter_content():
                        await f.write(chunk)
                
                print(f"✅ Download concluído: {path}")
                return path
            else:
                print(f"❌ Erro no download (Status {resp.status_code})")
                return None
        except Exception as e:
            print(f"🔥 Falha crítica no download: {e}")
            return None