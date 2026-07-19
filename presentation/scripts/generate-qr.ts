import { mkdir } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import QRCode from "qrcode";

const directory = new URL("../public/qrs/", import.meta.url);
await mkdir(directory, { recursive: true });
const directoryPath = fileURLToPath(directory);

const codes = {
  "product.png": "http://calls.feedfinch.com",
  "repository.png": "https://github.com/tjvjk/hack-nation-vas3k",
};

await Promise.all(
  Object.entries(codes).map(([filename, url]) =>
    QRCode.toFile(`${directoryPath}${filename}`, url, {
      errorCorrectionLevel: "M",
      margin: 1,
      width: 800,
      color: { dark: "#000000", light: "#ffffff" },
    }),
  ),
);
