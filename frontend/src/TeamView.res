type teamSummary = {
  matches: int,
  wins: int,
  draws: int,
  losses: int,
  goals_for: int,
  goals_against: int,
  seasons: int,
  yellow_cards: int,
  red_cards: int,
  penalties: int,
}

type teamEventSummary = {
  yellow_cards: int,
  red_cards: int,
  penalties: int,
}

type scorerRow = {
  player: string,
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

type state = {
  summary: option<teamSummary>,
  scorers: array<scorerRow>,
  matches: array<matchRow>,
}

let emptyState = {
  summary: None,
  scorers: [],
  matches: [],
}

let didTeamWin = (team, match) =>
  (match.home_team == team && match.home_score > match.away_score) ||
  (match.away_team == team && match.away_score > match.home_score)

let didTeamLose = (team, match) =>
  (match.home_team == team && match.home_score < match.away_score) ||
  (match.away_team == team && match.away_score < match.home_score)

@react.component
let make = (~team: string, ~language: Locale.t, ~navigate: Route.t => unit) => {
  let (state, setState) = React.useState(() => emptyState)

  React.useEffect1(() => {
    let summaries: array<teamSummary> = Database.runQuery(
      "SELECT COUNT(*) AS matches, " ++
      "SUM(CASE WHEN (home_team = ? AND home_score > away_score) OR (away_team = ? AND away_score > home_score) THEN 1 ELSE 0 END) AS wins, " ++
      "SUM(CASE WHEN home_score = away_score THEN 1 ELSE 0 END) AS draws, " ++
      "SUM(CASE WHEN (home_team = ? AND home_score < away_score) OR (away_team = ? AND away_score < home_score) THEN 1 ELSE 0 END) AS losses, " ++
      "SUM(CASE WHEN home_team = ? THEN home_score ELSE away_score END) AS goals_for, " ++
      "SUM(CASE WHEN home_team = ? THEN away_score ELSE home_score END) AS goals_against, " ++
      "COUNT(DISTINCT season) AS seasons " ++
      "FROM matches WHERE home_team = ? OR away_team = ?",
      [team, team, team, team, team, team, team, team],
    )
    let eventSummaries: array<teamEventSummary> = Database.runQuery(
      "SELECT " ++
      "COALESCE(SUM(CASE WHEN e.event_type = 'Yellow Card' THEN 1 ELSE 0 END), 0) AS yellow_cards, " ++
      "COALESCE(SUM(CASE WHEN e.event_type IN ('Red Card', 'Second Yellow Card') THEN 1 ELSE 0 END), 0) AS red_cards, " ++
      "COALESCE(SUM(CASE WHEN e.event_type = 'Penalty Goal' OR (e.event_type = 'Goal' AND COALESCE(e.player_1, '') != '' AND e.player_1 = e.player_2) THEN 1 ELSE 0 END), 0) AS penalties " ++
      "FROM events e JOIN matches m ON m.id = e.match_id " ++
      "WHERE (e.team = 'Home' AND m.home_team = ?) OR (e.team = 'Away' AND m.away_team = ?)",
      [team, team],
    )
    let scorers: array<scorerRow> = Database.runQuery(
      "SELECT e.player_1 AS player, COUNT(*) AS goals " ++
      "FROM events e JOIN matches m ON m.id = e.match_id " ++
      "WHERE e.event_type IN ('Goal', 'Penalty Goal') AND e.player_1 IS NOT NULL AND e.player_1 != '' " ++
      "AND ((e.team = 'Home' AND m.home_team = ?) OR (e.team = 'Away' AND m.away_team = ?)) " ++
      "GROUP BY e.player_1 ORDER BY goals DESC, e.player_1 ASC LIMIT 8",
      [team, team],
    )
    let matches: array<matchRow> = Database.runQuery(
      "SELECT id, season, matchday, home_team, away_team, home_score, away_score " ++
      "FROM matches WHERE home_team = ? OR away_team = ? " ++
      "ORDER BY season DESC, matchday DESC, home_team ASC",
      [team, team],
    )

    let summary =
      if Js.Array2.length(summaries) > 0 {
        let base = Js.Array2.unsafe_get(summaries, 0)
        let eventSummary =
          Js.Array2.length(eventSummaries) > 0
            ? Js.Array2.unsafe_get(eventSummaries, 0)
            : {yellow_cards: 0, red_cards: 0, penalties: 0}

        Some({
          matches: base.matches,
          wins: base.wins,
          draws: base.draws,
          losses: base.losses,
          goals_for: base.goals_for,
          goals_against: base.goals_against,
          seasons: base.seasons,
          yellow_cards: eventSummary.yellow_cards,
          red_cards: eventSummary.red_cards,
          penalties: eventSummary.penalties,
        })
      } else {
        None
      }

    setState(_ => {
      summary,
      scorers,
      matches,
    })

    None
  }, [team])

  let recentForm = state.matches->Array.filterWithIndex((_, index) => index < 5)

  <div className="team-page">
    <section className="page-hero compact">
      <div className="hero-copy">
        <button className="button-ghost" onClick={_ => navigate(Route.dashboard)}>
          {React.string(Copy.backHome(language))}
        </button>
        <div className="eyebrow">{React.string(Copy.teamHistoryTitle(language, team))}</div>
        <h1>{React.string(Copy.teamHistoryTitle(language, team))}</h1>
        <p>{React.string(Copy.teamSubtitle(language))}</p>
      </div>

      <div className="hero-highlight">
        <span className="hero-highlight-label">{React.string(Copy.recentFormTitle(language))}</span>
        <div className="form-strip">
          {React.array(recentForm->Array.map(match => {
            let didDraw = match.home_score == match.away_score
            let won = didTeamWin(team, match)
            let label = didDraw ? Copy.formDrawShort(language) : won ? Copy.formWonShort(language) : Copy.formLostShort(language)
            let className = didDraw ? "form-badge neutral" : won ? "form-badge positive" : "form-badge negative"

            <span key={match.id} className={className}>{React.string(label)}</span>
          }))}
        </div>
      </div>
    </section>

    {switch state.summary {
    | Some(summary) =>
      <section className="metric-strip">
        <article className="metric-card">
          <span className="metric-label">{React.string(Copy.matchesLabel(language))}</span>
          <strong>{React.int(summary.matches)}</strong>
        </article>
        <article className="metric-card">
          <span className="metric-label">{React.string(Copy.winsLabel(language))}</span>
          <strong>{React.int(summary.wins)}</strong>
        </article>
        <article className="metric-card">
          <span className="metric-label">{React.string(Copy.goalsForLabel(language))}</span>
          <strong>{React.int(summary.goals_for)}</strong>
        </article>
        <article className="metric-card">
          <span className="metric-label">{React.string(Copy.seasonsPlayedLabel(language))}</span>
          <strong>{React.int(summary.seasons)}</strong>
        </article>
        <article className="metric-card">
          <span className="metric-label">{React.string(Copy.yellowCardsLabel(language))}</span>
          <strong>{React.int(summary.yellow_cards)}</strong>
        </article>
        <article className="metric-card">
          <span className="metric-label">{React.string(Copy.redCardsLabel(language))}</span>
          <strong>{React.int(summary.red_cards)}</strong>
        </article>
        <article className="metric-card">
          <span className="metric-label">{React.string(Copy.penaltiesLabel(language))}</span>
          <strong>{React.int(summary.penalties)}</strong>
        </article>
      </section>
    | None => React.null
    }}

    <section className="dashboard-grid season-layout">
      <article className="section-card">
        <div className="section-heading">
          <h2>{React.string(Copy.allTimeRecordTitle(language))}</h2>
        </div>
        {switch state.summary {
        | Some(summary) =>
          <div className="record-grid">
            <div className="record-row">
              <span>{React.string(Copy.winsLabel(language))}</span>
              <strong>{React.int(summary.wins)}</strong>
            </div>
            <div className="record-row">
              <span>{React.string(Copy.drawsLabel(language))}</span>
              <strong>{React.int(summary.draws)}</strong>
            </div>
            <div className="record-row">
              <span>{React.string(Copy.lossesLabel(language))}</span>
              <strong>{React.int(summary.losses)}</strong>
            </div>
            <div className="record-row">
              <span>{React.string(Copy.goalsForLabel(language))}</span>
              <strong>{React.int(summary.goals_for)}</strong>
            </div>
            <div className="record-row">
              <span>{React.string(Copy.goalsAgainstLabel(language))}</span>
              <strong>{React.int(summary.goals_against)}</strong>
            </div>
            <div className="record-row">
              <span>{React.string(Copy.goalDifferenceLabel(language))}</span>
              <strong>{React.int(summary.goals_for - summary.goals_against)}</strong>
            </div>
            <div className="record-row">
              <span>{React.string(Copy.yellowCardsLabel(language))}</span>
              <strong>{React.int(summary.yellow_cards)}</strong>
            </div>
            <div className="record-row">
              <span>{React.string(Copy.redCardsLabel(language))}</span>
              <strong>{React.int(summary.red_cards)}</strong>
            </div>
            <div className="record-row">
              <span>{React.string(Copy.penaltiesLabel(language))}</span>
              <strong>{React.int(summary.penalties)}</strong>
            </div>
          </div>
        | None => <p>{React.string(Copy.noData(language))}</p>
        }}
      </article>

      <article className="section-card">
        <div className="section-heading">
          <h2>{React.string(Copy.clubTopScorersTitle(language))}</h2>
        </div>
        <div className="ranking-list">
          {React.array(state.scorers->Array.mapWithIndex((row, index) => {
            <div key={row.player} className="ranking-row">
              <div className="ranking-meta">
                <span className="ranking-index">{React.string("#" ++ Int.toString(index + 1))}</span>
                <div>
                  <strong>{React.string(row.player)}</strong>
                  <span>{React.string(team)}</span>
                </div>
              </div>
              <span className="ranking-value">{React.int(row.goals)}</span>
            </div>
          }))}
        </div>
      </article>

      <article className="section-card section-span-3">
        <div className="section-heading">
          <h2>{React.string(Copy.matchHistoryTitle(language))}</h2>
        </div>
        <div className="match-list">
          {React.array(state.matches->Array.map(match => {
            let didDraw = match.home_score == match.away_score
            let won = didTeamWin(team, match)
            let resultLabel = didDraw ? Copy.resultDraw(language) : won ? Copy.resultWon(language) : Copy.resultLost(language)
            let resultClass = didDraw ? "result-pill neutral" : won ? "result-pill positive" : "result-pill negative"

            <FixtureCard
              key={match.id}
              matchId={match.id}
              meta={SeasonLabel.format(match.season) ++ " • " ++ Copy.matchday(language, match.matchday)}
              homeTeam={match.home_team}
              awayTeam={match.away_team}
              homeScore={match.home_score}
              awayScore={match.away_score}
              language
              navigate
              resultLabel
              resultClassName={resultClass}
            />
          }))}
        </div>
      </article>
    </section>
  </div>
}
