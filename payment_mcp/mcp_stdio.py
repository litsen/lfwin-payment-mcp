from functools import lru_cache

from mcp.server.fastmcp import FastMCP

from payment_mcp.client import LFWinClient
from payment_mcp.config import load_settings
from payment_mcp.service import PaymentService


mcp = FastMCP("payment-mcp")


@lru_cache
def get_service() -> PaymentService:
    settings = load_settings()
    return PaymentService(LFWinClient(settings))


@mcp.tool()
async def create_payment_order(
    merchant_order_no: str,
    amount: float,
    currency: str = "CNY",
    channel: str = "comm",
    subject: str = "Payment order",
    notify_url: str | None = None,
) -> dict:
    """Create a payment order. The merchant order number must be unique. Amount is in yuan."""
    service = get_service()
    return await service.create_payment_order(
        merchant_order_no=merchant_order_no,
        amount=amount,
        currency=currency,
        channel=channel,
        subject=subject,
        notify_url=notify_url,
    )


@mcp.tool()
async def query_payment_order(order_no: str) -> dict:
    """Query payment order status by the platform order number."""
    service = get_service()
    return await service.query_payment_order(order_no=order_no)


@mcp.tool()
async def refund_payment_order(
    order_no: str,
    refund_amount: float,
    reason: str,
    mch_refund_no: str,
) -> dict:
    """Create a refund request. mch_refund_no is the merchant refund number and must be unique."""
    service = get_service()
    return await service.refund_payment_order(
        order_no=order_no,
        refund_amount=refund_amount,
        reason=reason,
        mch_refund_no=mch_refund_no,
    )


@mcp.tool()
async def query_refund_status(order_no: str, mch_refund_no: str | None = None) -> dict:
    """Query refund status. Optionally pass mch_refund_no to locate a specific refund."""
    service = get_service()
    return await service.query_refund_status(order_no=order_no, mch_refund_no=mch_refund_no)


def main() -> None:
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
