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

const runPython = (args) => {
  let missingPython = null;
  for (const command of ["python", "python3"]) {
    const result = spawnSync(command, args, {
      cwd: repoRoot,
      stdio: "inherit",
    });
    if (result.error?.code === "ENOENT") {
      missingPython = result.error;
      continue;
    }
    return result;
  }

  return { status: 127, error: missingPython };
};

const ensureCanonicalSchema = () => {
  const schemaResult = runPython(["-c", "import site_db; site_db.init_db()"]);

  if (schemaResult.status !== 0) {
    throw new Error("Failed to ensure canonical site.db schema");
  }
};

let rebuilt = false;

if (await fileExists(sourceDb)) {
  const buildResult = runPython(
    [
      resolve(repoRoot, "site_builder.py"),
      "--source",
      source,
      "--target",
      canonicalDb,
    ],
  );

  if (buildResult.status !== 0) {
    throw new Error(`Failed to build canonical site.db from source '${source}'`);
  }
  rebuilt = true;
} else if (await fileExists(canonicalDb)) {
  console.warn(
    `Source DB for '${source}' not found at ${sourceDb}. Reusing existing canonical site.db.`,
  );
  ensureCanonicalSchema();
} else {
  throw new Error(
    `Neither source DB (${sourceDb}) nor canonical DB (${canonicalDb}) is available.`,
  );
}

const assets = [
  {
    from: canonicalDb,
    to: resolve(publicDir, "site.db"),
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

console.log(
  rebuilt
    ? `Built site.db from ${source} and synced it with sql.js WASM into frontend/public`
    : "Reused existing site.db and synced it with sql.js WASM into frontend/public",
);
