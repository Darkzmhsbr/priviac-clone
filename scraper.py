import os, redis, json, re
from curl_cffi.requests import AsyncSession

r = redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379"))

async def list_media(username: str):
    username = username.lower()
    cookie_data = r.get("privacy_cookies")
    if not cookie_data: return []
    cookies = json.loads(cookie_data)
    media_list = []
    found_urls = set()

    def add_media(url, mtype, mid="unknown"):
        if not url: return
        # Limpa URL
        clean = url.replace(r"\/", "/").replace("\\", "")
        
        # LISTA NEGRA TURBINADA (Ignora foto de perfil/capa)
        # 'w240' e 'w1440' são tamanhos de thumbnails/capas
        bad_words = ["privacy-og", "avatar", "favicon", "logo", "icon", "svg", "static", "w240", "w1440", "blur"]
        if any(b in clean for b in bad_words): return
        
        if clean not in found_urls and clean.startswith("http"):
            media_list.append({"id": str(mid)[-8:], "url": clean, "type": mtype})
            found_urls.add(clean)

    async with AsyncSession(cookies=cookies, impersonate="chrome120") as s:
        s.headers.update({
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Referer": f"https://privacy.com.br/profile/{username}",
        })

        print(f"🕵️‍♂️ Acessando: {username}...")
        try:
            resp = await s.get(f"https://privacy.com.br/profile/{username}")
            html = resp.text
            
            # 1. Busca no JSON Oculto
            json_match = re.search(r'<script[^>]*id="__NEXT_DATA__"[^>]*>(.*?)</script>', html, re.DOTALL)
            if json_match:
                try:
                    data = json.loads(json_match.group(1))
                    def extract(obj):
                        if isinstance(obj, dict):
                            if "url" in obj and "type" in obj:
                                if obj["type"] in ["video", "image"]:
                                    add_media(obj["url"], obj["type"], obj.get("id"))
                            # Procura source original
                            if "source" in obj and isinstance(obj["source"], str):
                                add_media(obj["source"], "video", "src")
                            for v in obj.values(): extract(v)
                        elif isinstance(obj, list):
                            for i in obj: extract(i)
                    extract(data)
                except: pass

            # 2. Busca Links Soltos (MP4/M3U8)
            for v in re.findall(r'(https?:?\\?/\\?/[^"\'\s<>]+\.(?:mp4|m3u8))', html):
                add_media(v, "video", "regex")
            
            # Imagens apenas se não achou nada no JSON (pra evitar lixo)
            if not media_list:
                for i in re.findall(r'(https?:?\\?/\\?/[^"\'\s<>]+\.(?:jpg|png))', html):
                    add_media(i, "image", "regex_img")

        except Exception as e: print(f"Erro: {e}")

        print(f"🎉 Filtrado: {len(media_list)} mídias REAIS.")
        return media_list