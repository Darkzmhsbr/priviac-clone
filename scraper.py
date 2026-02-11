import os, redis, json, re
from curl_cffi.requests import AsyncSession

r = redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379"))

async def list_media(username: str):
    username = username.lower()
    
    # 1. Recupera cookies
    cookie_data = r.get("privacy_cookies")
    if not cookie_data:
        print("ERRO: Cookies não encontrados no Redis.")
        return []
    
    cookies = json.loads(cookie_data)

    # 2. Sessão Chrome
    async with AsyncSession(cookies=cookies, impersonate="chrome120") as s:
        print(f"Rastreando mídia no perfil: {username}...")
        url = f"https://privacy.com.br/profile/{username}"
        
        try:
            resp = await s.get(url)
            html = resp.text

            # Debug: Se o título for de erro, nem tenta
            if "Just a moment" in html or "Access denied" in html:
                print("ERRO: Bloqueio do Cloudflare detectado na página HTML.")
                return []

            media_list = []
            seen_ids = set() # Para evitar duplicados

            # --- ESTRATÉGIA 1: BUSCA BRUTA POR LINKS DE VÍDEO/IMAGEM ---
            # Procura por padrões: "url":"https://..."
            # O Regex captura qualquer URL que comece com https e termine com aspas
            print("Iniciando varredura via Regex...")
            
            # Padrão para pegar objetos de arquivo: {"id":"...","url":"..."}
            # Isso é mais seguro que pegar qualquer link solto
            # Procura por blocos que tenham 'url' e 'type' próximos
            pattern = re.compile(r'"id":"(.*?)".*?"url":"(https://[^"]+)".*?"type":"(.*?)"')
            
            matches = pattern.findall(html)
            
            for m in matches:
                media_id, media_url, media_type = m
                
                # Limpa escapes de barra invertida (ex: https:\/\/ -> https://)
                media_url = media_url.replace("\\u002F", "/").replace("\\", "")
                
                if media_id not in seen_ids:
                    # Filtra apenas o que interessa (video/image)
                    if media_type in ["video", "image"]:
                        media_list.append({
                            "id": media_id,
                            "url": media_url,
                            "type": media_type
                        })
                        seen_ids.add(media_id)

            # --- ESTRATÉGIA 2: JSON (FALLBACK RELAXADO) ---
            # Se o Regex falhar, tentamos achar o JSON de forma mais genérica
            if not media_list:
                print("Regex não achou nada. Tentando busca profunda no JSON...")
                try:
                    # Procura apenas pelo ID, sem se importar com o type="application/json"
                    if 'id="__NEXT_DATA__"' in html:
                        start = html.find('id="__NEXT_DATA__"')
                        json_start = html.find('>', start) + 1
                        json_end = html.find('</script>', json_start)
                        json_str = html[json_start:json_end]
                        data = json.loads(json_str)
                        
                        # Tenta navegar até a mídia (vários caminhos possíveis)
                        def extract_media(obj):
                            if isinstance(obj, dict):
                                if "url" in obj and "type" in obj and ("video" in obj["type"] or "image" in obj["type"]):
                                    clean_url = obj["url"].replace("\\", "")
                                    if clean_url not in [m["url"] for m in media_list]:
                                        media_list.append({
                                            "id": obj.get("id", "unknown"),
                                            "url": clean_url,
                                            "type": obj["type"]
                                        })
                                for k, v in obj.items():
                                    extract_media(v)
                            elif isinstance(obj, list):
                                for item in obj:
                                    extract_media(item)
                        
                        extract_media(data)
                except Exception as e:
                    print(f"Erro na busca profunda: {e}")

            print(f"🎉 RASTREIO CONCLUÍDO! {len(media_list)} mídias encontradas.")
            return media_list

        except Exception as e:
            print(f"Erro crítico no scraper: {e}")
            return []