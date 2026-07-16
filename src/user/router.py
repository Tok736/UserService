from faststream.rabbit import RabbitRouter

from src.rabbit import Response, queue

from .schemas import UserRead, UserReadRequest

router = RabbitRouter()


@router.subscriber(queue.get("user.me"))
async def register(
    request: UserReadRequest,
) -> Response[UserRead]:
    return Response(data=UserRead(text="Hello"))
