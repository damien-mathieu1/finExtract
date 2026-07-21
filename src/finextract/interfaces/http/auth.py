from __future__ import annotations

import jwt
from fastapi import HTTPException, Request


class ClerkTokenVerifier:
    """FastAPI dependency verifying Clerk-issued session JWTs.

    The backend's Cloud Run URL is public, so it must validate tokens itself
    rather than trust the Next.js proxy. Verification is fully local: the
    JWKS is fetched from the Clerk issuer once per key id and cached
    (PyJWKClient), so there is no per-request network call.

    Returns the Clerk user id (`sub` claim) for use as extraction owner.
    """

    def __init__(self, issuer: str, authorized_parties: list[str] | None = None) -> None:
        self._issuer = issuer.rstrip("/")
        self._authorized_parties = authorized_parties or []
        self._jwks = jwt.PyJWKClient(
            f"{self._issuer}/.well-known/jwks.json", cache_keys=True, lifespan=3600
        )

    def __call__(self, request: Request) -> str:
        header = request.headers.get("Authorization", "")
        if not header.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Not authenticated")
        token = header.removeprefix("Bearer ")
        try:
            key = self._jwks.get_signing_key_from_jwt(token)
            claims = jwt.decode(
                token,
                key.key,
                algorithms=["RS256"],
                issuer=self._issuer,
                leeway=10,
                options={"require": ["exp", "iat", "sub"]},
            )
        except jwt.PyJWTError as exc:
            raise HTTPException(status_code=401, detail="Invalid token") from exc
        azp = claims.get("azp")
        if self._authorized_parties and azp and azp not in self._authorized_parties:
            raise HTTPException(status_code=401, detail="Invalid authorized party")
        return str(claims["sub"])
