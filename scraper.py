import os, redis, json
from curl_cffi.requests import AsyncSession

r = redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379"))

async def list_media(username: str):
    username = username.lower()
    
    # 1. Recupera cookies (já limpos pelo auth.py)
    cookie_data = r.get("privacy_cookies")
    if not cookie_data:
        print("ERRO: Cookies não encontrados no Redis.")
        return []
    
    cookies = json.loads(cookie_data)

    # 2. Sessão Chrome
    async with AsyncSession(cookies=cookies, impersonate="chrome120") as s:
        # Headers idênticos aos de uma navegação real (feed)
        s.headers.update({
            "Accept": "application/json, text/plain, */*",
            "Referer": f"https://privacy.com.br/profile/{username}",
            "Origin": "https://privacy.com.br",
            "X-Requested-With": "XMLHttpRequest"
        })

        print(f"📡 Tentando API Feed para: {username}...")
        
        # URL da API que carrega o feed (Offset 0 = posts mais recentes)
        api_url = f"https://privacy.com.br/api/v1/feed/profile/{username}?offset=0&limit=20"
        
        try:
            resp = await s.get(api_url)
            
            # --- DIAGNÓSTICO DE ERRO (O Pulo do Gato) ---
            if resp.status_code != 200:
                print(f"❌ ERRO API: Status {resp.status_code}")
                # Mostra o título da página de erro para sabermos se é Cloudflare
                if "<title>" in resp.text:
                    start = resp.text.find("<title>") + 7
                    end = resp.text.find("</title>")
                    print(f"📄 Título da página recebida: {resp.text[start:end]}")
                else:
                    print(f"📄 Conteúdo (início): {resp.text[:200]}")
                return []
            
            # Verifica se veio JSON ou se o site devolveu HTML disfarçado de 200
            try:
                data = resp.json()
            except json.JSONDecodeError:
                print("⚠️ ALERTA: O site retornou 200 OK, mas o conteúdo é HTML (Bloqueio).")
                if "<title>" in resp.text:
                    start = resp.text.find("<title>") + 7
                    end = resp.text.find("</title>")
                    print(f"📄 Título real da página: {resp.text[start:end]}")
                return []

            # Se chegou aqui, temos dados!
            if not data.get("success"):
                print(f"⚠️ API Recusou: {data.get('error') or data.get('message') or 'Sem mensagem'}")
                return []

            posts = data.get("value", [])
            media_list = []

            print(f"🔎 Analisando {len(posts)} posts...")

            for post in posts:
                # Onde a mágica acontece: extrai vídeos e imagens
                if post.get("files"):
                    for file in post["files"]:
                        media_list.append({
                            "id": file.get("id"),
                            "url": file.get("url"),
                            "type": file.get("type", "unknown")
                        })
            
            if len(media_list) > 0:
                print(f"🎉 SUCESSO! {len(media_list)} mídias encontradas via API.")
            else:
                print("⚠️ Acesso permitido, mas nenhuma mídia encontrada nos primeiros 20 posts.")

            return media_list

        except Exception as e:
            print(f"🔥 Erro crítico no scraper: {e}")
            return []