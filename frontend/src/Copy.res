type language = Locale.t

let brand = language =>
  switch language {
  | #tr => "Süper Lig Atlas"
  | #en => "Super Lig Atlas"
  }

let navHome = language =>
  switch language {
  | #tr => "Ana Sayfa"
  | #en => "Home"
  }

let navLatestSeason = (language, season) => {
  let seasonLabel = SeasonLabel.format(season)
  switch language {
  | #tr => seasonLabel ++ " Sezonu"
  | #en => seasonLabel ++ " Season"
  }
}

let loadingTitle = language =>
  switch language {
  | #tr => "Veri tabani yükleniyor"
  | #en => "Loading the match database"
  }

let loadingSubtitle = language =>
  switch language {
  | #tr => "Gömülü SQLite arşivi tarayiciya aliniyor."
  | #en => "The embedded SQLite archive is being loaded into the browser."
  }

let loadErrorTitle = language =>
  switch language {
  | #tr => "Veri tabani açilamadi"
  | #en => "The database could not be opened"
  }

let loadErrorSubtitle = language =>
  switch language {
  | #tr => "Lütfen sayfayi yenileyip tekrar deneyin."
  | #en => "Please refresh the page and try again."
  }

let dashboardEyebrow = language =>
  switch language {
  | #tr => "Türkiye'nin son 15 sezonluk maç atlası"
  | #en => "A 15-season map of Turkey's top-flight football"
  }

let dashboardTitle = language =>
  switch language {
  | #tr => "Süper Lig'in ritmini sezonlar, puan tabloları ve olay akışlarıyla keşfet."
  | #en => "Explore the rhythm of the Super Lig through seasons, tables, and match events."
  }

let dashboardSubtitle = language =>
  switch language {
  | #tr => "GitHub Pages üzerinde çalışan, tarayıcı içinde SQLite sorgulayan hızlı bir veri vitrini."
  | #en => "A fast data showcase on GitHub Pages that queries SQLite directly in the browser."
  }

let jumpToLatestSeason = language =>
  switch language {
  | #tr => "Son Sezona Git"
  | #en => "Open Latest Season"
  }

let browseArchive = language =>
  switch language {
  | #tr => "Sezon Arşivini Tara"
  | #en => "Browse Season Archive"
  }

let seasonsLabel = language =>
  switch language {
  | #tr => "Sezon"
  | #en => "Seasons"
  }

let matchesLabel = language =>
  switch language {
  | #tr => "Maç"
  | #en => "Matches"
  }

let goalsLabel = language =>
  switch language {
  | #tr => "Gol"
  | #en => "Goals"
  }

let eventsLabel = language =>
  switch language {
  | #tr => "Olay"
  | #en => "Events"
  }

let goalsPerMatchLabel = language =>
  switch language {
  | #tr => "Maç başına gol"
  | #en => "Goals per match"
  }

let latestSeasonStandingsTitle = (language, season) => {
  let seasonLabel = SeasonLabel.format(season)
  switch language {
  | #tr => seasonLabel ++ " puan tablosu"
  | #en => seasonLabel ++ " standings"
  }
}

let topScorersTitle = language =>
  switch language {
  | #tr => "Gol krallığı"
  | #en => "Top scorers"
  }

let recentMatchesTitle = (language, season) => {
  let seasonLabel = SeasonLabel.format(season)
  switch language {
  | #tr => seasonLabel ++ " son maçlar"
  | #en => seasonLabel ++ " recent matches"
  }
}

let seasonArchiveTitle = language =>
  switch language {
  | #tr => "Sezon arşivi"
  | #en => "Season archive"
  }

let eventDistributionTitle = language =>
  switch language {
  | #tr => "Olay dağılımı"
  | #en => "Event distribution"
  }

let seasonTitle = (language, season) => {
  let seasonLabel = SeasonLabel.format(season)
  switch language {
  | #tr => seasonLabel ++ " sezonu"
  | #en => seasonLabel ++ " season"
  }
}

let seasonSubtitle = language =>
  switch language {
  | #tr => "Puan tablosu, skor üretimi ve maç akışı tek ekranda."
  | #en => "Standings, scoring output, and match flow in one place."
  }

let teamsLabel = language =>
  switch language {
  | #tr => "Takım"
  | #en => "Teams"
  }

let matchdaysLabel = language =>
  switch language {
  | #tr => "Hafta"
  | #en => "Matchdays"
  }

let standingsTitle = language =>
  switch language {
  | #tr => "Puan tablosu"
  | #en => "Standings"
  }

let seasonTopScorersTitle = language =>
  switch language {
  | #tr => "Sezonun en golcüleri"
  | #en => "Season top scorers"
  }

let matchListTitle = language =>
  switch language {
  | #tr => "Maç listesi"
  | #en => "Match list"
  }

let openTimeline = language =>
  switch language {
  | #tr => "Akışı aç"
  | #en => "Open timeline"
  }

let backHome = language =>
  switch language {
  | #tr => "Ana sayfaya dön"
  | #en => "Back home"
  }

let backToSeason = (language, season) => {
  let seasonLabel = SeasonLabel.format(season)
  switch language {
  | #tr => seasonLabel ++ " sezonuna dön"
  | #en => "Back to " ++ seasonLabel ++ " season"
  }
}

let teamHistoryTitle = (language, team) =>
  switch language {
  | #tr => team ++ " arşivi"
  | #en => team ++ " archive"
  }

let teamSubtitle = language =>
  switch language {
  | #tr => "Kulübün 15 sezondaki toplam performansı ve maç geçmişi."
  | #en => "The club's aggregate performance and match history across 15 seasons."
  }

let allTimeRecordTitle = language =>
  switch language {
  | #tr => "Tüm zamanlar karnesi"
  | #en => "All-time record"
  }

