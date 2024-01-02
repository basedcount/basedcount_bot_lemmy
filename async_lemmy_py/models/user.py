from attrs import define
from datetime import datetime
from typing import Optional, Self, Any

from aiohttp import ClientSession


@define
class UserFlair:
    community_actor_id: str
    display_name: str
    mod_only: bool
    name: str
    path: str


class User:
    def __init__(self, user: dict[str, Any]):
        self.actor_id = user.get("actor_id", "")
        self.admin = user.get("admin")
        self.avatar = user.get("avatar", "")
        self.ban_expires = user.get("ban_expires", "")
        self.banned = user.get("banned", False)
        self.banner = user.get("banner", "")
        self.bio = user.get("bio", "")
        self.bot_account = user.get("bot_account", False)
        self.deleted = user.get("deleted", False)
        self.display_name = user.get("display_name", "")
        self.id = user.get("id", -1)
        self.inbox_url = user.get("inbox_url", "")
        self.instance_id = user.get("instance_id", -1)
        self.local = user.get("local", False)
        self.matrix_user_id = user.get("matrix_user_id", "")
        self.name = user.get("name", "")
        self.published = datetime.fromisoformat(user.get("published", "1970-01-01T00:00:00Z"))
        self.updated = datetime.fromisoformat(user.get("updated", "1970-01-01T00:00:00Z"))

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        return cls(data)

    async def get_flair(self) -> Optional[UserFlair]:
        """Retrieve user flair information from the Lemmy API.

        :returns: An instance of UserFlair if the user has flair, else None.
        :rtype: Optional[UserFlair]
        :rtype: Awaitable[Optional[UserFlair]]

        """
        async with ClientSession() as session:
            params = {"community_actor_id": "https://lemmy.basedcount.com/c/pcm", "user_actor_id": self.actor_id}
            async with session.get("https://lemmy.basedcount.com/flair/api/v1/user", params=params) as resp:
                if resp.status != 200:
                    return None
                data = await resp.json()

                # Nerd02 skill issue. If a user doesn't have a flair it should ideally return resp.status == 404. But instead it returns None.
                if data is None:
                    return None
                return UserFlair(**data)
