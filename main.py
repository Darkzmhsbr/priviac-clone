from fastapi import FastAPI
import os, json, asyncio
from telegram import Bot

BOT_TOKEN = os.getenv("BOT_TOKEN")          # virá das variáveis do Railway
bot = Bot(BOT_TOKEN)
app = FastAPI()

@app.get("/")
def home():
    return {"status": "on-line", "bot": bot.get_me().username}

# health-check que o Railway usa para saber se o container está vivo
@app.get("/health")
def health():
    
    return "ok"
