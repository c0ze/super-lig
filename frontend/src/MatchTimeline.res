let minuteLabel = minute => Int.toString(minute) ++ "'"

let primaryText = (eventType, player1) => player1 != "" ? player1 : eventType

let isPenaltyGoal = (eventType, player1, player2) =>
  eventType == "Penalty Goal" || (eventType == "Goal" && player1 != "" && player1 == player2)

let isGoalEvent = eventType =>
  switch eventType {
  | "Goal"
  | "Penalty Goal" => true
  | _ => false
  }

let eventLabel = (language: Locale.t, eventType, player1, player2) =>
  Copy.eventType(language, isPenaltyGoal(eventType, player1, player2) ? "Penalty Goal" : eventType)

let detailText = (language: Locale.t, eventType, player1, player2) =>
  if isPenaltyGoal(eventType, player1, player2) {
    switch language {
    | #tr => "Penaltı"
    | #en => "Penalty"
    }
  } else {
    switch eventType {
    | "Goal" =>
      player2 == ""
        ? ""
        : switch language {
          | #tr => "Asist: " ++ player2
          | #en => "Assist: " ++ player2
          }
    | "Substitution" =>
      switch language {
      | #tr => "Giren: " ++ player1 ++ " • Çıkan: " ++ player2
      | #en => "In: " ++ player1 ++ " • Out: " ++ player2
      }
    | _ => ""
    }
  }

let toneClass = eventType =>
  switch eventType {
  | "Goal" => "goal"
  | "Penalty Goal" => "goal"
  | "Yellow Card" => "warning"
  | "Second Yellow Card"
  | "Red Card" => "danger"
  | "Substitution" => "neutral"
  | _ => "neutral"
  }

let sideClass = teamSide =>
  switch teamSide {
  | "Away" => "timeline-away"
  | _ => "timeline-home"
  }
