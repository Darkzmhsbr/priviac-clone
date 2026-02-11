import os, redis, json, httpx  # <--- Importações essenciais adicionadas

# Precisamos conectar ao Redis aqui também para ler os cookies
r = redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379"))

async def list_media(username: str):
    # Pega o cookie salvo ou cria um dicionário vazio se não existir
    cookie_data = r.get("privacy_cookies")
    jar = json.loads(cookie_data) if cookie_data else {}
    
    async with httpx.AsyncClient(cookies=jar) as cli:
        # Faz a consulta na API
        resp = await cli.post("https://privacy.com.br/graphql",
            json={"query": f'{{profile(username: "{username}") {{media {{id, url, type}}}}}}'})
        
        # Retorna a lista de mídias (ou lista vazia se der erro)
        try:
            return resp.json()["data"]["profile"]["media"]
        except (KeyError, TypeError):
            return []