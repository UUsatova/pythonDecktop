from dataclasses import dataclass
from typing import Dict


@dataclass
class ApiParams:
    page: str = "1"
    page_size: str = "100"
    status: str = "active"
    amount_min: str = "500"
    amount_max: str = "500"
    period_days_max: str = "30"
    rating_min: str = "45"

    @classmethod
    def from_dict(cls, data: Dict[str, str]):
        values = {field: data.get(field, getattr(cls(), field)) for field in cls.__annotations__}
        return cls(**values)

    def to_dict(self) -> Dict[str, str]:
        return {field: getattr(self, field) for field in self.__annotations__}


@dataclass
class AppConfig:
    json_path: str
    sql_path: str
    api_base_url: str
    aliases: str
    api_params: ApiParams

    @classmethod
    def from_dict(cls, data: Dict[str, str], defaults: "AppConfig"):
        api_params = ApiParams.from_dict(data.get("api_params", {}))
        return cls(
            json_path=data.get("json_path", defaults.json_path),
            sql_path=data.get("sql_path", defaults.sql_path),
            api_base_url=data.get("api_base_url", defaults.api_base_url),
            aliases=data.get("aliases", defaults.aliases),
            api_params=api_params,
        )

    def to_dict(self) -> Dict[str, str]:
        return {
            "json_path": self.json_path,
            "sql_path": self.sql_path,
            "api_base_url": self.api_base_url,
            "aliases": self.aliases,
            "api_params": self.api_params.to_dict(),
        }
