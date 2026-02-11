import os, redis, json
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

    # 2. Sessão Chrome
    async with AsyncSession(cookies=cookies, impersonate="chrome120") as s:
        print(f"Acessando perfil visual: {username}...")
        
        # Vamos direto na página do perfil (já que a API redireciona pra lá mesmo)
        url = f"https://privacy.com.br/profile/{username}"
        
        try:
            resp = await s.get(url)
            
            # 3. Procura os dados escondidos no HTML
            html = resp.text
            
            # O tesouro está dentro da tag <script id="__NEXT_DATA__">
            start_tag = '<script id="__NEXT_DATA__" type="application/json">'
            end_tag = '</script>'
            
            start_index = html.find(start_tag)
            if start_index == -1:
                print(f"ERRO: Tag de dados não encontrada. Título da página: {html[html.find('<title>'):html.find('</title>')]}")
                return []
            
            # Recorta só o JSON
            json_start = start_index + len(start_tag)
            json_end = html.find(end_tag, json_start)
            json_str = html[json_start:json_end]
            
            data = json.loads(json_str)
            
            # 4. Navega pelo JSON para achar a mídia
            # A estrutura muda às vezes, então vamos tentar vários caminhos
            media_list = []
            
            # Caminho 1: Dados do Perfil Direto
            try:
                profile_data = data["props"]["pageProps"]["initialState"]["profile"]
                if "media" in profile_data:
                    raw_media = profile_data["media"]
                else:
                    # Caminho 2: React Query (Dehydrated State) - Mais comum hoje em dia
                    queries = data["props"]["pageProps"]["dehydratedState"]["queries"]
                    raw_media = []
                    for q in queries:
                        # Procura a query que tem dados de 'media' ou 'feed'
                        if "state" in q and "data" in q["state"]:
                            content = q["state"]["data"]
                            # Pode estar dentro de 'profile' -> 'media'
                            if "profile" in content and "media" in content["profile"]:
                                raw_media.extend(content["profile"]["media"])
                            # Ou pode ser uma lista de posts direta
                            elif "value" in content and isinstance(content["value"], list):
                                # Verifica se parece post de feed
                                raw_media.extend(content["value"])

            except Exception as e:
                print(f"Aviso: Falha ao navegar na estrutura padrão ({e}). Tentando busca bruta...")
                raw_media = []

            # 5. Extrai os links limpos
            # Agora varremos o que achamos para pegar só id e url
            for item in raw_media:
                # Se for estrutura de Mídia direta
                if "url" in item and "type" in item:
                     media_list.append(item)
                
                # Se for estrutura de Post (tem arquivos dentro)
                elif "files" in item:
                    for f in item["files"]:
                        media_list.append(f)

            print(f"🎉 SUCESSO ABSOLUTO! {len(media_list)} mídias encontradas na página.")
            return media_list

        except Exception as e:
            print(f"Erro crítico no scraper: {e}")
            return []