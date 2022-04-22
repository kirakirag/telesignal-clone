from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
import json
import logging


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    with open("credentials.json", encoding="UTF-8") as f:
        API_TOKEN = json.load(f)["api_token"]
except FileNotFoundError:
    logger.error("Credentials not found. Please create a credentials.json file")
except KeyError:
    logger.error("Wrong credentials.json format")


# Initialize bot and dispatcher
bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)


class States(StatesGroup):
    """Class that implements bot states."""

    new = State()
    waiting = State()
    done = State()


@dp.message_handler(commands=["start"])
async def start(message: types.Message, state: FSMContext):
    """/start command handler. Changes the bot state to 'waiting' for sticker.

    Args:
        message (types.Message): message to be processed
        state (FSMContext): bot state"""

    await message.reply(
        "Hi! Send me a sticker. Animated stickers are not supported yet"
    )

    await States.waiting.set()


@dp.message_handler(state=States.waiting, content_types=types.ContentType.ANY)
async def sticker_handler(message: types.Message, state: FSMContext):
    """Sticker handler.

    Args:
        message (types.Message): message to be processed
        state (FSMContext): bot state
    """

    if not message.sticker:
        await message.reply("Not a sticker!")

    if message.sticker:
        SET_NAME = message.sticker.set_name
        STICKER_ID = message.sticker.file_id

        file = await bot.get_file(STICKER_ID)
        file_path = file.file_path

        await bot.download_file(file_path, "sticker")


if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
