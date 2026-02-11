import redis, json, os
from curl_cffi.requests import AsyncSession

r = redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379"))

async def login_privacy(email: str, password: str):
    # --- MODO BYPASS MANUAL ---
    cookie_mestre = os.getenv("COOKIE_MASTER")
    
    if cookie_mestre:
        print("🚀 MODO BYPASS: Usando Cookie Mestre (.AspNetCore.Cookies)!")
        
        # AQUI ESTÁ A CORREÇÃO: Usamos o nome que aparece na sua imagem
        cookies = {
            ".AspNetCore.Cookies": cookie_mestre, 
            "accepted-privacy-terms": "1",
            "user-accepted-cookies": "true"
        }
        
        # Se houver um cookie de sessão secundário, tentamos adicionar (opcional)
        # cookies[".AspNetCore.Session"] = "..." 
        
        r.setex("privacy_cookies", 3600, json.dumps(cookies))
        return cookies

    # --- MODO AUTOMÁTICO (Só roda se não tiver cookie mestre) ---
    print("Tentando login automático (Não recomendado se tiver COOKIE_MASTER)...")
    async with AsyncSession(impersonate="chrome120") as s:
        try:
            await s.get("https://privacy.com.br/auth/login")
            payload = {"userName": email, "password": password, "keepConnected": True}
            s.headers.update({"Origin": "https://privacy.com.br", "Referer": "https://privacy.com.br/auth/login"})
            
            resp = await s.post("https://privacy.com.br/api/v1/account/login", json=payload)
            data = resp.json()

            if data.get("success") is True:
                print("Login automático SUCESSO!")
                cookies = s.cookies.get_dict()
                r.setex("privacy_cookies", 3600, json.dumps(cookies))
                return cookies
            else:
                print(f"Falha login: {data.get('message')}")
                return None
        except Exception as e:
            print(f"Erro login auto: {e}")
            return None