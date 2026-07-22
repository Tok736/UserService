import json
from typing import Any

from pydantic import BaseModel
from pydantic_settings import BaseSettings

from src.logger import logger
from src.scripts.create_config import fill_from


# fmt: off
class ProjectSettings(BaseModel):
    workers:                   int


class SQLSettings(BaseModel):
    user:                      str
    password:                  str
    host:                      str
    port:                      int
    database:                  str

    @property
    def sqlalchemy_url(self) -> str:
        return f"postgresql+asyncpg://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"


class RabbitSettings(BaseModel):
    user:                      str | None
    password:                  str | None
    host:                      str
    port:                      int
    message_ttl:               int

    @property
    def rabbit_url(self) -> str:
        return f"amqp://{self.user}:{self.password}@{self.host}:{self.port}/"


class LogSettings(BaseModel):
    level:                     str
    console_output:            bool
    exceptions:                bool


class InvitationSettings(BaseModel):
    token_ttl_hours:           int

# fmt: on


class Settings(BaseSettings):
    """Класс со всеми настройками проекта"""

    # fmt: off
    project:        ProjectSettings
    sql:            SQLSettings
    rabbit:         RabbitSettings
    log:            LogSettings
    invitation:     InvitationSettings
    # fmt: on

    def load_config_file(self) -> list[str]:
        """
        Обновляет свои поля из конфиг файлов. Заполняет новыми значениями.
        Возвращает имена полей, которые были обновлены.
        """

        new_config = settings_from_files(self._config_path, self._web_config_path)

        stack: list[tuple[BaseModel, BaseModel]] = [(self, new_config)]
        updated_fields = []

        while len(stack) > 0:
            old, new = stack.pop()

            for (name, old_value), (_, new_value) in zip(old, new, strict=True):
                if isinstance(new_value, BaseModel):
                    stack.append((old_value, new_value))
                else:
                    old.__setattr__(name, new_value)
                    if old_value != new_value:
                        updated_fields.append(name)

        return updated_fields

    def set_config_paths(self, config_path: str, web_config_path: str) -> None:
        """Задает путь до конфиг файла"""
        self._config_path = config_path
        self._web_config_path = web_config_path

    @staticmethod
    def fill_from_web_config(config: dict[str, Any], web_config: dict[str, Any]) -> None:
        """Заполняет данные из главного веб конфига"""

        config["sql"]["user"] = web_config["sql"]["user"]
        config["sql"]["password"] = web_config["sql"]["password"]
        config["sql"]["host"] = web_config["sql"]["host"]
        config["sql"]["port"] = web_config["sql"]["port"]

        config["rabbit"]["user"] = web_config["rabbit_mq"]["login"]
        config["rabbit"]["password"] = web_config["rabbit_mq"]["pass"]
        config["rabbit"]["host"] = web_config["rabbit_mq"]["server"]
        config["rabbit"]["port"] = web_config["rabbit_mq"]["port"]


def settings_from_files(config_path: str, web_config_path: str) -> Settings:
    """Загружает конфиг из конфиг файла"""

    with open("config.json", encoding="utf-8") as f:
        default_config = json.load(f)

    try:
        with open(config_path, encoding="utf-8") as f:
            config = json.load(f)
        fill_from(config, default_config)
    except Exception as e:
        logger.warning(f"[Settings] Error opening {config_path}. {e}")
        raise ValueError(f"Error opening {config_path}. {e}") from e

    with open(web_config_path, encoding="utf-8") as f:
        web_config = json.load(f)

    Settings.fill_from_web_config(config, web_config)

    settings = Settings.model_validate(config)
    settings.set_config_paths(config_path, web_config_path)

    return settings


settings = settings_from_files(
    config_path="/edcurve/webconf/user_service/config.json",
    web_config_path="/edcurve/webconf/config.json",
)
