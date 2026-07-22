from functools import lru_cache

import jwt
from jwt import PyJWK
from jwt.exceptions import InvalidTokenError, PyJWKError

from src.exceptions import InvalidToken
from src.logger import logger

from .constants import ALLOWED_ALGORITHMS
from .schemas import JWKS, JWTPayload


class TokenService:
    def __init__(
        self,
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

    def refresh(self, jwks: JWKS) -> None:
        """Перестроить набор ключей"""
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
        logger.info("[TokenService] JWKS are refreshed successfully")

    def decode(self, token: str) -> JWTPayload:
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
            raw_data = jwt.decode(
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

            return JWTPayload.model_validate(raw_data)
        except InvalidTokenError as e:
            raise InvalidToken(str(e)) from e
        except Exception as e:
            logger.warning(f"[TokenService] Unexpected error: {e}")
            raise InvalidToken(str(e)) from e

    __call__ = decode


@lru_cache
def get_token_service() -> TokenService:
    """Singleton TokenService: грузит публичный ключ один раз"""
    return TokenService()
