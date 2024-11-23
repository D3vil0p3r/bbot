import logging
from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, List, Union, Annotated

from bbot.models.helpers import utc_now_timestamp

log = logging.getLogger("bbot_server.models")


class BBOTBaseModel(BaseModel):
    model_config = ConfigDict(extra="ignore")

    def __hash__(self):
        return hash(self.to_json())

    def __eq__(self, other):
        return hash(self) == hash(other)

    @classmethod
    def _indexed_fields(cls):
        return sorted(field_name for field_name, field in cls.model_fields.items() if "indexed" in field.metadata)

    # we keep these because they were a lot of work to make and maybe someday they'll be useful again

    # @classmethod
    # def _get_type_hints(cls):
    #     """
    #     Drills down past all the Annotated, Optional, and Union layers to get the underlying type hint
    #     """
    #     type_hints = get_type_hints(cls)
    #     unwrapped_type_hints = {}
    #     for field_name in cls.model_fields:
    #         type_hint = type_hints[field_name]
    #         while 1:
    #             if getattr(type_hint, "__origin__", None) in (Annotated, Optional, Union):
    #                 type_hint = type_hint.__args__[0]
    #             else:
    #                 break
    #         unwrapped_type_hints[field_name] = type_hint
    #     return unwrapped_type_hints

    # @classmethod
    # def _datetime_fields(cls):
    #     datetime_fields = []
    #     for field_name, type_hint in cls._get_type_hints().items():
    #         if type_hint == datetime:
    #             datetime_fields.append(field_name)
    #     return sorted(datetime_fields)


### EVENT ###


class Event(BBOTBaseModel):
    uuid: Annotated[str, "indexed", "unique"]
    id: Annotated[str, "indexed"]
    type: Annotated[str, "indexed"]
    scope_description: str
    data: Annotated[Optional[str], "indexed"] = None
    data_json: Optional[dict] = None
    host: Annotated[Optional[str], "indexed"] = None
    port: Optional[int] = None
    netloc: Optional[str] = None
    # we store the host in reverse to allow for instant subdomain queries
    # this works because indexes are left-anchored, but we need to search starting from the right side
    reverse_host: Annotated[Optional[str], "indexed"] = ""
    resolved_hosts: Union[List, None] = None
    dns_children: Union[dict, None] = None
    web_spider_distance: int = 10
    scope_distance: int = 10
    scan: Annotated[str, "indexed"]
    timestamp: Annotated[float, "indexed"]
    inserted_at: Annotated[Optional[float], "indexed"] = Field(default_factory=utc_now_timestamp)
    parent: Annotated[str, "indexed"]
    parent_uuid: Annotated[str, "indexed"]
    tags: List = []
    module: Annotated[Optional[str], "indexed"] = None
    module_sequence: Optional[str] = None
    discovery_context: str = ""
    discovery_path: List[str] = []
    parent_chain: List[str] = []

    def __init__(self, **data):
        super().__init__(**data)
        if self.host:
            self.reverse_host = self.host[::-1]

    def get_data(self):
        if self.data is not None:
            return self.data
        return self.data_json


### SCAN ###

class Scan(BBOTBaseModel):
    id: Annotated[str, "indexed", "unique"]
    name: str
    status: Annotated[str, "indexed"]
    started_at: Annotated[float, "indexed"]
    finished_at: Annotated[Optional[float], "indexed"] = None
    duration_seconds: Optional[float] = None
    duration: Optional[str] = None
    target: dict
    preset: dict

    @classmethod
    def from_scan(cls, scan):
        return cls(
            id=scan.id,
            name=scan.name,
            status=scan.status,
            started_at=scan.started_at,
        )


### TARGET ###

class Target(BBOTBaseModel):
    name: str = "Default Target"
    strict_scope: bool = False
    seeds: List = []
    whitelist: List = []
    blacklist: List = []
    hash: Annotated[str, "indexed", "unique"]
    scope_hash: Annotated[str, "indexed"]
    seed_hash: Annotated[str, "indexed"]
    whitelist_hash: Annotated[str, "indexed"]
    blacklist_hash: Annotated[str, "indexed"]
