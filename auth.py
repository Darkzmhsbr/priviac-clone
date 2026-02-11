import redis, json, httpx, os  # <--- Adicionei 'os' aqui

# Conecta ao Redis (garante que pega a URL correta ou usa local como fallback)
r = redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379"))

async def login_privacy(username: str, password: str):
    jar = httpx.Cookies()
    async with httpx.AsyncClient(cookies=jar, timeout=15) as cli:
        # Faz o login
        await cli.post("https://privacy.com.br/auth", data={"username": username, "password": password})
        
        # Salva o cookie no Redis por 1 hora (3600 segundos)
        r.setex("privacy_cookies", 3600, json.dumps(dict(jar)))
        return jar