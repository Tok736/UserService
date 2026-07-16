from __future__ import annotations

from typing import Any

import jwt
from jwt import PyJWK
from jwt.exceptions import InvalidTokenError, PyJWKError
from pydantic import BaseModel

from src.exceptions import InvalidToken

ALLOWED_ALGORITHMS = frozenset({"RS256", "RS384", "RS512", "PS256", "PS384", "PS512"})


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


class JWTValidator:
    def __init__(
        self,
        jwks: JWKS,
        *,
        issuer: str | None = None,
        audience: str | None = None,
        leeway: float = 0,
        require: tuple[str, ...] = ("exp", "iat"),
    ) -> None:
        self.issuer = issuer
        self.audience = audience
        self.leeway = leeway
        self.require = list(require)
        self.keys: dict[str, tuple[PyJWK, str]] = {}
        self.refresh(jwks)

    def refresh(self, jwks: JWKS) -> None:
        """Перестроить набор ключей (ротация ключей в AuthService)."""
        keys: dict[str, tuple[PyJWK, str]] = {}
        for key in jwks.keys:
            if key.use != "sig":
                continue
            if key.alg not in ALLOWED_ALGORITHMS:
                continue
            try:
                keys[key.kid] = (PyJWK.from_dict(key.model_dump()), key.alg)
            except PyJWKError as exc:
                raise ValueError(f"Некорректный JWK kid={key.kid}: {exc}") from exc

        if not keys:
            raise ValueError("JWKS не содержит подходящих ключей для проверки подписи")
        self.keys = keys

    def decode(self, token: str) -> dict[str, Any]:
        try:
            header = jwt.get_unverified_header(token)
        except InvalidTokenError as e:
            raise InvalidToken(f"Некорректный заголовок токена: {e}") from e

        kid = header.get("kid")
        if not kid:
            raise InvalidToken("В заголовке токена отсутствует kid")

        entry = self.keys.get(kid)
        if entry is None:
            raise InvalidToken(f"Неизвестный kid: {kid}")

        jwk, alg = entry
        if header.get("alg") != alg:
            raise InvalidToken(f"alg в токене ({header.get('alg')}) не совпадает с alg ключа ({alg})")

        try:
            return jwt.decode(
                token,
                key=jwk.key,
                algorithms=[alg],
                issuer=self.issuer,
                audience=self.audience,
                leeway=self.leeway,
                options={
                    "require": self.require,
                    "verify_aud": self.audience is not None,
                    "verify_iss": self.issuer is not None,
                },
            )
        except InvalidTokenError as e:
            raise InvalidToken(str(e)) from e

    __call__ = decode
