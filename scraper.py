import os, redis, json
from curl_cffi.requests import AsyncSession

r = redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379"))

async def list_media(username: str):
    username = username.lower()
    
    # 1. Recupera cookies
    cookie_data = r.get("privacy_cookies")
    if not cookie_data:
        print("ERRO: Cookies não encontrados. Verifique a variável COOKIE_MASTER.")
        return []
    
    cookies = json.loads(cookie_data)

    # 2. Configura a sessão
    async with AsyncSession(cookies=cookies, impersonate="chrome120") as s:
        # Headers completos para evitar 401
        s.headers.update({
            "Accept": "application/json, text/plain, */*",
            "Referer": f"https://privacy.com.br/profile/{username}",
            "Origin": "https://privacy.com.br",
            "X-Requested-With": "XMLHttpRequest",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
            "Te": "trailers"
        })

        print(f"Buscando API Feed para: {username}...")

        # Tenta pegar os posts
        api_url = f"https://privacy.com.br/api/v1/feed/profile/{username}?offset=0&limit=20"
        
        try:
            resp = await s.get(api_url)
            
            if resp.status_code == 401:
                print("ERRO 401: Cookies expirados ou inválidos. Copie novamente o 'Cookie' da aba Network.")
                return []
            
            if resp.status_code != 200:
                print(f"ERRO API ({resp.status_code})")
                return []

            data = resp.json()
            
            # Valida sucesso real da API
            if not data.get("success"):
                print("API respondeu, mas success=false. Perfil privado ou não assinado.")
                return []

            posts = data.get("value", [])
            media_list = []

            for post in posts:
                if post.get("files"):
                    for file in post["files"]:
                        media_list.append({
                            "id": file.get("id"),
                            "url": file.get("url"),
                            "type": file.get("type")
                        })

            print(f"Sucesso! {len(media_list)} mídias encontradas.")
            return media_list

        except Exception as e:
            print(f"Erro processamento: {e}")
            return []