import { spawnSync } from "node:child_process";
import { access, copyFile, mkdir } from "node:fs/promises";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const frontendRoot = resolve(__dirname, "..");
const publicDir = resolve(frontendRoot, "public");
const repoRoot = resolve(frontendRoot, "..");
const source = process.env.SITE_DB_SOURCE ?? "sofascore";
const canonicalDb = resolve(repoRoot, "data", "site.db");
const sourceDb =
  source === "sofascore"
    ? resolve(repoRoot, "data", "sofascore_super_lig.db")
    : resolve(repoRoot, "data", "super_lig.db");

const fileExists = async (path) => {
  try {
    await access(path);
    return true;
  } catch {
    return false;
  }
};

if (await fileExists(sourceDb)) {
  const buildResult = spawnSync(
    "python",
    [
      resolve(repoRoot, "site_builder.py"),
      "--source",
      source,
      "--target",
      canonicalDb,
    ],
    {
      cwd: repoRoot,
      stdio: "inherit",
    },
  );

  if (buildResult.status !== 0) {
    throw new Error(`Failed to build canonical site.db from source '${source}'`);
  }
} else if (await fileExists(canonicalDb)) {
  console.warn(
    `Source DB for '${source}' not found at ${sourceDb}. Reusing existing canonical site.db.`,
  );
} else {
  throw new Error(
    `Neither source DB (${sourceDb}) nor canonical DB (${canonicalDb}) is available.`,
  );
}

const assets = [
  {
    from: canonicalDb,
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

console.log(`Built site.db from ${source} and synced it with sql.js WASM into frontend/public`);
