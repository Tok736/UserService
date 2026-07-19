import json
import os
import shutil
import sys
from typing import Any

# Добавление рабочей директории (из которой запускается скрипт) для корректных импортов
sys.path.insert(0, os.getcwd())

from src.logger import logger


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
                logger.warning(f"[Settings] Field '{key}' must not be in config.json. Removing")
                del target[key]

        for key in source:
            if key not in target:
                logger.warning(f"[Settings] Field '{key}' is missing in config.json. Adding")
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


def fill_or_create_config(source: str, target: str) -> None:
    """Создает конфиг по указанному пути или обновляет его поля"""

    if not os.path.exists(target):
        os.makedirs(target[: target.rfind("/")], exist_ok=True)
        shutil.copy2(source, target)
    else:
        with open(target) as f, open(source) as f2:
            target_config = json.load(f)
            source_config = json.load(f2)

        fill_from(target_config, source_config)

        with open(target, "w") as f:
            json.dump(target_config, f, indent=4)


if __name__ == "__main__":
    fill_or_create_config(
        source="config.json",
        target="/edcurve/webconf/user_service/config.json",
    )
