import redis, json, os
from curl_cffi.requests import AsyncSession

r = redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379"))

def parse_cookie_string(cookie_string):
    """Transforma a string bruta e remove cookies de IP que bloqueiam o bot"""
    cookies = {}
    if not cookie_string:
        return cookies
    
    # Separa por ponto e vírgula
    items = cookie_string.split(';')
    for item in items:
        if '=' in item:
            name, value = item.split('=', 1)
            name = name.strip()
            value = value.strip()
            
            # FILTRO MESTRE: Ignora cookies do Cloudflare vinculados ao IP antigo
            # Mantemos apenas os cookies essenciais de sessão e rastreio de app
            if name.startswith("__cf") or name.startswith("cf_") or name == "_cfuvid":
                continue
                
            cookies[name] = value
            
    return cookies

async def login_privacy(email: str, password: str):
    # --- MODO BYPASS TOTAL ---
    cookie_master = os.getenv("COOKIE_MASTER")
    
    if cookie_master:
        print("🚀 MODO BYPASS: Filtrando cookies de IP...")
        
        # Limpa os cookies ruins
        cookies = parse_cookie_string(cookie_master)
        
        # Verifica se o principal sobrou
        if ".AspNetCore.Cookies" in cookies:
            print(f"✅ Cookie de Login APROVADO! (Total limpo: {len(cookies)} cookies)")
        else:
            print("⚠️ AVISO: O Cookie de Login (.AspNetCore.Cookies) sumiu ou não estava na lista!")

        r.setex("privacy_cookies", 3600, json.dumps(cookies))
        return cookies

    print("ERRO: COOKIE_MASTER não definido.")
    return None