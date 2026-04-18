type t = [#en | #tr]

let fromString = value =>
  switch value {
  | "en" => #en
  | "tr" => #tr
  | _ => #tr
  }

let toString = language =>
  switch language {
  | #en => "en"
  | #tr => "tr"
  }

let label = language =>
  switch language {
  | #en => "EN"
  | #tr => "TR"
  }

let toggle = language =>
  switch language {
  | #en => #tr
  | #tr => #en
  }
