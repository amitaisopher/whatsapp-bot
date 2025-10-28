from functools import lru_cache
from fastapi import HTTPException
from postgrest import APIResponse
from supabase import Client, create_client

from app.core.config import settings
from app.models.customer import Customer

@lru_cache()
def get_supabase_client() -> Client:
    """Create and return Supabase client"""
    url: str | None = settings.supabase_url
    key: str | None = settings.supabase_key

    if not url or not key:
        raise HTTPException(
            status_code=500, detail="Database configuration missing")

    return create_client(url, key)


class DatabaseService:
    """Database service to interact with Supabase"""

    def __init__(self, db_client: Client):
        self.db_client = db_client

    async def find_customer_by_id(self, customer_id: str) -> Customer | None:
        """Find a customer by their ID"""
        try:
            response: APIResponse | str = self.db_client.from_("customers").select("*").eq("id", customer_id).execute()
            if isinstance(response, str):
                raise HTTPException(status_code=500, detail=f"Database query failed: {response}")
            return Customer.model_validate(response.data[0])
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Database query failed: {str(e)}")

    async def get_api_key_of_customer(self, customer_id: str) -> str | None:
        """Get the API key of a customer by their ID"""
        customer: Customer | None = await self.find_customer_by_id(customer_id)
        
        if not customer or not customer.is_active:
            raise HTTPException(
                status_code=401, detail="Unauthorized action")
        
        res: APIResponse | str = self.db_client.from_("customer_api_keys").select("api_key").eq("customer_id", customer_id).execute()
        if isinstance(res, str):
            raise HTTPException(status_code=500, detail=f"Database query failed: {res}")
        if res.data and len(res.data) > 0:
            row = res.data[0]
            if isinstance(row, dict):
                key_value = row.get("api_key")
                return key_value if isinstance(key_value, str) else None
        return None

@lru_cache()
def get_database_service() -> DatabaseService:
    return DatabaseService(get_supabase_client())