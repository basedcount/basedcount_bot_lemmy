from __future__ import annotations

import json
from contextlib import asynccontextmanager
from logging import getLogger, Logger, config
from os import getenv
from pathlib import Path
from traceback import print_exc
from typing import AsyncGenerator, Optional

import aiohttp
from aiohttp import ClientSession
from colorlog import ColoredFormatter
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase, AsyncIOMotorCollection

Path("logs").mkdir(exist_ok=True)
conf_file = Path("logging.conf")
if conf_file.is_file():
    config.fileConfig(str(conf_file))
else:
    config.fileConfig(str(Path(__file__).parent / "logging.conf"))


async def post_to_pastebin(title: str, body: str) -> Optional[str]:
    """Uploads the text to PasteBin and returns the url of the Paste

    :param title: Title of the Paste
    :param body: Body of Paste

    :returns: url of Paste

    """
    login_data = {"api_dev_key": getenv("PASTEBIN_DEV_KEY"), "api_user_name": getenv("PASTEBIN_USERNAME"), "api_user_password": getenv("PASTEBIN_PASSWORD")}

    data = {
        "api_option": "paste",
        "api_dev_key": getenv("PASTEBIN_DEV_KEY"),
        "api_paste_code": body,
        "api_paste_name": title,
        "api_paste_expire_date": "1W",
        "api_user_key": None,
        "api_paste_format": "python",
    }

    try:
        async with ClientSession() as session:
            login_resp = await session.post("https://pastebin.com/api/api_login.php", data=login_data)
            if login_resp.status == 200:
                data["api_user_key"] = await login_resp.text()
                post_resp = await session.post("https://pastebin.com/api/api_post.php", data=data)
                if post_resp.status == 200:
                    return await post_resp.text()
    except aiohttp.ClientError:
        print_exc()
    return None


async def send_traceback_to_discord(exception_name: str, exception_message: str, exception_body: str) -> None:
    """Send the traceback of an exception to a Discord webhook.

    :param exception_name: The name of the exception.
    :param exception_message: A brief summary of the exception.
    :param exception_body: The full traceback of the exception.

    """
    paste_bin_url = await post_to_pastebin(f"{exception_name}: {exception_message}", exception_body)

    if paste_bin_url is None:
        return

    webhook = getenv("DISCORD_WEBHOOK", "deadass")
    data = {"content": f"[{exception_name}: {exception_message}]({paste_bin_url})", "username": "Lemmy_BasedCountBot"}
    async with ClientSession(headers={"Content-Type": "application/json"}) as session:
        async with session.post(url=webhook, data=json.dumps(data)):
            pass


@asynccontextmanager
async def get_databased() -> AsyncGenerator[AsyncIOMotorDatabase, None]:
    """Returns the MongoDB AsyncIOMotorClient

    :returns: AsyncIOMotorClient object
    :rtype: AsyncIOMotorClient

    """
    cluster = AsyncIOMotorClient(getenv("MONGO_PASS"))
    try:
        yield cluster["dataBased"]
    finally:
        cluster.close()


async def get_mongo_collection(collection_name: str, databased: AsyncIOMotorDatabase) -> AsyncIOMotorCollection:
    """Returns the user databased from dataBased Cluster from MongoDB

    :returns: Returns a Collection from Mongo DB

    """
    return databased[collection_name]


def create_logger(logger_name: str, set_format: bool = False) -> Logger:
    """Creates logger and returns an instance of logging object.

    :returns: Logging Object.

    """

    if set_format:
        log_format = "%(log_color)s[%(asctime)s] %(levelname)s [%(filename)s.%(funcName)s:%(lineno)d] %(message)s"
        root_logger = getLogger("root")
        for handler in root_logger.handlers:
            handler.setFormatter(ColoredFormatter(log_format, datefmt="%Y-%m-%dT%H:%M:%S%z"))

    return getLogger(logger_name)


def actor_id_to_user_mention(user_actor_id: str) -> str:
    """Convert an actor ID to a user mention format.

    :param str user_actor_id: The actor ID.

    :returns: The user mention format.
    :rtype: str

    """
    user_mention = f"[@{user_actor_id.split('/')[-1]}]({user_actor_id})"
    return user_mention
