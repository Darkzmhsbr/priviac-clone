import os, redis, json
from curl_cffi.requests import AsyncSession

r = redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379"))

async def list_media(username: str):
    username = username.lower()
    
    # 1. Recupera o cookie
    cookie_data = r.get("privacy_cookies")
    if not cookie_data:
        print("ERRO: Cookies não encontrados no Redis.")
        return []
    
    cookies = json.loads(cookie_data)

    # 2. Configura a sessão simulando Chrome
    async with AsyncSession(cookies=cookies, impersonate="chrome120") as s:
        # Headers para parecer uma chamada legítima do frontend (XHR)
        s.headers.update({
            "Accept": "application/json, text/plain, */*",
            "Referer": f"https://privacy.com.br/profile/{username}",
            "Origin": "https://privacy.com.br",
            "X-Requested-With": "XMLHttpRequest"
        })

        print(f"Buscando via API para: {username}...")

        # 3. TENTATIVA 1: API de Feed (Onde ficam os posts/mídia)
        # Traz os primeiros 20 posts
        api_url = f"https://privacy.com.br/api/v1/feed/profile/{username}?offset=0&limit=20"
        
        try:
            resp = await s.get(api_url)
            
            # --- DEBUG DE RESPOSTA ---
            if resp.status_code != 200:
                print(f"ERRO API ({resp.status_code}): Título da página recebida:")
                # Tenta ler o título do HTML de erro para sabermos se é Cloudflare
                try:
                    title_start = resp.text.find("<title>") + 7
                    title_end = resp.text.find("</title>")
                    print(resp.text[title_start:title_end] if title_start > 6 else "Sem título")
                except:
                    pass
                return []

            # 4. Processa o JSON
            data = resp.json()
            
            if not data.get("success"):
                print("API respondeu 200 mas com success: false (Provável bloqueio ou perfil inexistente).")
                return []

            posts = data.get("value", [])
            media_list = []

            print(f"Processando {len(posts)} posts da API...")

            for post in posts:
                # Verifica se tem mídia no post
                if post.get("files"):
                    for file in post["files"]:
                        # Filtra apenas vídeos ou imagens se quiser
                        # type: 'video', 'image'
                        media_list.append({
                            "id": file.get("id"),
                            "url": file.get("url"),
                            "type": file.get("type")
                        })

            print(f"Sucesso! Extraídas {len(media_list)} mídias da API.")
            return media_list

        except Exception as e:
            print(f"Erro ao processar API: {e}")
            return []