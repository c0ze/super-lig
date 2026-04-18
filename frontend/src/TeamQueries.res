let proppedUpGamesSql =
  "WITH benefit_events AS (" ++
  "SELECT " ++
  "e.match_id AS match_id, " ++
  "CASE " ++
  "WHEN e.event_type IN ('Penalty Goal', 'Missed Penalty') AND e.team = 'Home' THEN m.home_team " ++
  "WHEN e.event_type IN ('Penalty Goal', 'Missed Penalty') AND e.team = 'Away' THEN m.away_team " ++
  "WHEN e.event_type IN ('Red Card', 'Second Yellow Card') AND e.team = 'Home' THEN m.away_team " ++
  "WHEN e.event_type IN ('Red Card', 'Second Yellow Card') AND e.team = 'Away' THEN m.home_team " ++
  "ELSE '' END AS benefiting_team, " ++
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
  "SELECT COUNT(DISTINCT match_id) AS propped_up_games " ++
  "FROM benefit_events " ++
  "WHERE benefiting_team = ? AND qualifies = 1"
