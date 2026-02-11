import os, redis, json, re
from curl_cffi.requests import AsyncSession

r = redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379"))

async def list_media(username: str):
    username = username.lower()
    
    # 1. Recupera cookies (Login já validado!)
    cookie_data = r.get("privacy_cookies")
    if not cookie_data:
        print("ERRO: Cookies não encontrados no Redis.")
        return []
    
    cookies = json.loads(cookie_data)

    # 2. Sessão Chrome
    async with AsyncSession(cookies=cookies, impersonate="chrome120") as s:
        # Headers simples de navegador
        s.headers.update({
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Referer": "https://privacy.com.br/",
        })

        print(f"🕵️‍♂️ Acessando perfil visual: {username}...")
        url = f"https://privacy.com.br/profile/{username}"
        
        try:
            resp = await s.get(url)
            html = resp.text

            # Verificação básica de bloqueio
            if "Just a moment" in html or "Access denied" in html:
                print("❌ ERRO: Bloqueio visual do Cloudflare detectado.")
                return []

            # 3. MODO VARREDURA TOTAL (REGEX)
            # Procura por qualquer texto que pareça um link de vídeo/imagem
            print("🔍 Varrendo código fonte em busca de arquivos .mp4 e imagens...")
            
            media_list = []
            seen_urls = set()

            # PADRÃO DE BUSCA:
            # Procura strings que começam com http/https, podem ter barras escapadas (\/) 
            # e terminam com .mp4
            video_pattern = re.compile(r'https:(?:\\/|/)(?:\\/|/)[a-zA-Z0-9\-\.]+\.[a-zA-Z]{2,}(?:\\/|/)[^"\'\s<>]+\.mp4')
            
            # Padrão para imagens (opcional, filtra avatares depois)
            image_pattern = re.compile(r'https:(?:\\/|/)(?:\\/|/)[a-zA-Z0-9\-\.]+\.[a-zA-Z]{2,}(?:\\/|/)[^"\'\s<>]+\.(?:jpg|jpeg|png)')

            # --- Extraindo Vídeos ---
            videos = video_pattern.findall(html)
            for v in videos:
                # Corrige as barras invertidas do JSON (ex: https:\/\/ -> https://)
                clean_url = v.replace("\\/", "/")
                
                if clean_url not in seen_urls:
                    # Gera um ID falso baseado no final da URL para controle
                    media_list.append({
                        "id": "vid_" + clean_url[-15:], 
                        "url": clean_url, 
                        "type": "video"
                    })
                    seen_urls.add(clean_url)

            # --- Extraindo Imagens ---
            images = image_pattern.findall(html)
            for i in images:
                clean_url = i.replace("\\/", "/")
                
                # Filtra ícones de site e avatares pequenos para não sujar o download
                if clean_url not in seen_urls and "avatar" not in clean_url and "favicon" not in clean_url:
                    media_list.append({
                        "id": "img_" + clean_url[-15:], 
                        "url": clean_url, 
                        "type": "image"
                    })
                    seen_urls.add(clean_url)

            print(f"🎉 VARREDURA FINALIZADA! {len(media_list)} mídias encontradas.")
            
            # Debug se não achar nada
            if len(media_list) == 0:
                print("⚠️ Nenhuma mídia encontrada. Verifique se o perfil tem posts públicos ou se a assinatura está ativa.")
                # print(f"Amostra do HTML: {html[:500]}") # Descomente se precisar debugar
            
            return media_list

        except Exception as e:
            print(f"🔥 Erro no scraper: {e}")
            return []