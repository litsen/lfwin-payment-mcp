import type { PaymentSettings } from "./config.js";
import { md5Sign, type SignablePayload } from "./signature.js";

export type LFWinResponse = Record<string, unknown>;

export class LFWinClient {
  constructor(private readonly settings: PaymentSettings) {}

  async post(path: string, payload: SignablePayload): Promise<LFWinResponse> {
    const signedPayload: SignablePayload = {
      ...payload,
      apikey: this.settings.apiKey,
      sign_type: this.settings.signType,
    };
    signedPayload.sign = md5Sign(signedPayload, this.settings.signKey);

    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), this.settings.requestTimeoutMs);

    try {
      const response = await fetch(new URL(path, this.settings.apiBaseUrl), {
        method: "POST",
        headers: {
          "content-type": "application/x-www-form-urlencoded",
        },
        body: new URLSearchParams(
          Object.entries(signedPayload).map(([key, value]) => [key, String(value ?? "")]),
        ),
        signal: controller.signal,
      });

      if (!response.ok) {
        throw new Error(`LFWin request failed: HTTP ${response.status} ${response.statusText}`);
      }

      return (await response.json()) as LFWinResponse;
    } finally {
      clearTimeout(timeout);
    }
  }

  async createCashierOrder(payload: SignablePayload): Promise<LFWinResponse> {
    return this.post("/index/Payment/pre_order", payload);
  }

  async queryOrder(payload: SignablePayload): Promise<LFWinResponse> {
    return this.post("/payapi/pay/query_order", payload);
  }

  async refundOrder(payload: SignablePayload): Promise<LFWinResponse> {
    return this.post("/payapi/pay/refund_order", payload);
  }

  async queryRefund(payload: SignablePayload): Promise<LFWinResponse> {
    return this.post("/payapi/pay/query_refund", payload);
  }
}
