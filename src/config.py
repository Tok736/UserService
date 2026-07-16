import json
from typing import Any

from pydantic import BaseModel
from pydantic_settings import BaseSettings

from src.logger import logger


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


# fmt: on


class Settings(BaseSettings):
    """Класс со всеми настройками проекта"""

    # fmt: off
    project:        ProjectSettings
    sql:            SQLSettings
    rabbit:         RabbitSettings
    log:            LogSettings
    # fmt: on

    def load_config_file(self) -> list[str]:
        """
        Обновляет свои поля из конфиг файлов. Заполняет новыми значениями.
        Возвращает имена полей, которые были обновлены.
        """

        new_config = Settings.from_files(self._config_path, self._web_config_path)

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
    def fill_from(target_config: dict[str, Any], source_config: dict[str, Any]) -> None:
        """
        Обновляет поля конфига:
        - Если в дефолт конфиге появились новые поля, то они добавляются в конфиг
        - Если в конфиге есть поля, которых нет в дефолт конфиге, то они удаляются из конфига
        - Если поменялся тип поля, то сначала происходит попытка преобразовать
        к новому типу, при неудаче ставится значение из дефолт конфига
        - Если отличается только значение поля, то оно не меняется
        """

        if not isinstance(target_config, dict) or not isinstance(source_config, dict):
            raise ValueError("First layer in structure of config.json and config-default.json must be dict like")

        stack: list[tuple[dict[str, Any], dict[str, Any]]] = [(target_config, source_config)]

        while len(stack) > 0:
            target, source = stack.pop()

            for key in list(target.keys()):
                if key not in source:
                    logger.warning(f"[Settings] Field '{key}' must not be in config.json")
                    del target[key]

            for key in source:
                if key not in target:
                    logger.warning(f"[Settings] Field '{key}' is missing in config.json")
                    target[key] = source[key]

            temp_dict = {key: target[key] for key in source}

            target.clear()
            target.update(temp_dict)
            types = (str, int, float, bool)

            for key in target:
                if isinstance(target[key], dict) and isinstance(source[key], dict):
                    stack.append((target[key], source[key]))

                elif isinstance(target[key], list) and isinstance(source[key], list):
                    pass

                elif target[key] is None or source[key] is None:
                    pass

                elif type(target[key]) is not type(source[key]) and all(
                    t in types for t in (type(target[key]), type(source[key]))
                ):
                    try:
                        target[key] = type(source[key])(target[key])
                        logger.warning(f"[Settings] Type of field '{key}' successfully converted")
                    except ValueError:
                        target[key] = source[key]
                        logger.warning(f"[Settings] Type of field '{key}' is not right")

                elif type(target[key]) is type(source[key]):
                    pass

                else:
                    target[key] = source[key]
                    logger.warning(f"[Settings] Value {source[key]} is set on field '{key}'")

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

    @staticmethod
    def from_files(config_path: str, web_config_path: str) -> "Settings":
        """Загружает конфиг из конфиг файла"""

        with open("config.json", encoding="utf-8") as f:
            default_config = json.load(f)

        try:
            with open(config_path, encoding="utf-8") as f:
                config = json.load(f)
            Settings.fill_from(config, default_config)
        except FileNotFoundError:
            logger.warning(f"[Settings] There is no config file on {config_path}")
            logger.info(f"[Settings] Create a config file with such structure:\n{json.dumps(default_config, indent=4)}")
            config = default_config
        except Exception as e:
            logger.warning(f"[Settings] Error opening {config_path}. {e}. Will use data from default config")
            config = default_config

        with open(web_config_path, encoding="utf-8") as f:
            web_config = json.load(f)

        Settings.fill_from_web_config(config, web_config)

        settings = Settings.model_validate(config)
        settings.set_config_paths(config_path, web_config_path)

        return settings


settings = Settings.from_files(
    config_path="/edcurve/webconf/user_service/config.json",
    web_config_path="/edcurve/webconf/config.json",
)
