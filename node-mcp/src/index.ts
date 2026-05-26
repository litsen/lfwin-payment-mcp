#!/usr/bin/env node

import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import type { ContentBlock } from "@modelcontextprotocol/sdk/types.js";
import { z } from "zod";

import { LFWinClient } from "./client.js";
import { loadSettings } from "./config.js";
import { PaymentService } from "./service.js";

const server = new McpServer({
  name: "lfwin-payment-mcp",
  version: "0.1.0",
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
  const prefix = "data:image/png;base64,";
  if (image?.startsWith(prefix)) {
    content.push({
      type: "image" as const,
      data: image.slice(prefix.length),
      mimeType: "image/png",
    });
  }

  return { content };
}

server.tool(
  "create_payment_order",
  "Create a cashier payment order. Amount is in yuan. The merchant order number must be unique.",
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
  "Query payment order status by the platform order number.",
  {
    order_no: z.string().min(1),
  },
  async (input) => jsonResult(await getService().queryPaymentOrder(input.order_no)),
);

server.tool(
  "refund_payment_order",
  "Create a refund request. mch_refund_no is the merchant refund number and must be unique.",
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
  "Query refund status. Optionally pass mch_refund_no to locate a specific refund.",
  {
    order_no: z.string().min(1),
    mch_refund_no: z.string().min(1).optional(),
  },
  async (input) => jsonResult(await getService().queryRefundStatus(input.order_no, input.mch_refund_no)),
);

const transport = new StdioServerTransport();
await server.connect(transport);
