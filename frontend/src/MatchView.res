type matchSummary = {
  id: string,
  season: string,
  matchday: int,
  date: string,
  home_team: string,
  away_team: string,
  home_score: int,
  away_score: int,
  url: string,
}

type eventRow = {
  id: int,
  minute: int,
  team_side: string,
  team_name: string,
  event_type: string,
  player_1: string,
  player_2: string,
}

type state = {
  summary: option<matchSummary>,
  events: array<eventRow>,
}

let emptyState = {
  summary: None,
  events: [],
}

let isCardEvent = eventType =>
  switch eventType {
  | "Yellow Card"
  | "Second Yellow Card"
  | "Red Card" => true
  | _ => false
  }

@react.component
let make = (~matchId: string, ~language: Locale.t, ~navigate: Route.t => unit) => {
  let (state, setState) = React.useState(() => emptyState)

  React.useEffect1(() => {
    let summaries: array<matchSummary> = Database.runQuery(
      "SELECT id, season, matchday, date, home_team, away_team, home_score, away_score, url " ++
      "FROM matches WHERE id = ? LIMIT 1",
      [matchId],
    )
    let events: array<eventRow> = Database.runQuery(
      "SELECT e.id, e.minute, e.team AS team_side, " ++
      "CASE WHEN e.team = 'Home' THEN m.home_team WHEN e.team = 'Away' THEN m.away_team ELSE e.team END AS team_name, " ++
      "e.event_type, COALESCE(e.player_1, '') AS player_1, COALESCE(e.player_2, '') AS player_2 " ++
      "FROM events e JOIN matches m ON m.id = e.match_id " ++
      "WHERE e.match_id = ? ORDER BY e.minute ASC, e.id ASC",
      [matchId],
    )

    setState(_ => {
      summary: Js.Array2.length(summaries) > 0 ? Some(Js.Array2.unsafe_get(summaries, 0)) : None,
      events,
    })

    None
  }, [matchId])

  let goals =
    state.events->Array.filter(event => MatchTimeline.isGoalEvent(event.event_type))->Js.Array2.length
  let cards = state.events->Array.filter(event => isCardEvent(event.event_type))->Js.Array2.length
  let substitutions =
    state.events->Array.filter(event => event.event_type == "Substitution")->Js.Array2.length

  <div className="match-page">
    {switch state.summary {
    | None =>
      <section className="page-hero compact">
        <div className="hero-copy">
          <button className="button-ghost" onClick={_ => navigate(Route.dashboard)}>
            {React.string(Copy.backHome(language))}
          </button>
          <div className="eyebrow">{React.string(Copy.matchTimelineTitle(language))}</div>
          <h1>{React.string(Copy.notFoundTitle(language))}</h1>
          <p>{React.string(Copy.noData(language))}</p>
        </div>
      </section>
    | Some(summary) =>
      <>
        <section className="page-hero compact">
          <div className="hero-copy">
            <button className="button-ghost" onClick={_ => navigate(Route.season(summary.season))}>
              {React.string(Copy.backToSeason(language, summary.season))}
            </button>
            <div className="eyebrow">{React.string(Copy.matchTimelineTitle(language))}</div>
            <h1>{React.string(summary.home_team ++ " vs " ++ summary.away_team)}</h1>
            <p>{React.string(Copy.matchSubtitle(language))}</p>

            <div className="scoreboard">
              <button className="scoreboard-team" onClick={_ => navigate(Route.team(summary.home_team))}>
                {React.string(summary.home_team)}
              </button>
              <div className="scoreboard-core">
                <div className="scoreboard-score">
                  {React.string(Int.toString(summary.home_score) ++ " : " ++ Int.toString(summary.away_score))}
                </div>
                <div className="scoreboard-meta">
                  {React.string(SeasonLabel.format(summary.season) ++ " • " ++ Copy.matchday(language, summary.matchday))}
                </div>
              </div>
              <button className="scoreboard-team" onClick={_ => navigate(Route.team(summary.away_team))}>
                {React.string(summary.away_team)}
              </button>
            </div>
          </div>

          <div className="hero-highlight">
            <span className="hero-highlight-label">{React.string(Copy.matchDetailsTitle(language))}</span>
            <div className="match-info-list">
              <div className="record-row">
                <span>{React.string(Copy.matchIdLabel(language))}</span>
                <strong>{React.string(summary.id)}</strong>
              </div>
              <div className="record-row">
                <span>{React.string(Copy.matchdaysLabel(language))}</span>
                <strong>{React.string(Copy.matchday(language, summary.matchday))}</strong>
              </div>
              <div className="record-row">
                <span>{React.string(Copy.timelineEventCountLabel(language))}</span>
                <strong>{React.int(Js.Array2.length(state.events))}</strong>
              </div>
              <div className="record-row">
                <span>{React.string(Copy.rawDateLabel(language))}</span>
                <strong>{React.string(summary.date)}</strong>
              </div>
              {summary.url == ""
                ? React.null
                : <div className="record-row">
                    <span>{React.string("Source")}</span>
                    <a href={summary.url} target="_blank" rel="noreferrer noopener">
                      {React.string(Copy.viewOnTransfermarkt(language))}
                    </a>
                  </div>}
            </div>
          </div>
        </section>

        <section className="metric-strip">
          <article className="metric-card">
            <span className="metric-label">{React.string(Copy.timelineEventCountLabel(language))}</span>
            <strong>{React.int(Js.Array2.length(state.events))}</strong>
          </article>
          <article className="metric-card">
            <span className="metric-label">{React.string(Copy.goalsLabel(language))}</span>
            <strong>{React.int(goals)}</strong>
          </article>
          <article className="metric-card">
            <span className="metric-label">{React.string(Copy.cardsLabel(language))}</span>
            <strong>{React.int(cards)}</strong>
          </article>
          <article className="metric-card">
            <span className="metric-label">{React.string(Copy.substitutionsLabel(language))}</span>
            <strong>{React.int(substitutions)}</strong>
          </article>
        </section>

        <section className="dashboard-grid match-page-grid">
          <article className="section-card section-span-2">
            <div className="section-heading">
              <h2>{React.string(Copy.matchTimelineTitle(language))}</h2>
            </div>
            {if Js.Array2.length(state.events) == 0 {
              <p>{React.string(Copy.timelineEmpty(language))}</p>
            } else {
              <div className="timeline-list">
                {React.array(state.events->Array.map(event => {
                  let detail = MatchTimeline.detailText(language, event.event_type, event.player_1, event.player_2)

                  <article
                    key={Int.toString(event.id)}
                    className={"timeline-item " ++ MatchTimeline.sideClass(event.team_side)}>
                    <div className="timeline-minute">
                      {React.string(MatchTimeline.minuteLabel(event.minute))}
                    </div>
                    <div className="timeline-track">
                      <span className={"timeline-node " ++ MatchTimeline.toneClass(event.event_type)} />
                    </div>
                    <div className="timeline-card">
                      <div className="timeline-card-head">
                        <span className="timeline-team">{React.string(event.team_name)}</span>
                        <span className={"event-badge " ++ MatchTimeline.toneClass(event.event_type)}>
                          {React.string(MatchTimeline.eventLabel(language, event.event_type, event.player_1, event.player_2))}
                        </span>
                      </div>
                      <strong>{React.string(MatchTimeline.primaryText(event.event_type, event.player_1))}</strong>
                      {if detail != "" {
                        <p>{React.string(detail)}</p>
                      } else {
                        React.null
                      }}
                    </div>
                  </article>
                }))}
              </div>
            }}
          </article>

          <article className="section-card">
            <div className="section-heading">
              <h2>{React.string(Copy.matchQuickLinksTitle(language))}</h2>
            </div>
            <div className="ranking-list">
              <button className="ranking-row action-row" onClick={_ => navigate(Route.team(summary.home_team))}>
                <div className="ranking-meta">
                  <span className="ranking-index">{React.string("H")}</span>
                  <div>
                    <strong>{React.string(summary.home_team)}</strong>
                    <span>{React.string(Copy.teamHistoryTitle(language, summary.home_team))}</span>
                  </div>
                </div>
              </button>
              <button className="ranking-row action-row" onClick={_ => navigate(Route.team(summary.away_team))}>
                <div className="ranking-meta">
                  <span className="ranking-index">{React.string("A")}</span>
                  <div>
                    <strong>{React.string(summary.away_team)}</strong>
                    <span>{React.string(Copy.teamHistoryTitle(language, summary.away_team))}</span>
                  </div>
                </div>
              </button>
              <button className="ranking-row action-row" onClick={_ => navigate(Route.season(summary.season))}>
                <div className="ranking-meta">
                  <span className="ranking-index">{React.string("S")}</span>
                  <div>
                    <strong>{React.string(Copy.seasonTitle(language, summary.season))}</strong>
                    <span>{React.string(Copy.matchListTitle(language))}</span>
                  </div>
                </div>
              </button>
            </div>
          </article>
        </section>
      </>
    }}
  </div>
}
