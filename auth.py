import redis, json, os
from curl_cffi.requests import AsyncSession

r = redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379"))

async def login_privacy(email: str, password: str):
    if not email or not password:
        print("ERRO CRÍTICO: Email ou Senha não definidos nas Variáveis do Railway!")
        return None

    async with AsyncSession(impersonate="chrome") as s:
        print(f"Tentando logar na API com: {email}...")
        
        # Payload em JSON (O segredo está aqui: userName com N maiúsculo às vezes importa)
        payload = {
            "userName": email,
            "password": password,
            "keepConnected": True
        }
        
        # Batendo direto na API de conta, não na página HTML
        # Tentativa 1: Endpoint de API padrão
        try:
            resp = await s.post("https://privacy.com.br/api/v1/account/login", json=payload)
        except Exception as e:
            print(f"Erro de conexão no login: {e}")
            return None

        # Verifica sucesso
        if resp.status_code == 200:
            # Verifica se o retorno tem cara de sucesso (token ou usuário)
            if "token" in resp.text or "usuario" in resp.text or "success" in resp.text.lower():
                print("Login realizado com SUCESSO! Salvando sessão...")
                cookies = s.cookies.get_dict()
                r.setex("privacy_cookies", 3600, json.dumps(cookies))
                return cookies
            else:
                print(f"Login respondeu 200 mas sem confirmação clara: {resp.text[:100]}")
                # Tentamos salvar mesmo assim
                cookies = s.cookies.get_dict()
                r.setex("privacy_cookies", 3600, json.dumps(cookies))
                return cookies
        else:
            print(f"FALHA NO LOGIN (Status {resp.status_code}).")
            print(f"Resposta do site: {resp.text[:200]}")
            return None