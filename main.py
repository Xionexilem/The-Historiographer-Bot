import os
from pathlib import Path
from dotenv import load_dotenv
import asyncio
from aiogram import Bot, Dispatcher

from app.handlers import router

TEMP_PHOTOS_DIR = Path("temp_photos")
TEMP_PHOTOS_DIR.mkdir(exist_ok=True)

load_dotenv()

BOT_TOKEN = os.getenv('BOT_TOKEN')

async def main():
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher(bot=bot)
    dp.include_router(router)
    await dp.start_polling(bot)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Bot OFF")
