from app.core.config import settings
from functools import lru_cache
from app.core.logging import get_application_logger
from app.core.auth import get_active_api_key_of_customer
from app.models.chat import ChatRequest
from httpx import AsyncClient, HTTPError
from typing import Any


class NLInventorySearchService:
    def __init__(self, customer_id: str, http_client: AsyncClient) -> None:
        self.customer_id = customer_id
        self.logger = get_application_logger()
        self.api_key: str | None = None
        self.search_api_url = settings.search_api_url
        if not self.search_api_url:
            raise ValueError("Backend URL is not configured")
        self.http_client: AsyncClient = http_client
        self.logger.info(
            f"InventorySearchService initialized for customer {customer_id}")

    async def _ensure_api_key(self) -> None:
        """Ensure the API key is loaded for the customer."""
        if not self.api_key:
            self.api_key = await get_active_api_key_of_customer(self.customer_id)
            if not self.api_key:
                self.logger.error(
                    f"No active API key found for customer {self.customer_id}")
                raise ValueError(
                    f"No active API key found for customer {self.customer_id}")

    async def process_message(self, message: str, user_id: str) -> dict[str, Any] | None:
        """Search inventory items using the backend service."""

        # Ensure API key is available
        await self._ensure_api_key()
        assert self.api_key is not None  # Type narrowing after _ensure_api_key()

        search_endpoint = f"{self.search_api_url}/chat"
        headers = {
            "x-api-key": self.api_key  # api_key is guaranteed to be set by _ensure_api_key()
        }
        payload: ChatRequest = ChatRequest(
            user_id=user_id,
            message=message,
            session_id=None
        )

        try:
            response = await self.http_client.post(
                search_endpoint,
                headers=headers,
                json=payload.model_dump()
            )

            response.raise_for_status()
            data = response.json()
            self.logger.info(
                f"Search successful for customer {self.customer_id}")
            return data.get("response", None)
        except HTTPError as http_err:
            self.logger.error(f"HTTP error occurred while sending request to inventory-search API:\
                        Client: {self.customer_id}\
                        HTTP error: {http_err}")
        except Exception as err:
            self.logger.error(
                f"Unexpected error during interaction with invetory-seach API: {err}")


@lru_cache()
def get_inventory_search_service(
    customer_id: str,
    http_client: AsyncClient
) -> NLInventorySearchService:
    """
    Get an instance of NLInventorySearchService for the given customer.
    Caches instances to avoid redundant initializations.
    """
    return NLInventorySearchService(customer_id, http_client)
