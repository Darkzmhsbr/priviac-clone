import redis, json, os
from curl_cffi.requests import AsyncSession

r = redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379"))

async def login_privacy(email: str, password: str):
    if not email or not password:
        print("ERRO: Email ou Senha vazios.")
        return None

    # Usamos chrome120 para garantir uma assinatura digital moderna
    async with AsyncSession(impersonate="chrome120") as s:
        print(f"Iniciando fluxo de login para: {email}...")

        # PASSO 1: AQUECIMENTO (Acessar a página de login para pegar cookies de sessão/CSRF)
        # Isso engana o sistema de segurança, mostrando que somos um navegador "visitando" o site
        try:
            print("1. Acessando página de login (Aquecimento)...")
            await s.get("https://privacy.com.br/auth/login")
        except Exception as e:
            print(f"Erro no aquecimento: {e}")
            return None

        # PASSO 2: O LOGIN REAL
        # Agora que já temos os cookies da visita, mandamos as credenciais
        print("2. Enviando credenciais...")
        
        payload = {
            "userName": email,
            "password": password,
            "keepConnected": True
        }
        
        # Headers essenciais para parecer que o clique veio do botão de login
        s.headers.update({
            "Origin": "https://privacy.com.br",
            "Referer": "https://privacy.com.br/auth/login",
            "X-Requested-With": "XMLHttpRequest" # Diz que é uma chamada de site moderno (AJAX)
        })
        
        try:
            resp = await s.post("https://privacy.com.br/api/v1/account/login", json=payload)
            
            # Debug se falhar o JSON
            try:
                data = resp.json()
            except:
                # Se não vier JSON, provavelmente fomos bloqueados ou redirecionados
                print(f"ERRO: Resposta não é JSON. Status: {resp.status_code}")
                # Salva o HTML para você ver o erro real se precisar
                # print(f"Conteúdo recebido: {resp.text[:200]}") 
                return None

            # PASSO 3: VALIDAÇÃO
            if data.get("success") is True and data.get("authenticated") is True:
                print("LOGIN COM SUCESSO! 🔓")
                
                cookies = s.cookies.get_dict()
                
                # Verificação extra de segurança
                if "auth_token" in cookies:
                    print("Cookie Mestre (auth_token) capturado.")
                else:
                    print("AVISO: Logou, mas auth_token não apareceu. Pode falhar no download.")

                r.setex("privacy_cookies", 3600, json.dumps(cookies))
                return cookies
            else:
                msg = data.get("message", "Erro desconhecido")
                print(f"FALHA NO LOGIN (Recusado pelo site): {msg}")
                return None

        except Exception as e:
            print(f"Erro crítico durante o POST de login: {e}")
            return None