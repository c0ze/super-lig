@module("./SqlHelper.js")
external initDb: unit => promise<bool> = "initDb"

@module("./SqlHelper.js")
external runQueryRaw: (string, array<string>) => array<{..}> = "runQuery"

external castRows: array<{..}> => array<'a> = "%identity"

let runQuery = (sql, params) => runQueryRaw(sql, params)->castRows
