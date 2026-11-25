"""Who may press Approve / Stop / Resume (A3; owner decision 24/11/2026, scope ticket 25/11/2026).

One personal bearer token per person, from the environment (never from the DB, never logged):
  AUTH_OWNER=<name>:<token>                    the project owner: everything, and the only one who may resume
  AUTH_DELEGATES=<name>:<token>,<name>:<token>  authorized people: approve/reject drafts, emergency stop
  AUTH_MAX_DELEGATES=3                         the current limit; raise it here, no code change
Requests send `Authorization: Bearer <token>`. The server derives the person's name from the token and that
name is what gets stored (approvals.decided_by, system_stop.actor). No config = nobody can act (secure default).
"""
import hmac
import os

from fastapi import Header, HTTPException

OWNER, DELEGATE = 'owner', 'delegate'
MIN_TOKEN_LEN = 16


class AuthConfigError(ValueError):
    """Bad AUTH_* environment. The message never contains a token."""


def _pairs(raw: str, var: str) -> list:
    out = []
    for item in filter(None, (s.strip() for s in raw.split(','))):
        name, sep, token = item.partition(':')
        name, token = name.strip(), token.strip()
        if not sep or not name or not token:
            raise AuthConfigError(f'{var}: each entry must be <name>:<token>')
        if len(token) < MIN_TOKEN_LEN:
            raise AuthConfigError(f'{var}: token of {name!r} is shorter than {MIN_TOKEN_LEN} characters')
        out.append((name, token))
    return out


def actors() -> list:
    """[(name, token, role)] from the environment; raises AuthConfigError on a bad or over-limit config."""
    owner = _pairs(os.getenv('AUTH_OWNER', ''), 'AUTH_OWNER')
    if len(owner) > 1:
        raise AuthConfigError('AUTH_OWNER: exactly one owner')
    delegates = _pairs(os.getenv('AUTH_DELEGATES', ''), 'AUTH_DELEGATES')
    limit = int(os.getenv('AUTH_MAX_DELEGATES', '3'))
    if len(delegates) > limit:
        raise AuthConfigError(f'AUTH_DELEGATES: {len(delegates)} people, limit AUTH_MAX_DELEGATES={limit}')
    rows = [(n, t, OWNER) for n, t in owner] + [(n, t, DELEGATE) for n, t in delegates]
    names, tokens = [r[0] for r in rows], [r[1] for r in rows]
    if len(set(names)) != len(names) or len(set(tokens)) != len(tokens):
        raise AuthConfigError('AUTH_OWNER/AUTH_DELEGATES: names and tokens must be unique')
    return rows


def identify(authorization: str | None) -> tuple | None:
    """(name, role) for a valid `Bearer <token>`, else None. Compares every token in constant time."""
    scheme, _, token = (authorization or '').partition(' ')
    if scheme.lower() != 'bearer' or not token.strip():
        return None
    found = None
    for name, tok, role in actors():
        if hmac.compare_digest(tok.encode(), token.strip().encode()):
            found = (name, role)
    return found


def require(*roles):
    """FastAPI dependency: the caller's name if their token has one of `roles`; 401 unknown, 403 not allowed."""
    def dep(authorization: str | None = Header(default=None)) -> str:
        try:
            who = identify(authorization)
        except AuthConfigError as exc:
            raise HTTPException(500, f'authorization is misconfigured: {exc}')
        if who is None:
            raise HTTPException(401, 'a valid personal token is required (Authorization: Bearer <token>)',
                                headers={'WWW-Authenticate': 'Bearer'})
        if who[1] not in roles:
            raise HTTPException(403, f'{who[0]} is not allowed to do this')
        return who[0]
    return dep
