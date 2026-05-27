import { randomUUID } from "node:crypto";

import type { LFWinClient, LFWinResponse } from "./client.js";
import { makePngDataUrl } from "./qrcode-image.js";

export enum PaymentStatus {
  Pending = "PENDING",
  Processing = "PROCESSING",
  Success = "SUCCESS",
  Failed = "FAILED",
  Refunding = "REFUNDING",
  Refunded = "REFUNDED",
}

function valueAsString(value: unknown): string | undefined {
  if (value === null || value === undefined) {
    return undefined;
  }
  return String(value);
}

function valueAsNumber(value: unknown): number | undefined {
  if (value === null || value === undefined || value === "") {
    return undefined;
  }
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : undefined;
}

export function parseUnixSeconds(value: unknown): string | undefined {
  if (value === null || value === undefined || value === "" || value === "0" || value === 0) {
    return undefined;
  }

  const seconds = Number(value);
  if (!Number.isFinite(seconds)) {
    return undefined;
  }

  return new Intl.DateTimeFormat("zh-CN", {
    timeZone: "Asia/Shanghai",
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
    hour12: false,
  })
    .format(new Date(seconds * 1000))
    .replaceAll("/", "-");
}

export function mapRefundStatus(result: LFWinResponse): PaymentStatus {
  const rawStatus = valueAsString(result.status) ?? "";
  const refundStatus = valueAsString(result.refund_status) ?? "";
  const isRefund = valueAsString(result.is_refund) ?? "";

  if (rawStatus === "4001") {
    return PaymentStatus.Refunding;
  }
  if (["4000", "4002", "1002"].includes(rawStatus) || refundStatus === "2") {
    return PaymentStatus.Failed;
  }
  if (rawStatus === "10000" && (refundStatus === "1" || isRefund === "2")) {
    return PaymentStatus.Refunded;
  }
  if (rawStatus === "10000") {
    return PaymentStatus.Refunding;
  }
  return PaymentStatus.Processing;
}

function firstRefundRecord(result: LFWinResponse): LFWinResponse {
  const records = result.lists;
  if (Array.isArray(records) && records.length > 0 && typeof records[0] === "object" && records[0] !== null) {
    return records[0] as LFWinResponse;
  }
  return result;
}

function paymentUsageInstruction(orderNo: unknown): string {
  return [
    "Show pay_qrcode_markdown to the user when Markdown is supported; otherwise render pay_qrcode_image as an image,",
    "or use pay_url/qrcode as the payment link/QR content.",
    `Store order_no (${valueAsString(orderNo) ?? ""}) as the platform order number for all later payment query and refund tools.`,
    "Do not use merchant_order_no for query_payment_order unless a merchant-order query tool explicitly asks for merchant_order_no plus order_time.",
  ].join(" ");
}

export class PaymentService {
  constructor(private readonly client: LFWinClient) {}

  async createPaymentOrder(input: {
    merchantOrderNo: string;
    amount: number;
    notifyUrl?: string;
  }): Promise<Record<string, unknown>> {
    const result = await this.client.createCashierOrder({
      money: input.amount.toFixed(2),
      nonce_str: randomUUID().replaceAll("-", "").slice(0, 16),
      mch_orderid: input.merchantOrderNo,
      notify_url: input.notifyUrl ?? "",
    });

    const payUrl = valueAsString(result.data);
    const payQrcodeImage = payUrl ? await makePngDataUrl(payUrl) : undefined;
    const orderNo = valueAsString(result.orderid) ?? "";

    return {
      success: result.status === "10000",
      order_no: orderNo,
      platform_order_no: orderNo,
      query_order_no: orderNo,
      merchant_order_no: input.merchantOrderNo,
      amount: input.amount,
      status: PaymentStatus.Pending,
      pay_url: payUrl,
      qrcode: payUrl,
      pay_qrcode_image: payQrcodeImage,
      pay_qrcode_markdown: payQrcodeImage ? `![Payment QR Code](${payQrcodeImage})` : undefined,
      expire_time: new Intl.DateTimeFormat("zh-CN", {
        timeZone: "Asia/Shanghai",
        year: "numeric",
        month: "2-digit",
        day: "2-digit",
        hour: "2-digit",
        minute: "2-digit",
        second: "2-digit",
        hour12: false,
      })
        .format(new Date(Date.now() + 15 * 60 * 1000))
        .replaceAll("/", "-"),
      display_instruction: paymentUsageInstruction(orderNo),
      next_action: "Display the QR code/payment link, then poll query_payment_order with query_order_no/order_no.",
      message: valueAsString(result.message),
      raw_status: valueAsString(result.status) ?? "",
    };
  }

