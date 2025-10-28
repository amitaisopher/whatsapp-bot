from app.core.config import settings
from app.core.logging import get_application_logger
from app.core.auth import get_active_api_key_of_customer
from app.models.chat import ChatRequest
from httpx import AsyncClient, HTTPError


class NLInventorySearchService:
  def __init__(self, customer_id: str, http_client: AsyncClient) -> None:
    self.customer_id = customer_id
    self.logger = get_application_logger()
    self.api_key = get_active_api_key_of_customer(customer_id)
    if not self.api_key:
      raise ValueError("Active API key is required for the customer")
    self.search_api_url = settings.search_api_url
    if not self.search_api_url:
      raise ValueError("Backend URL is not configured")
    self.http_client: AsyncClient = http_client
    self.logger.info(f"InventorySearchService initialized for customer {customer_id}")


  async def process_message(self, message: str, user_id: str) -> list[dict] | None:
    """Search inventory items using the backend service."""
    search_endpoint = f"{self.search_api_url}/search"
    headers = {
      "x-api-key": self.api_key,
      "Content-Type": "application/json"
    }
    payload: ChatRequest = ChatRequest(
      user_id=self.customer_id,
      message=message
    )
    try:
      response = await self.http_client.post(
        search_endpoint,
        headers=headers,
        json=payload.model_dump_json()
      )
      response.raise_for_status()
      data = response.json()
      self.logger.info(f"Search successful for customer {self.customer_id}")
      return data.get("cars", None)
    except HTTPError as http_err:
      self.logger.error(f"HTTP error occurred during search: {http_err}")
    except Exception as err:
      self.logger.error(f"Unexpected error during search: {err}")