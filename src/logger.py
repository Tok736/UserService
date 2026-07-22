import json
import os
from logging import FileHandler, Formatter, Handler, Logger, StreamHandler, getLogger


def build_logger(
    level: str | int,
    log_path: str,
    console_output: bool,
    format: str = "%(asctime)s %(levelname)s - %(message)s",
) -> Logger:
    """Создать логгер с заданными параметрами"""

    os.makedirs(log_path.rsplit(sep="/", maxsplit=1)[0], exist_ok=True)

    logger = getLogger(__name__)
    logger.setLevel(level=level)

    handlers: list[Handler] = []
    formatter = Formatter(format)

    try:
        file_handler = FileHandler(log_path)
    except Exception:
        file_handler = FileHandler("logs.log")

    file_handler.setFormatter(formatter)
    handlers.append(file_handler)

    if console_output:
        console_handler = StreamHandler()

        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        handlers.append(console_handler)

    for handler in handlers:
        logger.addHandler(handler)

    return logger


container_id = os.uname().nodename
config_path = "/edcurve/webconf/user_service/config.json"

error = None
try:
    with open(config_path) as f:
        data = json.load(f)
except Exception as e:
    error = e
    data = {"log": {"level": "DEBUG", "console_output": True}}


logger = build_logger(
    level=data["log"]["level"],
    log_path=f"/var/log/edcurve/user_service/AuthConsumer_{container_id}.log",
    console_output=data["log"]["console_output"],
)
