import os, redis, json, re
from curl_cffi.requests import AsyncSession

r = redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379"))

async def list_media(username: str):
    username = username.lower()
    
    # 1. Recupera cookies
    cookie_data = r.get("privacy_cookies")
    if not cookie_data:
        print("ERRO: Cookies não encontrados no Redis.")
        return []
    cookies = json.loads(cookie_data)

    media_list = []
    found_urls = set()

    # Função para salvar mídia encontrada
    def add_media(url, mtype, mid="unknown"):
        if not url: return
        # A MÁGICA: Limpa as barras invertidas que o site usa pra esconder o link
        clean_url = url.replace(r"\/", "/").replace("\\", "")
        
        # Filtra lixo
        blacklist = ["privacy-og", "avatar", "favicon", "logo", "icon", "svg", "static", "placeholder"]
        if any(bad in clean_url for bad in blacklist): return
        
        if clean_url not in found_urls:
            # Garante que é um link completo
            if not clean_url.startswith("http"): return
            
            media_list.append({"id": str(mid)[-10:], "url": clean_url, "type": mtype})
            found_urls.add(clean_url)

    # 2. Sessão Chrome
    async with AsyncSession(cookies=cookies, impersonate="chrome120") as s:
        # Headers atualizados
        s.headers.update({
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Referer": f"https://privacy.com.br/profile/{username}",
            "Origin": "https://privacy.com.br",
            "Upgrade-Insecure-Requests": "1"
        })

        print(f"🕵️‍♂️ Acessando perfil: {username}...")
        try:
            resp = await s.get(f"https://privacy.com.br/profile/{username}")
            html = resp.text

            # --- ESTRATÉGIA 1: BUSCA NO JSON (RÁPIDA) ---
            # Procura o bloco de dados do Next.js
            json_match = re.search(r'<script[^>]*id="__NEXT_DATA__"[^>]*>(.*?)</script>', html, re.DOTALL)
            if json_match:
                print("📦 JSON encontrado! Processando...")
                try:
                    # Varredura recursiva no JSON
                    data = json.loads(json_match.group(1))
                    def extract(obj):
                        if isinstance(obj, dict):
                            # Padrão de mídia da Privacy
                            if "url" in obj and "type" in obj:
                                if obj["type"] in ["video", "image"]:
                                    add_media(obj["url"], obj["type"], obj.get("id"))
                            # Padrão alternativo (source)
                            if "source" in obj and isinstance(obj["source"], str):
                                if ".mp4" in obj["source"]:
                                    add_media(obj["source"], "video", "src")
                            for v in obj.values(): extract(v)
                        elif isinstance(obj, list):
                            for i in obj: extract(i)
                    extract(data)
                except:
                    print("Erro ao ler JSON interno.")

            # --- ESTRATÉGIA 2: VARREDURA BRUTA (REGEX CORRIGIDO) ---
            print("🔍 Varrendo código-fonte (Modo Raio-X)...")
            
            # Pega links que podem ter barras escapadas (https:\/\/...)
            # .mp4 e .m3u8
            video_regex = r'(https?:?\\?/\\?/[^"\'\s<>]+\.(?:mp4|m3u8))'
            for v in re.findall(video_regex, html):
                add_media(v, "video", "regex_vid")

            # .jpg, .png, .webp
            image_regex = r'(https?:?\\?/\\?/[^"\'\s<>]+\.(?:jpg|jpeg|png|webp))'
            for i in re.findall(image_regex, html):
                add_media(i, "image", "regex_img")

        except Exception as e:
            print(f"🔥 Erro crítico: {e}")

        print(f"🎉 Resultado Final: {len(media_list)} mídias prontas para download.")
        return media_list