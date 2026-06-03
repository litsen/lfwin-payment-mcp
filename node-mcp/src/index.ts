#!/usr/bin/env node

import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import type { ContentBlock } from "@modelcontextprotocol/sdk/types.js";
import { z } from "zod";

import { LFWinClient } from "./client.js";
import { loadSettings } from "./config.js";
import { PNG_DATA_URL_PREFIX } from "./qrcode-image.js";
import { PaymentService } from "./service.js";

const server = new McpServer({
  name: "lfwin-payment-mcp",
  version: "0.1.7",
});

let service: PaymentService | undefined;

function getService(): PaymentService {
  if (!service) {
    service = new PaymentService(new LFWinClient(loadSettings()));
  }
  return service;
}

function jsonResult(value: unknown) {
  return {
    content: [
      {
        type: "text" as const,
        text: JSON.stringify(value, null, 2),
      },
    ],
  };
}

function paymentOrderResult(value: Record<string, unknown>) {
  const content: ContentBlock[] = [
    {
      type: "text" as const,
      text: JSON.stringify(value, null, 2),
    },
  ];

  const image = typeof value.pay_qrcode_image === "string" ? value.pay_qrcode_image : undefined;
  if (image?.startsWith(PNG_DATA_URL_PREFIX)) {
    content.push({
      type: "image" as const,
      data: image.slice(PNG_DATA_URL_PREFIX.length),
      mimeType: "image/png",
    });
  }

  return { content };
}

server.tool(
  "create_payment_order",
  [
    "Create a cashier payment order. Amount is in yuan and merchant_order_no is the merchant's own unique order number.",
    "After success, display pay_qrcode_markdown, the returned image content block, pay_qrcode_image data URL, or pay_qrcode_base64 with pay_qrcode_mime_type as the QR code.",
    "If QR rendering fails, show pay_url/qrcode as the fallback payment link.",
    "Save order_no/query_order_no as the platform order number for later query and refund tools.",
  ].join(" "),
  {
    merchant_order_no: z.string().min(1),
    amount: z.number().positive(),
    notify_url: z.string().url().optional(),
  },
  async (input) =>
    paymentOrderResult(
      await getService().createPaymentOrder({
        merchantOrderNo: input.merchant_order_no,
        amount: input.amount,
        notifyUrl: input.notify_url,
      }),
    ),
);

server.tool(
  "query_payment_order",
  [
    "Query payment order status by the platform order_no/orderid returned by create_payment_order.",
    "Do not pass merchant_order_no here; LFWin merchant-order queries require merchant_order_no plus order_time and are not exposed by this tool.",
  ].join(" "),
  {
    order_no: z.string().min(1),
  },
  async (input) => jsonResult(await getService().queryPaymentOrder(input.order_no)),
);

server.tool(
  "refund_payment_order",
  [
    "Create a refund request by platform order_no/orderid.",
    "mch_refund_no is the merchant refund number and must be unique per refund.",
    "Successful submission means accepted/processing, not final refund success; call query_refund_status to confirm.",
  ].join(" "),
  {
    order_no: z.string().min(1),
    refund_amount: z.number().positive(),
    reason: z.string().min(1),
    mch_refund_no: z.string().min(1),
  },
  async (input) =>
    jsonResult(
      await getService().refundPaymentOrder({
        orderNo: input.order_no,
        refundAmount: input.refund_amount,
        reason: input.reason,
        mchRefundNo: input.mch_refund_no,
      }),
    ),
);

server.tool(
  "query_refund_status",
  [
    "Query refund status by platform order_no/orderid.",
    "Pass mch_refund_no when available to locate a specific partial refund.",
    "Only REFUNDED is final success; REFUNDING/PROCESSING means query again later.",
  ].join(" "),
  {
    order_no: z.string().min(1),
    mch_refund_no: z.string().min(1).optional(),
  },
  async (input) => jsonResult(await getService().queryRefundStatus(input.order_no, input.mch_refund_no)),
);

const transport = new StdioServerTransport();
await server.connect(transport);
