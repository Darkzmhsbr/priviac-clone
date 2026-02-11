import os, redis, json
from curl_cffi.requests import AsyncSession

r = redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379"))

async def list_media(username: str):
    username = username.lower()
    
    cookie_data = r.get("privacy_cookies")
    if not cookie_data:
        print("ERRO: Nenhum cookie encontrado no Redis.")
        return []
        
    cookies = json.loads(cookie_data)
    
    # Camuflagem de Chrome
    async with AsyncSession(cookies=cookies, impersonate="chrome120") as s:
        url = f"https://privacy.com.br/profile/{username}"
        print(f"Acessando: {url}")
        
        resp = await s.get(url)
        
        # Verifica se caiu no Checkout (login inválido)
        if "Checkout" in resp.text or "<title>Privacy | Checkout" in resp.text:
            print("ERRO FATAL: Redirecionado para Checkout. O Cookie Mestre pode ter expirado ou estar errado.")
            return []

        html = resp.text
        start_tag = '<script id="__NEXT_DATA__" type="application/json">'
        end_tag = '</script>'
        
        start_index = html.find(start_tag)
        if start_index == -1:
            print("ERRO: Dados da página não encontrados. O site pode ter mudado o layout.")
            return []
            
        json_str = html[start_index + len(start_tag) : html.find(end_tag, start_index)]
        
        try:
            data = json.loads(json_str)
            try:
                media = data["props"]["pageProps"]["initialState"]["profile"]["media"]
            except KeyError:
                media = data["props"]["pageProps"]["dehydratedState"]["queries"][0]["state"]["data"]["profile"]["media"]
                
            print(f"Sucesso! Encontradas {len(media)} mídias.")
            return media

        except Exception as e:
            print(f"Erro ao ler JSON da página: {e}")
            return []