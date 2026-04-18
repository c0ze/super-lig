type overview = {
  seasons: int,
  matches: int,
  goals: int,
  events: int,
  latest_season: string,
}

type seasonCard = {
  season: string,
  match_count: int,
  goals: int,
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
  season: string,
  matchday: int,
  home_team: string,
  away_team: string,
  home_score: int,
  away_score: int,
}

type eventRow = {
  event_type: string,
  count: int,
}

type state = {
  overview: option<overview>,
  seasonCards: array<seasonCard>,
  latestStandings: array<standingRow>,
  topScorers: array<scorerRow>,
  recentMatches: array<matchRow>,
  eventBreakdown: array<eventRow>,
}

let emptyState = {
  overview: None,
  seasonCards: [],
  latestStandings: [],
  topScorers: [],
  recentMatches: [],
  eventBreakdown: [],
}

@react.component
let make = (~language: Locale.t, ~latestSeason: string, ~navigate: Route.t => unit) => {
  let (state, setState) = React.useState(() => emptyState)

  React.useEffect0(() => {
    let rawOverview = Database.runQuery(
      "SELECT COUNT(DISTINCT season) AS seasons, COUNT(*) AS matches, " ++
      "SUM(home_score + away_score) AS goals, " ++
      "(SELECT COUNT(*) FROM events) AS events, " ++
      "(SELECT MAX(season) FROM matches) AS latest_season " ++
      "FROM matches",
      [],
    )
    let rawSeasonCards = Database.runQuery(
      "SELECT season, COUNT(*) AS match_count, SUM(home_score + away_score) AS goals, " ++
      "printf('%.2f', 1.0 * SUM(home_score + away_score) / COUNT(*)) AS goals_per_match " ++
      "FROM matches GROUP BY season ORDER BY season DESC",
      [],
    )
    let rawStandings = Database.runQuery(
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
      "FROM matches WHERE season = (SELECT MAX(season) FROM matches) " ++
      "UNION ALL " ++
      "SELECT away_team AS team, 1 AS played, " ++
      "CASE WHEN away_score > home_score THEN 1 ELSE 0 END AS wins, " ++
      "CASE WHEN away_score = home_score THEN 1 ELSE 0 END AS draws, " ++
      "CASE WHEN away_score < home_score THEN 1 ELSE 0 END AS losses, " ++
      "away_score AS goals_for, home_score AS goals_against, " ++
      "CASE WHEN away_score > home_score THEN 3 WHEN away_score = home_score THEN 1 ELSE 0 END AS points " ++
      "FROM matches WHERE season = (SELECT MAX(season) FROM matches)" ++
      ") GROUP BY team ORDER BY points DESC, goal_diff DESC, goals_for DESC, team ASC",
      [],
    )
    let rawTopScorers = Database.runQuery(
      "SELECT e.player_1 AS player, " ++
      "CASE WHEN e.team = 'Home' THEN m.home_team WHEN e.team = 'Away' THEN m.away_team ELSE e.team END AS team_name, " ++
      "COUNT(*) AS goals " ++
      "FROM events e JOIN matches m ON m.id = e.match_id " ++
      "WHERE e.event_type IN ('Goal', 'Penalty Goal') AND e.player_1 IS NOT NULL AND e.player_1 != '' " ++
      "GROUP BY e.player_1, team_name ORDER BY goals DESC, e.player_1 ASC LIMIT 8",
      [],
    )
    let rawRecentMatches = Database.runQuery(
      "SELECT id, season, matchday, home_team, away_team, home_score, away_score " ++
      "FROM matches WHERE season = (SELECT MAX(season) FROM matches) " ++
      "ORDER BY matchday DESC, home_team ASC LIMIT 6",
      [],
    )
    let rawEventBreakdown = Database.runQuery(
      "SELECT event_type, COUNT(*) AS count FROM events " ++
      "GROUP BY event_type ORDER BY count DESC LIMIT 5",
      [],
    )

    let overviews: array<overview> = Obj.magic(rawOverview)
    let seasonCards: array<seasonCard> = Obj.magic(rawSeasonCards)
    let latestStandings: array<standingRow> = Obj.magic(rawStandings)
    let topScorers: array<scorerRow> = Obj.magic(rawTopScorers)
    let recentMatches: array<matchRow> = Obj.magic(rawRecentMatches)
    let eventBreakdown: array<eventRow> = Obj.magic(rawEventBreakdown)

    setState(_ => {
      overview: Js.Array2.length(overviews) > 0 ? Some(Js.Array2.unsafe_get(overviews, 0)) : None,
      seasonCards,
      latestStandings,
      topScorers,
      recentMatches,
      eventBreakdown,
    })

    None
  })

  let leader =
    Js.Array2.length(state.latestStandings) > 0
      ? Some(Js.Array2.unsafe_get(state.latestStandings, 0))
      : None

  <div className="dashboard-view">
    <section className="page-hero">
      <div className="hero-copy">
        <div className="eyebrow">{React.string(Copy.dashboardEyebrow(language))}</div>
        <h1>{React.string(Copy.dashboardTitle(language))}</h1>
        <p>{React.string(Copy.dashboardSubtitle(language))}</p>
        <div className="hero-actions">
          <button className="button-primary" onClick={_ => navigate(Route.season(latestSeason))}>
            {React.string(Copy.jumpToLatestSeason(language))}
          </button>
          <button className="button-secondary" onClick={_ => Browser.scrollToId("season-archive")}>
            {React.string(Copy.browseArchive(language))}
          </button>
        </div>
      </div>

      <div className="hero-highlight">
        <span className="hero-highlight-label">
          {React.string(Copy.latestSeasonStandingsTitle(language, latestSeason))}
        </span>
        {switch leader {
        | Some(row) =>
          <>
            <strong>{React.string(row.team)}</strong>
            <p>
              {React.string(
                Int.toString(row.points) ++ " " ++ Copy.pointsLabel(language) ++ " • " ++
                Int.toString(row.wins) ++ "-" ++ Int.toString(row.draws) ++ "-" ++ Int.toString(row.losses),
              )}
            </p>
          </>
        | None => <p>{React.string(Copy.noData(language))}</p>
        }}
      </div>
    </section>

    {switch state.overview {
    | Some(overview) =>
      <section className="metric-strip">
        <article className="metric-card">
          <span className="metric-label">{React.string(Copy.seasonsLabel(language))}</span>
          <strong>{React.int(overview.seasons)}</strong>
        </article>
        <article className="metric-card">
          <span className="metric-label">{React.string(Copy.matchesLabel(language))}</span>
          <strong>{React.int(overview.matches)}</strong>
        </article>
        <article className="metric-card">
          <span className="metric-label">{React.string(Copy.goalsLabel(language))}</span>
          <strong>{React.int(overview.goals)}</strong>
        </article>
        <article className="metric-card">
          <span className="metric-label">{React.string(Copy.eventsLabel(language))}</span>
          <strong>{React.int(overview.events)}</strong>
        </article>
      </section>
    | None => React.null
    }}

    <section className="dashboard-grid">
      <article className="section-card section-span-2">
        <div className="section-heading">
          <h2>{React.string(Copy.latestSeasonStandingsTitle(language, latestSeason))}</h2>
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
                <th>{React.string(Copy.goalDifferenceLabel(language))}</th>
                <th>{React.string(Copy.pointsLabel(language))}</th>
              </tr>
            </thead>
            <tbody>
              {React.array(state.latestStandings->Array.mapWithIndex((row, index) => {
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
                  <td>{React.int(row.goal_diff)}</td>
                  <td className="points-cell">{React.int(row.points)}</td>
                </tr>
              }))}
            </tbody>
          </table>
        </div>
      </article>

      <div className="section-stack">
        <article className="section-card">
          <div className="section-heading">
            <h2>{React.string(Copy.topScorersTitle(language))}</h2>
          </div>
          <div className="ranking-list">
            {React.array(state.topScorers->Array.mapWithIndex((row, index) => {
              <div key={row.player ++ row.team_name} className="ranking-row">
                <div className="ranking-meta">
                  <span className="ranking-index">{React.string("#" ++ Int.toString(index + 1))}</span>
                  <div>
                    <strong>{React.string(row.player)}</strong>
                    <span>{React.string(row.team_name)}</span>
                  </div>
                </div>
                <span className="ranking-value">{React.int(row.goals)}</span>
              </div>
            }))}
          </div>
        </article>

        <article className="section-card">
          <div className="section-heading">
            <h2>{React.string(Copy.eventDistributionTitle(language))}</h2>
          </div>
          <div className="event-list">
            {React.array(state.eventBreakdown->Array.map(row => {
              <div key={row.event_type} className="event-row">
                <span>{React.string(Copy.eventType(language, row.event_type))}</span>
                <strong>{React.int(row.count)}</strong>
              </div>
            }))}
          </div>
        </article>
      </div>

      <article id="season-archive" className="section-card section-span-2">
        <div className="section-heading">
          <h2>{React.string(Copy.seasonArchiveTitle(language))}</h2>
        </div>
        <div className="season-card-grid">
          {React.array(state.seasonCards->Array.map(card => {
            <button
              key={card.season}
              className="season-card"
              onClick={_ => navigate(Route.season(card.season))}>
              <span className="season-card-kicker">{React.string(Copy.seasonTitle(language, card.season))}</span>
              <strong>{React.string(SeasonLabel.format(card.season))}</strong>
              <div className="season-card-stats">
                <div>
                  <span>{React.string(Copy.matchesLabel(language))}</span>
                  <strong>{React.int(card.match_count)}</strong>
                </div>
                <div>
                  <span>{React.string(Copy.goalsLabel(language))}</span>
                  <strong>{React.int(card.goals)}</strong>
                </div>
                <div>
                  <span>{React.string(Copy.goalsPerMatchLabel(language))}</span>
                  <strong>{React.string(card.goals_per_match)}</strong>
                </div>
              </div>
            </button>
          }))}
        </div>
      </article>

      <article className="section-card">
        <div className="section-heading">
          <h2>{React.string(Copy.recentMatchesTitle(language, latestSeason))}</h2>
        </div>
        <div className="match-list">
          {React.array(state.recentMatches->Array.map(match => {
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
