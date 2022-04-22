import io
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
async def start(message: types.Message, state: FSMContext) -> None:
    """/start command handler. Changes the bot state to 'waiting' for sticker.

    Args:
        message (types.Message): message to be processed
        state (FSMContext): bot state"""

    await message.reply(
        "Hi! Send me a sticker. Animated stickers are not supported yet"
    )

    await States.waiting.set()


@dp.message_handler(state=States.waiting, content_types=types.ContentType.ANY)
async def sticker_handler(message: types.Message, state: FSMContext) -> None:
    """Sticker handler.

    Args:
        message (types.Message): message to be processed
        state (FSMContext): bot state
    """

    if not message.sticker:
        await message.reply("Not a sticker!")

    if message.sticker:
        set_name = message.sticker.set_name
        sticker_set = await bot.get_sticker_set(set_name)
        logger.info("Found sticker set, length: %s", len(sticker_set.stickers))
        sticker_list = await get_sticker_list(sticker_set)
        link = await upload_stickers_to_signal(sticker_list)

        await message.reply(link)


async def upload_stickers_to_signal(sticker_list: list) -> str:
    """Upload list of stickers to Signal and return a link

    Args:
        sticker_list (list): list of image io.BytesIO objects

    Returns:
        str: link to signal sticker set
    """
    pass


async def get_sticker_list(sticker_set: types.sticker_set) -> list:
    """Make a list of io.BytesIO objects with sticker images
    from given sticker_set

    Args:
        sticker_set (types.sticker_set): sticker set to turn to image list

    Returns:
        list: sticker_list
    """
    sticker_list = []
    for count, sticker in enumerate(sticker_set.stickers):
        logger.info("Downloading %s sticker", count + 1)
        sticker_id = sticker.file_id

        file = await bot.get_file(sticker_id)
        file_path = file.file_path

        result: io.BytesIO = await bot.download_file(file_path)
        sticker_list.append(result)
    return sticker_list


if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
