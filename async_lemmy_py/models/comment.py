from dataclasses import dataclass
from datetime import datetime

from async_lemmy_py.models.community import Community
from async_lemmy_py.models.post import Post
from async_lemmy_py.models.user import User
from typing import Self, cast


@dataclass
class Comment:
    id: int
    creator_id: int
    post_id: int
    content: str
    removed: bool
    published: datetime
    deleted: bool
    ap_id: str
    local: bool
    path: str
    distinguished: bool
    language_id: int
    input_dict: dict[str, str | int | bool]

    post: Post
    community: Community
    user: User

    @classmethod
    def from_dict(cls, data: dict[str, dict[str, str | int | bool]]) -> Self:
        comment_data = data["comment"]
        published_datetime = datetime.fromisoformat(cast(str, comment_data.get("published", "1969-12-31T19:00:00")))
        return cls(
            id=cast(int, comment_data.get("id", 0)),
            creator_id=cast(int, comment_data.get("creator_id", 0)),
            post_id=cast(int, comment_data.get("post_id", 0)),
            content=cast(str, comment_data.get("content", "")),
            removed=cast(bool, comment_data.get("removed", False)),
            published=published_datetime,
            deleted=cast(bool, comment_data.get("deleted", False)),
            ap_id=cast(str, comment_data.get("ap_id", "")),
            local=cast(bool, comment_data.get("local", False)),
            path=cast(str, comment_data.get("path", "")),
            distinguished=cast(bool, comment_data.get("distinguished", False)),
            language_id=cast(int, comment_data.get("language_id", 0)),
            input_dict=comment_data,
            post=Post.from_dict(data["post"]),
            community=Community.from_dict(data["community"]),
            user=User.from_dict(data["creator"]),
        )
