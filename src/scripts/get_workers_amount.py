import json
import os
import sys

# Добавление рабочей директории (из которой запускается скрипт) для корректных импортов
sys.path.insert(0, os.getcwd())

from src.logger import logger


def get_worker_amount() -> None:
    """Получить количество воркеров из конфига"""

    try:
        with open("/edcurve/webconf/auth_consumer/config.json") as f:
            json_dict = json.load(f)
            workers = json_dict["project"]["workers"]
    except Exception as e:
        logger.warning(f"[get_worker_amount] Error getting workers amount. {e}. Set as default (4 workers)")
        workers = 4

    print(workers)
    logger.info(f"[get_worker_amount] Will use {workers} workers amount")


if __name__ == "__main__":
    get_worker_amount()
