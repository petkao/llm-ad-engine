from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any

import httpx


class ApiClientError(Exception):
    """Raised when the backend API cannot be reached or returns an error."""

    def __init__(self, message: str, *, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code


class ApiConfigurationError(ApiClientError):
    """Raised when an endpoint path is missing or misconfigured."""


@dataclass(frozen=True)
class ApiClientSettings:
    """Configuration for the deployed LLM Ad Engine backend API."""

    base_url: str
    timeout_seconds: float = 20.0
    api_token: str | None = None
    search_video_ads_path: str = "/api/buyer/semantic-match"
    rank_ads_path: str = "/api/buyer/semantic-match"
    ads_list_path: str = "/api/ads"
    get_ad_by_id_path_template: str = "/api/ads/{ad_id}"
    explain_ad_match_path: str | None = None
    sellers_list_path: str = "/api/sellers"
    seller_billing_status_path_template: str = "/api/sellers/{seller_id}/billing-status"
    create_billing_support_ticket_path: str = "/api/billing/support-tickets"


class AdEngineApiClient:
    """Thin HTTP client for calling the deployed LLM Ad Engine API."""

    def __init__(self, settings: ApiClientSettings) -> None:
        self.settings = settings
        headers = {"Accept": "application/json"}
        if settings.api_token:
            headers["Authorization"] = f"Bearer {settings.api_token}"

        self._client = httpx.Client(
            base_url=settings.base_url.rstrip("/"),
            headers=headers,
            timeout=settings.timeout_seconds,
        )

    def close(self) -> None:
        """Close the underlying HTTP client."""
        self._client.close()

    def search_video_ads_for_buyer(
        self,
        *,
        query: str,
        category: str | None,
        device_id: str,
        limit: int,
    ) -> dict[str, Any]:
        """Call the backend buyer-match endpoint used for ad search."""
        return self._request(
            "POST",
            self._require_path(
                self.settings.search_video_ads_path,
                env_var_name="SEARCH_VIDEO_ADS_PATH",
            ),
            json_body={
                "query": query,
                "category": category or "",
                "device_id": device_id,
                "limit": limit,
            },
        )

    def get_ad_by_id(self, *, ad_id: str) -> dict[str, Any]:
        """Fetch a single ad from the backend by its identifier."""
        template = self._require_path(
            self.settings.get_ad_by_id_path_template,
            env_var_name="GET_AD_BY_ID_PATH_TEMPLATE",
        )
        try:
            return self._request("GET", template.format(ad_id=ad_id))
        except ApiClientError as exc:
            if exc.status_code != 404:
                raise

        ads = self._get_collection(
            self.settings.ads_list_path,
            env_var_name="ADS_LIST_PATH",
        )
        for ad in ads:
            if str(ad.get("id", "")).strip() == ad_id:
                return {
                    "mode": "ads_list_fallback",
                    "ad": ad,
                }

        raise ApiClientError(f"Ad `{ad_id}` was not found in the ads list fallback.")

    def rank_ads_for_buyer(
        self,
        *,
        query: str,
        category: str | None,
        device_id: str,
        limit: int,
    ) -> dict[str, Any]:
        """Ask the backend to return ranked buyer-ad matches."""
        return self._request(
            "POST",
            self._require_path(
                self.settings.rank_ads_path,
                env_var_name="RANK_ADS_PATH",
            ),
            json_body={
                "query": query,
                "category": category or "",
                "device_id": device_id,
                "limit": limit,
            },
        )

    def explain_ad_match(
        self,
        *,
        ad_id: str,
        query: str,
        category: str | None,
        device_id: str,
    ) -> dict[str, Any]:
        """Call a dedicated backend explanation endpoint when configured."""
        path = (self.settings.explain_ad_match_path or "").strip()
        if not path:
            raise ApiConfigurationError(
                "EXPLAIN_AD_MATCH_PATH is not configured. "
                "Leave it blank to use the server's fallback explanation mode, "
                "or set it to your dedicated backend explanation route."
            )

        return self._request(
            "POST",
            path,
            json_body={
                "ad_id": ad_id,
                "query": query,
                "category": category or "",
                "device_id": device_id,
            },
        )

    def get_seller_billing_status(self, *, seller_id: str) -> dict[str, Any]:
        """Fetch seller billing information from the backend."""
        template = self._require_path(
            self.settings.seller_billing_status_path_template,
            env_var_name="SELLER_BILLING_STATUS_PATH_TEMPLATE",
        )
        try:
            return self._request("GET", template.format(seller_id=seller_id))
        except ApiClientError as exc:
            if exc.status_code != 404:
                raise

        sellers = self._get_collection(
            self.settings.sellers_list_path,
            env_var_name="SELLERS_LIST_PATH",
        )
        for seller in sellers:
            if str(seller.get("id", "")).strip() != seller_id:
                continue

            return {
                "mode": "sellers_list_fallback",
                "seller_id": seller_id,
                "seller_name": seller.get("name"),
                "email": seller.get("email"),
                "plan": seller.get("plan"),
                "balance": seller.get("balance"),
                "status": seller.get("status"),
                "is_verified": seller.get("is_verified"),
                "location": seller.get("location"),
                "raw_seller": seller,
            }

        raise ApiClientError(
            f"Seller `{seller_id}` was not found in the sellers list fallback."
        )

    def create_billing_support_ticket(
        self,
        *,
        seller_id: str,
        subject: str,
        description: str,
        email: str | None,
        priority: str,
    ) -> dict[str, Any]:
        """Create a billing support ticket through the backend."""
        return self._request(
            "POST",
            self._require_path(
                self.settings.create_billing_support_ticket_path,
                env_var_name="CREATE_BILLING_SUPPORT_TICKET_PATH",
            ),
            json_body={
                "seller_id": seller_id,
                "subject": subject,
                "description": description,
                "email": email,
                "priority": priority,
            },
        )

    def _get_collection(
        self,
        path_value: str | None,
        *,
        env_var_name: str,
    ) -> list[dict[str, Any]]:
        payload = self._request(
            "GET",
            self._require_path(path_value, env_var_name=env_var_name),
        )
        collection = payload.get("data", payload)
        if not isinstance(collection, list):
            raise ApiClientError(
                f"{env_var_name} did not return a list payload that can be used as a fallback."
            )

        result: list[dict[str, Any]] = []
        for item in collection:
            if isinstance(item, dict):
                result.append(item)
        return result

    def _request(
        self,
        method: str,
        path: str,
        *,
        json_body: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        try:
            response = self._client.request(method, path, json=json_body)
        except httpx.TimeoutException as exc:
            raise ApiClientError(
                f"{method} {path} timed out after {self.settings.timeout_seconds} seconds."
            ) from exc
        except httpx.HTTPError as exc:
            raise ApiClientError(f"{method} {path} failed: {exc}") from exc

        if response.status_code >= 400:
            detail = self._extract_error_detail(response)
            raise ApiClientError(
                f"{method} {path} returned {response.status_code}: {detail}",
                status_code=response.status_code,
            )

        if response.status_code == 204 or not response.content:
            return {"ok": True, "status_code": response.status_code}

        try:
            payload = response.json()
        except ValueError as exc:
            raise ApiClientError(
                f"{method} {path} returned non-JSON content."
            ) from exc

        if not isinstance(payload, dict):
            return {"data": payload}
        return payload

    @staticmethod
    def _extract_error_detail(response: httpx.Response) -> str:
        try:
            payload = response.json()
        except ValueError:
            text = response.text.strip()
            return text or "Unknown error"

        if isinstance(payload, dict):
            for key in ("error", "message", "detail"):
                value = payload.get(key)
                if isinstance(value, str) and value.strip():
                    return value
            return str(payload)

        return str(payload)

    @staticmethod
    def _require_path(value: str | None, *, env_var_name: str) -> str:
        path = (value or "").strip()
        if not path:
            raise ApiConfigurationError(
                f"{env_var_name} is not configured. "
                "Set it in your .env file before calling this tool."
            )
        if not path.startswith("/"):
            return f"/{path}"
        return path


def build_api_client_from_env() -> AdEngineApiClient:
    """Create an API client from environment variables."""

    base_url = os.getenv(
        "AD_ENGINE_API_BASE_URL",
        "https://ad-engine-api-610270819686.us-west1.run.app",
    ).strip()
    if not base_url:
        raise ApiConfigurationError("AD_ENGINE_API_BASE_URL must not be empty.")

    explain_path = (os.getenv("EXPLAIN_AD_MATCH_PATH") or "").strip() or None

    settings = ApiClientSettings(
        base_url=base_url,
        timeout_seconds=float(os.getenv("AD_ENGINE_API_TIMEOUT_SECONDS", "20")),
        api_token=(os.getenv("AD_ENGINE_API_TOKEN") or "").strip() or None,
        search_video_ads_path=os.getenv(
            "SEARCH_VIDEO_ADS_PATH", "/api/buyer/semantic-match"
        ),
        rank_ads_path=os.getenv("RANK_ADS_PATH", "/api/buyer/semantic-match"),
        ads_list_path=os.getenv("ADS_LIST_PATH", "/api/ads"),
        get_ad_by_id_path_template=os.getenv(
            "GET_AD_BY_ID_PATH_TEMPLATE", "/api/ads/{ad_id}"
        ),
        explain_ad_match_path=explain_path,
        sellers_list_path=os.getenv("SELLERS_LIST_PATH", "/api/sellers"),
        seller_billing_status_path_template=os.getenv(
            "SELLER_BILLING_STATUS_PATH_TEMPLATE",
            "/api/sellers/{seller_id}/billing-status",
        ),
        create_billing_support_ticket_path=os.getenv(
            "CREATE_BILLING_SUPPORT_TICKET_PATH",
            "/api/billing/support-tickets",
        ),
    )
    return AdEngineApiClient(settings)
