import asyncio
from base64 import b64decode

import pytest

from payment_mcp.models import PaymentStatus
from payment_mcp.service import PaymentService, extract_payment_target, map_refund_status


class FakeClient:
    def __init__(self, responses: dict[str, dict]) -> None:
        self.responses = responses
        self.calls: list[tuple[str, dict]] = []

    async def create_cashier_order(self, payload: dict) -> dict:
        self.calls.append(("create_cashier_order", payload))
        return self.responses["create_cashier_order"]

    async def query_order(self, payload: dict) -> dict:
        self.calls.append(("query_order", payload))
        return self.responses["query_order"]

    async def refund_order(self, payload: dict) -> dict:
        self.calls.append(("refund_order", payload))
        return self.responses["refund_order"]

    async def query_refund(self, payload: dict) -> dict:
        self.calls.append(("query_refund", payload))
        return self.responses["query_refund"]


def test_create_payment_order_returns_display_and_platform_order_hints() -> None:
    async def run() -> None:
        client = FakeClient(
            {
                "create_cashier_order": {
                    "status": "10000",
                    "orderid": 202605270001,
                    "data": "https://pay.example.test/cashier/202605270001",
                    "message": "ok",
                }
            }
        )
        service = PaymentService(client)  # type: ignore[arg-type]

        result = await service.create_payment_order("MCH-001", 12.3)

        assert result["success"] is True
        assert result["order_no"] == "202605270001"
        assert result["platform_order_no"] == "202605270001"
        assert result["query_order_no"] == "202605270001"
        assert result["order_no_available"] is True
        assert result["merchant_order_no"] == "MCH-001"
        assert str(result["order_time"]).isdigit()
        assert result["order_time_format"] == "yyyyMMddHHmmss"
        assert result["pay_url"] == "https://pay.example.test/cashier/202605270001"
        assert result["qrcode"] == result["pay_url"]
        assert str(result["pay_qrcode_markdown"]).startswith("![Payment QR Code](data:image/png;base64,")
        assert str(result["pay_qrcode_image"]).startswith("data:image/png;base64,")
        assert result["pay_qrcode_mime_type"] == "image/png"
        assert b64decode(str(result["pay_qrcode_base64"]))[:8] == b"\x89PNG\r\n\x1a\n"
        assert str(result["pay_qrcode_image"]).endswith(str(result["pay_qrcode_base64"]))
        examples = result["payment_display_examples"]
        assert examples["mcp_image_content"]["data"] == "pay_qrcode_base64"
        assert "pay_url" in examples["payment_link"]
        assert "Do not use merchant_order_no" in str(result["display_instruction"])

    asyncio.run(run())


def test_create_payment_order_marks_missing_platform_orderid() -> None:
    async def run() -> None:
        client = FakeClient(
            {
                "create_cashier_order": {
                    "status": "10000",
                    "data": {
                        "pay_url": "https://pay.example.test/cashier/no-orderid",
                    },
                    "message": "ok",
                }
            }
        )
        service = PaymentService(client)  # type: ignore[arg-type]

        result = await service.create_payment_order("MCH-NO-ORDERID", 1.0)

        assert result["order_no"] is None
        assert result["platform_order_no"] is None
        assert result["query_order_no"] is None
        assert result["order_no_available"] is False
        assert str(result["order_time"]).isdigit()
        assert result["pay_url"] == "https://pay.example.test/cashier/no-orderid"
        assert "did not include platform orderid" in str(result["display_instruction"])
        assert "merchant_order_no and order_time" in str(result["next_action"])

    asyncio.run(run())


def test_create_payment_order_extracts_url_from_data_object() -> None:
    async def run() -> None:
        client = FakeClient(
            {
                "create_cashier_order": {
                    "status": "10000",
                    "orderid": "PLAT-OBJECT",
                    "data": {
                        "orderid": "PLAT-OBJECT",
                        "payUrl": "https://pay.example.test/cashier/object",
                    },
                    "message": "ok",
                }
            }
        )
        service = PaymentService(client)  # type: ignore[arg-type]

        result = await service.create_payment_order("MCH-OBJECT", 9.9)

        assert result["pay_url"] == "https://pay.example.test/cashier/object"
        assert result["order_no"] == "PLAT-OBJECT"
        assert result["qrcode"] == "https://pay.example.test/cashier/object"
        assert "[object Object]" not in str(result["pay_qrcode_markdown"])
        assert b64decode(str(result["pay_qrcode_base64"]))[:8] == b"\x89PNG\r\n\x1a\n"
        assert result["raw_payment_data_json"] == (
            '{"orderid":"PLAT-OBJECT","payUrl":"https://pay.example.test/cashier/object"}'
        )
        assert "raw_payment_data" not in result

    asyncio.run(run())


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("https://pay.example.test/direct", "https://pay.example.test/direct"),
        ({"url": "https://pay.example.test/url"}, "https://pay.example.test/url"),
        ({"qrcode": "weixin://wxpay/bizpayurl?pr=test"}, "weixin://wxpay/bizpayurl?pr=test"),
        ({"data": {"code_url": "https://pay.example.test/nested"}}, "https://pay.example.test/nested"),
        ("[object Object]", None),
        ({}, None),
    ],
)
def test_extract_payment_target(raw: object, expected: str | None) -> None:
    assert extract_payment_target(raw) == expected


