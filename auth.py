import redis, json, os
from curl_cffi.requests import AsyncSession

r = redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379"))

def parse_cookie_string(cookie_string):
    """Transforma a string bruta do navegador em um dicionário Python"""
    cookies = {}
    if not cookie_string:
        return cookies
    
    # Separa por ponto e vírgula
    items = cookie_string.split(';')
    for item in items:
        if '=' in item:
            name, value = item.split('=', 1)
            cookies[name.strip()] = value.strip()
    return cookies

async def login_privacy(email: str, password: str):
    # --- MODO BYPASS TOTAL (Cookies Brutos) ---
    cookie_master = os.getenv("COOKIE_MASTER")
    
    if cookie_master:
        print("🚀 MODO BYPASS: Processando string completa de cookies...")
        
        # Transforma o texto gigante em dicionário
        cookies = parse_cookie_string(cookie_master)
        
        # Verifica se tem os essenciais
        if ".AspNetCore.Cookies" in cookies:
            print(f"Cookie principal detectado! (Carregados {len(cookies)} cookies auxiliares)")
        else:
            print("AVISO: String carregada, mas não achei o .AspNetCore.Cookies. Pode falhar.")

        # Salva no Redis
        r.setex("privacy_cookies", 3600, json.dumps(cookies))
        return cookies

    # --- MODO AUTOMÁTICO (Desativado se tiver Cookie Master) ---
    print("ERRO: COOKIE_MASTER inválido ou vazio. O login automático falhou anteriormente.")
    return None