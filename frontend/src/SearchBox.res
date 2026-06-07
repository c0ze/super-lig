type searchHit = {
  name: string,
  kind: string,
}

// True when focus moved entirely outside the search container (so the
// dropdown should close). Keeps it open while focus moves to a result button,
// which is what makes keyboard selection work.
let focusLeftContainer: ReactEvent.Focus.t => bool = %raw(`function (event) {
  return !event.currentTarget.contains(event.relatedTarget);
}`)

@react.component
let make = (~language: Locale.t, ~navigate: Route.t => unit) => {
  let (query, setQuery) = React.useState(() => "")
  let (hits, setHits) = React.useState((): array<searchHit> => [])
  let (focused, setFocused) = React.useState(() => false)

  React.useEffect1(() => {
    let trimmed = query->Js.String2.trim
    if Js.String2.length(trimmed) < 2 {
      setHits(_ => [])
    } else {
      let like = "%" ++ trimmed ++ "%"
      let rows: array<searchHit> = Database.runQuery(
        "SELECT name, kind FROM (" ++
        "SELECT DISTINCT home_team AS name, 'team' AS kind FROM matches WHERE home_team LIKE ? " ++
        "UNION SELECT DISTINCT away_team AS name, 'team' AS kind FROM matches WHERE away_team LIKE ? " ++
        "UNION SELECT DISTINCT player_1 AS name, 'player' AS kind FROM events WHERE player_1 LIKE ? AND player_1 <> '' " ++
        "UNION SELECT DISTINCT player_2 AS name, 'player' AS kind FROM events WHERE player_2 LIKE ? AND player_2 <> '') " ++
        "ORDER BY (kind <> 'team'), name LIMIT 10",
        [like, like, like, like],
      )
      setHits(_ => rows)
    }
    None
  }, [query])

  let goTo = hit => {
    setQuery(_ => "")
    setHits(_ => [])
    setFocused(_ => false)
    switch hit.kind {
    | "player" => navigate(Route.player(hit.name))
    | _ => navigate(Route.team(hit.name))
    }
  }

  let showResults = focused && Js.Array2.length(hits) > 0

  <div
    className="search-box"
    onFocus={_ => setFocused(_ => true)}
    onBlur={event =>
      if focusLeftContainer(event) {
        setFocused(_ => false)
      }}>
    <input
      className="search-input"
      type_="search"
      value={query}
      placeholder={Copy.searchPlaceholder(language)}
      onChange={event => {
        let value: string = ReactEvent.Form.target(event)["value"]
        setQuery(_ => value)
      }}
    />
    {showResults
      ? <ul className="search-results">
          {React.array(
            hits->Js.Array2.mapi((hit, index) =>
              <li key={hit.kind ++ "-" ++ Int.toString(index) ++ "-" ++ hit.name}>
                <button className="search-result" onClick={_ => goTo(hit)}>
                  <span className="search-result-name">{React.string(hit.name)}</span>
                  <span className="search-result-kind">
                    {React.string(
                      hit.kind == "player"
                        ? Copy.searchPlayerTag(language)
                        : Copy.searchTeamTag(language),
                    )}
                  </span>
                </button>
              </li>
            ),
          )}
        </ul>
      : React.null}
  </div>
}