def test_query_payment_order_uses_platform_orderid_payload_and_aliases() -> None:
    async def run() -> None:
        client = FakeClient(
            {
                "query_order": {
                    "status": "10000",
                    "paystatus": "1",
                    "orderid": "PLAT-123",
                    "mch_orderid": "MCH-123",
                    "paymoney": "88.50",
                    "paytime": "1710000000",
                }
            }
        )
        service = PaymentService(client)  # type: ignore[arg-type]

        result = await service.query_payment_order("PLAT-123")

        assert client.calls[0][1]["orderid"] == "PLAT-123"
        assert "mch_orderid" not in client.calls[0][1]
        assert result["success"] is True
        assert result["status"] == PaymentStatus.SUCCESS.value
        assert result["query_order_no"] == "PLAT-123"
        assert result["query_method"] == "platform_order_no"

    asyncio.run(run())


def test_query_payment_order_can_use_merchant_order_no_and_order_time() -> None:
    async def run() -> None:
        client = FakeClient(
            {
                "query_order": {
                    "status": "10000",
                    "paystatus": "0",
                    "mch_orderid": "MCH-123",
                }
            }
        )
        service = PaymentService(client)  # type: ignore[arg-type]

        result = await service.query_payment_order(
            merchant_order_no="MCH-123",
            order_time="20260603163000",
        )

        payload = client.calls[0][1]
        assert payload["mch_orderid"] == "MCH-123"
        assert payload["order_time"] == "20260603163000"
        assert "orderid" not in payload
        assert result["success"] is False
        assert result["status"] == PaymentStatus.PENDING.value
        assert result["merchant_order_no"] == "MCH-123"
        assert result["order_time"] == "20260603163000"
        assert result["query_method"] == "merchant_order_no_order_time"

    asyncio.run(run())


def test_refund_submission_4001_is_processing_not_final_success() -> None:
    async def run() -> None:
        client = FakeClient(
            {
                "refund_order": {
                    "status": "4001",
                    "orderid": "PLAT-123",
                    "mch_refund_no": "RF-001",
                    "refundmoney": "10.00",
                }
            }
        )
        service = PaymentService(client)  # type: ignore[arg-type]

        result = await service.refund_payment_order("PLAT-123", 10, "customer request", "RF-001")

        assert result["success"] is True
        assert result["status"] == PaymentStatus.REFUNDING.value
        assert result["query_order_no"] == "PLAT-123"
        assert "query_refund_status" in str(result["next_action"])

    asyncio.run(run())


def test_query_refund_status_reads_first_list_record() -> None:
    async def run() -> None:
        client = FakeClient(
            {
                "query_refund": {
                    "status": "10000",
                    "message": "ok",
                    "lists": [
                        {
                            "orderid": "PLAT-123",
                            "refund_no": "LF-RF-1",
                            "mch_refund_no": "RF-001",
                            "refundmoney": "10.00",
                            "refund_status": "1",
                            "refundtime": "1710000000",
                        }
                    ],
                }
            }
        )
        service = PaymentService(client)  # type: ignore[arg-type]

        result = await service.query_refund_status("PLAT-123", "RF-001")

        assert result["success"] is True
        assert result["status"] == PaymentStatus.REFUNDED.value
        assert result["refund_no"] == "LF-RF-1"
        assert result["mch_refund_no"] == "RF-001"
        assert result["refund_amount"] == 10.0
        assert result["query_order_no"] == "PLAT-123"

    asyncio.run(run())


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ({"status": "10000", "refund_status": "1"}, PaymentStatus.REFUNDED),
        ({"status": "10000", "is_refund": "2"}, PaymentStatus.REFUNDED),
        ({"status": "10000"}, PaymentStatus.REFUNDING),
        ({"status": "4001"}, PaymentStatus.REFUNDING),
        ({"status": "10000", "refund_status": "2"}, PaymentStatus.FAILED),
        ({"status": "4002"}, PaymentStatus.FAILED),
    ],
)
def test_map_refund_status(raw: dict, expected: PaymentStatus) -> None:
    assert map_refund_status(raw) == expected
