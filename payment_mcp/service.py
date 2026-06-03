from datetime import UTC, datetime, timedelta, timezone
import json
import uuid

from payment_mcp.client import LFWinClient
from payment_mcp.models import PaymentStatus
from payment_mcp.qrcode_image import PNG_DATA_URL_PREFIX, make_png_data_url


CHINA_TZ = timezone(timedelta(hours=8))


def parse_unix_seconds(value: object) -> str | None:
    if value in (None, "", "0", 0):
        return None
    try:
        return datetime.fromtimestamp(int(value), CHINA_TZ).strftime("%Y-%m-%d %H:%M:%S")
    except (TypeError, ValueError, OSError):
        return None


def to_float(value: object) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def to_str(value: object) -> str | None:
    if value is None:
        return None
    return str(value)


PAYMENT_TARGET_KEYS = (
    "pay_url",
    "payUrl",
    "payurl",
    "payment_url",
    "paymentUrl",
    "cashier_url",
    "cashierUrl",
    "url",
    "link",
    "h5_url",
    "h5Url",
    "qrcode",
    "qr_code",
    "qrCode",
    "qr_url",
    "qrUrl",
    "qr_code_url",
    "qrCodeUrl",
    "code_url",
    "codeUrl",
)


ORDER_NO_KEYS = (
    "orderid",
    "order_id",
    "orderNo",
    "order_no",
    "platform_order_no",
    "platformOrderNo",
)


def extract_payment_target(value: object) -> str | None:
    if value in (None, ""):
        return None
    if isinstance(value, str):
        return None if value == "[object Object]" else value
    if isinstance(value, (int, float, bool)):
        return str(value)
    if isinstance(value, dict):
        for key in PAYMENT_TARGET_KEYS:
            target = extract_payment_target(value.get(key))
            if target:
                return target
        for nested in value.values():
            target = extract_payment_target(nested)
            if target:
                return target
        return None
    if isinstance(value, list):
        for item in value:
            target = extract_payment_target(item)
            if target:
                return target
    return None


def extract_order_no(value: object) -> str | None:
    if value in (None, "", "[object Object]"):
        return None
    if isinstance(value, (str, int, float)):
        return str(value)
    if isinstance(value, dict):
        for key in ORDER_NO_KEYS:
            target = extract_order_no(value.get(key))
            if target:
                return target
    return None


def normalize_payment_target(value: object) -> str | None:
    target = extract_payment_target(value)
    if not target or target == "[object Object]":
        return None
    return target


def value_as_json_string(value: object) -> str | None:
    if value is None:
        return None
    try:
        return json.dumps(value, ensure_ascii=False, separators=(",", ":"))
    except (TypeError, ValueError):
        return to_str(value)


def map_refund_status(result: dict) -> PaymentStatus:
    raw_status = str(result.get("status", ""))
    refund_status = str(result.get("refund_status", ""))
    is_refund = str(result.get("is_refund", ""))

    if raw_status == "4001":
        return PaymentStatus.REFUNDING
    if raw_status in {"4000", "4002", "1002"} or refund_status == "2":
        return PaymentStatus.FAILED
    if raw_status == "10000" and (refund_status == "1" or is_refund == "2"):
        return PaymentStatus.REFUNDED
    if raw_status == "10000":
        return PaymentStatus.REFUNDING
    return PaymentStatus.PROCESSING


def first_refund_record(result: dict) -> dict:
    records = result.get("lists")
    if isinstance(records, list) and records:
        first = records[0]
        if isinstance(first, dict):
            return first
    return result


def payment_usage_instruction(order_no: object) -> str:
    if not order_no:
        return (
            "Display pay_qrcode_markdown or pay_qrcode_image to the user for QR payment, "
            "and keep pay_url/qrcode as the fallback payment link. The cashier pre_order "
            "response did not include platform orderid, so order_no/query_order_no is null. "
            "Poll query_payment_order with merchant_order_no plus order_time returned by "
            "create_payment_order. Do not invent an order_no from merchant_order_no."
        )
    return (
        "Show pay_qrcode_markdown to the user when Markdown is supported; otherwise render "
        "pay_qrcode_image as an image data URL, use pay_qrcode_base64 with mime_type image/png "
        "when the client expects raw base64, or use pay_url/qrcode as the payment link/QR content. "
        f"Store order_no ({order_no}) as the platform order number for all later payment query "
        "and refund tools. Do not use merchant_order_no for query_payment_order unless a "
        "merchant-order query tool explicitly asks for merchant_order_no plus order_time."
    )


