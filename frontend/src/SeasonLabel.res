let format = season =>
  if Js.String2.indexOf(season, "-") >= 0 || Js.String2.indexOf(season, "/") >= 0 {
    season
  } else {
    switch Int.fromString(season) {
    | Some(startYear) => season ++ "-" ++ Int.toString(startYear + 1)
    | None => season
    }
  }
