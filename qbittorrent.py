import aiohttp


class QbittorrentClient:
    def __init__(
        self,
        host: str | None = None,
        username: str | None = None,
        password: str | None = None,
    ):
        self.host = host
        self.username = username
        self.password = password
        self._session: aiohttp.ClientSession | None = None
        self._is_logged_in = False

    @property
    def session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            cookie_jar = aiohttp.CookieJar(unsafe=True)
            self._session = aiohttp.ClientSession(cookie_jar=cookie_jar)
        return self._session

    async def close(self) -> None:
        if self._session is not None:
            await self._session.close()
            self._session = None
        self._is_logged_in = False

    async def __aenter__(self) -> "QbittorrentClient":
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        await self.close()

    async def login(self) -> bool:
        url = f"{self.host}/api/v2/auth/login"
        data = {
            "username": self.username or "",
            "password": self.password or "",
        }
        async with self.session.post(url, data=data) as response:
            response.raise_for_status()
            text = (await response.text()).strip()

        success = text == "Ok."
        self._is_logged_in = success
        return success

    async def ensure_login(self) -> None:
        if not self._is_logged_in:
            await self.login()

    async def add_torrent(
        self,
        urls: str | list[str],
        **kwargs,
    ) -> str:
        await self.ensure_login()
        url = f"{self.host}/api/v2/torrents/add"
        if isinstance(urls, list):
            urls_value = "\n".join(urls)
        else:
            urls_value = urls
        form = aiohttp.FormData()
        form.add_field("urls", urls_value)
        for key, value in kwargs.items():
            if value is not None:
                form.add_field(key, str(value))
        async with self.session.post(url, data=form) as response:
            response.raise_for_status()
            return (await response.text()).strip()

    async def get_torrents(
        self,
        status_filter: str | None = None,
        category: str | None = None,
        tag: str | None = None,
    ) -> list[dict]:
        await self.ensure_login()
        url = f"{self.host}/api/v2/torrents/info"
        params: dict[str, str] = {}
        if status_filter:
            params["filter"] = status_filter
        if category:
            params["category"] = category
        if tag:
            params["tag"] = tag
        async with self.session.get(url, params=params or None) as response:
            response.raise_for_status()
            return await response.json()
