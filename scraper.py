import os, redis, json
from curl_cffi.requests import AsyncSession

r = redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379"))

async def list_media(username: str):
    # Força minúsculo para evitar erro de redirecionamento 301
    username = username.lower()
    
    # Recupera cookies
    cookie_data = r.get("privacy_cookies")
    if not cookie_data:
        print("ERRO: Nenhum cookie encontrado no Redis.")
        return []
        
    cookies = json.loads(cookie_data)
    
    # Debug: Confirma se o cookie de login está aqui
    if "auth_token" not in cookies:
        print("ALERTA: Cookie 'auth_token' faltando no scraper. O login provavelmente falhou antes.")

    async with AsyncSession(cookies=cookies, impersonate="chrome") as s:
        url = f"https://privacy.com.br/profile/{username}"
        print(f"Acessando: {url}")
        
        resp = await s.get(url)
        
        # Se for redirecionado para Checkout, o cookie não funcionou
        if "Checkout" in resp.text or "<title>Privacy | Checkout" in resp.text:
            print("ERRO FATAL: Redirecionado para Checkout. A assinatura não foi detectada.")
            return []

        # Procura o JSON mágico
        html = resp.text
        start_tag = '<script id="__NEXT_DATA__" type="application/json">'
        end_tag = '</script>'
        
        start_index = html.find(start_tag)
        if start_index == -1:
            print("ERRO: Estrutura da página não encontrada.")
            return []
            
        json_str = html[start_index + len(start_tag) : html.find(end_tag, start_index)]
        
        try:
            data = json.loads(json_str)
            # Tenta pegar a mídia
            try:
                # Caminho padrão
                media = data["props"]["pageProps"]["initialState"]["profile"]["media"]
            except KeyError:
                # Caminho alternativo
                media = data["props"]["pageProps"]["dehydratedState"]["queries"][0]["state"]["data"]["profile"]["media"]
                
            print(f"Sucesso! Encontradas {len(media)} mídias.")
            return media

        except Exception as e:
            print(f"Erro ao extrair mídia do JSON: {e}")
            return []