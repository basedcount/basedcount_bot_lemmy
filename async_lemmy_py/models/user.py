from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Self, Any


@dataclass
class User:
    id: int
    name: str
    banned: bool
    published: datetime
    actor_id: str
    local: bool
    deleted: bool
    admin: bool
    bot_account: bool
    instance_id: int
    bio: Optional[str] = None
    inbox_url: Optional[str] = None
    matrix_user_id: Optional[str] = None
    display_name: Optional[str] = None
    avatar: Optional[str] = None
    ban_expires: Optional[str] = None
    banner: Optional[str] = None
    updated: Optional[str] = None

    @classmethod
    def from_dict(cls, data: dict[Any, Any]) -> Self:
        data_copy = data.copy()

        published_str = data_copy.get("published")

        if published_str:
            data_copy["published"] = datetime.fromisoformat(published_str)

        return cls(**data_copy)
