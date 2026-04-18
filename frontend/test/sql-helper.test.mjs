import test from "node:test";
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";

test("SqlHelper uses the explicit sql.js wasm entrypoint", async () => {
  const source = await readFile(new URL("../src/SqlHelper.js", import.meta.url), "utf8");

  assert.match(source, /from ['"]sql\.js\/dist\/sql-wasm\.js['"]/);
});
