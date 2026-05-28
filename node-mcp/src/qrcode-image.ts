import QRCode from "qrcode";

export const PNG_DATA_URL_PREFIX = "data:image/png;base64,";

export async function makePngDataUrl(value: string): Promise<string> {
  return QRCode.toDataURL(value, {
    errorCorrectionLevel: "M",
    margin: 2,
    type: "image/png",
  });
}
