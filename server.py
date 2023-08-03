#!/usr/bin/env python3
from os import getenv, remove

import fastapi
import pyrogram
import shelve
import logging
from dataclasses import dataclass

API_ID = getenv("TELEGRAM_API_ID")
API_HASH = getenv("TELEGRAM_API_HASH")
assert API_ID
assert API_HASH

DATA_DIR = getenv("DATA_DIR") or "./data/"

APP_NAME = "tg-dnd"
COMMAND_PREFIX = r"!dnd"


@dataclass
class Status:
    alias: str
    emoji: str
    custom_emoji_id: int


# status database
status_db: dict[str, Status] = shelve.open(DATA_DIR + "status.shelve")

# telegram
tg = pyrogram.Client(APP_NAME, api_id=API_ID, api_hash=API_HASH, workdir=DATA_DIR)

# web server
fastapi_app = fastapi.FastAPI()

# global logger
logger = logging.getLogger("uvicorn")


@fastapi_app.on_event("startup")
async def start_tg_client():
    """Start Telegram API client and check authoriation, exit if unseccessful"""
    try:
        await tg.start()
    except pyrogram.errors.exceptions.unauthorized_401.AuthKeyUnregistered:
        remove(DATA_DIR + f"/{APP_NAME}.session")
        exit("[!] restart and authorize manually")


@fastapi_app.on_event("shutdown")
async def stop_tg_client():
    """Disconnect from Telegram and free the session before exit"""
    await tg.stop()


async def add_command_output_to_message(
    message: pyrogram.types.Message, command_output: str
):
    """Add text at the end of the original message, preserve entities"""
    await tg.edit_message_text(
        chat_id=message.chat.id,
        message_id=message.id,
        text=message.text.html + "\n" + command_output,
        parse_mode=pyrogram.enums.ParseMode.HTML,
    )


@tg.on_message(
    pyrogram.filters.regex(COMMAND_PREFIX + r" (.*) (.*)$")
    & pyrogram.filters.me
    & pyrogram.filters.private
)
async def alias_save_handler(
    client: pyrogram.Client,
    message: pyrogram.types.Message,
):
    """Save new status

    Command example:
        !dnd ✅ green-check
        !dnd ❌ red-cross

    Edits the message in-place to a confirmational message.
    """
    assert message.matches
    assert message.entities

    emoji = message.matches[0].group(1).strip()
    alias = message.matches[0].group(2).strip()
    custom_emoji_id = message.entities[0].custom_emoji_id

    assert emoji
    assert alias
    assert custom_emoji_id

    new_status = Status(
        alias=alias,
        emoji=emoji,
        custom_emoji_id=custom_emoji_id,
    )
    status_db[alias] = new_status
    logger.info("Saved: %s" % new_status)
    await add_command_output_to_message(
        message=message, command_output=f"alias <code>{alias}</code> saved."
    )


@tg.on_message(
    pyrogram.filters.regex(COMMAND_PREFIX + r"\?$")
    & pyrogram.filters.me
    & pyrogram.filters.private
)
async def alias_list_handler(
    client: pyrogram.Client,
    message: pyrogram.types.Message,
):
    """List all available aliases

    Command:
        !dnd?

    Edits the message in-place to a list of aliases and corresponding custom emojis.
    """
    txt = ""
    for status in status_db.values():
        txt += f"· <code>{status.alias}</code> <emoji id={status.custom_emoji_id}>{status.emoji}</emoji>\n"
    if txt == "":
        txt = f"no aliases yet :p\nset one with {COMMAND_PREFIX} <custom_emoji> <alias>"
    await add_command_output_to_message(message=message, command_output=txt)


@fastapi_app.get("/status/{alias}")
async def set_status(alias: str) -> str:
    """Set Telegram status by saved alias."""
    status = status_db.get(alias)
    if not status:
        return fastapi.Response(
            content="no such alias", status_code=fastapi.status.HTTP_404_NOT_FOUND
        )
    await tg.set_emoji_status(
        emoji_status=pyrogram.types.EmojiStatus(custom_emoji_id=status.custom_emoji_id)
    )
    logger.info("status set to %s" % status)
    return alias


@fastapi_app.get("/")
async def index() -> str:
    return "https://github.com/MikeWent/tg-dnd"
