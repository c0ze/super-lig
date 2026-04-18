type kind = [#dashboard | #season | #team | #match | #notFound]

type t = {
  kind: kind,
  param: option<string>,
}

let dashboard = {kind: #dashboard, param: None}
let season = param => {kind: #season, param: Some(param)}
let team = param => {kind: #team, param: Some(param)}
let match = param => {kind: #match, param: Some(param)}
let notFound = param => {kind: #notFound, param: Some(param)}

let stripHashPrefix = hash =>
  switch hash->Js.String2.get(0) {
  | "#" => hash->Js.String2.sliceToEnd(~from=1)
  | _ => hash
  }

let stripLeadingSlash = path =>
  switch path->Js.String2.get(0) {
  | "/" => path->Js.String2.sliceToEnd(~from=1)
  | _ => path
  }

let stripTrailingSlash = path =>
  switch path->Js.String2.get(path->Js.String2.length - 1) {
  | "/" => path->Js.String2.slice(~from=0, ~to_=-1)
  | _ => path
  }

let cleanPath = hash => {
  let raw = hash->stripHashPrefix
  let raw = switch raw {
  | ""
  | "/" => ""
  | _ => raw
  }
  let raw = switch raw->Js.String2.splitAtMost("?", ~limit=2) {
  | [path, _] => path
  | _ => raw
  }

  if raw == "" {
    ""
  } else {
    raw->stripLeadingSlash->stripTrailingSlash
  }
}

let parseHash = hash => {
  let cleaned = cleanPath(hash)
  let segments =
    cleaned
    ->Js.String2.split("/")
    ->Js.Array2.filter(segment => segment->Js.String2.length != 0)

  switch segments->Js.Array2.length {
  | 0 => dashboard
  | 2 =>
    let first = segments->Js.Array2.unsafe_get(0)
    let second = segments->Js.Array2.unsafe_get(1)
    switch first {
    | "season" => season(second->decodeURIComponent)
    | "team" => team(second->decodeURIComponent)
    | "match" => match(second->decodeURIComponent)
    | _ => notFound(cleaned)
    }
  | _ => cleaned == "" ? dashboard : notFound(cleaned)
  }
}

let toHash = route =>
  switch route.kind {
  | #dashboard => "#/"
  | #season =>
    switch route.param {
    | Some(year) => "#/season/" ++ year->encodeURIComponent
    | None => "#/"
    }
  | #team =>
    switch route.param {
    | Some(name) => "#/team/" ++ name->encodeURIComponent
    | None => "#/"
    }
  | #match =>
    switch route.param {
    | Some(id) => "#/match/" ++ id->encodeURIComponent
    | None => "#/"
    }
  | #notFound =>
    switch route.param {
    | Some(path) => "#/" ++ path
    | None => "#/"
    }
  }
