type seasonSummary = {
  matches: int,
  goals: int,
  teams: int,
  max_matchday: int,
  goals_per_match: string,
}

type standingRow = {
  team: string,
  played: int,
  wins: int,
  draws: int,
  losses: int,
  goals_for: int,
  goals_against: int,
  goal_diff: int,
  points: int,
}

type scorerRow = {
  player: string,
  team_name: string,
  goals: int,
}

type matchRow = {
  id: string,
  date: string,
  matchday: int,
  home_team: string,
  away_team: string,
  home_score: int,
  away_score: int,
}

type state = {
  summary: option<seasonSummary>,
  standings: array<standingRow>,
  scorers: array<scorerRow>,
  matches: array<matchRow>,
}

let emptyState = {
  summary: None,
  standings: [],
  scorers: [],
  matches: [],
}

@react.component
let make = (~year: string, ~language: Locale.t, ~navigate: Route.t => unit) => {
  let (state, setState) = React.useState(() => emptyState)

  React.useEffect1(() => {
    let summaries: array<seasonSummary> = Database.runQuery(
      "SELECT COUNT(*) AS matches, SUM(home_score + away_score) AS goals, " ++
      "COUNT(DISTINCT home_team) AS teams, MAX(matchday) AS max_matchday, " ++
      "printf('%.2f', 1.0 * SUM(home_score + away_score) / COUNT(*)) AS goals_per_match " ++
      "FROM matches WHERE season = ?",
      [year],
    )
    let standings: array<standingRow> = Database.runQuery(
      "SELECT team, SUM(played) AS played, SUM(wins) AS wins, SUM(draws) AS draws, " ++
      "SUM(losses) AS losses, SUM(goals_for) AS goals_for, SUM(goals_against) AS goals_against, " ++
      "SUM(goals_for) - SUM(goals_against) AS goal_diff, SUM(points) AS points " ++
      "FROM (" ++
      "SELECT home_team AS team, 1 AS played, " ++
      "CASE WHEN home_score > away_score THEN 1 ELSE 0 END AS wins, " ++
      "CASE WHEN home_score = away_score THEN 1 ELSE 0 END AS draws, " ++
      "CASE WHEN home_score < away_score THEN 1 ELSE 0 END AS losses, " ++
      "home_score AS goals_for, away_score AS goals_against, " ++
      "CASE WHEN home_score > away_score THEN 3 WHEN home_score = away_score THEN 1 ELSE 0 END AS points " ++
      "FROM matches WHERE season = ? " ++
      "UNION ALL " ++
      "SELECT away_team AS team, 1 AS played, " ++
      "CASE WHEN away_score > home_score THEN 1 ELSE 0 END AS wins, " ++
      "CASE WHEN away_score = home_score THEN 1 ELSE 0 END AS draws, " ++
      "CASE WHEN away_score < home_score THEN 1 ELSE 0 END AS losses, " ++
      "away_score AS goals_for, home_score AS goals_against, " ++
      "CASE WHEN away_score > home_score THEN 3 WHEN away_score = home_score THEN 1 ELSE 0 END AS points " ++
      "FROM matches WHERE season = ? " ++
      ") GROUP BY team ORDER BY points DESC, goal_diff DESC, goals_for DESC, team ASC",
      [year, year],
    )
    let scorers: array<scorerRow> = Database.runQuery(
      "SELECT e.player_1 AS player, " ++
      "CASE WHEN e.team = 'Home' THEN m.home_team WHEN e.team = 'Away' THEN m.away_team ELSE e.team END AS team_name, " ++
      "COUNT(*) AS goals " ++
      "FROM events e JOIN matches m ON m.id = e.match_id " ++
      "WHERE e.event_type IN ('Goal', 'Penalty Goal') AND e.player_1 IS NOT NULL AND e.player_1 != '' AND m.season = ? " ++
      "GROUP BY e.player_1, team_name ORDER BY goals DESC, e.player_1 ASC LIMIT 8",
      [year],
    )
    let matches: array<matchRow> = Database.runQuery(
      "SELECT id, date, matchday, home_team, away_team, home_score, away_score " ++
      "FROM matches WHERE season = ? ORDER BY matchday DESC, home_team ASC",
      [year],
    )

    setState(_ => {
      summary: Js.Array2.length(summaries) > 0 ? Some(Js.Array2.unsafe_get(summaries, 0)) : None,
      standings,
      scorers,
      matches,
    })

    None
  }, [year])

  let leader =
    Js.Array2.length(state.standings) > 0 ? Some(Js.Array2.unsafe_get(state.standings, 0)) : None

  <div className="season-page">
    <section className="page-hero compact">
      <div className="hero-copy">
        <button className="button-ghost" onClick={_ => navigate(Route.dashboard)}>
          {React.string(Copy.backHome(language))}
        </button>
        <div className="eyebrow">{React.string(Copy.seasonTitle(language, year))}</div>
        <h1>{React.string(Copy.seasonTitle(language, year))}</h1>
        <p>{React.string(Copy.seasonSubtitle(language))}</p>
      </div>

      <div className="hero-highlight">
        <span className="hero-highlight-label">{React.string(Copy.standingsTitle(language))}</span>
        {switch leader {
        | Some(row) =>
          <>
            <strong>{React.string(row.team)}</strong>
            <p>{React.string(Int.toString(row.points) ++ " " ++ Copy.pointsLabel(language))}</p>
          </>
        | None => <p>{React.string(Copy.noData(language))}</p>
        }}
      </div>
    </section>

    {switch state.summary {
    | Some(summary) =>
      <section className="metric-strip">
        <article className="metric-card">
          <span className="metric-label">{React.string(Copy.teamsLabel(language))}</span>
          <strong>{React.int(summary.teams)}</strong>
        </article>
        <article className="metric-card">
          <span className="metric-label">{React.string(Copy.matchesLabel(language))}</span>
          <strong>{React.int(summary.matches)}</strong>
        </article>
        <article className="metric-card">
          <span className="metric-label">{React.string(Copy.matchdaysLabel(language))}</span>
          <strong>{React.int(summary.max_matchday)}</strong>
        </article>
        <article className="metric-card">
          <span className="metric-label">{React.string(Copy.goalsPerMatchLabel(language))}</span>
          <strong>{React.string(summary.goals_per_match)}</strong>
        </article>
      </section>
    | None => React.null
    }}

    <section className="dashboard-grid season-layout">
      <article className="section-card section-span-2">
        <div className="section-heading">
          <h2>{React.string(Copy.standingsTitle(language))}</h2>
        </div>
        <div className="table-shell">
          <table className="standings-table">
            <thead>
              <tr>
                <th>{React.string(Copy.positionLabel(language))}</th>
                <th>{React.string(Copy.clubLabel(language))}</th>
                <th>{React.string(Copy.playedLabel(language))}</th>
                <th>{React.string(Copy.winsLabel(language))}</th>
                <th>{React.string(Copy.drawsLabel(language))}</th>
                <th>{React.string(Copy.lossesLabel(language))}</th>
                <th>{React.string(Copy.goalsForLabel(language))}</th>
                <th>{React.string(Copy.goalsAgainstLabel(language))}</th>
                <th>{React.string(Copy.goalDifferenceLabel(language))}</th>
                <th>{React.string(Copy.pointsLabel(language))}</th>
              </tr>
            </thead>
            <tbody>
              {React.array(state.standings->Array.mapWithIndex((row, index) => {
                <tr key={row.team}>
                  <td>{React.int(index + 1)}</td>
                  <td>
                    <button className="table-team-button" onClick={_ => navigate(Route.team(row.team))}>
                      {React.string(row.team)}
                    </button>
                  </td>
                  <td>{React.int(row.played)}</td>
                  <td>{React.int(row.wins)}</td>
                  <td>{React.int(row.draws)}</td>
                  <td>{React.int(row.losses)}</td>
                  <td>{React.int(row.goals_for)}</td>
                  <td>{React.int(row.goals_against)}</td>
                  <td>{React.int(row.goal_diff)}</td>
                  <td className="points-cell">{React.int(row.points)}</td>
                </tr>
              }))}
            </tbody>
          </table>
        </div>
      </article>

      <article className="section-card">
        <div className="section-heading">
          <h2>{React.string(Copy.seasonTopScorersTitle(language))}</h2>
        </div>
        <div className="ranking-list">
          {React.array(state.scorers->Array.mapWithIndex((row, index) => {
            <div key={row.player ++ row.team_name} className="ranking-row">
              <div className="ranking-meta">
                <span className="ranking-index">{React.string("#" ++ Int.toString(index + 1))}</span>
                <div>
                  <strong>
                    <button className="player-link-button" onClick={_ => navigate(Route.player(row.player))}>
                      {React.string(row.player)}
                    </button>
                  </strong>
                  <span>{React.string(row.team_name)}</span>
                </div>
              </div>
              <span className="ranking-value">{React.int(row.goals)}</span>
            </div>
          }))}
        </div>
      </article>

      <article className="section-card section-span-3">
        <div className="section-heading">
          <h2>{React.string(Copy.matchListTitle(language))}</h2>
        </div>
        <div className="match-list">
          {React.array(state.matches->Array.map(match => {
            <FixtureCard
              key={match.id}
              matchId={match.id}
              meta={Copy.matchday(language, match.matchday)}
              homeTeam={match.home_team}
              awayTeam={match.away_team}
              homeScore={match.home_score}
              awayScore={match.away_score}
              language
              navigate
            />
          }))}
        </div>
      </article>
    </section>
  </div>
}
