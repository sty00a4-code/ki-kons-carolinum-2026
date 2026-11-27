"""Anmeldung: POST /auth/login liefert ein Bearer-Token, GET /me den Benutzer."""

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from .. import config
from ..database import get_db
from ..passwords import burn_time, verify_password
from ..repositories import users as users_repo
from ..schemas import CurrentUserOut, LoginIn, TokenOut
from ..security import User, create_access_token, get_current_user
from ..throttle import login_throttle

router = APIRouter(tags=["auth"])


def _out(user: User) -> CurrentUserOut:
    return CurrentUserOut(
        id=user.id,
        username=user.username,
        role=user.role,
        student_id=user.student_id,
        auth=user.auth,
    )


@router.post("/auth/login", response_model=TokenOut)
def login(payload: LoginIn, request: Request, db: Session = Depends(get_db)):
    """Benutzername und Passwort gegen ein Zugriffstoken tauschen. Das Token
    gilt PROJEKT2_TOKEN_MINUTES (Standard 60) und wird bei jeder Anfrage als
    `Authorization: Bearer <token>` mitgeschickt. Nach 5 Fehlversuchen in 15
    Minuten (je Benutzername und Adresse) antwortet die API mit 429."""
    secret = config.jwt_secret()
    if not secret:
        raise HTTPException(
            status_code=503,
            detail="Anmeldung nicht verfügbar: PROJEKT2_JWT_SECRET ist nicht gesetzt",
        )
    client = request.client.host if request.client else "unbekannt"
    key = f"{payload.username.lower()}|{client}"
    wait = login_throttle.retry_after(key)
    if wait:
        raise HTTPException(
            status_code=429,
            detail="Zu viele Fehlversuche, bitte später erneut versuchen",
            headers={"Retry-After": str(wait)},
        )

    row = users_repo.get_by_username(db, payload.username)
    if row is None:
        burn_time(payload.password)
        valid = False
    else:
        valid = bool(row["active"]) and verify_password(
            payload.password, row["password_hash"]
        )
    if not valid:
        login_throttle.failure(key)
        # Bewusst dieselbe Meldung für "unbekannt", "falsches Passwort", "gesperrt".
        raise HTTPException(
            status_code=401,
            detail="Benutzername oder Passwort falsch",
            headers={"WWW-Authenticate": "Bearer"},
        )

    login_throttle.success(key)
    users_repo.touch_login(db, row["id"])
    db.commit()
    token, expires_in = create_access_token(row["id"], secret, config.token_ttl_minutes())
    user = User(
        id=row["id"], username=row["username"], role=row["role"], student_id=row["student_id"]
    )
    return TokenOut(access_token=token, expires_in=expires_in, user=_out(user))


@router.get("/me", response_model=CurrentUserOut)
def me(user: User = Depends(get_current_user)):
    """Wer bin ich? Praktisch, damit die UI Rolle und student_id kennt."""
    return _out(user)
