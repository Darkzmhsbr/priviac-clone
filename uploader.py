from telegram import InputFile, Bot
import os

# Precisamos iniciar o Bot aqui para enviar a mensagem
BOT_TOKEN = os.getenv("BOT_TOKEN")
bot = Bot(BOT_TOKEN) if BOT_TOKEN else None

async def send_tg(chat_id: int, path: str, caption: str = ""):
    if not bot:
        print("ERRO: Bot não configurado no uploader.")
        return

    # Abre o arquivo e envia
    with open(path, "rb") as f:
        await bot.send_video(chat_id, InputFile(f), caption=caption, supports_streaming=True)
    
    # Remove o arquivo temporário para não lotar o servidor
    if os.path.exists(path):
        os.remove(path)