from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, Field

from src.enums import AccountStatus, BasicRole


# fmt: off
class UserRead(BaseModel):
    id:                    int
    user_id:               UUID | None
    basic_role:            BasicRole
    account_status:        AccountStatus
    email:                 str
    first_name:            str | None      = None
    last_name:             str | None      = None
    middle_name:           str | None      = None
    nickname:              str | None      = None
    avatar_url:            str | None      = None
    date_of_birth:         date | None     = None
    contacts:              dict | None     = None
    messengers:            dict | None     = None
    timezone:              str
    locale:                str
    bio:                   str | None      = None
    created_at:            datetime
    updated_at:            datetime
    version:               int

    model_config = {"from_attributes": True}


class UserCreate(BaseModel):
    user_id:               UUID | None
    basic_role:            BasicRole
    account_status:        AccountStatus   = AccountStatus.active
    email:                 str
    first_name:            str | None      = None
    last_name:             str | None      = None
    middle_name:           str | None      = None
    nickname:              str | None      = None
    avatar_url:            str | None      = None
    date_of_birth:         date | None     = None
    contacts:              dict | None     = None
    messengers:            dict | None     = None
    timezone:              str
    locale:                str
    bio:                   str | None      = None


class ReadProfileRequest(BaseModel):
    access_token:          str


class ReadRelatedProfileRequest(BaseModel):
    access_token:          str
    target_user_row:       int


class UpdateProfileRequest(BaseModel):
    access_token:          str
    version:               int
    first_name:            str | None       = Field(default=None, max_length=100)
    last_name:             str | None       = Field(default=None, max_length=100)
    middle_name:           str | None       = Field(default=None, max_length=100)
    nickname:              str | None       = Field(default=None, max_length=200)
    avatar_url:            str | None       = Field(default=None, max_length=512)
    date_of_birth:         date | None      = None
    contacts:              dict | None      = None
    messengers:            dict | None      = None
    timezone:              str | None       = Field(default=None, max_length=64)
    locale:                str | None       = Field(default=None, max_length=16)
    bio:                   str | None       = None
    basic_role:            BasicRole | None = None


class DeleteProfileRequest(BaseModel):
    access_token:          str

# fmt: on
