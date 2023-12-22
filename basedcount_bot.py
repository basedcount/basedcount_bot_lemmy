from __future__ import annotations

import asyncio
import re
from os import getenv
from time import sleep
from traceback import format_exc
from typing import Awaitable, Callable, NamedTuple, Optional

import aiofiles
from aiohttp import ClientResponseError
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorDatabase
from yaml import safe_load

from async_lemmy_py import AsyncLemmyPy
from async_lemmy_py.models.comment import Comment
from async_lemmy_py.models.post import Post
from async_lemmy_py.models.user import UserFlair
from bot_commands import get_based_count, most_based, based_and_pilled, my_compass, remove_pill, add_to_based_history, set_subscription, check_unsubscribed
from utility_functions import (
    create_logger,
    get_databased,
    send_traceback_to_discord,
)

load_dotenv()


def exception_wrapper(func: Callable[[AsyncLemmyPy, AsyncIOMotorDatabase], Awaitable[None]]) -> Callable[[AsyncLemmyPy, AsyncIOMotorDatabase], Awaitable[None]]:
    """Decorator to handle the exceptions and to ensure the code doesn't exit unexpectedly.

    :param func: function that needs to be called

    :returns: wrapper function
    :rtype: Callable[[Reddit, AsyncIOMotorDatabase], Awaitable[None]]

    """

    async def wrapper(lemmy_instance: AsyncLemmyPy, databased: AsyncIOMotorDatabase) -> None:
        global cool_down_timer

        while True:
            try:
                await func(lemmy_instance, databased)
            except ClientResponseError as response_err_exc:
                main_logger.exception("AsyncLemmyPyExpection", exc_info=True)
                await send_traceback_to_discord(
                    exception_name=type(response_err_exc).__name__, exception_message=str(response_err_exc), exception_body=format_exc()
                )

                sleep(cool_down_timer)
                cool_down_timer = (cool_down_timer + 30) % 360
                main_logger.info(f"Cooldown: {cool_down_timer} seconds")
            except Exception as general_exc:
                main_logger.critical("Serious Exception", exc_info=True)
                await send_traceback_to_discord(exception_name=type(general_exc).__name__, exception_message=str(general_exc), exception_body=format_exc())

                sleep(cool_down_timer)
                cool_down_timer = (cool_down_timer + 30) % 360
                main_logger.info(f"Cooldown: {cool_down_timer} seconds")

    return wrapper


async def bot_commands(command: Comment, command_body_lower: str, databased: AsyncIOMotorDatabase) -> None:
    """Responsible for the basic based count bot commands

    :param command: Lemmy post that triggered the command, could be a message or comment
    :param command_body_lower: The body of that message or command
    :param databased: MongoDB database used to get the collections

    :returns: None

    """

    if command_body_lower.startswith("/"):
        main_logger.info(f"Received {type(command).__name__} from {command.user.actor_id}, {command_body_lower!r}")

    if command_body_lower.startswith("/info"):
        async with aiofiles.open("data_dictionaries/bot_replies.yaml", "r") as fp:
            replies = safe_load(await fp.read())
            await command.reply(replies.get("info_message"))

    elif command_body_lower.startswith("/mybasedcount"):
        my_based_count = await get_based_count(user_actor_id=command.user.actor_id, is_me=True, databased=databased)
        await command.reply(my_based_count)

    elif result := re.match(r"/basedcount\s*(u/)?([A-Za-z0-9_-]+)", command.content, re.IGNORECASE):
        # TODO: Make this work later. The username is a url which might be very hard to capture.
        user_name = result.group(2)
        user_based_count = await get_based_count(user_actor_id=user_name, is_me=False, databased=databased)
        await command.reply(user_based_count)

    elif command_body_lower.startswith("/mostbased"):
        await command.reply(await most_based())

    elif command_body_lower.startswith("/removepill"):
        response = await remove_pill(user_actor_id=command.user.actor_id, pill=command_body_lower.replace("/removepill ", ""), databased=databased)
        await command.reply(response)

    elif command_body_lower.startswith("/mycompass"):
        response = await my_compass(user_actor_id=command.user.actor_id, compass=command_body_lower.replace("/mycompass ", ""), databased=databased)
        await command.reply(response)

    elif command_body_lower.startswith("/unsubscribe"):
        response = await set_subscription(subscribe=False, user_actor_id=command.user.actor_id, databased=databased)
        await command.reply(response)

    elif command_body_lower.startswith("/subscribe"):
        response = await set_subscription(subscribe=True, user_actor_id=command.user.actor_id, databased=databased)
        await command.reply(response)


BASED_VARIATION = (
    "Oj +1 byczq +1",
    "Oj+1byczq+1",
    "basado",
    "basat",
    "basato",
    "baseado",
    "based",
    "baserad",
    "baseret",
    "basert",
    "basiert",
    "baste",
    "basé",
    "baza",
    "bazat",
    "bazirano",
    "bazita",
    "bazowane",
    "berdasar",
    "fondatum",
    "fundiert",
    "gebaseerd",
    "gebasseerd",
    "na základě",
    "oparte",
    "perustunut",
    "perustuvaa",
    "založené",
    "Базирано",
    "основано",
    "מבוסס",
    "ベース",
    "基于",
)

