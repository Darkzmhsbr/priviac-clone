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
    try:
        me = await bot.get_me()
        return {"status": "on-line", "bot": me.username}
    except Exception as e:
        return {"status": "erro", "detalhe": str(e)}

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/grab")
async def grab(profile: str, chat_id: int):
    # 1. Tenta Logar
    email = os.getenv("PRIV_EMAIL")
    senha = os.getenv("PRIV_PASS")
    
    # Debug: Mostra no log se as variáveis estão vazias (sem mostrar a senha)
    if not email:
        print("ALERTA: Variável PRIV_EMAIL está vazia!")
    
    jar = await login_privacy(email, senha)
    
    # TRAVA DE SEGURANÇA: Se o login falhou, aborta a missão.
    if not jar:
        return {"ok": 0, "msg": "ERRO DE LOGIN: Verifique o log do Railway para ver o motivo (Senha errada? Captcha?)"}
    
    # 2. Lista mídias
    print(f"Buscando mídia de {profile}...")
    media = await list_media(profile)
    
    if not media:
        return {"ok": 0, "msg": "Nenhuma mídia encontrada (Perfil vazio ou bloqueio)"}
    
    # 3. Baixa e envia
    count = 0
    for m in media[:5]:
        try:
            tmp = await download(m["url"])
            if tmp:
                await send_tg(chat_id, tmp, m["id"])
                count += 1
        except Exception as e:
            print(f"Erro no envio: {e}")
            
    return {"ok": count, "total_encontrado": len(media)}