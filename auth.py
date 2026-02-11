import redis, json, httpx, os

r = redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379"))

async def login_privacy(email: str, password: str):
    # --- CAMUFLAGEM (HEADERS) ---
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Origin": "https://privacy.com.br",
        "Referer": "https://privacy.com.br/auth/login"
    }

    jar = httpx.Cookies()
    async with httpx.AsyncClient(cookies=jar, headers=headers) as cli:
        # Tenta logar
        resp = await cli.post("https://privacy.com.br/auth", data={"username": email, "password": password})
        
        # Verifica se logou
        if resp.status_code == 200:
            # Salva cookie no Redis
            r.setex("privacy_cookies", 3600, json.dumps(dict(jar)))
            return jar
        else:
            print(f"Falha no login: {resp.status_code}")
            return None