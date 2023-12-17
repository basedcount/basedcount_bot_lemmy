from datetime import datetime
from typing import Optional, Any, Self

from async_lemmy_py.request_builder import RequestBuilder


class Post:
    """Represents a post."""

    def __init__(
        self,
        request_builder: RequestBuilder,
        id: int,
        name: str,
        creator_id: int,
        community_id: int,
        removed: bool,
        locked: bool,
        published: datetime,
        deleted: bool,
        nsfw: bool,
        ap_id: str,
        local: bool,
        language_id: int,
        featured_community: bool,
        featured_local: bool,
        body: Optional[str] = None,
        embed_description: Optional[str] = None,
        embed_title: Optional[str] = None,
        embed_video_url: Optional[str] = None,
        thumbnail_url: Optional[str] = None,
        updated: Optional[str] = None,
        url: Optional[str] = None,
    ) -> None:
        self.request_builder = request_builder
        self.id = id
        self.name = name
        self.creator_id = creator_id
        self.community_id = community_id
        self.removed = removed
        self.locked = locked
        self.published = published
        self.deleted = deleted
        self.nsfw = nsfw
        self.ap_id = ap_id
        self.local = local
        self.language_id = language_id
        self.featured_community = featured_community
        self.featured_local = featured_local
        self.body = body
        self.embed_description = embed_description
        self.embed_title = embed_title
        self.embed_video_url = embed_video_url
        self.thumbnail_url = thumbnail_url
        self.updated = updated
        self.url = url

    @classmethod
    def from_dict(cls, data: dict[str, Any], request_builder: RequestBuilder) -> Self:
        """Create a Post instance from a dictionary.

        :param dict data: The dictionary containing post data.
        :param RequestBuilder request_builder: An instance of the RequestBuilder.

        :returns: An instance of the Post class.
        :rtype: Post

        """
        data_copy = data.copy()

        published_str = data_copy.get("published")
        if published_str:
            data_copy["published"] = datetime.fromisoformat(published_str)

        data_copy["request_builder"] = request_builder
        return cls(**data_copy)

    @classmethod
    async def from_id(cls, post_id: int, request_builder: RequestBuilder) -> Self:
        """Create a Post instance asynchronously from a post ID and a RequestBuilder.

        :param int post_id: The ID of the post.
        :param RequestBuilder request_builder: An instance of the RequestBuilder.

        :returns: An instance of the Post class.
        :rtype: Post

        """
        post_data = await request_builder.get("post", params={"id": post_id})
        return cls.from_dict(post_data["post_view"]["post"], request_builder=request_builder)

    async def parent(self) -> Self:
        """Exists for duck typing."""
        return self

    async def reply(self, response: str) -> None:
        payload = {
            "content": response,
            "post_id": self.id,
            "language_id": self.language_id,
        }
        await self.request_builder.post("comment", json=payload)
