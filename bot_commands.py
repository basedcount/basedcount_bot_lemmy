from __future__ import annotations

import asyncio
import random
import re
from contextlib import suppress
from time import time
from typing import Mapping, Optional, Any
from urllib.parse import urlsplit, parse_qs

import aiofiles
import yaml
from motor.motor_asyncio import AsyncIOMotorCollection, AsyncIOMotorDatabase
from pymongo import ReturnDocument

from models.ranks import rank_name, rank_message
from models.user import User
from utility_functions import get_mongo_collection, create_logger, actor_id_to_user_mention

bot_commands_logger = create_logger(logger_name="basedcount_bot")


async def find_or_create_user_profile(user_actor_id: str, users_collection: AsyncIOMotorCollection) -> Mapping[str, Any]:
    """Finds the user in the users_collection, or creates one if it doesn't exist using default values

    :param user_actor_id: The user whose profile to find or create
    :param users_collection: The collection in which the profile will be searched or inserted

    :returns: Dict object with user profile info

    """
    query = {"$and": [{"name": re.compile(rf"^{user_actor_id}$", re.I)}, {"is_lemmy": {"$exists": True, "$eq": True}}]}
    profile = await users_collection.find_one(query)
    if profile is None:
        profile = await users_collection.find_one_and_update(
            {"name": user_actor_id},
            {
                "$setOnInsert": {
                    "flair": "Unflaired",
                    "count": 0,
                    "pills": [],
                    "compass": [],
                    "sapply": [],
                    "basedTime": [],
                    "mergedAccounts": [],
                    "unsubscribed": False,
                    "is_lemmy": True,
                }
            },
            upsert=True,
            return_document=ReturnDocument.AFTER,
        )
    return profile


async def based_and_pilled(user_actor_id: str, flair_name: str, pill: Optional[dict[str, str | int]], databased: AsyncIOMotorDatabase) -> Optional[str]:
    """Increments the based count and adds the pill to a user database in mongo

    :param user_actor_id: user whose based count/pill will be added.
    :param flair_name: flair of the user.
    :param pill: name of the pill that will be added.
    :param databasedd: MongoDB Client used to get the collections.

    :returns: Comment response for the user when based count is 1, multiple of 5 and when they reach a new rank

    """
    bot_commands_logger.info(f"based_and_pilled args: {user_actor_id}, flair: {flair_name}, pill: {pill}")
    users_collection = await get_mongo_collection(collection_name="users", databased=databased)
    profile = await find_or_create_user_profile(user_actor_id, users_collection)
    bot_commands_logger.info(f"Based Count before: {profile['count']}")
    await asyncio.gather(
        add_based_count(user_actor_id, flair_name, users_collection),
        add_pills(user_actor_id, pill, users_collection),
    )
    profile = await find_or_create_user_profile(user_actor_id, users_collection)
    bot_commands_logger.info(f"Based Count: {profile['count']}")

    user = User.from_data(profile)
    all_based_counts = await user.get_all_accounts_based_count(users_collection)
    combined_based_count = sum(map(lambda x: x[1], all_based_counts))
    combined_pills = await user.combined_formatted_pills(users_collection)
    combined_rank = await rank_name(combined_based_count, user_actor_id)
    rank_up = await rank_message(combined_based_count)

    user_mention = actor_id_to_user_mention(user_actor_id)
    if user.based_count == 1:
        return (
            f"{user_mention} is officially based! Their Based Count is now 1.\n\n"
            f"Rank: {combined_rank}\n\n"
            f"Pills: {combined_pills}\n\n"
            f"Compass: {user.format_compass()}\n\n"
            f"I am a bot. Reply /info for more info."
        )
    elif user.based_count % 5 == 0:
        if rank_up is not None:
            # Reply if user reaches a new rank
            return (
                f"{user_mention}'s Based Count has increased by 1. Their Based Count is now {user.based_count}.\n\n"
                f"Congratulations, {user_mention}! You have ranked up to {combined_rank}! {rank_up}\n\n"
                f"Pills: {combined_pills}\n\n"
                f"Compass: {user.format_compass()}\n\n"
                f"I am a bot. Reply /info for more info."
            )
        # normal reply
        return (
            f"{user_mention}'s Based Count has increased by 1. Their Based Count is now {user.based_count}.\n\n"
            f"Rank: {combined_rank}\n\n"
            f"Pills: {combined_pills}\n\n"
            f"Compass: {user.format_compass()}\n\n"
            f"I am a bot. Reply /info for more info."
        )
    return None


