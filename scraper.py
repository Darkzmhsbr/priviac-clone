import os, redis, json, httpx

# Conecta ao Redis
r = redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379"))

async def list_media(username: str):
    # Recupera cookies
    cookie_data = r.get("privacy_cookies")
    jar = json.loads(cookie_data) if cookie_data else {}
    
    # --- CAMUFLAGEM (HEADERS) ---
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Origin": "https://privacy.com.br",
        "Referer": f"https://privacy.com.br/profile/{username}",
        "Content-Type": "application/json"
    }

    async with httpx.AsyncClient(cookies=jar, headers=headers, follow_redirects=True) as cli:
        payload = {
            "query": f'{{profile(username: "{username}") {{media {{id, url, type}}}}}}'
        }
        
        # Faz a consulta
        resp = await cli.post("https://privacy.com.br/graphql", json=payload)
        
        # Debug: Se der erro, mostra no log o que veio (HTML ou Texto)
        if resp.status_code != 200:
            print(f"ERRO API ({resp.status_code}): {resp.text[:200]}")

        try:
            return resp.json()["data"]["profile"]["media"]
        except (json.JSONDecodeError, KeyError, TypeError):
            print(f"Falha ao ler JSON. Resposta recebida: {resp.text[:100]}...")
            return []