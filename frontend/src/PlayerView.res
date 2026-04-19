type playerSummary = {
  matches: int,
  seasons: int,
  clubs: int,
  goals: int,
  assists: int,
  var_denied_goals: int,
  var_denied_assists: int,
}

type seasonRow = {
  season: string,
  games: int,
}

type matchRow = {
  id: string,
  season: string,
  matchday: int,
  home_team: string,
  away_team: string,
  home_score: int,
  away_score: int,
  team_name: string,
  goals: int,
  assists: int,
  var_denied_goals: int,
  var_denied_assists: int,
}

type state = {
  summary: option<playerSummary>,
  seasons: array<seasonRow>,
  matches: array<matchRow>,
}

let emptyState = {
  summary: None,
  seasons: [],
  matches: [],
}

let playerParams = player => [player, player, player, player, player, player, player, player]

let didPlayerTeamWin = match =>
  (match.team_name == match.home_team && match.home_score > match.away_score) ||
  (match.team_name == match.away_team && match.away_score > match.home_score)

@react.component
let make = (~player: string, ~language: Locale.t, ~navigate: Route.t => unit) => {
  let (state, setState) = React.useState(() => emptyState)
  let (selectedSeason, setSelectedSeason) = React.useState(() => "")

  React.useEffect1(() => {
    let params = player->playerParams
    let summaries: array<playerSummary> = Database.runQuery(PlayerQueries.playerSummarySql, params)
    let seasons: array<seasonRow> = Database.runQuery(PlayerQueries.playerMatchSeasonsSql, params)
    let defaultSeason =
      Js.Array2.length(seasons) > 0 ? Js.Array2.unsafe_get(seasons, 0).season : ""
    let summary =
      if Js.Array2.length(summaries) > 0 {
        let row = Js.Array2.unsafe_get(summaries, 0)
        row.matches > 0 ? Some(row) : None
      } else {
        None
      }

    setState(_ => {
      summary,
      seasons,
      matches: [],
    })
    setSelectedSeason(_ => defaultSeason)

    None
  }, [player])

  React.useEffect2(() => {
    let matches: array<matchRow> =
      if selectedSeason == "" {
        []
      } else {
        Database.runQuery(
          PlayerQueries.playerMatchesBySeasonSql,
          [player, player, player, player, player, player, player, player, selectedSeason],
        )
      }

    setState(current => {
      ...current,
      matches,
    })

    None
  }, (player, selectedSeason))

  <div className="player-page">
    {switch state.summary {
    | None =>
      <section className="page-hero compact">
        <div className="hero-copy">
          <button className="button-ghost" onClick={_ => navigate(Route.dashboard)}>
            {React.string(Copy.backHome(language))}
          </button>
          <div className="eyebrow">{React.string(Copy.playerLabel(language))}</div>
          <h1>{React.string(Copy.playerArchiveTitle(language, player))}</h1>
          <p>{React.string(Copy.noData(language))}</p>
        </div>
      </section>
    | Some(summary) =>
      <>
        <section className="page-hero compact">
          <div className="hero-copy">
            <button className="button-ghost" onClick={_ => navigate(Route.dashboard)}>
              {React.string(Copy.backHome(language))}
            </button>
            <div className="eyebrow">{React.string(Copy.playerLabel(language))}</div>
            <h1>{React.string(Copy.playerArchiveTitle(language, player))}</h1>
            <p>{React.string(Copy.playerSubtitle(language))}</p>
          </div>

          <div className="hero-highlight">
            <span className="hero-highlight-label">{React.string(Copy.goalInvolvementsLabel(language))}</span>
            <strong>{React.int(summary.goals + summary.assists)}</strong>
            <p>
              {React.string(
                Copy.goalCountText(language, summary.goals) ++ " • " ++
                Copy.assistCountText(language, summary.assists),
              )}
            </p>
          </div>
        </section>

        <section className="metric-strip">
          <article className="metric-card">
            <span className="metric-label">{React.string(Copy.matchesLabel(language))}</span>
            <strong>{React.int(summary.matches)}</strong>
          </article>
          <article className="metric-card">
            <span className="metric-label">{React.string(Copy.goalsLabel(language))}</span>
            <strong>{React.int(summary.goals)}</strong>
          </article>
          <article className="metric-card">
            <span className="metric-label">{React.string(Copy.assistsLabel(language))}</span>
            <strong>{React.int(summary.assists)}</strong>
          </article>
          <article className="metric-card">
            <span className="metric-label">{React.string(Copy.varDeniedGoalsLabel(language))}</span>
            <strong>{React.int(summary.var_denied_goals)}</strong>
          </article>
          <article className="metric-card">
            <span className="metric-label">{React.string(Copy.varDeniedAssistsLabel(language))}</span>
            <strong>{React.int(summary.var_denied_assists)}</strong>
          </article>
          <article className="metric-card">
            <span className="metric-label">{React.string(Copy.seasonsLabel(language))}</span>
            <strong>{React.int(summary.seasons)}</strong>
          </article>
        </section>

        <section className="dashboard-grid season-layout">
          <article className="section-card">
            <div className="section-heading">
              <h2>{React.string(Copy.allTimeRecordTitle(language))}</h2>
            </div>
            <div className="record-grid">
              <div className="record-row">
                <span>{React.string(Copy.matchesLabel(language))}</span>
                <strong>{React.int(summary.matches)}</strong>
              </div>
              <div className="record-row">
                <span>{React.string(Copy.goalsLabel(language))}</span>
                <strong>{React.int(summary.goals)}</strong>
              </div>
              <div className="record-row">
                <span>{React.string(Copy.assistsLabel(language))}</span>
                <strong>{React.int(summary.assists)}</strong>
              </div>
              <div className="record-row">
                <span>{React.string(Copy.goalInvolvementsLabel(language))}</span>
                <strong>{React.int(summary.goals + summary.assists)}</strong>
              </div>
              <div className="record-row">
                <span>{React.string(Copy.varDeniedGoalsLabel(language))}</span>
                <strong>{React.int(summary.var_denied_goals)}</strong>
              </div>
              <div className="record-row">
                <span>{React.string(Copy.varDeniedAssistsLabel(language))}</span>
                <strong>{React.int(summary.var_denied_assists)}</strong>
              </div>
              <div className="record-row">
                <span>{React.string(Copy.clubsLabel(language))}</span>
                <strong>{React.int(summary.clubs)}</strong>
              </div>
              <div className="record-row">
                <span>{React.string(Copy.seasonsLabel(language))}</span>
                <strong>{React.int(summary.seasons)}</strong>
              </div>
            </div>
          </article>

          <article className="section-card section-span-2">
            <div className="section-heading">
              <h2>
                {React.string(
                  selectedSeason == ""
                    ? Copy.playerMatchHistoryTitle(language)
                    : SeasonLabel.format(selectedSeason) ++ " • " ++ Copy.playerMatchHistoryTitle(language),
                )}
              </h2>
            </div>
            <div className="tab-strip">
              {React.array(state.seasons->Array.map(row => {
                let isActive = row.season == selectedSeason

                <button
                  key={row.season}
                  className={isActive ? "season-tab active" : "season-tab"}
                  onClick={_ => setSelectedSeason(_ => row.season)}>
                  <span>{React.string(SeasonLabel.format(row.season))}</span>
                  <strong>{React.int(row.games)}</strong>
                </button>
              }))}
            </div>
            {if Js.Array2.length(state.matches) == 0 {
              <p>{React.string(Copy.noData(language))}</p>
            } else {
              <div className="match-list">
                {React.array(state.matches->Array.map(match => {
                  let didDraw = match.home_score == match.away_score
                  let won = didPlayerTeamWin(match)
                  let resultLabel =
                    didDraw ? Copy.resultDraw(language) : won ? Copy.resultWon(language) : Copy.resultLost(language)
                  let resultClass =
                    didDraw ? "result-pill neutral" : won ? "result-pill positive" : "result-pill negative"
                  let meta =
                    Copy.matchday(language, match.matchday) ++
                    (match.team_name != "" ? " • " ++ match.team_name : "")

                  <div key={match.id} className="player-match-card">
                    <FixtureCard
                      matchId={match.id}
                      meta
                      homeTeam={match.home_team}
                      awayTeam={match.away_team}
                      homeScore={match.home_score}
                      awayScore={match.away_score}
                      language
                      navigate
                      resultLabel
                      resultClassName={resultClass}
                    />
                    <div className="player-impact-strip">
                      {match.goals > 0
                        ? <span className="event-badge goal">
                            {React.string(Copy.goalCountText(language, match.goals))}
                          </span>
                        : React.null}
                      {match.assists > 0
                        ? <span className="event-badge neutral">
                            {React.string(Copy.assistCountText(language, match.assists))}
                          </span>
                        : React.null}
                      {match.var_denied_goals > 0
                        ? <span className="event-badge warning">
                            {React.string(Copy.varDeniedGoalCountText(language, match.var_denied_goals))}
                          </span>
                        : React.null}
                      {match.var_denied_assists > 0
                        ? <span className="event-badge warning">
                            {React.string(Copy.varDeniedAssistCountText(language, match.var_denied_assists))}
                          </span>
                        : React.null}
                    </div>
                  </div>
                }))}
              </div>
            }}
          </article>
        </section>
      </>
    }}
  </div>
}
