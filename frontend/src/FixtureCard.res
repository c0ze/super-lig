@react.component
let make = (
  ~matchId: string,
  ~meta: string,
  ~homeTeam: string,
  ~awayTeam: string,
  ~homeScore: int,
  ~awayScore: int,
  ~language: Locale.t,
  ~navigate: Route.t => unit,
  ~resultLabel: option<string>=?,
  ~resultClassName: option<string>=?,
) => {
  let openMatch = () => navigate(Route.match(matchId))
  let isHomeWin = homeScore > awayScore
  let isAwayWin = awayScore > homeScore

  let handleCardKeyDown = event =>
    switch event->ReactEvent.Keyboard.key {
    | "Enter"
    | " " =>
      event->ReactEvent.Keyboard.preventDefault
      openMatch()
    | _ => ()
    }

  <div
    className="match-card spacious match-card-interactive"
    role="button"
    tabIndex={0}
    ariaLabel={homeTeam ++ " " ++ Int.toString(homeScore) ++ " : " ++ Int.toString(awayScore) ++ " " ++ awayTeam}
    onClick={_ => openMatch()}
    onKeyDown={handleCardKeyDown}>
    <div className="match-card-topline">
      <div className="match-card-meta">{React.string(meta)}</div>
      <button
        className="match-timeline-link"
        onClick={event => {
          event->ReactEvent.Mouse.stopPropagation
          openMatch()
        }}>
        {React.string(Copy.openTimeline(language))}
      </button>
    </div>

    <div className="match-card-scoreline">
      <button
        className={isHomeWin ? "team-link winner" : "team-link"}
        onClick={event => {
          event->ReactEvent.Mouse.stopPropagation
          navigate(Route.team(homeTeam))
        }}>
        {React.string(homeTeam)}
      </button>
      <span className="score-chip">
        {React.string(Int.toString(homeScore) ++ " : " ++ Int.toString(awayScore))}
      </span>
      <button
        className={isAwayWin ? "team-link winner" : "team-link"}
        onClick={event => {
          event->ReactEvent.Mouse.stopPropagation
          navigate(Route.team(awayTeam))
        }}>
        {React.string(awayTeam)}
      </button>
    </div>

    {switch (resultLabel, resultClassName) {
    | (Some(label), Some(className)) => <span className={className}>{React.string(label)}</span>
    | _ => React.null
    }}
  </div>
}
