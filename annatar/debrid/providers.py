from abc import ABC, abstractmethod
from typing import Optional

from annatar.debrid import pm, rd
from annatar.debrid.models import StreamLink
from annatar.torrent import Torrent


class DebridService(ABC):
    api_key: str

    def __init__(self, api_key: str):
        self.api_key = api_key

    @abstractmethod
    async def get_stream_links(
        self,
        torrents: list[Torrent],
        season_episode: list[int],
        max_results: int = 5,
    ) -> list[StreamLink]:
        return []


class RealDebridProvider(DebridService):
    def __str__(self) -> str:
        return "RealDebridProvider"

    async def get_stream_links(
        self,
        torrents: list[Torrent],
        season_episode: list[int],
        max_results: int = 5,
    ) -> list[StreamLink]:
        return await rd.get_stream_links(
            torrents=torrents,
            debrid_token=self.api_key,
            season_episode=season_episode,
            max_results=max_results,
        )


class PremiumizeProvider(DebridService):
    def __str__(self) -> str:
        return "PremiumizeProvider"

    async def get_stream_links(
        self,
        torrents: list[Torrent],
        season_episode: list[int],
        max_results: int = 5,
    ) -> list[StreamLink]:
        return await pm.get_stream_links(
            torrents=torrents,
            debrid_token=self.api_key,
            season_episode=season_episode,
            max_results=max_results,
        )


def list_providers() -> list[dict[str, str]]:
    return [
        {
            "id": "real_debrid",
            "name": "Real Debrid",
        },
        {
            "id": "premiumize",
            "name": "Premiumize.me",
        },
    ]


def get_provider(provider_name: str, api_key: str) -> Optional[DebridService]:
    if provider_name == "real-debrid":
        return RealDebridProvider(api_key)
    if provider_name == "premiumize":
        return PremiumizeProvider(api_key)
    return None
