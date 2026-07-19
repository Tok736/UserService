from faststream import Depends
from faststream.rabbit import RabbitRouter

from src.rabbit import Response, queue
from src.user.dependencies import get_user_service
from src.user.schemas import (
    DeleteProfileRequest,
    ReadProfileRequest,
    ReadRelatedProfileRequest,
    UpdateProfileRequest,
    UserRead,
)
from src.user.service import UserService

router = RabbitRouter()


# --- CRUD профиля (request/reply RPC от фронта) ---


@router.subscriber(queue.get("profile/me"))
async def read_own_profile(
    request: ReadProfileRequest, service: UserService = Depends(get_user_service)
) -> Response[UserRead]:
    return await service.read_own_profile(request)


@router.subscriber(queue.get("profile"))
async def read_related_profile(
    request: ReadRelatedProfileRequest, service: UserService = Depends(get_user_service)
) -> Response[UserRead]:
    return await service.read_related_profile(request)


@router.subscriber(queue.put("profile/me"))
async def update_own_profile(
    request: UpdateProfileRequest, service: UserService = Depends(get_user_service)
) -> Response[UserRead]:
    return await service.update_own_profile(request)


@router.subscriber(queue.delete("profile/me"))
async def delete_own_profile(
    request: DeleteProfileRequest, service: UserService = Depends(get_user_service)
) -> Response[UserRead]:
    return await service.delete_own_profile(request)
