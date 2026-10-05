"""Thin client for the Etsy Open API v3, authenticated with the token from etsy_auth.

Covers only what the PeraColor workflow needs: reading the shop and listings,
replacing a digital listing's files and images, and editing listing fields.
Every call raises on HTTP errors; nothing is retried silently.
"""

import json
import mimetypes
import time
from pathlib import Path
from typing import BinaryIO

import requests
from loguru import logger
from pydantic import BaseModel

from peracolor.etsy_auth import REQUEST_TIMEOUT_S, TOKEN_PATH, TOKEN_URL, EtsySettings, EtsyToken, save_token

API_BASE = "https://api.etsy.com/v3/application"
# Refresh a little before expiry so a long upload never starts with a stale token.
REFRESH_MARGIN_S = 120
UPLOAD_TIMEOUT_S = 300


class UnsupportedFileTypeError(ValueError):
    """Raised for files whose content type cannot be determined; Etsy rejects untyped uploads."""


def content_type(path: Path) -> str:
    """Etsy returns a generic 400 for uploads without an explicit content type."""
    guessed, _ = mimetypes.guess_type(path.name)
    if guessed is None:
        raise UnsupportedFileTypeError(f"Cannot determine content type for {path.name}")
    return guessed


class ListingFile(BaseModel):
    listing_file_id: int
    filename: str
    filesize: str


class ListingImage(BaseModel):
    listing_image_id: int
    rank: int


class EtsyClient:
    def __init__(self, settings: EtsySettings | None = None, token_path: Path = TOKEN_PATH) -> None:
        self._settings = settings or EtsySettings()
        self._token_path = token_path
        self._token = EtsyToken.model_validate(json.loads(token_path.read_text()))

    def _refresh_if_needed(self) -> None:
        if self._token.expires_at - time.time() > REFRESH_MARGIN_S:
            return
        response = requests.post(
            TOKEN_URL,
            data={
                "grant_type": "refresh_token",
                "client_id": self._settings.api_keystring.get_secret_value(),
                "refresh_token": self._token.refresh_token.get_secret_value(),
            },
            timeout=REQUEST_TIMEOUT_S,
        )
        response.raise_for_status()
        payload = response.json()
        self._token = EtsyToken(
            access_token=payload["access_token"],
            refresh_token=payload["refresh_token"],
            expires_at=time.time() + payload["expires_in"],
        )
        save_token(self._token, self._token_path)
        logger.debug("Refreshed Etsy access token")

    def _headers(self) -> dict[str, str]:
        self._refresh_if_needed()
        return {
            "x-api-key": self._settings.api_key_header,
            "Authorization": f"Bearer {self._token.access_token.get_secret_value()}",
        }

    def request(
        self,
        method: str,
        path: str,
        timeout: int = REQUEST_TIMEOUT_S,
        data: dict[str, str] | None = None,
        files: dict[str, tuple[str, BinaryIO]] | None = None,
    ) -> dict:
        response = requests.request(method, f"{API_BASE}{path}", headers=self._headers(), timeout=timeout, data=data, files=files)
        if not response.ok:
            raise requests.HTTPError(f"{method} {path} -> {response.status_code}: {response.text[:500]}", response=response)
        return response.json() if response.content else {}

    @property
    def user_id(self) -> str:
        return self._token.user_id

    def shop_id(self) -> int:
        return int(self.request("GET", f"/users/{self.user_id}/shops")["shop_id"])

    def listing_files(self, shop_id: int, listing_id: int) -> list[ListingFile]:
        results = self.request("GET", f"/shops/{shop_id}/listings/{listing_id}/files")["results"]
        return [ListingFile.model_validate(item) for item in results]

    def delete_listing_file(self, shop_id: int, listing_id: int, file_id: int) -> None:
        self.request("DELETE", f"/shops/{shop_id}/listings/{listing_id}/files/{file_id}")

    def upload_listing_file(self, shop_id: int, listing_id: int, path: Path) -> ListingFile:
        """Append a digital file; Etsy rejects uploads that also set `rank`, so order follows upload order."""
        with path.open("rb") as handle:
            result = self.request(
                "POST",
                f"/shops/{shop_id}/listings/{listing_id}/files",
                timeout=UPLOAD_TIMEOUT_S,
                files={"file": (path.name, handle, content_type(path))},
                data={"name": path.name},
            )
        return ListingFile.model_validate(result)

    def listing_images(self, listing_id: int) -> list[ListingImage]:
        results = self.request("GET", f"/listings/{listing_id}/images")["results"]
        return [ListingImage.model_validate(item) for item in results]

    def delete_listing_image(self, shop_id: int, listing_id: int, image_id: int) -> None:
        self.request("DELETE", f"/shops/{shop_id}/listings/{listing_id}/images/{image_id}")

    def upload_listing_image(self, shop_id: int, listing_id: int, path: Path, rank: int) -> ListingImage:
        with path.open("rb") as handle:
            result = self.request(
                "POST",
                f"/shops/{shop_id}/listings/{listing_id}/images",
                timeout=UPLOAD_TIMEOUT_S,
                files={"image": (path.name, handle)},
                data={"rank": str(rank)},
            )
        return ListingImage.model_validate(result)

    def update_listing(self, shop_id: int, listing_id: int, fields: dict[str, str]) -> dict:
        return self.request("PATCH", f"/shops/{shop_id}/listings/{listing_id}", data=fields)
