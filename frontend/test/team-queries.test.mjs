import test from "node:test";
import assert from "node:assert/strict";

import initSqlJs from "sql.js/dist/sql-wasm.js";

import * as TeamQueries from "../src/TeamQueries.res.js";

const SQL = await initSqlJs({
  locateFile: (file) => new URL(`../node_modules/sql.js/dist/${file}`, import.meta.url).pathname,
});

const makeDb = () => {
  const db = new SQL.Database();

  db.run(`
    CREATE TABLE matches (
      id TEXT PRIMARY KEY,
      season TEXT,
      matchday INTEGER,
      date TEXT,
      home_team TEXT,
      away_team TEXT,
      home_score INTEGER,
      away_score INTEGER,
      url TEXT
    );

    CREATE TABLE events (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      match_id TEXT NOT NULL,
      minute INTEGER,
      minute_label TEXT,
      minute_base INTEGER,
      minute_extra INTEGER,
      team TEXT,
      event_type TEXT,
      event_order INTEGER,
      event_subtype TEXT,
      event_detail TEXT,
      player_1 TEXT,
      player_2 TEXT,
      home_score_before INTEGER,
      away_score_before INTEGER,
      home_score_after INTEGER,
      away_score_after INTEGER
    );
  `);

  db.run(`
    INSERT INTO matches (id, season, matchday, date, home_team, away_team, home_score, away_score, url)
    VALUES
      ('m1', '2025', 1, '', 'Fenerbahce', 'Rizespor', 2, 1, ''),
      ('m2', '2025', 2, '', 'Besiktas', 'Fenerbahce', 0, 0, ''),
      ('m3', '2025', 3, '', 'Fenerbahce', 'Goztepe', 1, 2, '');

    INSERT INTO events (
      match_id, minute, minute_label, minute_base, minute_extra, team, event_type, event_order,
      event_subtype, event_detail, player_1, player_2,
      home_score_before, away_score_before, home_score_after, away_score_after
    ) VALUES
      ('m1', 75, '75', 75, 0, 'Away', 'Second Yellow Card', 1, '', 'Faul', 'Defender', '', 0, 0, 0, 0),
      ('m2', 90, '90', 90, 0, 'Away', 'Missed Penalty', 1, 'Faul penaltısı', 'Kurtarış', 'Talisca', 'Keeper', 0, 0, 0, 0),
      ('m3', 55, '55', 55, 0, 'Home', 'Penalty Goal', 1, 'Penaltı', '', 'Talisca', 'Talisca', 2, 1, 3, 1);
  `);

  return db;
};

const runSingleValue = (db, sql, team) => {
  const statement = db.prepare(sql);
  statement.bind([team]);
  assert.equal(statement.step(), true);
  const row = statement.getAsObject();
  statement.free();
  return row.propped_up_games;
};

test("propped up games count matches with penalties or opponent reds while level or behind", () => {
  const db = makeDb();

  assert.equal(runSingleValue(db, TeamQueries.proppedUpGamesSql, "Fenerbahce"), 2);
});
