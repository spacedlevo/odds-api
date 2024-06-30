from dotenv import load_dotenv
import sqlite3
import requests
import os

# Load the API key from an environment variable
load_dotenv()
API_KEY = os.getenv('MY_API_KEY')
super_6_db = os.getenv('SUPER_6_DB')

# Load the super 6 team IDs from the SQLite database
def super6_ids():
    conn = sqlite3.connect(super_6_db)
    cursor = conn.cursor()
    cursor.execute('SELECT id, name FROM teams')
    teams = cursor.fetchall()
    conn.close()
    team_dict = {name.lower(): id for id, name in teams}  # Convert team names to lower case
    return team_dict

# Load the JSON data from the file
def get_uefa_european_championship_odds(api_key):
    url = "https://api.the-odds-api.com/v4/sports/soccer_uefa_european_championship/odds"
    params = {
        'regions': 'uk',
        'oddsFormat': 'decimal',
        'apiKey': api_key
    }

    response = requests.get(url, params=params)

    if response.status_code == 200:
        odds_data = response.json()
        return odds_data
    else:
        print(f"Failed to retrieve data: {response.status_code}")
        return None

def write_database(data):
    # Prepare sets for unique bookmakers and teams
    bookmakers = set()
    teams = set()

    # Prepare lists for inserting odds
    odds_data = []

    for match in data:
        home_team = match['home_team'].lower()  # Convert to lower case
        away_team = match['away_team'].lower()  # Convert to lower case
        match_id = match['id']
        
        teams.add(home_team)
        teams.add(away_team)
        
        for bookmaker in match['bookmakers']:
            bookmaker_name = bookmaker['title'].lower()  # Convert to lower case
            bookmakers.add(bookmaker_name)
            for market in bookmaker['markets']:
                if market['key'] == 'h2h':
                    for outcome in market['outcomes']:
                        if outcome['name'].lower() == home_team:
                            odds_data.append(
                                        (
                                            match_id, 
                                            home_team, 
                                            away_team, 
                                            bookmaker_name, 
                                            'home win', 
                                            outcome['price']
                                        )
                                    )
                        elif outcome['name'].lower() == away_team:
                            odds_data.append(
                                (
                                    match_id, 
                                    home_team, 
                                    away_team, 
                                    bookmaker_name, 
                                    'away win', 
                                    outcome['price']
                                )
                            )
                        elif outcome['name'].lower() == 'draw':
                            odds_data.append(
                                (
                                    match_id, 
                                    home_team, 
                                    away_team, 
                                    bookmaker_name, 
                                    'draw', 
                                    outcome['price']
                                    )
                                )

    # Create the SQLite database
    conn = sqlite3.connect('uefa_odds.db')
    cursor = conn.cursor()

    # Create tables for bookmakers, teams, and odds
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS bookmaker (
        id INTEGER PRIMARY KEY,
        name TEXT UNIQUE
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS team (
        id INTEGER PRIMARY KEY,
        name TEXT UNIQUE,
        super6_id INTEGER DEFAULT NULL
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS odds (
        id INTEGER PRIMARY KEY,
        match_id TEXT,
        home_team_id INTEGER,
        away_team_id INTEGER,
        bookmaker_id INTEGER,
        bet_type TEXT,
        odds REAL,
        UNIQUE (match_id, home_team_id, away_team_id, bookmaker_id, bet_type),
        FOREIGN KEY (home_team_id) REFERENCES team(id),
        FOREIGN KEY (away_team_id) REFERENCES team(id),
        FOREIGN KEY (bookmaker_id) REFERENCES bookmaker(id)
    )
    ''')

    # Insert unique bookmakers into the bookmaker table
    for bookmaker in bookmakers:
        cursor.execute('INSERT OR IGNORE INTO bookmaker (name) VALUES (?)', (bookmaker,))

    # Insert unique teams into the team table
    for team in teams:
        try:
            super6_id = super6.get(team)
            if super6_id:
                cursor.execute(
                        'INSERT OR IGNORE INTO team (name, super6_id) VALUES (?, ?)', 
                        (team, super6_id))
            else:
                cursor.execute('INSERT OR IGNORE INTO team (name) VALUES (?)', (team,))
        except KeyError:
            cursor.execute('INSERT OR IGNORE INTO team (name) VALUES (?)', (team,))

    # Commit the transactions for teams and bookmakers
    conn.commit()

    # Create a mapping from names to IDs for teams and bookmakers
    cursor.execute('SELECT id, name FROM team')
    team_id_map = {name: id for id, name in cursor.fetchall()}

    cursor.execute('SELECT id, name FROM bookmaker')
    bookmaker_id_map = {name: id for id, name in cursor.fetchall()}

    # Insert or update odds data into the odds table
    for match_id, home_team, away_team, bookmaker, bet_type, odds in odds_data:
        home_team_id = team_id_map[home_team]
        away_team_id = team_id_map[away_team]
        bookmaker_id = bookmaker_id_map[bookmaker]
        
        # Check if the record already exists
        cursor.execute('''
        SELECT id FROM odds
        WHERE match_id = ? AND home_team_id = ? AND away_team_id = ? AND bookmaker_id = ? AND bet_type = ?
        ''', (match_id, home_team_id, away_team_id, bookmaker_id, bet_type))
        
        result = cursor.fetchone()
        
        if result:
            # Update the existing record
            cursor.execute('''
            UPDATE odds
            SET odds = ?
            WHERE id = ?
            ''', (odds, result[0]))
        else:
            # Insert the new record
            cursor.execute('''
            INSERT INTO odds (match_id, home_team_id, away_team_id, bookmaker_id, bet_type, odds)
            VALUES (?, ?, ?, ?, ?, ?)
            ''', (match_id, home_team_id, away_team_id, bookmaker_id, bet_type, odds))

    # Update super6_id for teams if it becomes available
    for team in teams:
        super6_id = super6.get(team)
        if super6_id:
            cursor.execute('''
            UPDATE team
            SET super6_id = ?
            WHERE name = ?
            ''', (super6_id, team))

    # Commit the transactions for odds
    conn.commit()

    # Close the connection
    conn.close()
    print("Data written to the database")

if __name__ == "__main__":
    api_key = API_KEY # Your API key here
    
    # Get odds from the API
    odds = get_uefa_european_championship_odds(api_key)
    super6 = super6_ids()
    
    if odds:
        write_database(odds)
