from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from faststream import FastStream

from src.auth.schemas import JWKS
from src.auth.service import get_token_service
from src.logger import logger
from src.rabbit import Response, broker, rpc_call
from src.user.router import router as user_router


@asynccontextmanager
async def lifespan() -> AsyncIterator[None]:
    await broker.connect()
    jwks_response = await rpc_call(
        "",
        "GET-auth_consumer/jwks",
        Response[JWKS],
        timeout=5,
    )
    if jwks_response is None or jwks_response.data is None:
        raise ValueError("Can't get JWKS from AuthConsumer")
    get_token_service().refresh(jwks_response.data)
    logger.info("[lifespan] Successfully got JWKS from auth consumer")

    yield


broker.include_router(user_router)

app = FastStream(broker, lifespan=lifespan)
