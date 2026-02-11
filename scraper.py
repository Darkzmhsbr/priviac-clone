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

    # 2. Sessão: Mudamos para 'chrome' genérico para tentar pegar a versão mais recente
    async with AsyncSession(cookies=cookies, impersonate="chrome") as s:
        s.headers.update({
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Referer": "https://privacy.com.br/",
            "Origin": "https://privacy.com.br",
            "Upgrade-Insecure-Requests": "1"
        })

        media_list = []
        found_urls = set()

        # --- FASE 1: ACESSO À PÁGINA (VISUAL) ---
        print(f"🕵️‍♂️ Acessando perfil: {username}...")
        try:
            resp = await s.get(f"https://privacy.com.br/profile/{username}")
            html = resp.text
            
            # DIAGNÓSTICO DE BLOQUEIO (Olhe isso no Log!)
            title_match = re.search(r'<title>(.*?)</title>', html, re.IGNORECASE)
            page_title = title_match.group(1) if title_match else "Sem Título"
            print(f"📄 Título da Página recebida: [{page_title}]")

            if "Just a moment" in page_title or "Access denied" in html:
                print("❌ BLOQUEIO DETECTADO: O Cloudflare barrou o IP do Railway.")
                print("Solução: Tente gerar um NOVO cookie no seu PC e atualizar a variável COOKIE_MASTER.")
                return []

            # --- FASE 2: MINERAÇÃO DE DADOS (JSON) ---
            print("⛏️ Minerando dados ocultos...")
            # Regex super permissivo para achar o JSON do Next.js
            json_match = re.search(r'<script[^>]*id="__NEXT_DATA__"[^>]*>(.*?)</script>', html, re.DOTALL)
            
            if json_match:
                try:
                    data = json.loads(json_match.group(1))
                    # Função que vasculha o JSON inteiro atrás de 'url' e 'type'
                    def extract_recursive(obj):
                        if isinstance(obj, dict):
                            if "url" in obj and "type" in obj:
                                if obj["type"] in ["video", "image"]:
                                    add_media(obj["url"], obj["type"], obj.get("id"))
                            for k, v in obj.items():
                                extract_recursive(v)
                        elif isinstance(obj, list):
                            for item in obj:
                                extract_recursive(item)
                    
                    extract_recursive(data)
                    print(f"✅ Mineração JSON encontrou {len(media_list)} itens.")
                except:
                    print("⚠️ JSON encontrado mas falhou ao ler.")

            # --- FASE 3: VARREDURA BRUTA (REGEX) ---
            # Se o JSON falhar, procuramos links de video na força bruta
            print("🔍 Varrendo código-fonte por links soltos...")
            
            # Padrão para vídeos MP4 e M3U8 (comum em streaming)
            video_pattern = re.compile(r'(https?://[^"\']+\.(?:mp4|m3u8))')
            for v in video_pattern.findall(html):
                add_media(v, "video", "regex_video")

            # Padrão para imagens (JPG, PNG, WEBP)
            image_pattern = re.compile(r'(https?://[^"\']+\.(?:jpg|jpeg|png|webp))')
            for img in image_pattern.findall(html):
                add_media(img, "image", "regex_image")

        except Exception as e:
            print(f"🔥 Erro crítico na varredura: {e}")

        # Função auxiliar para filtrar e adicionar
        def add_media(url, mtype, mid="unknown"):
            # LIMPEZA DE URL
            url = url.replace("\\u002F", "/").replace("\\", "")
            
            # --- FILTRO DE LIXO (LISTA NEGRA) ---
            # Ignora logos, ícones, avatares e scripts
            blacklist = ["privacy-og", "avatar", "favicon", "logo", "icon", "svg", "static"]
            if any(bad in url for bad in blacklist):
                return
            
            if url not in found_urls:
                media_list.append({"id": str(mid), "url": url, "type": mtype})
                found_urls.add(url)

        # --- RESUMO FINAL ---
        print(f"🧹 Filtragem concluída. Total válido: {len(media_list)}")
        
        if len(media_list) == 0:
            print("⚠️ Nenhuma mídia encontrada. Dica: Se o título foi 'Privacy | ...', o perfil pode estar vazio para visitantes.")
            
        return media_list

# Necessário definir a função auxiliar fora ou dentro (coloquei dentro da lógica acima, mas ajustei aqui para funcionar no escopo)
# Ajuste: A função add_media precisa estar acessível. No código acima, ela foi definida depois do uso (o que daria erro).
# VOU REESCREVER A ESTRUTURA PARA FICAR PERFEITA:

async def list_media(username: str):
    username = username.lower()
    cookie_data = r.get("privacy_cookies")
    if not cookie_data: return []
    cookies = json.loads(cookie_data)

    media_list = []
    found_urls = set()

    def add_media(url, mtype, mid="unknown"):
        if not url: return
        url = url.replace("\\u002F", "/").replace("\\", "")
        blacklist = ["privacy-og", "avatar", "favicon", "logo", "icon", "svg", "static", "placeholder"]
        if any(bad in url for bad in blacklist): return
        if url not in found_urls:
            media_list.append({"id": str(mid)[-10:], "url": url, "type": mtype})
            found_urls.add(url)

    async with AsyncSession(cookies=cookies, impersonate="chrome") as s:
        s.headers.update({"Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8", "Referer": f"https://privacy.com.br/profile/{username}"})
        
        print(f"🕵️‍♂️ Acessando perfil: {username}...")
        try:
            resp = await s.get(f"https://privacy.com.br/profile/{username}")
            html = resp.text
            
            # Debug Título
            title = re.search(r'<title>(.*?)</title>', html, re.IGNORECASE)
            print(f"📄 Título: [{title.group(1) if title else '?'}]")

            # 1. Busca JSON
            json_match = re.search(r'<script[^>]*id="__NEXT_DATA__"[^>]*>(.*?)</script>', html, re.DOTALL)
            if json_match:
                try:
                    data = json.loads(json_match.group(1))
                    def extract(obj):
                        if isinstance(obj, dict):
                            if "url" in obj and "type" in obj and obj["type"] in ["video", "image"]:
                                add_media(obj["url"], obj["type"], obj.get("id"))
                            for v in obj.values(): extract(v)
                        elif isinstance(obj, list):
                            for i in obj: extract(i)
                    extract(data)
                except: pass
            
            # 2. Busca Regex (Backup)
            for v in re.findall(r'(https?://[^"\'\s]+\.mp4)', html):
                add_media(v, "video", "regex")
            for i in re.findall(r'(https?://[^"\'\s]+\.(?:jpg|png))', html):
                add_media(i, "image", "regex")

        except Exception as e:
            print(f"Erro: {e}")

        print(f"🎉 Resultado: {len(media_list)} mídias prontas.")
        return media_list