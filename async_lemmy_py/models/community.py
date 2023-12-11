from dataclasses import dataclass
from datetime import datetime
from typing import Any, Self


@dataclass
class Community:
    id: int
    name: str
    title: str
    description: str
    removed: bool
    published: datetime
    updated: datetime
    deleted: bool
    nsfw: bool
    actor_id: str
    local: bool
    icon: str
    banner: str
    hidden: bool
    posting_restricted_to_mods: bool
    instance_id: int

    @classmethod
    def from_dict(cls, data: dict[Any, Any]) -> Self:
        data_copy = data.copy()

        published_str = data_copy.get("published")
        updated_str = data_copy.get("updated")

        if published_str:
            data_copy["published"] = datetime.fromisoformat(published_str)

        if updated_str:
            data_copy["updated"] = datetime.fromisoformat(updated_str)

        return cls(**data_copy)
