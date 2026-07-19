from faststream import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.service import get_token_service
from src.database import get_session
from src.invitation.repository import InvitationRepository
from src.relation.repository import UserRelationRepository

from .repository import UserRepository
from .service import UserService


def get_user_service(session: AsyncSession = Depends(get_session)) -> UserService:
    """Собирает UserService на каждый запрос с сессией"""
    return UserService(
        session=session,
        users=UserRepository(session),
        relations=UserRelationRepository(session),
        invitations=InvitationRepository(session),
        tokens=get_token_service(),
    )
