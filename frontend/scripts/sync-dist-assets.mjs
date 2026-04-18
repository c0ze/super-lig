import { copyFile, mkdir } from "node:fs/promises";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const frontendRoot = resolve(__dirname, "..");
const distDir = resolve(frontendRoot, "dist");

await mkdir(distDir, { recursive: true });
await copyFile(resolve(frontendRoot, "..", "CNAME"), resolve(distDir, "CNAME"));

console.log("Synced CNAME into frontend/dist");
