import httpx

from payment_mcp.config import PaymentSettings
from payment_mcp.signature import md5_sign


class LFWinClient:
    def __init__(self, settings: PaymentSettings) -> None:
        self.settings = settings
        self.client = httpx.AsyncClient(
            base_url=settings.api_base_url,
            timeout=settings.request_timeout_seconds,
        )

    async def post(self, path: str, payload: dict[str, object]) -> dict:
        signed_payload = dict(payload)
        signed_payload["apikey"] = self.settings.api_key
        signed_payload["sign_type"] = self.settings.sign_type
        signed_payload["sign"] = md5_sign(signed_payload, self.settings.sign_key)

        response = await self.client.post(path, data=signed_payload)
        response.raise_for_status()
        return response.json()

    async def create_order(self, payload: dict[str, object]) -> dict:
        return await self.post("/payapi/trans/kxpay", payload)

    async def create_cashier_order(self, payload: dict[str, object]) -> dict:
        return await self.post("/index/Payment/pre_order", payload)

    async def query_order(self, payload: dict[str, object]) -> dict:
        return await self.post("/payapi/pay/query_order", payload)

    async def refund_order(self, payload: dict[str, object]) -> dict:
        return await self.post("/payapi/pay/refund_order", payload)

    async def query_refund(self, payload: dict[str, object]) -> dict:
        return await self.post("/payapi/pay/query_refund", payload)
