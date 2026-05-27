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
    notify_url: str | None = None,
) -> dict:
    """Create a cashier payment order.

    merchant_order_no is the merchant's own unique order number. After success,
    show pay_qrcode_markdown or pay_qrcode_image to the user for QR payment and
    save order_no/query_order_no as the platform order number for later query
    and refund tools.
    """
    service = get_service()
    return await service.create_payment_order(
        merchant_order_no=merchant_order_no,
        amount=amount,
        notify_url=notify_url,
    )


@mcp.tool()
async def query_payment_order(order_no: str) -> dict:
    """Query payment status by platform order_no/orderid returned by create_payment_order.

    Do not pass merchant_order_no here. The LFWin merchant-order query path needs
    merchant_order_no plus order_time and is not exposed by this tool.
    """
    service = get_service()
    return await service.query_payment_order(order_no=order_no)


@mcp.tool()
async def refund_payment_order(
    order_no: str,
    refund_amount: float,
    reason: str,
    mch_refund_no: str,
) -> dict:
    """Create a refund request by platform order_no/orderid.

    mch_refund_no is the merchant refund number and must be unique per refund.
    A successful submission means accepted/processing, not final refund success;
    call query_refund_status with order_no and mch_refund_no to confirm.
    """
    service = get_service()
    return await service.refund_payment_order(
        order_no=order_no,
        refund_amount=refund_amount,
        reason=reason,
        mch_refund_no=mch_refund_no,
    )


@mcp.tool()
async def query_refund_status(order_no: str, mch_refund_no: str | None = None) -> dict:
    """Query refund status by platform order_no/orderid.

    Pass mch_refund_no when available to locate a specific partial refund. Only
    REFUNDED is final success; REFUNDING/PROCESSING means query again later.
    """
    service = get_service()
    return await service.query_refund_status(order_no=order_no, mch_refund_no=mch_refund_no)


def main() -> None:
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
