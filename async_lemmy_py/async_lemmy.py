import asyncio
import random
from typing import Any, AsyncIterator, Self

from cachetools import Cache

from async_lemmy_py.models.comment import Comment
from async_lemmy_py.request_builder import RequestBuilder
from logging import getLogger


class AsyncLemmyPy:
    """A client for interacting with the Lemmy API asynchronously.

    This class provides an asynchronous interface to interact with the Lemmy API, allowing users to stream comments from a specified community. It supports
    asynchronous context management and can be used within an 'async with' block.

    :param str base_url: The base URL of the Lemmy instance.
    :param str username: The username for authentication.
    :param str password: The password for authentication.

    :var RequestBuilder request_builder: An instance of RequestBuilder for building API requests.

    """

    def __init__(self, base_url: str, username: str, password: str) -> None:
        """Initialize the AsyncLemmyPy instance.

        :param str base_url: The base URL of the Lemmy instance.
        :param str username: The username for authentication.
        :param str password: The password for authentication.

        """
        self._async_lemmy_logger = getLogger("async_lemmy")
        self.request_builder = RequestBuilder(base_url, username, password)

    async def __aenter__(self) -> Self:
        """Enter the asynchronous context.

        :returns: The current instance of AsyncLemmyPy.
        :rtype: AsyncLemmyPy

        """
        return self

    async def __aexit__(self, *_: Any) -> None:
        """Exit the asynchronous context and close the request builder."""
        await self.request_builder.close()

    async def stream_comments(self, *, skip_existing: bool = True) -> AsyncIterator[Comment]:
        """Asynchronously stream comments from a Lemmy community.

        :rtype: Comment

        :yields: A Comment object representing a comment from the Lemmy community.

        """
        exponential_counter = ExponentialCounter(max_counter=16)
        seen_comments: Cache[int, Comment] = Cache(maxsize=600)
        skip_first = skip_existing

        while True:
            found = False
            comments = await self.request_builder.get(
                "comment/list", params={"type_": "Local", "sort": "New", "max_depth": 8, "page": 1, "community_id": 2, "community_name": "pcm"}
            )
            self._async_lemmy_logger.debug("Request made to server")

            for raw_comment in reversed(comments.get("comments", [])):
                comment = Comment.from_dict(comment_view=raw_comment, request_builder=self.request_builder)
                if comment.comment_id in seen_comments:
                    continue
                found = True
                seen_comments.update({comment.comment_id: comment})
                if not skip_first:
                    yield comment

            skip_first = False
            if found:
                self._async_lemmy_logger.debug("New comment found resetting the counter.")
                exponential_counter.reset()
            else:
                sleep_time = exponential_counter.counter()
                self._async_lemmy_logger.debug(f"No new comments, sleeping for {sleep_time} seconds.")
                await asyncio.sleep(sleep_time)


class ExponentialCounter:
    """A class to provide an exponential counter with jitter."""

    def __init__(self, max_counter: int):
        """Initialize an :class:`.ExponentialCounter` instance.

        :param max_counter: The maximum base value.

            .. note::

                The computed value may be 3.125% higher due to jitter.

        """
        self._base = 1
        self._max = max_counter

    def counter(self) -> int | float:
        """Increment the counter and return the current value with jitter."""
        max_jitter = self._base / 16.0
        value = self._base + random.random() * max_jitter - max_jitter / 2  # noqa: S311
        self._base = min(self._base * 2, self._max)
        return value

    def reset(self) -> None:
        """Reset the counter to 1."""
        self._base = 1
