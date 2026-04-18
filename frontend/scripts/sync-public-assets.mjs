import { copyFile, mkdir } from "node:fs/promises";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const frontendRoot = resolve(__dirname, "..");
const publicDir = resolve(frontendRoot, "public");

const assets = [
  {
    from: resolve(frontendRoot, "..", "data", "super_lig.db"),
    to: resolve(publicDir, "super_lig.db"),
  },
  {
    from: resolve(frontendRoot, "node_modules", "sql.js", "dist", "sql-wasm.wasm"),
    to: resolve(publicDir, "sql-wasm.wasm"),
  },
];

await mkdir(publicDir, { recursive: true });

for (const asset of assets) {
  await copyFile(asset.from, asset.to);
}

console.log("Synced database and sql.js WASM into frontend/public");
