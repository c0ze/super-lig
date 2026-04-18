import test from "node:test";
import assert from "node:assert/strict";

import * as Locale from "../src/Locale.res.js";

test("locale falls back to Turkish when input is missing", () => {
  assert.equal(Locale.fromString(undefined), "tr");
  assert.equal(Locale.fromString(""), "tr");
});

test("locale accepts english and turkish values", () => {
  assert.equal(Locale.fromString("en"), "en");
  assert.equal(Locale.fromString("tr"), "tr");
});

test("locale toggles between languages", () => {
  assert.equal(Locale.toggle("tr"), "en");
  assert.equal(Locale.toggle("en"), "tr");
});

test("locale labels are stable", () => {
  assert.equal(Locale.label("tr"), "TR");
  assert.equal(Locale.label("en"), "EN");
});
