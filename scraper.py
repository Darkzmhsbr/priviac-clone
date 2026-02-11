import os, redis, json, httpx

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
        
        # --- BLOCO DE CORREÇÃO E TRATAMENTO DE ERROS ---
        
        # 1. Verifica se a resposta veio vazia
        if not resp.text.strip():
            raise RuntimeError("Resposta vazia – Pode ser cookie inválido, perfil privado ou bloqueio de IP.")

        # 2. Tenta converter para JSON
        try:
            data = resp.json()
        except Exception as e:
            # Se falhar (ex: recebeu HTML de erro do Cloudflare), mostra o início do texto no log
            raise RuntimeError(f"JSON inválido recebido: {resp.text[:200]}") from e

        # 3. Tenta acessar os dados da mídia
        try:
            return data["data"]["profile"]["media"]
        except (KeyError, TypeError):
            # Se o JSON veio, mas a estrutura mudou ou o perfil não tem mídia
            return []