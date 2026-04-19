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
  has_goal_swing: int,
  has_penalty_swing: int,
  has_red_card_swing: int,
}

type state = {
  seasons: array<seasonRow>,
  matches: array<matchRow>,
}

let emptyState = {
  seasons: [],
  matches: [],
}

let reasonLabel = (language, match) =>
  switch (
    match.has_goal_swing > 0,
    match.has_penalty_swing > 0,
    match.has_red_card_swing > 0,
  ) {
  | (true, false, false) => Copy.varSwingGoalReason(language)
  | (false, true, false) => Copy.varSwingPenaltyReason(language)
  | (false, false, true) => Copy.varSwingRedCardReason(language)
  | (false, false, false) => Copy.varSwingWinsLabel(language)
  | _ => Copy.varSwingCombinedReason(language)
  }

@react.component
let make = (~team: string, ~language: Locale.t, ~navigate: Route.t => unit) => {
  let (state, setState) = React.useState(() => emptyState)
  let (selectedSeason, setSelectedSeason) = React.useState(() => "")

  React.useEffect1(() => {
    let seasons: array<seasonRow> = Database.runQuery(TeamQueries.varSwingWinSeasonsSql, [team])
    let defaultSeason =
      Js.Array2.length(seasons) > 0 ? Js.Array2.unsafe_get(seasons, 0).season : ""

    setState(_ => {
      seasons,
      matches: [],
    })
    setSelectedSeason(_ => defaultSeason)

    None
  }, [team])

  React.useEffect2(() => {
    let matches =
      if selectedSeason == "" {
        []
      } else {
        Database.runQuery(TeamQueries.varSwingWinMatchesBySeasonSql, [team, selectedSeason])
      }

    setState(current => {
      ...current,
      matches,
    })

    None
  }, (team, selectedSeason))

  let totalGames =
    state.seasons->Array.reduce(0, (sum, row) => sum + row.games)

  <div className="team-page">
    <section className="page-hero compact">
      <div className="hero-copy">
        <button className="button-ghost" onClick={_ => navigate(Route.team(team))}>
          {React.string(Copy.backToTeam(language, team))}
        </button>
        <div className="eyebrow">{React.string(Copy.varSwingWinsLabel(language))}</div>
        <h1>{React.string(Copy.varSwingWinsPageTitle(language, team))}</h1>
        <p>{React.string(Copy.varSwingWinsPageSubtitle(language))}</p>
      </div>

      <div className="hero-highlight">
        <span className="hero-highlight-label">{React.string(Copy.varSwingWinsLabel(language))}</span>
        <strong className="hero-highlight-number">{React.int(totalGames)}</strong>
        <p>{React.string(Copy.varSwingWinsDescription(language))}</p>
      </div>
    </section>

    {if Js.Array2.length(state.seasons) == 0 {
      <section className="dashboard-grid season-layout">
        <article className="section-card section-span-3">
          <div className="section-heading">
            <h2>{React.string(Copy.noVarSwingWinsTitle(language))}</h2>
          </div>
          <p>{React.string(Copy.noVarSwingWinsSubtitle(language))}</p>
        </article>
      </section>
    } else {
      <section className="dashboard-grid season-layout">
        <article className="section-card">
          <div className="section-heading">
            <h2>{React.string(Copy.seasonFilterTitle(language))}</h2>
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
        </article>

        <article className="section-card section-span-2">
          <div className="section-heading">
            <h2>{React.string(Copy.qualifyingMatchesTitle(language))}</h2>
          </div>
          <div className="match-list">
            {React.array(state.matches->Array.map(match => {
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
                resultLabel={reasonLabel(language, match)}
                resultClassName="result-pill neutral"
              />
            }))}
          </div>
        </article>
      </section>
    }}
  </div>
}
