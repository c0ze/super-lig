@module("./BrowserApi.js")
external readHash: unit => string = "readHash"

@module("./BrowserApi.js")
external writeHash: string => unit = "writeHash"

@module("./BrowserApi.js")
external subscribeToHashChange: (string => unit) => (unit => unit) = "subscribeToHashChange"

@module("./BrowserApi.js")
external readStoredLanguage: unit => string = "readStoredLanguage"

@module("./BrowserApi.js")
external writeStoredLanguage: string => unit = "writeStoredLanguage"

@module("./BrowserApi.js")
external scrollToId: string => unit = "scrollToId"
