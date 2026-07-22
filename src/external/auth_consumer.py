from uuid import UUID

from pydantic import BaseModel

from src.exceptions import AuthConsumerUnavailable
from src.rabbit import Response, rpc_call


# fmt: off
class SoftDeleteRequest(BaseModel):
    user_id:         UUID
# fmt: on


class ExternalAuthConsumer:
    """Класс для взаимодействия с микросервисом UserService"""

    async def soft_delete_user(self, user_id: UUID, correlation_id: str) -> Response:
        """Создать пользователя"""

        result = await rpc_call(
            SoftDeleteRequest(user_id=user_id),
            "DELETE-auth_consumer/user",
            Response,
            correlation_id=correlation_id,
            timeout=3,
        )

        if result is None:
            raise AuthConsumerUnavailable()

        return result
