"""Environment and CDF connection settings."""

from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


def _first(*keys: str) -> str:
    for key in keys:
        value = os.getenv(key, "").strip()
        if value:
            return value
    return ""


def _split_scopes(raw: str) -> list[str] | None:
    if not raw:
        return None
    parts = [part.strip() for part in raw.replace(",", " ").split() if part.strip()]
    return parts or None


@dataclass(frozen=True)
class CdfSettings:
    project: str
    cluster: str
    tenant_id: str
    client_id: str
    client_secret: str
    base_url: str
    token_url: str
    audience: str
    extra_scopes: tuple[str, ...]

    @property
    def ready(self) -> bool:
        return all(
            [
                self.project,
                self.cluster,
                self.tenant_id,
                self.client_id,
                self.client_secret,
            ]
        )

    @property
    def scopes(self) -> list[str]:
        if self.extra_scopes:
            return list(self.extra_scopes)
        return [f"{self.base_url}/.default"]


def load_cdf_settings() -> CdfSettings:
    cluster = _first("CDF_CLUSTER") or "api"
    tenant_id = _first("CDF_TENANT_ID", "IDP_TENANT_ID")
    base_url = _first("CDF_BASE_URL", "CDF_URL") or f"https://{cluster}.cognitedata.com"
    base_url = base_url.rstrip("/")
    token_url = _first("CDF_TOKEN_URL", "IDP_TOKEN_URL")
    if not token_url and tenant_id:
        token_url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"
    extra = _split_scopes(_first("IDP_SCOPES", "CDF_SCOPES")) or ()
    return CdfSettings(
        project=_first("CDF_PROJECT"),
        cluster=cluster,
        tenant_id=tenant_id,
        client_id=_first("CDF_CLIENT_ID", "IDP_CLIENT_ID", "INGESTION_CLIENT_ID"),
        client_secret=_first("CDF_CLIENT_SECRET", "IDP_CLIENT_SECRET", "INGESTION_CLIENT_SECRET"),
        base_url=base_url,
        token_url=token_url,
        audience=_first("IDP_AUDIENCE", "CDF_AUDIENCE"),
        extra_scopes=tuple(extra),
    )
