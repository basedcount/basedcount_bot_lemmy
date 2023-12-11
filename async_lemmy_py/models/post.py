from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Self, Any


@dataclass
class Post:
    id: int
    name: str
    creator_id: int
    community_id: int
    removed: bool
    locked: bool
    published: datetime
    deleted: bool
    nsfw: bool
    ap_id: str
    local: bool
    language_id: int
    featured_community: bool
    featured_local: bool
    body: Optional[str] = None
    embed_description: Optional[str] = None
    embed_title: Optional[str] = None
    embed_video_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    updated: Optional[str] = None
    url: Optional[str] = None

    @classmethod
    def from_dict(cls, data: dict[Any, Any]) -> Self:
        data_copy = data.copy()

        published_str = data_copy.get("published")

        if published_str:
            data_copy["published"] = datetime.fromisoformat(published_str)

        return cls(**data_copy)
