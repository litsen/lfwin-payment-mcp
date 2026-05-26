import { createHash } from "node:crypto";

type SignableValue = string | number | boolean | null | undefined;

export type SignablePayload = Record<string, SignableValue>;

export function buildSigningPayload(data: SignablePayload, signKey: string): string {
  const pairs = Object.entries(data)
    .filter(([key, value]) => key !== "sign" && value !== null && value !== undefined)
    .map(([key, value]) => {
      const rawValue = key === "notify_url" ? decodeURIComponent(String(value)) : String(value);
      return [key, rawValue] as const;
    })
    .sort(([left], [right]) => left.localeCompare(right))
    .map(([key, value]) => `${key}=${value}`);

  return `${pairs.join("&")}&signkey=${signKey}`;
}

export function md5Sign(data: SignablePayload, signKey: string): string {
  return createHash("md5").update(buildSigningPayload(data, signKey), "utf8").digest("hex");
}
