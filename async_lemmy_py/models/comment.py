from datetime import datetime
from typing import Self, Any, Union

from async_lemmy_py.models.community import Community
from async_lemmy_py.models.post import Post
from async_lemmy_py.models.user import User
from async_lemmy_py.request_builder import RequestBuilder


class Comment:
    """This class represents a lemmy comment."""

    def __init__(
        self,
        request_builder: RequestBuilder,
        post: dict[str, Any],
        community: dict[str, Any],
        user: dict[str, Any],
        comment_dict: dict[str, Any],
    ) -> None:
        self.request_builder = request_builder
        self.post: Post = Post.from_dict(post_view={"post": post, "community": community, "creator": user}, request_builder=request_builder)
        self.community: Community = Community.from_dict(community)
        self.user: User = User.from_dict(user)

        # Comment Data
        self.ap_id: str = comment_dict.get("ap_id", "")
        self.comment_id: int = comment_dict.get("id", -1)
        self.content: str = comment_dict.get("content", "")
        self.creator_id: int = comment_dict.get("creator_id", -1)
        self.deleted: bool = comment_dict.get("deleted", False)
        self.distinguished: bool = comment_dict.get("distinguished", False)
        self.language_id: int = comment_dict.get("language_id", -1)
        self.local: bool = comment_dict.get("local", False)
        self.path: str = comment_dict.get("path", "0.0")
        self.post_id: int = comment_dict.get("post_id", -1)
        self.published: datetime = datetime.fromisoformat(comment_dict.get("published", "1970-01-01T00:00:00Z"))
        self.removed: bool = comment_dict.get("removed", False)
        self.updated: datetime = datetime.fromisoformat(comment_dict.get("updated", "1970-01-01T00:00:00Z"))

    @classmethod
    async def from_id(cls, comment_id: int, request_builder: RequestBuilder) -> Self:
        comment_data = await request_builder.get("comment", params={"id": comment_id})
        return cls.from_dict(comment_view=comment_data["comment_view"], request_builder=request_builder)

    @classmethod
    def from_dict(cls, *, comment_view: dict[str, Any], request_builder: RequestBuilder) -> Self:
        comment_dict = comment_view["comment"]
        return cls(
            request_builder=request_builder,
            post=comment_view["post"],
            community=comment_view["community"],
            user=comment_view["creator"],
            comment_dict=comment_dict,
        )

    async def parent(self) -> Union["Comment", Post]:
        parent_ids = self.path.split(".")
        parent_id = int(parent_ids[-2])
        if parent_id == 0 or len(parent_ids) <= 1:
            return await Post.from_id(self.post_id, self.request_builder)
        else:
            return await Comment.from_id(parent_id, self.request_builder)

    async def reply(self, response: str) -> None:
        payload = {
            "content": response,
            "post_id": self.post_id,
            "parent_id": self.comment_id,
            "language_id": self.language_id,
        }
        await self.request_builder.post("comment", json=payload)
