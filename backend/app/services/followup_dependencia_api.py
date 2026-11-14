from fastapi import Depends, HTTPException
from fastapi.security import (
    HTTPAuthorizationCredentials,
    HTTPBearer,
)
from sqlalchemy.orm import Session

from app.database.database import SessionLocal
from app.services.followup_identidade_api import identificar_usuario_api


bearer = HTTPBearer(auto_error=False)


def obter_db_api():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


def exigir_usuario_api(
    credenciais: HTTPAuthorizationCredentials | None = Depends(bearer),
    db: Session = Depends(obter_db_api),
) -> dict:
    if (
        credenciais is None
        or credenciais.scheme.lower() != "bearer"
    ):
        raise HTTPException(
            status_code=401,
            detail="Autenticacao obrigatoria.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    identidade, motivo = identificar_usuario_api(
        db,
        token=credenciais.credentials,
    )

    if identidade is None:
        raise HTTPException(
            status_code=401,
            detail=motivo,
            headers={"WWW-Authenticate": "Bearer"},
        )

    return identidade
