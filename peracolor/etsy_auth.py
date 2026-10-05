"""One-off OAuth 2.0 (PKCE) authorisation for the Etsy Open API v3.

Run `uv run python -m peracolor.etsy_auth`: it opens Etsy's consent page in the
browser, catches the redirect on a local port and stores the access and refresh
tokens in `.etsy-token.json` (git-ignored, readable only by you). Credentials
come from `.env` and are never printed.
"""

import base64
import hashlib
import json
import secrets
import time
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlencode, urlparse

import requests
from loguru import logger
from pydantic import BaseModel, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

REPO_ROOT = Path(__file__).resolve().parent.parent
TOKEN_PATH = REPO_ROOT / ".etsy-token.json"
REDIRECT_PORT = 3003
REDIRECT_URI = f"http://localhost:{REDIRECT_PORT}/callback"
CONNECT_URL = "https://www.etsy.com/oauth/connect"
TOKEN_URL = "https://api.etsy.com/v3/public/oauth/token"
# Read and write listings (including files and images); read shop details.
SCOPES = ("listings_r", "listings_w", "shops_r")
REQUEST_TIMEOUT_S = 30
CALLBACK_TIMEOUT_S = 300


class EtsySettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=REPO_ROOT / ".env", env_prefix="ETSY_", extra="ignore")

    api_keystring: SecretStr
    shared_secret: SecretStr

    @property
    def api_key_header(self) -> str:
        """Etsy expects `keystring:shared_secret` in the x-api-key header."""
        return f"{self.api_keystring.get_secret_value()}:{self.shared_secret.get_secret_value()}"


class EtsyToken(BaseModel):
    access_token: SecretStr
    refresh_token: SecretStr
    expires_at: float

    @property
    def user_id(self) -> str:
        """Etsy prefixes access tokens with the numeric user id."""
        return self.access_token.get_secret_value().split(".", 1)[0]


class AuthorisationError(Exception):
    """Raised when Etsy's consent flow does not return a valid authorisation code."""


def pkce_pair() -> tuple[str, str]:
    verifier = secrets.token_urlsafe(64)[:96]
    challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).rstrip(b"=").decode()
    return verifier, challenge


def consent_url(settings: EtsySettings, challenge: str, state: str) -> str:
    params = {
        "response_type": "code",
        "redirect_uri": REDIRECT_URI,
        "scope": " ".join(SCOPES),
        "client_id": settings.api_keystring.get_secret_value(),
        "state": state,
        "code_challenge": challenge,
        "code_challenge_method": "S256",
    }
    return f"{CONNECT_URL}?{urlencode(params)}"


def wait_for_code(expected_state: str) -> str:
    """Serve one request on the redirect URI and return the authorisation code."""
    received: dict[str, str] = {}

    class CallbackHandler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:  # noqa: N802 - name required by BaseHTTPRequestHandler
            query = parse_qs(urlparse(self.path).query)
            received.update({key: values[0] for key, values in query.items()})
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write("<p>PeraColor is authorised. You can close this tab.</p>".encode())

        def log_message(self, format: str, *args: object) -> None:  # noqa: A002 - base class parameter name
            """Silence the default per-request stderr logging."""

    server = HTTPServer(("localhost", REDIRECT_PORT), CallbackHandler)
    server.timeout = CALLBACK_TIMEOUT_S
    server.handle_request()
    server.server_close()
    if received.get("state") != expected_state:
        raise AuthorisationError("Etsy redirect did not return the expected state (possible stale or forged request)")
    if "code" not in received:
        raise AuthorisationError(f"Etsy did not return an authorisation code: {received.get('error', 'no response')}")
    return received["code"]


def exchange_code(settings: EtsySettings, code: str, verifier: str) -> EtsyToken:
    response = requests.post(
        TOKEN_URL,
        data={
            "grant_type": "authorization_code",
            "client_id": settings.api_keystring.get_secret_value(),
            "redirect_uri": REDIRECT_URI,
            "code": code,
            "code_verifier": verifier,
        },
        timeout=REQUEST_TIMEOUT_S,
    )
    response.raise_for_status()
    payload = response.json()
    return EtsyToken(
        access_token=payload["access_token"],
        refresh_token=payload["refresh_token"],
        expires_at=time.time() + payload["expires_in"],
    )


def save_token(token: EtsyToken, path: Path = TOKEN_PATH) -> None:
    data = {
        "access_token": token.access_token.get_secret_value(),
        "refresh_token": token.refresh_token.get_secret_value(),
        "expires_at": token.expires_at,
    }
    path.write_text(json.dumps(data))
    path.chmod(0o600)


def authorise() -> EtsyToken:
    settings = EtsySettings()
    verifier, challenge = pkce_pair()
    state = secrets.token_urlsafe(24)
    url = consent_url(settings, challenge, state)
    # The URL holds only the public client id and one-time PKCE values, never the shared secret.
    print(f"Open this URL to approve access:\n{url}", flush=True)
    webbrowser.open(url)
    token = exchange_code(settings, wait_for_code(state), verifier)
    save_token(token)
    logger.info("Saved Etsy token for user {} to {}", token.user_id, TOKEN_PATH.name)
    return token


if __name__ == "__main__":
    authorise()
