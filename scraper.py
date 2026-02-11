import os, redis, json
from curl_cffi.requests import AsyncSession

r = redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379"))

async def list_media(username: str):
    # Recupera cookies
    cookie_data = r.get("privacy_cookies")
    cookies = json.loads(cookie_data) if cookie_data else {}
    
    # Camuflagem perfeita de Chrome
    async with AsyncSession(cookies=cookies, impersonate="chrome") as s:
        print(f"Acessando perfil (Modo Chrome): {username}...")
        
        # Acessa a página
        resp = await s.get(f"https://privacy.com.br/profile/{username}")
        
        if resp.status_code != 200:
            print(f"Erro HTTP: {resp.status_code}")
            return []

        html = resp.text
        
        # Procura o JSON mágico (__NEXT_DATA__)
        start_tag = '<script id="__NEXT_DATA__" type="application/json">'
        end_tag = '</script>'
        
        start_index = html.find(start_tag)
        if start_index == -1:
            # Se cair aqui, vamos ver o título da página para saber se é bloqueio
            title_start = html.find('<title>')
            title_end = html.find('</title>')
            title = html[title_start:title_end] if title_start != -1 else "Sem título"
            print(f"ERRO: Dados não encontrados. Título da página: {title}")
            return []
            
        # Extrai e converte o JSON
        start_index += len(start_tag)
        end_index = html.find(end_tag, start_index)
        json_str = html[start_index:end_index]
        
        try:
            data = json.loads(json_str)
            
            # Navega até a mídia (Caminho padrão do Privacy)
            try:
                profile = data["props"]["pageProps"]["initialState"]["profile"]
            except KeyError:
                # Tenta caminho alternativo
                try:
                    profile = data["props"]["pageProps"]["dehydratedState"]["queries"][0]["state"]["data"]["profile"]
                except:
                    print("Estrutura do JSON mudou ou perfil não carregou.")
                    return []

            media = profile.get("media", [])
            print(f"Sucesso! Encontradas {len(media)} mídias.")
            return media

        except Exception as e:
            print(f"Erro ao processar JSON: {e}")
            return []