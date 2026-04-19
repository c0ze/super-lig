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

test("penalty goals are labeled via the player_1 == player_2 heuristic", () => {
  const english = Locale.fromString("en");

  assert.equal(
    MatchTimeline.detailText(english, "Goal", "Talisca", "Talisca"),
    "Penalty",
  );
});

test("penalty goals are labeled when the scraper marks them explicitly", () => {
  const english = Locale.fromString("en");

  assert.equal(
    MatchTimeline.detailText(english, "Penalty Goal", "Talisca", ""),
    "Penalty",
  );
});

test("missed penalties keep the penalty context in the timeline", () => {
  const english = Locale.fromString("en");

  assert.equal(
    MatchTimeline.detailText(english, "Missed Penalty", "Talisca", "Mateusz Lis"),
    "Missed penalty • Goalkeeper: Mateusz Lis",
  );
});

test("own goals count as goal events in the timeline", () => {
  assert.equal(MatchTimeline.isGoalEvent("Own Goal"), true);
  assert.equal(MatchTimeline.toneClass("Own Goal"), "goal");
});

test("var decisions use a dedicated timeline label and localized subtype details", () => {
  const english = Locale.fromString("en");

  assert.equal(MatchTimeline.eventLabel(english, "VAR Decision", "", ""), "VAR decision");
  assert.equal(
    MatchTimeline.detailTextWithMetadata(
      english,
      "VAR Decision",
      "goalAwarded",
      "overturned",
      "Leroy Sane",
      "",
    ),
    "Goal awarded • Overturned",
  );
});