BASED_REGEX = re.compile(f"({'|'.join(BASED_VARIATION)})\\b(?!\\s*(on|off))", re.IGNORECASE)
PILL_REGEX = re.compile("(?<=(and|but))(.+)pilled", re.IGNORECASE)


async def is_valid_comment(comment: Comment, parent_info: ParentInfo, databased: AsyncIOMotorDatabase) -> bool:
    """Runs checks for self based/pills, unflaired users, and cheating in general

    :param comment: Comment which triggered the bot command
    :param parent_info: The parent comment/post info.
    :param databased: MongoDB database used to get the collections

    :returns: True if checks passed and False if checks failed

    """
    main_logger.info(f"Based Comment: {comment.content!r} from: {comment.user.actor_id} to: {parent_info.parent_actor_id} <{parent_info.parent_flair}>")
    if parent_info.parent_actor_id.lower() in [comment.user.actor_id.lower(), "https://lemmy.basedcount.com/u/basedcount_bot"]:
        main_logger.info("Checks failed, self based or giving basedcount_bot based.")
        return False

    if parent_info.parent_flair is None:
        main_logger.info("(Temp) Giving based to unflaired user.")
        # TODO: Letting Unflaired give based temporarily
        return True

    # Check if people aren't just giving each other low effort based
    if parent_info.parent_body.startswith(BASED_VARIATION) and len(parent_info.parent_body) < 50:
        main_logger.info("Checks failed, parent comment starts with based and is less than 50 chars long")
        return False

    # fire and forget background tasks
    task = asyncio.create_task(
        add_to_based_history(user_actor_id=comment.user.actor_id, parent_author_actor_id=parent_info.parent_actor_id, databased=databased)
    )
    background_tasks.add(task)
    task.add_done_callback(background_tasks.discard)
    return True


class ParentInfo(NamedTuple):
    parent_actor_id: str
    parent_body: str
    parent_flair: Optional[UserFlair]
    link: str


async def get_parent_info(comment: Comment | Post) -> ParentInfo:
    """Gets the parent comment/submission information and returns the data in dict.

    :param comment: Comment which triggered the bot command and whose parent data will be checked

    :returns: dict with all the information such as author name and content

    """
    parent_post = await comment.parent()
    parent_actor_id = parent_post.user.actor_id
    parent_body = "submission" if isinstance(parent_post, Post) else parent_post.content.lower()
    parent_flair = await parent_post.user.get_flair()
    link = parent_post.ap_id
    return ParentInfo(
        parent_actor_id=parent_actor_id,
        parent_body=parent_body,
        parent_flair=parent_flair,
        link=link,
    )


@exception_wrapper
async def read_comments(lemmy_instance: AsyncLemmyPy, databased: AsyncIOMotorDatabase) -> None:
    """Checks comments as they come on !pcm@lemmy.basedcount.com and performs actions accordingly.

    :param lemmy_instance: The AsyncLemmyPy Instance. Used to make API calls.
    :param databased: MongoDB database used to get the collections

    :returns: Nothing is returned

    """
    main_logger.info(f"Logged into {lemmy_instance.request_builder.username} Account.")
    async for comment in lemmy_instance.stream_comments(skip_existing=False):  # Comment
        # Skips its own comments
        if comment.user.actor_id == "https://lemmy.basedcount.com/u/basedcount_bot":
            continue

        comment_body_lower = comment.content.lower()
        if re.match(BASED_REGEX, comment_body_lower.replace("\n", "")):
            try:
                parent_info = await get_parent_info(comment)
            except ClientResponseError:
                main_logger.warn("Parent Removed or Deleted")
                continue
            # Skip Unflaired scums and low effort based
            if not await is_valid_comment(comment, parent_info, databased=databased):
                continue
            main_logger.info("Checks passed")

            pill = None
            first_non_empty_line = next(line for line in comment_body_lower.splitlines() if line)
            if pill_match := re.search(PILL_REGEX, first_non_empty_line):
                clean_pill = pill_match.group(2).strip(" -")  # strips both space and - character
                if 70 > len(clean_pill) > 0:
                    pill = {
                        "name": clean_pill,
                        "commentID": comment.ap_id,
                        "fromUser": comment.user.actor_id,
                        "date": int(comment.published.timestamp()),
                        "amount": 1,
                    }

            if parent_info.parent_flair is None:
                parent_flair = "Unflaired"
            else:
                parent_flair = parent_info.parent_flair.display_name
            reply_message = await based_and_pilled(parent_info.parent_actor_id, parent_flair, pill, databased=databased)
            if reply_message is not None:
                if await check_unsubscribed(parent_info.parent_actor_id, databased):
                    continue
                await comment.reply(reply_message)
        else:
            await bot_commands(comment, comment_body_lower, databased=databased)


async def main() -> None:
    async with (
        get_databased() as databased,
        AsyncLemmyPy(base_url="https://lemmy.basedcount.com", username=getenv("LEMMY_USERNAME", "username"), password=getenv("LEMMY_PASSWORD", "pas")) as lemmy,
    ):
        await asyncio.gather(
            read_comments(lemmy, databased),
        )


if __name__ == "__main__":
    cool_down_timer = 0
    main_logger = create_logger(__name__)
    background_tasks: set[asyncio.Task[None]] = set()
    asyncio.run(main())
