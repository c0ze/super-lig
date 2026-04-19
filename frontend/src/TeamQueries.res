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

let varBenefitTeamCase =
  "CASE " ++
  "WHEN e.event_subtype = 'goalAwarded' AND e.event_detail = 'overturned' THEN CASE WHEN e.team = 'Home' THEN m.away_team ELSE m.home_team END " ++
  "WHEN e.event_subtype = 'goalAwarded' AND e.event_detail = 'confirmed' THEN CASE WHEN e.team = 'Home' THEN m.home_team ELSE m.away_team END " ++
  "WHEN e.event_subtype = 'goalNotAwarded' AND e.event_detail = 'overturned' THEN CASE WHEN e.team = 'Home' THEN m.home_team ELSE m.away_team END " ++
  "WHEN e.event_subtype = 'goalNotAwarded' AND e.event_detail = 'confirmed' THEN CASE WHEN e.team = 'Home' THEN m.away_team ELSE m.home_team END " ++
  "WHEN e.event_subtype = 'penaltyAwarded' AND e.event_detail = 'overturned' THEN CASE WHEN e.team = 'Home' THEN m.away_team ELSE m.home_team END " ++
  "WHEN e.event_subtype = 'penaltyAwarded' AND e.event_detail = 'confirmed' THEN CASE WHEN e.team = 'Home' THEN m.home_team ELSE m.away_team END " ++
  "WHEN e.event_subtype = 'penaltyNotAwarded' AND e.event_detail = 'overturned' THEN CASE WHEN e.team = 'Home' THEN m.home_team ELSE m.away_team END " ++
  "WHEN e.event_subtype = 'penaltyNotAwarded' AND e.event_detail = 'confirmed' THEN CASE WHEN e.team = 'Home' THEN m.away_team ELSE m.home_team END " ++
  "WHEN e.event_subtype = 'cardUpgrade' AND e.event_detail = 'confirmed' THEN CASE WHEN e.team = 'Home' THEN m.away_team ELSE m.home_team END " ++
  "WHEN e.event_subtype = 'cardUpgrade' AND e.event_detail = 'overturned' THEN CASE WHEN e.team = 'Home' THEN m.home_team ELSE m.away_team END " ++
  "WHEN e.event_subtype = 'redCardGiven' AND e.event_detail = 'confirmed' THEN CASE WHEN e.team = 'Home' THEN m.away_team ELSE m.home_team END " ++
  "WHEN e.event_subtype = 'redCardGiven' AND e.event_detail = 'overturned' THEN CASE WHEN e.team = 'Home' THEN m.home_team ELSE m.away_team END " ++
  "ELSE '' END"

let varBenefitEventsSql =
  "WITH raw_var_events AS (" ++
  "SELECT " ++
  "e.match_id AS match_id, " ++
  "m.season AS season, " ++
  "m.matchday AS matchday, " ++
  "m.home_team AS home_team, " ++
  "m.away_team AS away_team, " ++
  "m.home_score AS home_score, " ++
  "m.away_score AS away_score, " ++
  "e.home_score_before AS home_score_before, " ++
  "e.away_score_before AS away_score_before, " ++
  varBenefitTeamCase ++ " AS benefiting_team, " ++
  "CASE WHEN e.event_subtype IN ('goalAwarded', 'goalNotAwarded') THEN 1 ELSE 0 END AS has_goal_swing, " ++
  "CASE WHEN e.event_subtype IN ('penaltyAwarded', 'penaltyNotAwarded') THEN 1 ELSE 0 END AS has_penalty_swing, " ++
  "CASE WHEN e.event_subtype IN ('cardUpgrade', 'redCardGiven') THEN 1 ELSE 0 END AS has_red_card_swing " ++
  "FROM events e " ++
  "JOIN matches m ON m.id = e.match_id " ++
  "WHERE e.event_type = 'VAR Decision' " ++
  "AND e.home_score_before IS NOT NULL " ++
  "AND e.away_score_before IS NOT NULL" ++
  "), var_benefit_events AS (" ++
  "SELECT *, " ++
  "CASE " ++
  "WHEN benefiting_team = home_team THEN CASE WHEN home_score_before <= away_score_before THEN 1 ELSE 0 END " ++
  "WHEN benefiting_team = away_team THEN CASE WHEN away_score_before <= home_score_before THEN 1 ELSE 0 END " ++
  "ELSE 0 END AS qualifies, " ++
  "CASE " ++
  "WHEN benefiting_team = home_team THEN CASE WHEN home_score = away_score + 1 THEN 1 ELSE 0 END " ++
  "WHEN benefiting_team = away_team THEN CASE WHEN away_score = home_score + 1 THEN 1 ELSE 0 END " ++
  "ELSE 0 END AS one_goal_win " ++
  "FROM raw_var_events" ++
  ") " ++
  ""

let varSwingWinsSql =
  varBenefitEventsSql ++
  "SELECT COUNT(DISTINCT match_id) AS var_swing_wins " ++
  "FROM var_benefit_events " ++
  "WHERE benefiting_team = ? AND qualifies = 1 AND one_goal_win = 1"

let varSwingWinSeasonsSql =
  varBenefitEventsSql ++
  "SELECT season, COUNT(DISTINCT match_id) AS games " ++
  "FROM var_benefit_events " ++
  "WHERE benefiting_team = ? AND qualifies = 1 AND one_goal_win = 1 " ++
  "GROUP BY season " ++
  "ORDER BY season DESC"

let varSwingWinMatchesBySeasonSql =
  varBenefitEventsSql ++
  "SELECT " ++
  "match_id AS id, season, matchday, home_team, away_team, home_score, away_score, " ++
  "MAX(has_goal_swing) AS has_goal_swing, " ++
  "MAX(has_penalty_swing) AS has_penalty_swing, " ++
  "MAX(has_red_card_swing) AS has_red_card_swing " ++
  "FROM var_benefit_events " ++
  "WHERE benefiting_team = ? AND qualifies = 1 AND one_goal_win = 1 AND season = ? " ++
  "GROUP BY match_id, season, matchday, home_team, away_team, home_score, away_score " ++
  "ORDER BY matchday DESC, id DESC"

let teamMatchSeasonsSql =
  "SELECT season, COUNT(*) AS games " ++
  "FROM matches " ++
  "WHERE home_team = ? OR away_team = ? " ++
  "GROUP BY season " ++
  "ORDER BY season DESC"

let teamTopAssistersSql =
  "SELECT e.player_2 AS player, COUNT(*) AS assists " ++
  "FROM events e JOIN matches m ON m.id = e.match_id " ++
  "WHERE e.event_type IN ('Goal', 'Penalty Goal') " ++
  "AND e.player_2 IS NOT NULL AND e.player_2 != '' " ++
  "AND COALESCE(e.player_1, '') != COALESCE(e.player_2, '') " ++
  "AND ((e.team = 'Home' AND m.home_team = ?) OR (e.team = 'Away' AND m.away_team = ?)) " ++
  "GROUP BY e.player_2 ORDER BY assists DESC, e.player_2 ASC LIMIT 8"

let teamMatchesBySeasonSql =
  "SELECT id, season, matchday, home_team, away_team, home_score, away_score " ++
  "FROM matches " ++
  "WHERE (home_team = ? OR away_team = ?) AND season = ? " ++
  "ORDER BY matchday DESC, id DESC"
