import json
import csv
import statistics

# Load the JSON data from the file
with open('uefa_european_championship_odds.json') as f:
    data = json.load(f)

# Prepare the header for the CSV
header = ["Game"]
bookmakers = set()

# Extract all unique bookmaker titles
for match in data:
    for bookmaker in match["bookmakers"]:
        bookmakers.add(bookmaker["title"])

# Create header columns for each bookmaker's home win, draw, and away win odds
for bookmaker in bookmakers:
    header.extend([f"{bookmaker} home win", f"{bookmaker} draw", f"{bookmaker} away win"])

# Add columns for mean and median calculations
header.extend([
    "home win mean", "draw mean", "away win mean", 
    "home win median", "draw median", "away win median"
])

# Write data to CSV
with open('uefa_odds.csv', 'w', newline='') as csvfile:
    csvwriter = csv.writer(csvfile)
    
    # Write the header row
    csvwriter.writerow(header)
    
    for match in data:
        row = [f"{match['home_team']} vs {match['away_team']}"]
        odds = {bookmaker: {"home win": None, "draw": None, "away win": None} for bookmaker in bookmakers}
        
        for bookmaker in match["bookmakers"]:
            title = bookmaker["title"]
            for market in bookmaker["markets"]:
                if market["key"] == "h2h":
                    for outcome in market["outcomes"]:
                        if outcome["name"] == match["home_team"]:
                            odds[title]["home win"] = outcome["price"]
                        elif outcome["name"] == match["away_team"]:
                            odds[title]["away win"] = outcome["price"]
                        elif outcome["name"] == "Draw":
                            odds[title]["draw"] = outcome["price"]
        
        home_win_odds = [odds[bookmaker]["home win"] for bookmaker in bookmakers if odds[bookmaker]["home win"] is not None]
        draw_odds = [odds[bookmaker]["draw"] for bookmaker in bookmakers if odds[bookmaker]["draw"] is not None]
        away_win_odds = [odds[bookmaker]["away win"] for bookmaker in bookmakers if odds[bookmaker]["away win"] is not None]

        home_win_mean = statistics.mean(home_win_odds) if home_win_odds else None
        draw_mean = statistics.mean(draw_odds) if draw_odds else None
        away_win_mean = statistics.mean(away_win_odds) if away_win_odds else None
        
        home_win_median = statistics.median(home_win_odds) if home_win_odds else None
        draw_median = statistics.median(draw_odds) if draw_odds else None
        away_win_median = statistics.median(away_win_odds) if away_win_odds else None
        
        for bookmaker in bookmakers:
            row.extend([odds[bookmaker]["home win"], odds[bookmaker]["draw"], odds[bookmaker]["away win"]])
        
        row.extend([
            home_win_mean, draw_mean, away_win_mean, 
            home_win_median, draw_median, away_win_median
        ])
        
        csvwriter.writerow(row)
