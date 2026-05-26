import QRCode from "qrcode";

export async function makePngDataUrl(value: string): Promise<string> {
  return QRCode.toDataURL(value, {
    errorCorrectionLevel: "M",
    margin: 2,
    type: "image/png",
  });
}
