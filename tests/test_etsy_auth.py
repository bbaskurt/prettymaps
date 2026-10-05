import base64
import hashlib
from urllib.parse import parse_qs, urlparse

from pydantic import SecretStr

from peracolor.etsy_auth import REDIRECT_URI, SCOPES, EtsySettings, EtsyToken, consent_url, pkce_pair


def settings() -> EtsySettings:
    return EtsySettings(api_keystring=SecretStr("key123"), shared_secret=SecretStr("secret456"), _env_file=None)


class TestPkce:
    def test_challenge_is_s256_of_verifier(self) -> None:
        """Given a PKCE pair, when the challenge is recomputed from the verifier, then they match (S256)."""
        verifier, challenge = pkce_pair()

        expected = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).rstrip(b"=").decode()

        assert challenge == expected
        assert 43 <= len(verifier) <= 128


def test_consent_url_requests_listing_scopes_with_pkce() -> None:
    """Given app settings, when the consent URL is built, then it asks for listing scopes via PKCE and the local callback."""
    query = parse_qs(urlparse(consent_url(settings(), "challenge", "state")).query)

    assert query["scope"] == [" ".join(SCOPES)]
    assert query["code_challenge_method"] == ["S256"]
    assert query["redirect_uri"] == [REDIRECT_URI]
    assert query["client_id"] == ["key123"]


def test_api_key_header_combines_keystring_and_secret() -> None:
    """Given app settings, when the API key header is built, then it is keystring:shared_secret."""
    assert settings().api_key_header == "key123:secret456"


def test_user_id_is_token_prefix() -> None:
    """Given an Etsy access token, when the user id is read, then it is the numeric prefix."""
    token = EtsyToken(access_token=SecretStr("12345.abcdef"), refresh_token=SecretStr("r"), expires_at=0)

    assert token.user_id == "12345"