let seasonsPlayedLabel = language =>
  switch language {
  | #tr => "Sezon sayısı"
  | #en => "Seasons played"
  }

let recentFormTitle = language =>
  switch language {
  | #tr => "Son 5 maç"
  | #en => "Last 5 matches"
  }

let clubTopScorersTitle = language =>
  switch language {
  | #tr => "Kulüp tarihinin golcüleri"
  | #en => "Club scoring leaders"
  }

let matchHistoryTitle = language =>
  switch language {
  | #tr => "Maç geçmişi"
  | #en => "Match history"
  }

let matchTimelineTitle = language =>
  switch language {
  | #tr => "Maç zaman çizelgesi"
  | #en => "Match timeline"
  }

let matchSubtitle = language =>
  switch language {
  | #tr => "Goller, kartlar ve oyuncu değişiklikleri tek akışta."
  | #en => "Goals, cards, and substitutions in one chronological feed."
  }

let matchDetailsTitle = language =>
  switch language {
  | #tr => "Maç detayları"
  | #en => "Match details"
  }

let matchQuickLinksTitle = language =>
  switch language {
  | #tr => "Hızlı geçişler"
  | #en => "Quick links"
  }

let timelineEventCountLabel = language =>
  switch language {
  | #tr => "Zaman çizelgesi olayı"
  | #en => "Timeline events"
  }

let cardsLabel = language =>
  switch language {
  | #tr => "Kart"
  | #en => "Cards"
  }

let yellowCardsLabel = language =>
  switch language {
  | #tr => "Sarı kart"
  | #en => "Yellow cards"
  }

let redCardsLabel = language =>
  switch language {
  | #tr => "Kırmızı kart"
  | #en => "Red cards"
  }

let penaltiesLabel = language =>
  switch language {
  | #tr => "Penaltı"
  | #en => "Penalties"
  }

let substitutionsLabel = language =>
  switch language {
  | #tr => "Değişiklik"
  | #en => "Substitutions"
  }

let matchIdLabel = language =>
  switch language {
  | #tr => "Maç kimliği"
  | #en => "Match id"
  }

let rawDateLabel = language =>
  switch language {
  | #tr => "Ham tarih alanı"
  | #en => "Raw date field"
  }

let timelineEmpty = language =>
  switch language {
  | #tr => "Bu maç için olay kaydı bulunamadı."
  | #en => "No event log was found for this match."
  }

let playedLabel = language =>
  switch language {
  | #tr => "O"
  | #en => "P"
  }

let winsLabel = language =>
  switch language {
  | #tr => "G"
  | #en => "W"
  }

let drawsLabel = language =>
  switch language {
  | #tr => "B"
  | #en => "D"
  }

let lossesLabel = language =>
  switch language {
  | #tr => "M"
  | #en => "L"
  }

let goalsForLabel = language =>
  switch language {
  | #tr => "AG"
  | #en => "GF"
  }

let goalsAgainstLabel = language =>
  switch language {
  | #tr => "YG"
  | #en => "GA"
  }

let goalDifferenceLabel = language =>
  switch language {
  | #tr => "AV"
  | #en => "GD"
  }

let pointsLabel = language =>
  switch language {
  | #tr => "P"
  | #en => "Pts"
  }

let clubLabel = language =>
  switch language {
  | #tr => "Kulüp"
  | #en => "Club"
  }

let playerLabel = language =>
  switch language {
  | #tr => "Oyuncu"
  | #en => "Player"
  }

let positionLabel = language =>
  switch language {
  | #tr => "Sıra"
  | #en => "Pos"
  }

let notFoundTitle = language =>
  switch language {
  | #tr => "Sayfa bulunamadi"
  | #en => "Page not found"
  }

let notFoundSubtitle = language =>
  switch language {
  | #tr => "İstedigin rota bu veri atlasında yok."
  | #en => "That route does not exist in this data atlas."
  }

let noData = language =>
  switch language {
  | #tr => "Bu görünüm için henüz veri yok."
  | #en => "There is no data for this view yet."
  }

let resultWon = language =>
  switch language {
  | #tr => "Galibiyet"
  | #en => "Won"
  }

let resultDraw = language =>
  switch language {
  | #tr => "Beraberlik"
  | #en => "Draw"
  }

let resultLost = language =>
  switch language {
  | #tr => "Mağlubiyet"
  | #en => "Lost"
  }

let formWonShort = language =>
  switch language {
  | #tr => "G"
  | #en => "W"
  }

let formDrawShort = language =>
  switch language {
  | #tr => "B"
  | #en => "D"
  }

let formLostShort = language =>
  switch language {
  | #tr => "M"
  | #en => "L"
  }

let matchday = (language, value) =>
  switch language {
  | #tr => Int.toString(value) ++ ". hafta"
  | #en => "Matchday " ++ Int.toString(value)
  }

let seasonMatchesPlayed = (language, count) =>
  switch language {
  | #tr => Int.toString(count) ++ " maç"
  | #en => Int.toString(count) ++ " matches"
  }

let eventType = (language, label) =>
  switch (language, label) {
  | (#en, "Second Yellow Card") => "Red second yellow"
  | (#en, "Penalty Goal") => "Penalty goal"
  | (#en, "Missed Penalty") => "Missed penalty"
  | (#tr, "Substitution") => "Oyuncu değişikliği"
  | (#tr, "Yellow Card") => "Sarı kart"
  | (#tr, "Goal") => "Gol"
  | (#tr, "Second Yellow Card") => "İkinci sarıdan kırmızı"
  | (#tr, "Red Card") => "Kırmızı kart"
  | (#tr, "Penalty Goal") => "Penaltı golü"
  | (#tr, "Missed Penalty") => "Kaçan penaltı"
  | _ => label
  }
