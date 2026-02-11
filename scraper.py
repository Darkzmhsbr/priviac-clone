import os, redis, json
from curl_cffi.requests import AsyncSession

r = redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379"))

async def list_media(username: str):
    username = username.lower()
    
    cookie_data = r.get("privacy_cookies")
    if not cookie_data:
        print("ERRO: Cookies não encontrados.")
        return []
    
    cookies = json.loads(cookie_data)

    # Impersonate 'chrome120' é ótimo, mas se falhar, tentaremos ser mais simples na proxima
    async with AsyncSession(cookies=cookies, impersonate="chrome120") as s:
        # Headers mínimos e essenciais (muitos headers as vezes atrapalham)
        s.headers.update({
            "Accept": "application/json, text/plain, */*",
            "Referer": f"https://privacy.com.br/profile/{username}",
            "Origin": "https://privacy.com.br",
            "X-Requested-With": "XMLHttpRequest"
        })

        print(f"Buscando API Feed para: {username}...")
        api_url = f"https://privacy.com.br/api/v1/feed/profile/{username}?offset=0&limit=20"
        
        try:
            resp = await s.get(api_url)
            
            # Se não for JSON, vamos descobrir o que é
            try:
                data = resp.json()
            except json.JSONDecodeError:
                print(f"❌ ERRO DE BLOQUEIO (Status {resp.status_code})")
                print("O site devolveu HTML em vez de JSON. Veja o conteúdo:")
                
                # Pega o título da página para saber o erro
                try:
                    html_content = resp.text
                    title_start = html_content.find("<title>") + 7
                    title_end = html_content.find("</title>")
                    if title_start > 6 and title_end > title_start:
                        print(f"Título da Página: {html_content[title_start:title_end]}")
                    else:
                        print(f"Início do conteúdo: {html_content[:100]}")
                except:
                    pass
                return []

            # Se chegou aqui, é JSON válido!
            if not data.get("success"):
                print("API respondeu success=false. Perfil privado ou erro de conta.")
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

            print(f"🎉 SUCESSO! {len(media_list)} mídias extraídas.")
            return media_list

        except Exception as e:
            print(f"Erro crítico: {e}")
            return []