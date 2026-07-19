from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from faststream import FastStream

from src.auth.schemas import JWKS
from src.auth.service import get_token_service
from src.rabbit import Response, broker, rpc_call

# from src.user.router import router as user_router


@asynccontextmanager
async def lifespan() -> AsyncIterator[None]:
    await broker.connect()
    jwks_response = await rpc_call(
        "",
        "auth_consumer.GET.jwks",
        Response[JWKS],
        timeout=5,
    )
    if jwks_response is None or jwks_response.data is None:
        raise ValueError("Can't get jwks from AuthConsumer")
    get_token_service().refresh(jwks_response.data)

    yield


# broker.include_router(user_router)

app = FastStream(broker, lifespan=lifespan)