  async queryPaymentOrder(orderNo: string): Promise<Record<string, unknown>> {
    const result = await this.client.queryOrder({
      service: "pay.comm.query_order",
      orderid: orderNo,
      nonce_str: randomUUID().replaceAll("-", "").slice(0, 16),
    });

    const payStatus = valueAsString(result.paystatus) ?? "0";
    let status = PaymentStatus.Pending;
    if (payStatus === "1") {
      status = PaymentStatus.Success;
    } else if (payStatus === "2") {
      status = PaymentStatus.Failed;
    }

    return {
      success: result.status === "10000" && status === PaymentStatus.Success,
      order_no: valueAsString(result.orderid) ?? orderNo,
      platform_order_no: valueAsString(result.orderid) ?? orderNo,
      query_order_no: valueAsString(result.orderid) ?? orderNo,
      merchant_order_no: valueAsString(result.mch_orderid),
      status,
      paid_amount: valueAsNumber(result.paymoney) ?? 0,
      paid_time: parseUnixSeconds(result.paytime),
      query_instruction:
        "This result was queried by platform order_no/orderid. Treat paystatus=1 as paid, paystatus=2 as failed, otherwise keep pending.",
      message: valueAsString(result.message),
      raw_status: valueAsString(result.status) ?? "",
      raw_paystatus: payStatus,
    };
  }

  async refundPaymentOrder(input: {
    orderNo: string;
    refundAmount: number;
    reason: string;
    mchRefundNo: string;
  }): Promise<Record<string, unknown>> {
    const result = await this.client.refundOrder({
      service: "pay.comm.refund_order",
      orderid: input.orderNo,
      refundmoney: input.refundAmount.toFixed(2),
      version: "4.0",
      nonce_str: randomUUID().replaceAll("-", "").slice(0, 16),
      reason: input.reason,
      mch_refund_no: input.mchRefundNo,
    });
    const status = mapRefundStatus(result);

    return {
      success: ["10000", "4001"].includes(valueAsString(result.status) ?? ""),
      order_no: valueAsString(result.orderid) ?? input.orderNo,
      platform_order_no: valueAsString(result.orderid) ?? input.orderNo,
      query_order_no: valueAsString(result.orderid) ?? input.orderNo,
      refund_no: valueAsString(result.refund_no),
      mch_refund_no: valueAsString(result.mch_refund_no) ?? input.mchRefundNo,
      refund_amount: valueAsNumber(result.refundmoney) ?? input.refundAmount,
      status,
      next_action:
        "Refund submission accepted only means processing; call query_refund_status with order_no and mch_refund_no to confirm the final result.",
      message: valueAsString(result.message),
      raw_status: valueAsString(result.status) ?? "",
    };
  }

  async queryRefundStatus(orderNo: string, mchRefundNo?: string): Promise<Record<string, unknown>> {
    const payload: Record<string, string> = {
      service: "pay.comm.query_refund",
      orderid: orderNo,
      version: "4.0",
      nonce_str: randomUUID().replaceAll("-", "").slice(0, 16),
    };
    if (mchRefundNo) {
      payload.mch_refund_no = mchRefundNo;
    }

    const result = await this.client.queryRefund(payload);
    const record = firstRefundRecord(result);
    const status = mapRefundStatus({ ...result, ...record });
    const rawStatus = valueAsString(result.status) ?? "";

    return {
      success: rawStatus === "10000" && status === PaymentStatus.Refunded,
      order_no: valueAsString(record.orderid) ?? valueAsString(result.orderid) ?? orderNo,
      platform_order_no: valueAsString(record.orderid) ?? valueAsString(result.orderid) ?? orderNo,
      query_order_no: valueAsString(record.orderid) ?? valueAsString(result.orderid) ?? orderNo,
      refund_no: valueAsString(record.refund_no) ?? valueAsString(result.refund_no),
      mch_refund_no: valueAsString(record.mch_refund_no) ?? valueAsString(result.mch_refund_no) ?? mchRefundNo,
      refund_amount: valueAsNumber(record.refundmoney),
      status,
      refund_time: parseUnixSeconds(record.refundtime),
      query_instruction:
        "REFUNDED is final success, FAILED is final failure, and REFUNDING/PROCESSING should be queried again later.",
      message: valueAsString(result.message),
      raw_status: rawStatus,
    };
  }
}
