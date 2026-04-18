type dbState = [#loading | #ready | #error]

type latestSeasonRow = {
  latest_season: string,
}

@react.component
let make = () => {
  let (dbState, setDbState) = React.useState(() => #loading)
  let (route, setRoute) = React.useState(() => Browser.readHash()->Route.parseHash)
  let (latestSeason, setLatestSeason) = React.useState(() => "2024")
  let (language, setLanguage) = React.useState(() => Browser.readStoredLanguage()->Locale.fromString)

  React.useEffect0(() => {
    let unsubscribe = Browser.subscribeToHashChange(hash => {
      setRoute(_ => Route.parseHash(hash))
    })

    Some(() => unsubscribe())
  })

  React.useEffect1(() => {
    Browser.writeStoredLanguage(language->Locale.toString)
    None
  }, [language])

  React.useEffect0(() => {
    Database.initDb()
    ->Promise.then(success => {
      if success {
        setDbState(_ => #ready)

        let rawLatestSeason = Database.runQuery(
          "SELECT MAX(season) AS latest_season FROM matches",
          [],
        )
        let latestSeasonRows: array<latestSeasonRow> = Obj.magic(rawLatestSeason)

        if Js.Array2.length(latestSeasonRows) > 0 {
          setLatestSeason(_ => Js.Array2.unsafe_get(latestSeasonRows, 0).latest_season)
        }
      } else {
        setDbState(_ => #error)
      }

      Promise.resolve()
    })
    ->ignore

    None
  })

  let navigate = nextRoute => {
    setRoute(_ => nextRoute)
    Browser.writeHash(Route.toHash(nextRoute))
  }

  let renderRoute = () =>
    switch route.kind {
    | #dashboard => <Dashboard language latestSeason navigate />
    | #season =>
      switch route.param {
      | Some(year) => <SeasonView year language navigate />
      | None => <Dashboard language latestSeason navigate />
      }
    | #team =>
      switch route.param {
      | Some(team) => <TeamView team language navigate />
      | None => <Dashboard language latestSeason navigate />
      }
    | #match =>
      switch route.param {
      | Some(matchId) => <MatchView matchId language navigate />
      | None => <Dashboard language latestSeason navigate />
      }
    | #notFound =>
      <section className="page-hero compact">
        <div className="eyebrow">{React.string(Copy.notFoundTitle(language))}</div>
        <h1>{React.string(Copy.notFoundTitle(language))}</h1>
        <p>{React.string(Copy.notFoundSubtitle(language))}</p>
        <div className="hero-actions">
          <button className="button-primary" onClick={_ => navigate(Route.dashboard)}>
            {React.string(Copy.backHome(language))}
          </button>
        </div>
      </section>
    }

  let latestSeasonRoute = Route.season(latestSeason)
  let isHomeActive = route.kind == #dashboard
  let isLatestSeasonActive =
    route.kind == #season && route.param == Some(latestSeason)

  <div className="app-shell">
    <div className="app-backdrop app-backdrop-left" />
    <div className="app-backdrop app-backdrop-right" />
    <nav className="topbar">
      <button className="brand-lockup" onClick={_ => navigate(Route.dashboard)}>
        <div className="brand-mark">
          <span className="brand-mark-ball" />
        </div>
        <div className="brand-copy">
          <span className="brand-name">{React.string(Copy.brand(language))}</span>
          <span className="brand-domain">{React.string("super-lig.arda.tr")}</span>
        </div>
      </button>

      <div className="topbar-actions">
        <button
          className={isHomeActive ? "nav-chip active" : "nav-chip"}
          onClick={_ => navigate(Route.dashboard)}>
          {React.string(Copy.navHome(language))}
        </button>
        <button
          className={isLatestSeasonActive ? "nav-chip active" : "nav-chip"}
          onClick={_ => navigate(latestSeasonRoute)}>
          {React.string(Copy.navLatestSeason(language, latestSeason))}
        </button>
        <div className="language-switcher">
          {React.array([#tr, #en]->Array.map(locale => {
            let isActive = locale == language
            <button
              key={locale->Locale.toString}
              className={isActive ? "language-pill active" : "language-pill"}
              onClick={_ => setLanguage(_ => locale)}>
              {React.string(locale->Locale.label)}
            </button>
          }))}
        </div>
      </div>
    </nav>

    <main className="page-shell">
      {switch dbState {
      | #loading =>
        <section className="page-hero compact">
          <div className="eyebrow">{React.string(Copy.loadingTitle(language))}</div>
          <h1>{React.string(Copy.loadingTitle(language))}</h1>
          <p>{React.string(Copy.loadingSubtitle(language))}</p>
          <div className="loading-dots">
            <span />
            <span />
            <span />
          </div>
        </section>
      | #error =>
        <section className="page-hero compact">
          <div className="eyebrow">{React.string(Copy.loadErrorTitle(language))}</div>
          <h1>{React.string(Copy.loadErrorTitle(language))}</h1>
          <p>{React.string(Copy.loadErrorSubtitle(language))}</p>
        </section>
      | #ready => renderRoute()
      }}
    </main>
  </div>
}
