import test from "node:test";
import assert from "node:assert/strict";

import * as Route from "../src/Route.res.js";

test("empty hash resolves to dashboard", () => {
  const route = Route.parseHash("");

  assert.equal(route.kind, "dashboard");
  assert.equal(route.param, undefined);
});

test("season hash resolves to season route", () => {
  const route = Route.parseHash("#/season/2024");

  assert.equal(route.kind, "season");
  assert.equal(route.param, "2024");
});

test("team hash decodes URL-encoded names", () => {
  const route = Route.parseHash("#/team/Besiktas%20JK");

  assert.equal(route.kind, "team");
  assert.equal(route.param, "Besiktas JK");
});

test("match hash resolves to match route", () => {
  const route = Route.parseHash("#/match/4393440");

  assert.equal(route.kind, "match");
  assert.equal(route.param, "4393440");
});

test("route hashes encode team names safely", () => {
  const hash = Route.toHash(Route.team("Göztepe"));

  assert.equal(hash, "#/team/G%C3%B6ztepe");
});

test("route hashes encode match ids safely", () => {
  const hash = Route.toHash(Route.match("4393440"));

  assert.equal(hash, "#/match/4393440");
});

test("unknown hashes resolve to not-found", () => {
  const route = Route.parseHash("#/archive/2012");

  assert.equal(route.kind, "notFound");
  assert.equal(route.param, "archive/2012");
});
