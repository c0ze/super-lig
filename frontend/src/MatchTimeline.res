let minuteLabel = minute => Int.toString(minute) ++ "'"

let minuteLabelWithFallback = (minuteLabelRaw, minute) =>
  (minuteLabelRaw != "" ? minuteLabelRaw : Int.toString(minute)) ++ "'"

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

let detailTextWithMetadata = (language: Locale.t, eventType, eventSubtype, eventDetail, player1, player2) =>
  if isPenaltyGoal(eventType, player1, player2) {
    switch language {
    | #tr => eventSubtype != "" && eventSubtype != "Penaltı" ? "Penaltı • " ++ eventSubtype : "Penaltı"
    | #en => eventSubtype != "" && eventSubtype != "Penaltı" ? "Penalty • " ++ eventSubtype : "Penalty"
    }
  } else {
    switch eventType {
    | "Goal" =>
      if eventDetail != "" {
        eventDetail
      } else if player2 != "" {
        switch language {
        | #tr => "Asist: " ++ player2
        | #en => "Assist: " ++ player2
        }
      } else {
        eventSubtype
      }
    | "Substitution" =>
      switch language {
      | #tr =>
        "Giren: " ++ player1 ++ " • Çıkan: " ++ player2 ++ (eventDetail != "" ? " • " ++ eventDetail : "")
      | #en =>
        "In: " ++ player1 ++ " • Out: " ++ player2 ++ (eventDetail != "" ? " • " ++ eventDetail : "")
      }
    | "Missed Penalty" =>
      let base =
        switch language {
        | #tr => "Kaçan penaltı"
        | #en => "Missed penalty"
        }
      let keeperDetail =
        if player2 != "" {
          switch language {
          | #tr => "Kaleci: " ++ player2
          | #en => "Goalkeeper: " ++ player2
          }
        } else {
          ""
        }
      let pieces = [eventSubtype, keeperDetail, eventDetail]->Js.Array2.filter(text => text != "")
      pieces->Js.Array2.length == 0 ? base : base ++ " • " ++ pieces->Js.Array2.joinWith(" • ")
    | "Yellow Card"
    | "Second Yellow Card"
    | "Red Card" =>
      eventDetail != "" ? eventDetail : eventSubtype
    | _ => eventDetail != "" ? eventDetail : eventSubtype
    }
  }

let detailText = (language: Locale.t, eventType, player1, player2) =>
  detailTextWithMetadata(language, eventType, "", "", player1, player2)

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
