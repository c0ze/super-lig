import test from "node:test";
import assert from "node:assert/strict";

import * as Copy from "../src/Copy.res.js";
import * as Locale from "../src/Locale.res.js";

test("season labels render full season ranges in English", () => {
  const english = Locale.fromString("en");

  assert.equal(Copy.seasonTitle(english, "2025"), "2025-2026 season");
  assert.equal(Copy.latestSeasonStandingsTitle(english, "2025"), "2025-2026 standings");
  assert.equal(Copy.backToSeason(english, "2025"), "Back to 2025-2026 season");
});

test("season labels render full season ranges in Turkish", () => {
  const turkish = Locale.fromString("tr");

  assert.equal(Copy.seasonTitle(turkish, "2025"), "2025-2026 sezonu");
  assert.equal(Copy.latestSeasonStandingsTitle(turkish, "2025"), "2025-2026 puan tablosu");
  assert.equal(Copy.navLatestSeason(turkish, "2025"), "2025-2026 Sezonu");
});

test("propped up games labels are localized", () => {
  const english = Locale.fromString("en");
  const turkish = Locale.fromString("tr");

  assert.equal(Copy.proppedUpGamesLabel(english), "Propped up games");
  assert.equal(Copy.proppedUpGamesLabel(turkish), "Kollandığı maçlar");
});