def payment_display_examples(pay_url: str | None, pay_qrcode_image: str | None, pay_qrcode_base64: str | None) -> dict:
    return {
        "markdown": "Output pay_qrcode_markdown directly in Markdown-capable chat clients.",
        "html_img": '<img alt="Payment QR Code" src="{pay_qrcode_image}" />',
        "frontend_image_src": "Set an image element src to pay_qrcode_image; it already includes data:image/png;base64,.",
        "mcp_image_content": {
            "type": "image",
            "mimeType": "image/png",
            "data": "pay_qrcode_base64",
        },
        "payment_link": "If the QR image cannot be displayed, show pay_url as a clickable payment link.",
        "current_values": {
            "pay_url": pay_url,
            "qrcode": pay_url,
            "pay_qrcode_image_prefix": PNG_DATA_URL_PREFIX if pay_qrcode_image else None,
            "pay_qrcode_base64_available": bool(pay_qrcode_base64),
            "pay_qrcode_mime_type": "image/png" if pay_qrcode_base64 else None,
        },
    }


class PaymentService:
    def __init__(self, client: LFWinClient) -> None:
        self.client = client

    async def create_payment_order(
        self,
        merchant_order_no: str,
        amount: float,
        notify_url: str | None = None,
    ) -> dict:
        created_at = datetime.now(UTC).astimezone(CHINA_TZ)
        order_time = created_at.strftime("%Y%m%d%H%M%S")
        payload = {
            "money": f"{amount:.2f}",
            "nonce_str": uuid.uuid4().hex[:16],
            "mch_orderid": merchant_order_no,
            "notify_url": notify_url or "",
        }
        result = await self.client.create_cashier_order(payload)
        pay_url = normalize_payment_target(result.get("data"))
        pay_qrcode_image = make_png_data_url(pay_url) if pay_url else None
        pay_qrcode_base64 = (
            pay_qrcode_image.removeprefix(PNG_DATA_URL_PREFIX)
            if pay_qrcode_image and pay_qrcode_image.startswith(PNG_DATA_URL_PREFIX)
            else None
        )
        order_no = extract_order_no(result) or extract_order_no(result.get("data"))
        return {
            "success": result.get("status") == "10000",
            "order_no": order_no,
            "platform_order_no": order_no,
            "query_order_no": order_no,
            "merchant_order_no": merchant_order_no,
            "order_time": order_time,
            "order_time_format": "yyyyMMddHHmmss",
            "order_no_available": bool(order_no),
            "amount": amount,
            "status": PaymentStatus.PENDING.value,
            "pay_url": normalize_payment_target(pay_url),
            "qrcode": normalize_payment_target(pay_url),
            "pay_qrcode_image": pay_qrcode_image,
            "pay_qrcode_base64": pay_qrcode_base64,
            "pay_qrcode_mime_type": "image/png" if pay_qrcode_base64 else None,
            "pay_qrcode_markdown": f"![Payment QR Code]({pay_qrcode_image})" if pay_qrcode_image else None,
            "payment_display_examples": payment_display_examples(to_str(pay_url), pay_qrcode_image, pay_qrcode_base64),
            "raw_payment_data_json": value_as_json_string(result.get("data")),
            "expire_time": (created_at + timedelta(minutes=15)).strftime("%Y-%m-%d %H:%M:%S"),
            "display_instruction": payment_usage_instruction(order_no),
            "next_action": (
                "Display the QR code/payment link, then poll query_payment_order with merchant_order_no and order_time."
                if not order_no
                else "Display the QR code/payment link, then poll query_payment_order with query_order_no/order_no."
            ),
            "message": result.get("message"),
            "raw_status": str(result.get("status", "")),
        }

    async def query_payment_order(
        self,
        order_no: str | None = None,
        merchant_order_no: str | None = None,
        order_time: str | None = None,
    ) -> dict:
        payload = {
            "service": "pay.comm.query_order",
            "nonce_str": uuid.uuid4().hex[:16],
        }
        if order_no:
            payload["orderid"] = order_no
            query_method = "platform_order_no"
        elif merchant_order_no and order_time:
            payload["mch_orderid"] = merchant_order_no
            payload["order_time"] = order_time
            query_method = "merchant_order_no_order_time"
        else:
            raise ValueError("Pass either order_no, or merchant_order_no plus order_time.")

        result = await self.client.query_order(payload)
        paystatus = str(result.get("paystatus", "0"))
        raw_status = str(result.get("status", ""))
        is_pre_scan_missing = query_method == "merchant_order_no_order_time" and raw_status == "3040"
        status = PaymentStatus.PENDING
        if paystatus == "1":
            status = PaymentStatus.SUCCESS
        elif paystatus == "2":
            status = PaymentStatus.FAILED
        result_order_no = to_str(result.get("orderid")) or order_no
        return {
            "success": result.get("status") == "10000" and status == PaymentStatus.SUCCESS,
            "order_no": result_order_no,
            "platform_order_no": result_order_no,
            "query_order_no": result_order_no,
            "merchant_order_no": to_str(result.get("mch_orderid")) or merchant_order_no,
            "order_time": order_time,
            "query_method": query_method,
            "status": status.value,
            "pending_reason": "WAITING_FOR_USER_SCAN_OR_PAYMENT_ORDER_CREATION" if is_pre_scan_missing else None,
            "paid_amount": to_float(result.get("paymoney")) or 0,
            "paid_time": parse_unix_seconds(result.get("paytime")),
            "query_instruction": (
                "The cashier payment order may not exist before the user scans or opens the payment link. "
                "Treat raw_status=3040 as PENDING and keep polling with merchant_order_no plus order_time."
                if is_pre_scan_missing
                else "Treat paystatus=1 as paid, paystatus=2 as failed, otherwise keep pending."
            ),
            "message": "待支付：用户扫码或打开支付链接前，平台支付订单可能尚未生成。" if is_pre_scan_missing else result.get("message"),
            "raw_message": result.get("message"),
            "raw_status": raw_status,
            "raw_paystatus": paystatus,
        }

    async def refund_payment_order(
        self,
        order_no: str,
        refund_amount: float,
        reason: str,
        mch_refund_no: str,
    ) -> dict:
        payload = {
            "service": "pay.comm.refund_order",
            "orderid": order_no,
            "refundmoney": f"{refund_amount:.2f}",
            "version": "4.0",
            "nonce_str": uuid.uuid4().hex[:16],
            "reason": reason,
            "mch_refund_no": mch_refund_no,
        }
        result = await self.client.refund_order(payload)
        status = map_refund_status(result)
        return {
            "success": str(result.get("status")) in {"10000", "4001"},
            "order_no": to_str(result.get("orderid")) or order_no,
            "platform_order_no": to_str(result.get("orderid")) or order_no,
            "query_order_no": to_str(result.get("orderid")) or order_no,
            "refund_no": to_str(result.get("refund_no")),
            "mch_refund_no": to_str(result.get("mch_refund_no")) or mch_refund_no,
            "refund_amount": to_float(result.get("refundmoney")) or refund_amount,
            "status": status.value,
            "next_action": "Refund submission accepted only means processing; call query_refund_status with order_no and mch_refund_no to confirm the final result.",
            "message": result.get("message"),
            "raw_status": str(result.get("status", "")),
        }

    async def query_refund_status(self, order_no: str, mch_refund_no: str | None = None) -> dict:
        payload = {
            "service": "pay.comm.query_refund",
            "orderid": order_no,
            "version": "4.0",
            "nonce_str": uuid.uuid4().hex[:16],
        }
        if mch_refund_no:
            payload["mch_refund_no"] = mch_refund_no

        result = await self.client.query_refund(payload)
        record = first_refund_record(result)
        status = map_refund_status({**result, **record})
        raw_status = str(result.get("status", ""))
        return {
            "success": raw_status == "10000" and status == PaymentStatus.REFUNDED,
            "order_no": to_str(record.get("orderid")) or to_str(result.get("orderid")) or order_no,
            "platform_order_no": to_str(record.get("orderid")) or to_str(result.get("orderid")) or order_no,
            "query_order_no": to_str(record.get("orderid")) or to_str(result.get("orderid")) or order_no,
            "refund_no": to_str(record.get("refund_no")) or to_str(result.get("refund_no")),
            "mch_refund_no": to_str(record.get("mch_refund_no")) or to_str(result.get("mch_refund_no")) or mch_refund_no,
            "refund_amount": to_float(record.get("refundmoney")),
            "status": status.value,
            "refund_time": parse_unix_seconds(record.get("refundtime")),
            "query_instruction": "REFUNDED is final success, FAILED is final failure, and REFUNDING/PROCESSING should be queried again later.",
            "message": result.get("message"),
            "raw_status": raw_status,
        }
