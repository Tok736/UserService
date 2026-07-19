from pydantic import BaseModel


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
# fmt: on
