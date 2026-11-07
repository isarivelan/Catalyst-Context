"""Environment and CDF connection settings."""

from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class CdfSettings:
    project: str
    cluster: str
    tenant_id: str
    client_id: str
    client_secret: str
    base_url: str
    token_url: str

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
        return [f"{self.base_url}/.default"]


def load_cdf_settings() -> CdfSettings:
    cluster = os.getenv("CDF_CLUSTER", "api").strip()
    tenant_id = os.getenv("CDF_TENANT_ID", "").strip()
    base_url = os.getenv("CDF_BASE_URL", "").strip() or f"https://{cluster}.cognitedata.com"
    token_url = os.getenv("CDF_TOKEN_URL", "").strip() or (
        f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"
        if tenant_id
        else ""
    )
    return CdfSettings(
        project=os.getenv("CDF_PROJECT", "").strip(),
        cluster=cluster,
        tenant_id=tenant_id,
        client_id=os.getenv("CDF_CLIENT_ID", "").strip(),
        client_secret=os.getenv("CDF_CLIENT_SECRET", "").strip(),
        base_url=base_url.rstrip("/"),
        token_url=token_url,
    )
