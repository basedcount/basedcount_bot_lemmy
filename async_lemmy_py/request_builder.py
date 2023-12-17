from typing import Optional, Any

from aiohttp import ClientResponse, ClientResponseError, ClientSession


class RequestBuilder:
    def __init__(self, base_url: str, username: str, password: str) -> None:
        """Initialize the RequestBuilder.

        :param base_url: The base URL for API requests.
        :param username: The username for authentication.
        :param password: The password for authentication.

        """
        self.base_url: str = base_url
        self.username: str = username
        self.password: str = password
        self.jwt_token: Optional[str] = None

        # Initialize aiohttp ClientSession with default headers
        self.client_session: ClientSession = ClientSession(headers={"accept": "application/json", "content-type": "application/json"})

    async def get_jwt_token(self) -> None:
        """Get JWT token by sending a POST request to the login endpoint.

        The token will be stored in the instance variable `jwt_token`.

        """
        auth = {"password": self.password, "username_or_email": self.username}
        async with self.client_session.post(f"{self.base_url}/api/v3/user/login", json=auth) as resp:
            data = await resp.json()
            self.jwt_token = data.get("jwt")

    async def close(self) -> None:
        """Close the aiohttp ClientSession."""
        await self.client_session.close()

    async def get(self, endpoint: str, params: Optional[dict[Any, Any]] = None) -> dict[Any, Any]:
        """Perform an HTTP GET request.

        If jwt_token is None, it will first call get_jwt_token to obtain the token.

        :param endpoint: The API endpoint to send the GET request to.
        :param params: Optional query parameters.

        :returns: JSON response from the server.

        :raises: If the HTTP response status code indicates an error (not in the 2xx range).

        """
        if self.jwt_token is None:
            await self.get_jwt_token()

        url: str = f"{self.base_url}/api/v3/{endpoint}"
        headers = {"Authorization": f"Bearer {self.jwt_token}"}
        params_with_auth = {"auth": self.jwt_token} if params is None else {**params, "auth": self.jwt_token}

        async with self.client_session.get(url, headers=headers, params=params_with_auth) as resp:
            return await self._handle_response(resp)

    async def post(
        self, endpoint: str, params: Optional[dict[Any, Any]] = None, data: Optional[dict[Any, Any]] = None, json: Optional[dict[Any, Any]] = None
    ) -> dict[Any, Any]:
        """Perform an HTTP POST request.

        :param endpoint: The API endpoint to send the POST request to.
        :param params: Optional query parameters.
        :param data: Optional data for the request body (used for form data).
        :param json: Optional JSON data for the request body.

        :returns: JSON response from the server.

        :raises: If the HTTP response status code indicates an error (not in the 2xx range).

        """
        url: str = f"{self.base_url}/api/v3/{endpoint}"
        headers = {"Authorization": f"Bearer {self.jwt_token}"}
        json_with_auth = {"auth": self.jwt_token} if json is None else {**json, "auth": self.jwt_token}

        async with self.client_session.post(url, headers=headers, params=params, data=data, json=json_with_auth) as resp:
            return await self._handle_response(resp)

    async def _handle_response(self, resp: ClientResponse) -> dict[Any, Any]:
        """Handle the response from the server.

        :param resp: The aiohttp ClientResponse object.

        :returns: JSON response from the server.

        :raises ClientResponseError: If the HTTP response status code indicates an error (not in the 2xx range).

        """

        if resp.status >= 300:
            raise ClientResponseError(
                request_info=resp.request_info,
                history=resp.history,
                status=resp.status,
                message=f"Request failed with status {resp.status}: {resp.reason}",
                headers=resp.headers,
            )

        data: dict[Any, Any] = await resp.json()
        return data
