from faststream import Context, Depends
from faststream.rabbit import RabbitRouter

from src.rabbit import Response, queue
from src.user.dependencies import get_user_service
from src.user.schemas import (
    DeleteProfileRequest,
    ReadProfileRequest,
    ReadRelatedProfileRequest,
    UpdateProfileRequest,
    UserCreate,
    UserRead,
)
from src.user.service import UserService

router = RabbitRouter()


# --- Frontend эндпоинты ---
@router.subscriber(queue.get("profile/me"))
async def read_me(request: ReadProfileRequest, service: UserService = Depends(get_user_service)) -> Response[UserRead]:
    """Прочитать свой профиль"""
    return await service.read_me(request)


@router.subscriber(queue.get("profile"))
async def read_related_profile(
    request: ReadRelatedProfileRequest, service: UserService = Depends(get_user_service)
) -> Response[UserRead]:
    """Прочитать профиль связанного человека с проверкой связи"""
    return await service.read_related_profile(request)


@router.subscriber(queue.put("profile/me"))
async def update_me(
    request: UpdateProfileRequest, service: UserService = Depends(get_user_service)
) -> Response[UserRead]:
    """Обновить свой профиль (оптимистичная блокировка)"""
    return await service.update_me(request)


@router.subscriber(queue.delete("profile/me"))
async def delete_me(
    request: DeleteProfileRequest,
    service: UserService = Depends(get_user_service),
    correlation_id: str = Context("message.correlation_id"),
) -> Response[UserRead]:
    """Удалить свой профиль: soft delete + анонимизация"""
    return await service.delete_me(request, correlation_id)


# --- Backend эндпоинты ---
@router.subscriber(queue.post("user"))
async def create_user(user: UserCreate, service: UserService = Depends(get_user_service)) -> Response:
    """Создать пользователя"""
    return await service.create_user(user)
