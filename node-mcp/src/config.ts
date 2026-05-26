export type PaymentSettings = {
  apiBaseUrl: string;
  apiKey: string;
  signKey: string;
  signType: string;
  requestTimeoutMs: number;
};

function requiredEnv(name: string): string {
  const value = process.env[name];
  if (!value) {
    throw new Error(`${name} is required`);
  }
  return value;
}

export function loadSettings(): PaymentSettings {
  return {
    apiBaseUrl: process.env.PAYMENT_API_BASE_URL ?? "https://api2.lfwin.com",
    apiKey: requiredEnv("PAYMENT_API_KEY"),
    signKey: requiredEnv("PAYMENT_SIGN_KEY"),
    signType: process.env.PAYMENT_SIGN_TYPE ?? "MD5",
    requestTimeoutMs: Number(process.env.PAYMENT_REQUEST_TIMEOUT_MS ?? 15000),
  };
}
