import os, redis, json, httpx
from bs4 import BeautifulSoup  # Se der erro de falta, avise, mas geralmente o pacote basicos tem. 
# Caso não tenha bs4, faremos via texto puro para garantir. Vou usar TEXTO PURO para não precisar instalar nada novo.

r = redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379"))

async def list_media(username: str):
    # Recupera cookies
    cookie_data = r.get("privacy_cookies")
    jar = json.loads(cookie_data) if cookie_data else {}
    
    # Headers de navegador real
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Referer": "https://privacy.com.br/",
    }

    async with httpx.AsyncClient(cookies=jar, headers=headers, follow_redirects=True) as cli:
        # Acessa a página do perfil (Porta da Frente)
        print(f"Acessando perfil: {username}...")
        resp = await cli.get(f"https://privacy.com.br/profile/{username}")
        
        if resp.status_code != 200:
            print(f"Erro ao acessar perfil: {resp.status_code}")
            return []

        # Procura pelo JSON escondido no HTML (Next.js Data)
        html = resp.text
        start_tag = '<script id="__NEXT_DATA__" type="application/json">'
        end_tag = '</script>'
        
        start_index = html.find(start_tag)
        if start_index == -1:
            print("ERRO: Não foi possível encontrar os dados na página (Estrutura mudou ou bloqueio severo).")
            # Salva o HTML para debug se precisar
            # with open("debug_error.html", "w", encoding="utf-8") as f: f.write(html)
            return []
            
        # Extrai apenas o pedaço do JSON
        start_index += len(start_tag)
        end_index = html.find(end_tag, start_index)
        json_str = html[start_index:end_index]
        
        try:
            data = json.loads(json_str)
            
            # Navega até a mídia (O caminho pode variar, vamos tentar o padrão)
            # Geralmente: props -> pageProps -> initialState -> profile -> media
            profile_data = data.get("props", {}).get("pageProps", {}).get("initialState", {}).get("profile", {})
            
            if not profile_data:
                # Tenta outro caminho comum
                profile_data = data.get("props", {}).get("pageProps", {}).get("dehydratedState", {}).get("queries", [{}])[0].get("state", {}).get("data", {}).get("profile", {})

            media = profile_data.get("media", [])
            print(f"Sucesso! Encontradas {len(media)} mídias.")
            return media

        except Exception as e:
            print(f"Erro ao processar dados da página: {e}")
            return []