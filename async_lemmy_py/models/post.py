from datetime import datetime
from typing import Any, Self

from async_lemmy_py.models.community import Community
from async_lemmy_py.models.user import User
from async_lemmy_py.request_builder import RequestBuilder


class Post:
    """Represents a post."""

    def __init__(self, request_builder: RequestBuilder, community: dict[str, Any], user: dict[str, Any], post_dict: dict[str, Any]):
        self.request_builder = request_builder
        self.community: Community = Community.from_dict(community)
        self.user: User = User.from_dict(user)

        self.ap_id = post_dict.get("ap_id", "")
        self.body = post_dict.get("body")
        self.community_id = post_dict.get("community_id", -1)
        self.creator_id = post_dict.get("creator_id", -1)
        self.deleted = post_dict.get("deleted", False)
        self.embed_description = post_dict.get("embed_description")
        self.embed_title = post_dict.get("embed_title")
        self.embed_video_url = post_dict.get("embed_video_url")
        self.featured_community = post_dict.get("featured_community", False)
        self.featured_local = post_dict.get("featured_local", False)
        self.language_id = post_dict.get("language_id", -1)
        self.local = post_dict.get("local", False)
        self.locked = post_dict.get("locked", False)
        self.name = post_dict.get("name", "")
        self.nsfw = post_dict.get("nsfw", False)
        self.post_id = post_dict.get("id", -1)
        self.published = datetime.fromisoformat(post_dict.get("published", "1970-01-01T00:00:00Z"))
        self.removed = post_dict.get("removed", False)
        self.thumbnail_url = post_dict.get("thumbnail_url")
        self.updated = datetime.fromisoformat(post_dict.get("updated", "1970-01-01T00:00:00Z"))
        self.url = post_dict.get("url")

    @classmethod
    def from_dict(cls, *, post_view: dict[str, Any], request_builder: RequestBuilder) -> Self:
        """Create a Post instance from a dictionary.

        :param dict post_view: The dictionary containing post data.
        :param RequestBuilder request_builder: An instance of the RequestBuilder.

        :returns: An instance of the Post class.
        :rtype: Post

        """
        post_dict = post_view["post"]
        return cls(
            request_builder=request_builder,
            community=post_view["community"],
            user=post_view["creator"],
            post_dict=post_dict,
        )

    @classmethod
    async def from_id(cls, post_id: int, request_builder: RequestBuilder) -> Self:
        """Create a Post instance asynchronously from a post ID and a RequestBuilder.

        :param int post_id: The ID of the post.
        :param RequestBuilder request_builder: An instance of the RequestBuilder.

        :returns: An instance of the Post class.
        :rtype: Post

        """
        post_data = await request_builder.get("post", params={"id": post_id})
        return cls.from_dict(post_view=post_data["post_view"], request_builder=request_builder)

    async def parent(self) -> Self:
        """Exists for duck typing."""
        return self

    async def reply(self, response: str) -> None:
        payload = {
            "content": response,
            "post_id": self.post_id,
            "language_id": self.language_id,
        }
        await self.request_builder.post("comment", json=payload)
