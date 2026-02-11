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

    async with AsyncSession(cookies=cookies, impersonate="chrome120") as s:
        # Headers para parecer navegação real
        s.headers.update({
            "Accept": "application/json, text/plain, */*",
            "Referer": f"https://privacy.com.br/profile/{username}",
            "Origin": "https://privacy.com.br"
        })

        media_list = []
        
        # --- TENTATIVA 1: API DIRETA (Melhor qualidade) ---
        print(f"📡 Tentando API Feed para: {username}...")
        try:
            # Timestamp para evitar cache
            api_url = f"https://privacy.com.br/api/v1/feed/profile/{username}?offset=0&limit=20"
            resp = await s.get(api_url)
            
            # Verifica se veio JSON real
            try:
                data = resp.json()
                # Se for HTML disfarçado, vai dar erro aqui ou na checagem de success
                if data.get("success") and "value" in data:
                    print(f"✅ API respondeu! Processando {len(data['value'])} posts...")
                    for post in data["value"]:
                        if post.get("files"):
                            for file in post["files"]:
                                media_list.append({
                                    "id": file.get("id"),
                                    "url": file.get("url"),
                                    "type": file.get("type", "unknown")
                                })
            except:
                print("⚠️ API retornou HTML (Bloqueio ou Redirecionamento). Indo para Plano B...")
        except Exception as e:
            print(f"Erro na API: {e}")

        # --- TENTATIVA 2: LEITURA PROFUNDA DA PÁGINA (Plano B) ---
        if not media_list:
            print("🕵️‍♂️ Acessando página do perfil para busca profunda...")
            try:
                # Mudamos o header para aceitar HTML agora
                s.headers.update({"Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"})
                resp = await s.get(f"https://privacy.com.br/profile/{username}")
                html = resp.text
                
                # BUSCA INTELIGENTE DO NEXT_DATA (Regex robusto)
                # Procura: <script ... id="__NEXT_DATA__" ... > ...json... </script>
                # Não importa a ordem dos atributos (id, type, etc)
                script_pattern = re.compile(r'<script[^>]*id="__NEXT_DATA__"[^>]*>(.*?)</script>', re.DOTALL)
                match = script_pattern.search(html)
                
                if match:
                    print("📦 JSON Oculto (__NEXT_DATA__) encontrado! Extraindo dados...")
                    json_str = match.group(1)
                    data = json.loads(json_str)
                    
                    # Função recursiva para achar "media" onde quer que ela esteja escondida
                    def find_media_in_json(obj):
                        found = []
                        if isinstance(obj, dict):
                            # Se achou um objeto com url e type, é mídia
                            if "url" in obj and "type" in obj:
                                if "video" in obj["type"] or "image" in obj["type"]:
                                    found.append(obj)
                            # Continua procurando dentro do dicionário
                            for v in obj.values():
                                found.extend(find_media_in_json(v))
                        elif isinstance(obj, list):
                            for item in obj:
                                found.extend(find_media_in_json(item))
                        return found
                    
                    # Extrai tudo que parece mídia desse JSON gigante
                    raw_media = find_media_in_json(data)
                    
                    for item in raw_media:
                        # Limpa URLs
                        clean_url = item["url"].replace("\\", "")
                        media_list.append({
                            "id": item.get("id", "json_found"),
                            "url": clean_url,
                            "type": item.get("type")
                        })
                else:
                    print("❌ JSON Oculto não encontrado. O site pode ter mudado a estrutura.")

            except Exception as e:
                print(f"Erro na leitura da página: {e}")

        # --- FILTRO FINAL (A Correção da Mira) 🎯 ---
        # Remove lixo (logos, avatares, favicons) e duplicados
        clean_list = []
        seen_urls = set()
        
        print(f"🧹 Filtrando {len(media_list)} itens encontrados...")
        
        for m in media_list:
            u = m["url"]
            # LISTA NEGRA: O que NÃO queremos baixar
            if "privacy-og.jpg" in u or "avatar" in u or "favicon" in u or "logo" in u or ".svg" in u:
                continue
                
            if u not in seen_urls:
                clean_list.append(m)
                seen_urls.add(u)

        if clean_list:
            print(f"🎉 SUCESSO! {len(clean_list)} mídias VÁLIDAS prontas para download.")
        else:
            print("⚠️ Nenhuma mídia válida encontrada (apenas logos/lixo foram filtrados).")

        return clean_list