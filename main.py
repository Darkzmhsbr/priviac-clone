from fastapi import FastAPI, HTTPException
import os, redis, json
from telegram import Bot
from auth import login_privacy
from scraper import list_media
from downloader import download
from uploader import send_tg

BOT_TOKEN = os.getenv("BOT_TOKEN")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

# Pega o Chat ID das variáveis de ambiente
DEFAULT_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

app = FastAPI()
bot = Bot(BOT_TOKEN) if BOT_TOKEN else None
r = redis.from_url(REDIS_URL)

@app.get("/")
async def home():
    if not bot:
        raise HTTPException(500, "BOT_TOKEN não configurado")
    try:
        me = await bot.get_me()
        return {"status": "on-line", "bot": me.username}
    except Exception as e:
        return {"status": "erro", "detalhe": str(e)}

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/grab")
async def grab(profile: str, chat_id: str = None):
    # Se não informar chat_id na URL, usa o da variável de ambiente
    target_chat_id = chat_id if chat_id else DEFAULT_CHAT_ID
    
    if not target_chat_id:
        return {"ok": 0, "msg": "ERRO: TELEGRAM_CHAT_ID não definido nas variáveis e nem na URL."}

    # 1. Login (Verifica cookies)
    email = os.getenv("PRIV_EMAIL")
    senha = os.getenv("PRIV_PASS")
    
    # O auth.py atual já cuida da limpeza, só chamamos para garantir
    jar = await login_privacy(email, senha)
    if not jar:
        return {"ok": 0, "msg": "Falha no login/cookies."}
    
    # 2. Lista mídias
    print(f"🚀 Iniciando extração para: {profile}")
    media = await list_media(profile)
    
    if not media:
        return {"ok": 0, "msg": "Nenhuma mídia encontrada."}
    
    # 3. Baixa e Envia
    count = 0
    print(f"📤 Preparando envio para ID: {target_chat_id}")
    
    # Limite de 5 para não travar o servidor, aumente depois se quiser
    for m in media[:5]:
        tmp_path = await download(m["url"])
        
        if tmp_path:
            try:
                print(f"✈️ Enviando para Telegram...")
                await send_tg(target_chat_id, tmp_path, caption=f"Mídia ID: {m['id']}")
                count += 1
                print("✅ Enviado!")
            except Exception as e:
                print(f"❌ Erro ao enviar pro Telegram: {e}")
        else:
            print("Pulei envio (download falhou).")
            
    return {"ok": count, "total_encontrado": len(media)}