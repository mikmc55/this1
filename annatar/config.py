import json
import os
from base64 import b64decode
from datetime import datetime

import structlog
from pydantic import BaseModel, ValidationError, root_validator

from annatar.api.filters import Filter, by_category
from annatar.api.filters import by_id as filter_by_id

log = structlog.get_logger()
DEFAULT_INDEXERS = (
    "audiences,btsow,hdarea,hdatmos,hdfans,hdsky,milkie,monikadesign-api,ncore,passthepopcorn,thesceneplace,torlock,torrentseeds-api"
)

APP_ID = os.getenv("APP_ID", "community.annatar.addon.stremio")
APP_NAME = os.getenv("APP_NAME", "Annatar")
BUILD_VERSION: str = os.getenv("BUILD_VERSION", "1.1.1")
ENV = os.getenv("ENV", "dev")
HOST: str = os.getenv("LISTEN_HOST", "0.0.0.0")
JACKETT_INDEXERS_LIST = (os.getenv("JACKETT_INDEXERS") or DEFAULT_INDEXERS).split(",")
PORT: int = int(os.getenv("LISTEN_PORT", "8000"))
PROM_DIR = os.getenv(
    "PROMETHEUS_MULTIPROC_DIR", f"/tmp/annatar.metrics-{datetime.now().timestamp()}"
)
VERSION = os.getenv("BUILD_VERSION") or "1.1.1"

RESOLUTION_FILTERS = [f for f in by_category("Resolution")]


class UserConfig(BaseModel):
    debrid_service: str
    debrid_api_key: str
    filters: list[Filter] = []
    max_results: int = 5

    class Config:
        extra = "allow"

    @root_validator(pre=True)
    @classmethod
    def convert_resolutions(cls, values):
        """
        Convert from previous versions that let you filter by resolution to a
        more generic filter system
        """
        if "resolutions" not in values:
            return values
        resolutions = [r.lower() for r in values["resolutions"]]
        filters = values.get("filters", []).copy()
        # the filters are exclusive so we find those that are not in the list
        for f in by_category("Resolution"):
            if f.id.lower() not in resolutions:
                filters.append(f)
        values["filters"] = filters
        return values

    @staticmethod
    def defaults() -> "UserConfig":
        return UserConfig(
            debrid_service="",
            debrid_api_key="",
            max_results=5,
            filters=[],
        )


def parse_config(b64config: str) -> UserConfig:
    if not b64config:
        return UserConfig.defaults()
    try:
        data = json.loads(b64decode(b64config))
        
        # Filter out non-existent filter IDs
        valid_filters = []
        for filter_id in data.get("filters", []):
            try:
                valid_filters.append(filter_by_id(filter_id))
            except StopIteration:
                log.warning(f"Filter with ID '{filter_id}' not found, skipping.")
        
        data["filters"] = valid_filters
        
        return UserConfig.model_validate(data)
    except (json.JSONDecodeError, ValidationError) as e:
        log.error("Error parsing configuration", exc_info=e)
        raise
    except Exception as e:
        log.error("Unrecognized config parsing error", exc_info=e)
        return UserConfig.defaults()


