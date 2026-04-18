import test from "node:test";
import assert from "node:assert/strict";

import * as Locale from "../src/Locale.res.js";
import * as MatchTimeline from "../src/MatchTimeline.res.js";

test("minute labels use football notation", () => {
  assert.equal(MatchTimeline.minuteLabel(17), "17'");
  assert.equal(MatchTimeline.minuteLabel(90), "90'");
});

test("goal timeline details include assists when present", () => {
  const english = Locale.fromString("en");

  assert.equal(
    MatchTimeline.detailText(english, "Goal", "Victor Osimhen", "Kaan Ayhan"),
    "Assist: Kaan Ayhan",
  );
});

test("substitution timeline details describe in and out players", () => {
  const turkish = Locale.fromString("tr");

  assert.equal(
    MatchTimeline.detailText(turkish, "Substitution", "Elias Jelert", "Przemyslaw Frankowski"),
    "Giren: Elias Jelert • Çıkan: Przemyslaw Frankowski",
  );
});

test("second yellow cards use red-card tone in the timeline", () => {
  assert.equal(MatchTimeline.toneClass("Second Yellow Card"), "danger");
});

test("penalty goals are labeled when the data marks them", () => {
  const english = Locale.fromString("en");

  assert.equal(
    MatchTimeline.detailText(english, "Goal", "Talisca", "Talisca"),
    "Penalty",
  );
});
