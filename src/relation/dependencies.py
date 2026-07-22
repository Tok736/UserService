from faststream import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.service import get_token_service
from src.database import get_session
from src.relation.repository import UserRelationRepository
from src.relation.service import RelationService
from src.user.repository import UserRepository


def get_relation_service(session: AsyncSession = Depends(get_session)) -> RelationService:
    """Собирает RelationService на каждый запрос с сессией"""
    return RelationService(
        session=session,
        users=UserRepository(session),
        relations=UserRelationRepository(session),
        tokens=get_token_service(),
    )
