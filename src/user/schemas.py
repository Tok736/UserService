from pydantic import BaseModel, SecretStr


# fmt: off
class UserReadRequest(BaseModel):
    access_token:   SecretStr


class UserRead(BaseModel):
    text:           str

# fmt: on
