let benefitEventsSql =
  "WITH benefit_events AS (" ++
  "SELECT " ++
  "e.match_id AS match_id, " ++
  "m.season AS season, " ++
  "m.matchday AS matchday, " ++
  "m.home_team AS home_team, " ++
  "m.away_team AS away_team, " ++
  "m.home_score AS home_score, " ++
  "m.away_score AS away_score, " ++
  "CASE " ++
  "WHEN e.event_type IN ('Penalty Goal', 'Missed Penalty') AND e.team = 'Home' THEN m.home_team " ++
  "WHEN e.event_type IN ('Penalty Goal', 'Missed Penalty') AND e.team = 'Away' THEN m.away_team " ++
  "WHEN e.event_type IN ('Red Card', 'Second Yellow Card') AND e.team = 'Home' THEN m.away_team " ++
  "WHEN e.event_type IN ('Red Card', 'Second Yellow Card') AND e.team = 'Away' THEN m.home_team " ++
  "ELSE '' END AS benefiting_team, " ++
  "CASE " ++
  "WHEN e.event_type IN ('Penalty Goal', 'Missed Penalty') THEN 1 " ++
  "ELSE 0 END AS has_penalty, " ++
  "CASE " ++
  "WHEN e.event_type IN ('Red Card', 'Second Yellow Card') THEN 1 " ++
  "ELSE 0 END AS has_red_card, " ++
  "CASE " ++
  "WHEN e.event_type IN ('Penalty Goal', 'Missed Penalty') AND e.team = 'Home' THEN CASE WHEN e.home_score_before <= e.away_score_before THEN 1 ELSE 0 END " ++
  "WHEN e.event_type IN ('Penalty Goal', 'Missed Penalty') AND e.team = 'Away' THEN CASE WHEN e.away_score_before <= e.home_score_before THEN 1 ELSE 0 END " ++
  "WHEN e.event_type IN ('Red Card', 'Second Yellow Card') AND e.team = 'Home' THEN CASE WHEN e.away_score_before <= e.home_score_before THEN 1 ELSE 0 END " ++
  "WHEN e.event_type IN ('Red Card', 'Second Yellow Card') AND e.team = 'Away' THEN CASE WHEN e.home_score_before <= e.away_score_before THEN 1 ELSE 0 END " ++
  "ELSE 0 END AS qualifies " ++
  "FROM events e " ++
  "JOIN matches m ON m.id = e.match_id " ++
  "WHERE e.event_type IN ('Penalty Goal', 'Missed Penalty', 'Red Card', 'Second Yellow Card') " ++
  "AND e.home_score_before IS NOT NULL " ++
  "AND e.away_score_before IS NOT NULL" ++
  ") " ++
  ""

let proppedUpGamesSql =
  benefitEventsSql ++
  "SELECT COUNT(DISTINCT match_id) AS propped_up_games " ++
  "FROM benefit_events " ++
  "WHERE benefiting_team = ? AND qualifies = 1"

let proppedUpSeasonsSql =
  benefitEventsSql ++
  "SELECT season, COUNT(DISTINCT match_id) AS games " ++
  "FROM benefit_events " ++
  "WHERE benefiting_team = ? AND qualifies = 1 " ++
  "GROUP BY season " ++
  "ORDER BY season DESC"

let proppedUpMatchesBySeasonSql =
  benefitEventsSql ++
  "SELECT " ++
  "match_id AS id, season, matchday, home_team, away_team, home_score, away_score, " ++
  "MAX(has_penalty) AS has_penalty, " ++
  "MAX(has_red_card) AS has_red_card " ++
  "FROM benefit_events " ++
  "WHERE benefiting_team = ? AND qualifies = 1 AND season = ? " ++
  "GROUP BY match_id, season, matchday, home_team, away_team, home_score, away_score " ++
  "ORDER BY matchday DESC, id DESC"

let teamMatchSeasonsSql =
  "SELECT season, COUNT(*) AS games " ++
  "FROM matches " ++
  "WHERE home_team = ? OR away_team = ? " ++
  "GROUP BY season " ++
  "ORDER BY season DESC"

let teamMatchesBySeasonSql =
  "SELECT id, season, matchday, home_team, away_team, home_score, away_score " ++
  "FROM matches " ++
  "WHERE (home_team = ? OR away_team = ?) AND season = ? " ++
  "ORDER BY matchday DESC, id DESC"
