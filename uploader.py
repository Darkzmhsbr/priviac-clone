from telegram import InputFile
async def send_tg(chat_id: int, path: str, caption: str = ""):
    with open(path, "rb") as f:
        await bot.send_video(chat_id, InputFile(f), caption=caption, supports_streaming=True)
    os.remove(path)   # limpa tmp
