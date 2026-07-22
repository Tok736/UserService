import asyncio
from typing import Any, Generic, NamedTuple, TypeVar
from uuid import uuid4

from faststream import ExceptionMiddleware, FastStream
from faststream.rabbit import RabbitBroker, RabbitMessage, RabbitQueue
from pydantic import BaseModel

from src.config import settings
from src.exceptions import AppException
from src.logger import logger

broker = RabbitBroker(settings.rabbit.rabbit_url, logger=logger)
app = FastStream(broker)


def create_queue(prefix: str, method: str, path: str) -> RabbitQueue:
    name = f"{method}-{prefix}/{path}"
    logger.info(f"[create_queue] Creating queue with name {name}")
    return RabbitQueue(
        name=name,
        durable=True,
        arguments={"x-message-ttl": settings.rabbit.message_ttl},
    )


class queue:
    """Класс для создания RestAPI-подобных очередей"""

    prefix = "user_service"

    @staticmethod
    def get(path: str) -> RabbitQueue:
        return create_queue(queue.prefix, "GET", path)

    @staticmethod
    def post(path: str) -> RabbitQueue:
        return create_queue(queue.prefix, "POST", path)

    @staticmethod
    def put(path: str) -> RabbitQueue:
        return create_queue(queue.prefix, "PUT", path)

    @staticmethod
    def delete(path: str) -> RabbitQueue:
        return create_queue(queue.prefix, "DELETE", path)


T_response = TypeVar("T_response", bound=BaseModel)


class Pending(NamedTuple):
    """Ожидающий ответа запрос: future + схема для валидации ответа."""

    future: asyncio.Future[Any]
    response_schema: type[BaseModel]


class RabbitRPCManager:
    """
    Менеджер RPC-запросов поверх RabbitMQ.

    Обязанности:
      * лениво создать единственную callback-очередь (при первом запросе)
        и держать её живой до конца жизни процесса;
      * сопоставлять ответы с запросами по correlation_id;
      * валидировать ответ в переданную pydantic-схему.
    """

    def __init__(self, broker: RabbitBroker) -> None:
        self.broker = broker
        self.pending: dict[str, Pending] = {}
        self.callback_queue: RabbitQueue | None = None
        self.subscriber: Any = None
        self.setup_lock = asyncio.Lock()

    async def get_callback_queue(self) -> RabbitQueue:
        """Идемпотентно создаёт callback-очередь и подписчика"""

        if self.callback_queue is not None:
            return self.callback_queue

        async with self.setup_lock:
            if self.callback_queue is not None:
                return self.callback_queue

            callback_queue = RabbitQueue(f"Gateway_Callback_{uuid4().hex[:16]}", exclusive=True)
            subscriber = self.broker.subscriber(callback_queue)

            @subscriber
            async def _callback(body: dict[str, Any], message: RabbitMessage) -> None:
                await self._on_response(body, message)

            await subscriber.start()

            self.subscriber = subscriber
            self.callback_queue = callback_queue
            logger.debug(f"[RabbitRPCManager] Callback queue '{callback_queue.name}' is ready")
            return callback_queue

    async def _on_response(self, body: dict[str, Any], message: RabbitMessage) -> None:
        correlation_id = message.correlation_id

        if correlation_id is None:
            logger.warning("[RabbitRPCManager] Response without correlation_id dropped")
            return

        pending = self.pending.pop(correlation_id, None)
        if pending is None:
            logger.warning(f"[RabbitRPCManager] Unknown correlation_id '{correlation_id}' dropped")
            return

        if pending.future.done():
            return

        try:
            pending.future.set_result(pending.response_schema.model_validate(body))
        except Exception as exc:
            pending.future.set_exception(exc)

    async def call(
        self,
        request: BaseModel | str,
        queue: str,
        response_schema: type[T_response],
        *,
        timeout: float = 60,
        ttl: float = 3600,
        correlation_id: str | None = None,
    ) -> T_response | None:

        callback_queue = await self.get_callback_queue()
        if correlation_id is None:
            correlation_id = uuid4().hex
        future: asyncio.Future[T_response] = asyncio.get_running_loop().create_future()
        self.pending[correlation_id] = Pending(future, response_schema)

        try:
            logger.debug(f"[RabbitRPCManager] -> '{queue}' (cid={correlation_id})")
            await self.broker.publish(
                request.model_dump() if isinstance(request, BaseModel) else request,
                queue,
                correlation_id=correlation_id,
                reply_to=callback_queue.name,
                timeout=timeout,
                expiration=ttl,
            )
            return await asyncio.wait_for(future, timeout=timeout)
        except TimeoutError:
            logger.warning(f"[RabbitRPCManager] Timeout waiting for response (cid={correlation_id})")
        except Exception as e:
            logger.warning(f"[RabbitRPCManager] Error on request (cid={correlation_id}): {e}")
        finally:
            self.pending.pop(correlation_id, None)

        return None


manager = RabbitRPCManager(broker)


async def rpc_call(
    request: BaseModel | str,
    queue: str,
    response_schema: type[T_response],
    *,
    timeout: float = 60,
    ttl: float = 3600,
    correlation_id: str | None = None,
) -> T_response | None:
    """Выполнить RPC-запрос по RabbitMQ"""

    result = await manager.call(
        request, queue, response_schema, timeout=timeout, ttl=ttl, correlation_id=correlation_id
    )

    if result is not None:
        logger.debug(f"[rpc_call] Answer from rpc call to {queue}:\n{result.model_dump()}")

    return result


T = TypeVar("T", bound=BaseModel)


# fmt: off
class Response(BaseModel, Generic[T]):
    """Классический формат для ответов от rabbit RPC сервисов"""

    status:   int      = 200
    message:  str      = "Ok"
    data:     T | None = None

    @property
    def ok(self) -> bool:
        return self.status < 300

# fmt: on


def err(status: int, message: str) -> Response:
    return Response(status=status, message=message, data=None)


exception_middleware = ExceptionMiddleware()


@exception_middleware.add_handler(AppException, publish=True)
async def handle_app_exception(e: AppException) -> Response:
    """Хендлер для отлова AppException, которые пробрасываются при вызовах функций"""
    return err(e.status, e.message)


@exception_middleware.add_handler(Exception, publish=True)
async def handle_unexpected(e: Exception) -> Response:
    """Хендлер для отлова неожиданных ошибок"""
    logger.warning(f"[handle_unexpected] Unexpected error. {e}")
    if settings.log.exceptions:
        logger.exception(e)
    return err(500, "Internal Server Error")


broker.add_middleware(exception_middleware)
