import json
import logging
import io
from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from signalstickers_client import StickersClient
from signalstickers_client.models import LocalStickerPack, Sticker


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    with open("credentials.json", encoding="UTF-8") as f:
        parsed = json.load(f)
        TG_API_TOKEN = parsed["api_token"]
        SIGNAL_UID = parsed["signal_uid"]
        SIGNAL_PASSWORD = parsed["signal_password"]
except FileNotFoundError:
    logger.error("Credentials not found. Please create a credentials.json file")
except KeyError:
    logger.error("Wrong credentials.json format")


# Initialize bot and dispatcher
bot = Bot(token=TG_API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)


class States(StatesGroup):
    """Bot states implementation"""

    new = State()
    waiting = State()
    done = State()


class DownloadedSticker:
    """Downloaded sticker object

    Returns:
        DownloadSticker: object
    """

    def __init__(self, emoji: str, image: io.BytesIO):
        self.emoji = emoji
        self.image = image


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
        link = await upload_stickers_to_signal(
            pack_title=set_name, sticker_list=sticker_list
        )

        await message.reply(link)


def add_sticker(pack: LocalStickerPack, sticker: DownloadedSticker):
    stick = Sticker()
    stick.emoji = sticker.emoji
    stick.image_data = sticker.image.read()
    stick.id = pack.nb_stickers

    logger.info("Adding sticker %s to local sticker pack", stick.id)
    pack._addsticker(stick)


async def upload_stickers_to_signal(
    pack_title: str,
    sticker_list: str,
    pack_author: str = "SignalStickerBot",
    cover: io.BytesIO = None,
) -> str:
    """Upload list of stickers to Signal and return a link

    Args:
        sticker_list (list): list of image io.BytesIO objects

    Returns:
        str: link to signal sticker set
    """

    pack = LocalStickerPack()

    # Set here the pack title and author
    pack.title = pack_title
    pack.author = pack_author

    # Add the stickers here, with their emoji
    # Accepted format:
    # - Non-animated webpz
    # - PNG
    # - GIF <100kb for animated stickers
    for sticker in sticker_list:
        add_sticker(pack, sticker)
    logger.info("Created a local sticker pack")

    # Instantiate the client with your Signal crendentials
    async with StickersClient(SIGNAL_UID, SIGNAL_PASSWORD) as client:
        # Upload the pack
        try:
            logger.info("Uploading local sticker pack to Signal")
            pack_id, pack_key = await client.upload_pack(pack)
            link = (
                f"https://signal.art/addstickers/#pack_id={pack_id}&pack_key={pack_key}"
            )
            logger.info("Pack uploaded, link = %s", link)
        except Exception as e:
            logger.error("Couldn't upload sticker pack! Exception: %s", e)
            link = "Error, couldn't upload sticker set."

    return link


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

        sticker_image: io.BytesIO = await bot.download_file(file_path)
        sticker_list.append(DownloadedSticker(sticker.emoji, sticker_image))
    return sticker_list


if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
