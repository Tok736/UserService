from uuid import UUID

from pydantic import BaseModel, Field


# fmt: off
class JWK(BaseModel):
    kty:             str = "RSA"
    use:             str = "sig"
    alg:             str
    kid:             str
    n:               str
    e:               str


class JWKS(BaseModel):
    keys:            list[JWK]


class JWTPayload(BaseModel):
    user_id:         UUID   = Field(alias="sub")
    type:            str
    iss:             str
    aud:             str
    iat:             int
    exp:             int
    jti:             UUID

# fmt: on
