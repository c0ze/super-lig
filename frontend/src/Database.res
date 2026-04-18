type queryResult = {
  id: string,
  season: string,
  matchday: int,
  date: string,
  home_team: string,
  away_team: string,
  home_score: int,
  away_score: int,
  url: string,
  
  // Fields for events
  match_id: option<string>,
  minute: option<int>,
  team: option<string>,
  event_type: option<string>,
  player_1: option<string>,
  player_2: option<string>,
  description: option<string>
}

// These external functions map identically to `SqlHelper.js` exports.
@module("./SqlHelper.js")
external initDb: unit => promise<bool> = "initDb"

@module("./SqlHelper.js")
external runQuery: (string, array<string>) => array<{..}> = "runQuery"

// Cast the JS objects to our strongly typed record structure. Note that we can do this safely via an abstract type in rescript, but for ease of prototyping with sql.js we'll assume it returns matching objects.
external asMatches: array<{..}> => array<queryResult> = "%identity"