async def add_based_count(user_actor_id: str, flair_name: str, users_collection: AsyncIOMotorCollection) -> None:
    """Increases the based count of user by one

    :param user_actor_id: user whose based count will be increased
    :param flair_name: flair of the user.
    :param users_collection: The collection in which the profile will be updated

    :returns: None

    """
    await users_collection.update_one({"name": user_actor_id}, {"$set": {"flair": flair_name}, "$inc": {"count": 1}, "$push": {"basedTime": int(time())}})


async def add_pills(user_actor_id: str, pill: Optional[dict[str, str | int]], users_collection: AsyncIOMotorCollection) -> None:
    """Add the pill to the user database

    :param user_actor_id: The user's whose pill will be added
    :param pill: pill that will be added
    :param users_collection: The collection in which the profile will be updated

    :returns: None

    """
    if pill is None:
        return None

    await users_collection.update_one({"name": user_actor_id, "pills.name": {"$ne": pill["name"]}}, {"$push": {"pills": pill}})


async def add_to_based_history(user_actor_id: str, parent_author_actor_id: str, databased: AsyncIOMotorDatabase) -> None:
    """Adds the based count record to based history database, so it can be sent to mods for cheating report

    :param user_actor_id: user who gave the based and pills
    :param parent_author: user who received the based
    :param AsyncIOMotorClient databasedd: MongoDB Client used to get the collections

    :returns: None

    """
    based_history_collection = await get_mongo_collection(collection_name="basedHistory", databased=databased)
    await based_history_collection.update_one({"to": parent_author_actor_id, "from": user_actor_id}, {"$inc": {"count": 1}}, upsert=True)


async def most_based() -> str:
    """Returns the link to the basedcount.com leaderboard.

    :returns: Str object containing the top 10 most based users

    """
    return "See the Based Count Leaderboard at https://basedcount.com/leaderboard"


async def get_based_count(user_actor_id: str, databased: AsyncIOMotorDatabase, is_me: bool = False) -> str:
    """Retrieves the Based Count for the given username.

    :param user_actor_id: Username whose based count will be retrieved
    :param databasedd: MongoDB Client used to get the collections
    :param is_me: Flag to indicate if a user is requesting their own based count

    :returns: str object with based count summary of the user

    """
    users_collection = await get_mongo_collection(collection_name="users", databased=databased)
    profile = await users_collection.find_one({"name": re.compile(rf"^{user_actor_id}$", re.I)})

    if profile is not None:
        user = User.from_data(profile)

        all_based_counts = await user.get_all_accounts_based_count(users_collection)
        combined_based_count = sum(map(lambda x: x[1], all_based_counts))
        combined_pills = await user.combined_formatted_pills(users_collection)
        combined_rank = await rank_name(combined_based_count, user_actor_id)

        build_username = f"{profile['name']}'s"
        reply_message = (
            f"{'Your' if is_me else build_username} Based Count is {combined_based_count}\n\n"
            f"Rank: {combined_rank}\n\n"
            f"Pills: {combined_pills}\n\n"
            f"{user.format_compass()}"
        )

        if user.merged_accounts:
            merged_acc_summary = "\n\n".join([f"- [{x[0]}](https://basedcount.com/u/{x[0]}) {x[1]} based & {x[2]} pills" for x in all_based_counts])
            merged_account_reply = f"Based and Pill Count breakdown\n\n{merged_acc_summary}"
            reply_message = f"{reply_message}\n\n{merged_account_reply}"

    else:
        async with aiofiles.open("data_dictionaries/bot_replies.yaml", "r") as fp:
            replies = yaml.safe_load(await fp.read())
        if is_me:
            reply_message = random.choice(replies.get("my_based_no_user_reply"))
        else:
            reply_message = random.choice(replies.get("based_count_no_user_reply"))
    return reply_message


