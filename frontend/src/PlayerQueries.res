let deniedGoalCondition =
  "e.event_type = 'VAR Decision' AND e.event_subtype = 'goalAwarded' AND e.event_detail = 'overturned'"

let goalCondition =
  "e.event_type IN ('Goal', 'Penalty Goal') AND COALESCE(e.player_1, '') = ?"

let assistCondition =
  "e.event_type IN ('Goal', 'Penalty Goal') AND COALESCE(e.player_2, '') = ? " ++
  "AND COALESCE(e.player_1, '') != COALESCE(e.player_2, '')"

let deniedGoalPlayerCondition = deniedGoalCondition ++ " AND COALESCE(e.player_1, '') = ?"

let deniedAssistPlayerCondition =
  deniedGoalCondition ++ " AND COALESCE(e.player_2, '') = ? " ++
  "AND COALESCE(e.player_1, '') != COALESCE(e.player_2, '')"

let trackedContributionCondition =
  "(" ++
  "(" ++ goalCondition ++ ") " ++
  "OR (" ++ assistCondition ++ ") " ++
  "OR (" ++ deniedGoalPlayerCondition ++ ") " ++
  "OR (" ++ deniedAssistPlayerCondition ++ ")" ++
  ")"

let playerEventsCte =
  "WITH player_events AS (" ++
  "SELECT " ++
  "m.id AS id, " ++
  "m.season AS season, " ++
  "m.matchday AS matchday, " ++
  "m.home_team AS home_team, " ++
  "m.away_team AS away_team, " ++
  "m.home_score AS home_score, " ++
  "m.away_score AS away_score, " ++
  "CASE " ++
  "WHEN e.team = 'Home' THEN m.home_team " ++
  "WHEN e.team = 'Away' THEN m.away_team " ++
  "ELSE '' END AS team_name, " ++
  "CASE WHEN " ++ goalCondition ++ " THEN 1 ELSE 0 END AS goals, " ++
  "CASE WHEN " ++ assistCondition ++ " THEN 1 ELSE 0 END AS assists, " ++
  "CASE WHEN " ++ deniedGoalPlayerCondition ++ " THEN 1 ELSE 0 END AS var_denied_goals, " ++
  "CASE WHEN " ++ deniedAssistPlayerCondition ++ " THEN 1 ELSE 0 END AS var_denied_assists " ++
  "FROM events e " ++
  "JOIN matches m ON m.id = e.match_id " ++
  "WHERE " ++ trackedContributionCondition ++
  ") "

let playerSummarySql =
  playerEventsCte ++
  "SELECT " ++
  "COUNT(DISTINCT id) AS matches, " ++
  "COUNT(DISTINCT season) AS seasons, " ++
  "COUNT(DISTINCT CASE WHEN team_name != '' THEN team_name END) AS clubs, " ++
  "COALESCE(SUM(goals), 0) AS goals, " ++
  "COALESCE(SUM(assists), 0) AS assists, " ++
  "COALESCE(SUM(var_denied_goals), 0) AS var_denied_goals, " ++
  "COALESCE(SUM(var_denied_assists), 0) AS var_denied_assists " ++
  "FROM player_events"

let playerMatchSeasonsSql =
  playerEventsCte ++
  "SELECT season, COUNT(DISTINCT id) AS games " ++
  "FROM player_events " ++
  "GROUP BY season " ++
  "ORDER BY season DESC"

let playerMatchesBySeasonSql =
  playerEventsCte ++
  "SELECT " ++
  "id, season, matchday, home_team, away_team, home_score, away_score, " ++
  "COALESCE(MAX(team_name), '') AS team_name, " ++
  "COALESCE(SUM(goals), 0) AS goals, " ++
  "COALESCE(SUM(assists), 0) AS assists, " ++
  "COALESCE(SUM(var_denied_goals), 0) AS var_denied_goals, " ++
  "COALESCE(SUM(var_denied_assists), 0) AS var_denied_assists " ++
  "FROM player_events " ++
  "WHERE season = ? " ++
  "GROUP BY id, season, matchday, home_team, away_team, home_score, away_score " ++
  "ORDER BY matchday DESC, id DESC"
