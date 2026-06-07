import { spawnSync } from "node:child_process";
import { access, copyFile, mkdir, readFile, rm, writeFile } from "node:fs/promises";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { gzipSync } from "node:zlib";

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

await mkdir(publicDir, { recursive: true });

// Ship the DB gzip-compressed (~3x smaller) and decompress it in the browser.
// The ".gzip" extension (not ".gz") avoids dev/prod static servers auto-setting
// Content-Encoding: gzip, which would transparently decompress and conflict with
// our explicit DecompressionStream in SqlHelper.
const dbBuffer = await readFile(canonicalDb);
await writeFile(resolve(publicDir, "site.db.gzip"), gzipSync(dbBuffer, { level: 9 }));
// Drop uncompressed / legacy copies so they never ship in dist.
await rm(resolve(publicDir, "site.db"), { force: true });
await rm(resolve(publicDir, "site.db.gz"), { force: true });

await copyFile(
  resolve(frontendRoot, "node_modules", "sql.js", "dist", "sql-wasm.wasm"),
  resolve(publicDir, "sql-wasm.wasm"),
);

console.log(
  rebuilt
    ? `Built site.db from ${source}, gzipped it, and synced sql.js WASM into frontend/public`
    : "Reused existing site.db, gzipped it, and synced sql.js WASM into frontend/public",
);
