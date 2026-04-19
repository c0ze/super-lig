import test from "node:test";
import assert from "node:assert/strict";

import initSqlJs from "sql.js/dist/sql-wasm.js";

import * as PlayerQueries from "../src/PlayerQueries.res.js";

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
      ('m1', '2025', 30, '', 'Genclerbirligi', 'Galatasaray', 1, 2, ''),
      ('m2', '2025', 29, '', 'Galatasaray', 'Kasimpasa', 3, 0, ''),
      ('m3', '2024', 12, '', 'Samsunspor', 'Galatasaray', 0, 1, '');

    INSERT INTO events (
      match_id, minute, minute_label, minute_base, minute_extra, team, event_type, event_order,
      event_subtype, event_detail, player_1, player_2,
      home_score_before, away_score_before, home_score_after, away_score_after
    ) VALUES
      ('m1', 2, '2', 2, 0, 'Away', 'Goal', 1, '', '', 'Mauro Icardi', 'Yunus Akgun', 0, 0, 0, 1),
      ('m1', 35, '35', 35, 0, 'Away', 'Goal', 2, '', '', 'Yunus Akgun', 'Gabriel Sara', 0, 1, 0, 2),
      ('m1', 64, '64', 64, 0, 'Away', 'VAR Decision', 3, 'goalAwarded', 'overturned', 'Leroy Sane', '', NULL, NULL, NULL, NULL),
      ('m2', 18, '18', 18, 0, 'Home', 'Goal', 1, '', '', 'Mauro Icardi', 'Leroy Sane', 0, 0, 1, 0),
      ('m2', 75, '75', 75, 0, 'Home', 'Penalty Goal', 2, '', '', 'Leroy Sane', 'Leroy Sane', 2, 0, 3, 0),
      ('m3', 11, '11', 11, 0, 'Away', 'Goal', 1, '', '', 'Leroy Sane', 'Dries Mertens', 0, 0, 0, 1);
  `);

  return db;
};

const collectRows = (db, sql, params) => {
  const statement = db.prepare(sql);
  statement.bind(params);
  const rows = [];
  while (statement.step()) {
    rows.push(statement.getAsObject());
  }
  statement.free();
  return rows;
};

test("player summary query aggregates goals, assists, seasons, and denied goals", () => {
  const db = makeDb();
  const rows = collectRows(db, PlayerQueries.playerSummarySql, Array(8).fill("Leroy Sane"));

  assert.deepEqual(rows, [
    {
      matches: 3,
      seasons: 2,
      clubs: 1,
      goals: 2,
      assists: 1,
      var_denied_goals: 1,
      var_denied_assists: 0,
    },
  ]);
});

test("player season tabs and season match lists include contribution counts", () => {
  const db = makeDb();
  const seasons = collectRows(db, PlayerQueries.playerMatchSeasonsSql, Array(8).fill("Leroy Sane"));

  assert.deepEqual(seasons, [
    {season: "2025", games: 2},
    {season: "2024", games: 1},
  ]);

  const matches = collectRows(
    db,
    PlayerQueries.playerMatchesBySeasonSql,
    [...Array(8).fill("Leroy Sane"), "2025"],
  );

  assert.deepEqual(
    matches.map(
      ({id, season, matchday, team_name, goals, assists, var_denied_goals, var_denied_assists}) => ({
        id,
        season,
        matchday,
        team_name,
        goals,
        assists,
        var_denied_goals,
        var_denied_assists,
      }),
    ),
    [
      {
        id: "m1",
        season: "2025",
        matchday: 30,
        team_name: "Galatasaray",
        goals: 0,
        assists: 0,
        var_denied_goals: 1,
        var_denied_assists: 0,
      },
      {
        id: "m2",
        season: "2025",
        matchday: 29,
        team_name: "Galatasaray",
        goals: 1,
        assists: 1,
        var_denied_goals: 0,
        var_denied_assists: 0,
      },
    ],
  );
});
