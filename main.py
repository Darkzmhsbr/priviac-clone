from fastapi import FastAPI
import os
from telegram import Bot

# Pega o token das variáveis de ambiente
BOT_TOKEN = os.getenv("BOT_TOKEN")

app = FastAPI()

# Inicializa o bot (no modo assíncrono v20+, a inicialização é leve)
# Se o token não existir, evitamos quebrar o app logo no início
if BOT_TOKEN:
    bot = Bot(BOT_TOKEN)
else:
    bot = None

@app.get("/")
async def home():  # <--- MUDANÇA 1: Adicionado 'async'
    if not bot:
        return {"status": "erro", "detalhe": "BOT_TOKEN não configurado no Railway"}
    
    # <--- MUDANÇA 2: Adicionado 'await' para esperar o Telegram responder
    bot_info = await bot.get_me() 
    
    return {"status": "on-line", "bot": bot_info.username}

@app.get("/health")
def health():
    return {"status": "ok"}