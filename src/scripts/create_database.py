import os
import sys
from contextlib import closing

# Добавление рабочей директории (из которой запускается скрипт) для корректных импортов
sys.path.insert(0, os.getcwd())

import psycopg2
from psycopg2 import sql

from src.config import settings
from src.logger import logger


def create_database() -> None:
    """Создает базу данных с именем из конфига в случае если такой базы данных еще нет"""

    connection = psycopg2.connect(
        host=settings.sql.host,
        port=settings.sql.port,
        user=settings.sql.user,
        password=settings.sql.password,
        dbname="postgres",
    )
    connection.autocommit = True
    with closing(connection) as connection:
        with connection.cursor() as cur:
            cur.execute("SELECT 1 FROM pg_catalog.pg_database WHERE datname = %s", (settings.sql.database,))
            if not cur.fetchone():
                cur.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(settings.sql.database)))
                logger.info(f"[create_database] Created database {settings.sql.database}")
            else:
                logger.info(f"[create_database] Database {settings.sql.database} is already created")


if __name__ == "__main__":
    create_database()
