from fastapi import FastAPI, HTTPException
import os, redis, json
from telegram import Bot
from auth import login_privacy
from scraper import list_media
from downloader import download
from uploader import send_tg

BOT_TOKEN = os.getenv("BOT_TOKEN")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

app = FastAPI()
bot = Bot(BOT_TOKEN) if BOT_TOKEN else None
r = redis.from_url(REDIS_URL)

@app.get("/")
async def home():
    if not bot:
        raise HTTPException(500, "BOT_TOKEN não configurado")
    me = await bot.get_me()
    return {"status": "on-line", "bot": me.username}

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/grab")
async def grab(profile: str, chat_id: int):
    # 1. login (cookie fica 1 h no Redis)
    # ATENÇÃO: Lembre-se de criar a variável PRIV_EMAIL no Railway!
    jar = await login_privacy(os.getenv("PRIV_EMAIL"), os.getenv("PRIV_PASS"))
    
    # 2. lista mídias
    media = await list_media(profile)
    if not media:
        return {"ok": 0, "msg": "nenhuma mídia"}
    
    # 3. baixa e envia
    for m in media[:5]:
        tmp = await download(m["url"])
        await send_tg(chat_id, tmp, m["id"])
    return {"ok": len(media)}