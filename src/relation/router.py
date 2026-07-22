from faststream import Depends
from faststream.rabbit import RabbitRouter

from src.rabbit import Response, queue
from src.relation.service import RelationService
from src.schemas import Page

from .dependencies import get_relation_service
from .schemas import (
    AttachParentRequest,
    AttachStudentRequest,
    CreateStudentRequest,
    ListStudentsRequest,
    ListTutorsRequest,
    RelationIdRequest,
    RelationRead,
    StudentListItem,
    TutorListItem,
    UpdateParentRightsRequest,
    UpdateRelationRequest,
)

router = RabbitRouter()


@router.subscriber(queue.post("student"))
async def create_student(
    request: CreateStudentRequest, service: RelationService = Depends(get_relation_service)
) -> Response[RelationRead]:
    """Создать управляемую карточку ученика + связь tutor_of одной операцией"""
    return await service.create_student(request)


@router.subscriber(queue.post("student/attach"))
async def attach_student(
    request: AttachStudentRequest, service: RelationService = Depends(get_relation_service)
) -> Response[RelationRead]:
    """Прикрепить существующего пользователя как своего ученика"""
    return await service.attach_student(request)


@router.subscriber(queue.get("student"))
async def list_students(
    request: ListStudentsRequest, service: RelationService = Depends(get_relation_service)
) -> Response[Page[StudentListItem]]:
    """Список своих учеников с фильтрами/поиском/сортировкой"""
    return await service.list_students(request)


@router.subscriber(queue.get("tutor"))
async def list_tutors(
    request: ListTutorsRequest, service: RelationService = Depends(get_relation_service)
) -> Response[Page[TutorListItem]]:
    """Список своих репетиторов"""
    return await service.list_tutors(request)


@router.subscriber(queue.put("relation"))
async def update_relation(
    request: UpdateRelationRequest, service: RelationService = Depends(get_relation_service)
) -> Response[RelationRead]:
    """Обновить связь (предметы, уровень, заметки, статус, теги)"""
    return await service.update_relation(request)


@router.subscriber(queue.post("relation/archive"))
async def archive_relation(
    request: RelationIdRequest, service: RelationService = Depends(get_relation_service)
) -> Response[RelationRead]:
    """Архивировать связь (soft, история сохраняется)"""
    return await service.archive_relation(request)


@router.subscriber(queue.delete("relation"))
async def delete_relation(
    request: RelationIdRequest, service: RelationService = Depends(get_relation_service)
) -> Response[RelationRead]:
    """soft удалить связь"""
    return await service.delete_relation(request)


@router.subscriber(queue.post("parent"))
async def attach_parent(
    request: AttachParentRequest, service: RelationService = Depends(get_relation_service)
) -> Response[RelationRead]:
    """Прикрепить родителя к ученику (связь parent_of)"""
    return await service.attach_parent(request)


@router.subscriber(queue.put("parent/rights"))
async def update_parent_rights(
    request: UpdateParentRightsRequest, service: RelationService = Depends(get_relation_service)
) -> Response[RelationRead]:
    """Настроить доступ родителя на уровне связи parent_of"""
    return await service.update_parent_rights(request)
