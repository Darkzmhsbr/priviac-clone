from fastapi import FastAPI, HTTPException
import os, redis, json
from telegram import Bot
from auth import login_privacy
from scraper import list_media
from downloader import download
from uploader import send_tg

BOT_TOKEN = os.getenv("BOT_TOKEN")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
DEFAULT_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

app = FastAPI()
bot = Bot(BOT_TOKEN) if BOT_TOKEN else None
r = redis.from_url(REDIS_URL)

@app.get("/")
async def home():
    if not bot: raise HTTPException(500, "BOT_TOKEN não configurado")
    me = await bot.get_me()
    return {"status": "on-line", "bot": me.username}

@app.get("/health")
def health(): return {"status": "ok"}

@app.post("/grab")
async def grab(profile: str, chat_id: str = None):
    target_chat_id = chat_id if chat_id else DEFAULT_CHAT_ID
    if not target_chat_id: return {"ok": 0, "msg": "ERRO: Faltou chat_id."}

    # Login rápido (Refresh cookie)
    await login_privacy("check", "check")
    
    print(f"🚀 Extraindo de: {profile}")
    media = await list_media(profile)
    
    if not media: return {"ok": 0, "msg": "Nenhuma mídia encontrada."}
    
    count = 0
    # Monta a URL do perfil para usar como 'Referer' e enganar o servidor
    profile_url = f"https://privacy.com.br/profile/{profile}"
    
    print(f"📤 Baixando e enviando {len(media)} arquivos...")
    
    for m in media[:5]:
        # AQUI MUDOU: Passamos o profile_url
        tmp_path = await download(m["url"], profile_url)
        
        if tmp_path:
            try:
                print(f"✈️ Enviando Telegram...")
                await send_tg(target_chat_id, tmp_path, caption=f"Mídia ID: {m['id']}")
                count += 1
                print("✅ Enviado!")
            except Exception as e:
                print(f"❌ Erro Telegram: {e}")
        else:
            print("Pulei (erro download).")
            
    return {"ok": count, "total": len(media)}