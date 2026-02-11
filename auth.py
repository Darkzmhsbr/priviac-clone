import redis, json, os
from curl_cffi.requests import AsyncSession

r = redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379"))

async def login_privacy(email: str, password: str):
    if not email or not password:
        print("ERRO: Email ou Senha vazios.")
        return None

    async with AsyncSession(impersonate="chrome") as s:
        print(f"Tentando logar: {email}...")
        
        payload = {
            "userName": email,
            "password": password,
            "keepConnected": True
        }
        
        try:
            # Bate na API de Login
            resp = await s.post("https://privacy.com.br/api/v1/account/login", json=payload)
            
            # Converte a resposta para JSON ( dicionário Python )
            try:
                data = resp.json()
            except:
                print(f"ERRO: API não retornou JSON. Texto: {resp.text[:100]}")
                return None

            # AQUI ESTÁ A CORREÇÃO: Verifica se success é True
            if data.get("success") is True and data.get("authenticated") is True:
                print("Login CONFIRMADO! Cookies capturados.")
                
                # Pega os cookies da sessão
                cookies = s.cookies.get_dict()
                
                # Debug: Mostra se pegou o cookie principal (auth_token)
                if "auth_token" in cookies:
                    print("Cookie 'auth_token' encontrado! Acesso garantido.")
                else:
                    print("AVISO: 'auth_token' não encontrado nos cookies (Pode dar erro).")

                r.setex("privacy_cookies", 3600, json.dumps(cookies))
                return cookies
            else:
                # Se o login falhou (senha errada, etc), mostra o erro real
                msg = data.get("message", "Erro desconhecido")
                print(f"FALHA NO LOGIN: {msg}")
                return None

        except Exception as e:
            print(f"Erro crítico no login: {e}")
            return None