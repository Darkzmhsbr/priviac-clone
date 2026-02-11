import redis, json, os
from curl_cffi.requests import AsyncSession

r = redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379"))

async def login_privacy(email: str, password: str):
    # impersonate="chrome" faz o servidor achar que somos o navegador real
    async with AsyncSession(impersonate="chrome") as s:
        
        # 1. Acessa a home para pegar tokens iniciais
        await s.get("https://privacy.com.br/")
        
        # 2. Faz o login
        payload = {"username": email, "password": password}
        resp = await s.post("https://privacy.com.br/auth", data=payload)
        
        if resp.status_code == 200:
            # Pega os cookies da sessão
            cookies_dict = s.cookies.get_dict()
            # Salva no Redis
            r.setex("privacy_cookies", 3600, json.dumps(cookies_dict))
            return cookies_dict
        else:
            print(f"Falha login: {resp.status_code} - {resp.text[:100]}")
            return None