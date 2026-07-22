from datetime import date, datetime

from pydantic import BaseModel, Field

from src.relation.enums import RelationStatus, RelationType, StudentSort
from src.user.schemas import UserRead

# fmt: off


class RelationRead(BaseModel):
    id:            int
    from_user_id:  int
    to_user_id:    int
    relation_type: RelationType
    subjects:      list | None    = None
    level:         str | None     = None
    status:        RelationStatus
    notes:         str | None     = None
    tags:          list | None    = None
    parent_rights: dict | None    = None
    start_date:    date | None    = None
    end_date:      date | None    = None
    created_at:    datetime
    updated_at:    datetime
    version:       int

    model_config = {"from_attributes": True}


class CreateStudentRequest(BaseModel):
    access_token:  str
    first_name:    str | None  = Field(default=None, max_length=100)
    last_name:     str | None  = Field(default=None, max_length=100)
    middle_name:   str | None  = Field(default=None, max_length=100)
    nickname:      str | None  = Field(default=None, max_length=200)
    date_of_birth: date | None = None
    contacts:      dict | None = None
    messengers:    dict | None = None
    timezone:      str         = Field(default="UTC", max_length=64)
    locale:        str         = Field(default="ru", max_length=16)
    subjects:      list | None = None
    level:         str | None  = Field(default=None, max_length=100)
    notes:         str | None  = None
    tags:          list | None = None


class AttachStudentRequest(BaseModel):
    access_token:  str
    student_id:    int
    subjects:      list | None  = None
    level:         str | None   = Field(default=None, max_length=100)
    notes:         str | None   = None
    tags:          list | None  = None


class AttachParentRequest(BaseModel):
    access_token:  str
    parent_id:     int
    student_id:    int
    parent_rights: dict | None = None


class ListStudentsRequest(BaseModel):
    access_token:  str
    limit:         int                   = Field(default=50, ge=1, le=200)
    offset:        int                   = Field(default=0, ge=0)
    status:        RelationStatus | None = None
    subject:       str | None            = None
    tag:           str | None            = None
    group_row:     int | None            = None
    search:        str | None            = None
    sort:          StudentSort           = StudentSort.created
    descending:    bool                  = True


class ListTutorsRequest(BaseModel):
    access_token:  str
    limit:         int                   = Field(default=50, ge=1, le=200)
    offset:        int                   = Field(default=0, ge=0)


class UpdateRelationRequest(BaseModel):
    access_token:  str
    relation_id:   int
    version:       int
    subjects:      list | None           = None
    level:         str | None            = Field(default=None, max_length=100)
    notes:         str | None            = None
    tags:          list | None           = None
    status:        RelationStatus | None = None
    start_date:    date | None           = None
    end_date:      date | None           = None


class UpdateParentRightsRequest(BaseModel):
    access_token:  str
    relation_id:   int
    version:       int
    parent_rights: dict


class RelationIdRequest(BaseModel):
    access_token:  str
    relation_id:   int
    version:       int


class StudentListItem(BaseModel):
    relation:      RelationRead
    student:       UserRead


class TutorListItem(BaseModel):
    relation:      RelationRead
    tutor:         UserRead

# fmt: on