async def my_compass(user_actor_id: str, compass: str, databased: AsyncIOMotorDatabase) -> str:
    """Parses the Political Compass/Sapply Values url and saves to compass values in database

    :param user_actor_id: User whose compass will be updated
    :param compass: The url given by the user
    :param databasedd: MongoDB Client used to get the collections

    :returns: str message from parsed data

    """
    users_collection = await get_mongo_collection(collection_name="users", databased=databased)
    profile = await find_or_create_user_profile(user_actor_id, users_collection)
    split_url = urlsplit(compass)
    root_domain = split_url.netloc or split_url.path
    url_query = parse_qs(split_url.query)

    with suppress(KeyError):
        if "sapplyvalues.github.io" in root_domain:
            sv_eco_type = url_query["right"][0]
            sv_soc_type = url_query["auth"][0]
            sv_prog_type = url_query["prog"][0]
            sapply_values = [sv_prog_type, sv_soc_type, sv_eco_type]
            bot_commands_logger.info(f"Sapply Values: {sapply_values}")
            await users_collection.update_one({"name": user_actor_id}, {"$set": {"sapply": sapply_values}})
            user = User.from_data({**profile, "sapply": sapply_values})
            return f"Your Sapply compass has been updated.\n\n{user.sappy_values_type}"

        elif "politicalcompass.org" in root_domain:
            compass_economic_axis = url_query["ec"][0]
            compass_social_axis = url_query["soc"][0]
            compass_values = [compass_economic_axis, compass_social_axis]
            bot_commands_logger.info(f"PCM Values: {profile['compass']}")
            await users_collection.update_one({"name": user_actor_id}, {"$set": {"compass": compass_values}})
            user = User.from_data({**profile, "compass": compass_values})
            return f"Your political compass has been updated.\n\n{user.political_compass_type}"

    return (
        "Sorry, but that isn't a valid URL. "
        "Please copy/paste the entire test result URL from politicalcompass.org or sapplyvalues.github.io, starting with 'https'."
    )


async def remove_pill(user_actor_id: str, pill: str, databased: AsyncIOMotorDatabase) -> str:
    """Removes the pill by adding deleted = True field in the dict obj

    :param user_actor_id: The user whose pill is going to be removed
    :param pill: Name of the pill being removed
    :param databasedd: MongoDB Client used to get the collections

    :returns: Message that is sent back to the user

    """
    users_collection = await get_mongo_collection(collection_name="users", databased=databased)
    res = await users_collection.find_one_and_update(
        {"name": user_actor_id, "pills.name": pill}, {"$set": {"pills.$.deleted": True}}, return_document=ReturnDocument.AFTER
    )
    if not res:
        return "You do not have that pill!"
    else:
        return f'"{pill}" pill removed. See your pills at https://basedcount.com/u/{user_actor_id}'


async def set_subscription(subscribe: bool, user_actor_id: str, databased: AsyncIOMotorDatabase) -> str:
    """Sets the user's unsubscribed bool to True or False

    :param subscribe: Boolean indicating whether to set the status to subscribed or unsubscribed
    :param user_actor_id: The user whose subscription status is being changed
    :param databased: MongoDB Client used to get the collections

    :returns: Message that is sent back to the user

    """
    users_collection = await get_mongo_collection(collection_name="users", databased=databased)
    profile = await find_or_create_user_profile(user_actor_id, users_collection)
    res = await users_collection.update_one({"name": profile["name"]}, {"$set": {"unsubscribed": not subscribe}})
    if res:
        return "You have unsubscribed from basedcount_bot." if subscribe else "Thank you for subscribing to basedcount_bot!"
    else:
        return "Error: Please contact the mods."


async def check_unsubscribed(user_actor_id: str, databased: AsyncIOMotorDatabase) -> bool:
    """Check the value of the "unsubscribed" field for a user with the given username in a MongoDB collection.

    If the "unsubscribed" field is missing, add it to the user document and set its value to False.

    :param user_actor_id: The username to search for in the collection.
    :param databased: A MotorAsyncIOMotorClient instance representing the MongoDB client.

    :returns: The value of the "unsubscribed" field for the user, or False if the user doesn't exist or the "unsubscribed" field is missing.

    """
    users_collection = await get_mongo_collection(collection_name="users", databased=databased)
    profile = await users_collection.find_one({"name": user_actor_id})

    if profile is not None and profile.get("unsubscribed") is not None:
        unsub: bool = profile.get("unsubscribed", False)
        return unsub
    else:
        # If the "unsubscribed" field is missing, add it and set its value to False
        await users_collection.update_one({"name": user_actor_id}, {"$set": {"unsubscribed": False}})
        return False
