import requests
import concurrent.futures
import pandas as pd
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
import os

@dataclass
class Goal:
    team_id: int
    player_id: int
    period: int
    time: str
    situation_code: str
    x: int
    y: int
    url: str
    shot_type: str
    goalie: str
    home_team_defending_side: str
    team_score: int
    opponent_score: int
    game_date: str


# curl for seasons is `curl -X GET "https://api-web.nhle.com/v1/season"`#
#19171918,19181919,19191920,19201921,19211922,19221923,19231924,19241925,19251926,19261927,19271928,19281929,19291930,19301931,19311932,19321933,19331934,19341935,19351936,19361937,19371938,19381939,19391940,19401941,19411942,19421943,19431944,19441945,19451946,19461947,19471948,19481949,19491950,19501951,19511952,19521953,19531954,19541955,19551956,19561957,19571958,19581959,19591960,19601961,19611962,19621963,19631964,19641965,19651966,19661967,19671968,19681969,19691970,19701971,19711972,19721973,19731974,19741975,
seasons = [19751976,19761977,19771978,19781979,19791980,19801981,19811982,19821983,19831984,19841985,19851986,19861987,19871988,19881989,19891990,19901991,19911992,19921993,19931994,19941995,19951996,19961997,19971998,19981999,19992000,20002001,20012002,20022003,20032004,20052006,20062007,20072008,20082009,20092010,20102011,20112012,20122013,20132014,20142015,20152016,20162017,20172018,20182019,20192020,20202021,20212022,20222023,20232024,20242025,20252026]

def get_goals_for_game(game_id):
    url = f"https://api-web.nhle.com/v1/gamecenter/{game_id}/play-by-play"
    time.sleep(0.2)  # Increased delay to avoid rate limiting
    try:
        response = requests.get(url, timeout=30)  # Add timeout
        if response.status_code != 200:
            print(f"Failed to fetch game data for {game_id} with status code {response.status_code}")
            return []
        data = response.json()
    except requests.exceptions.Timeout:
        print(f"Timeout fetching game data for {game_id}")
        return []
    except requests.exceptions.RequestException as e:
        print(f"Request error for game {game_id}: {e}")
        return []

    # check if the game is a regular season game
    if data.get("gameType", 0) != 2:
        print(f"Game {game_id} is not a regular season game, skipping.")
        return []
    
    plays = data.get("plays", [])
    if not plays:
        print(f"Failed to get plays for game {game_id}")
        return []
    goals = []
    home_team = data.get("homeTeam", {}).get("id", -1)
    away_team = data.get("awayTeam", {}).get("id", -1)
    if home_team == -1 or away_team == -1:
        print(f"Failed to get team IDs for game {game_id}")
        return []
    for play in plays:
        if play.get("typeDescKey", "").lower() == "goal":
            details = play.get("details", {})
            if not details:
                print(f"No details found for goal in game {game_id}")
                continue

            team_id = home_team if details.get("eventOwnerTeamId") == home_team else away_team
            goal = Goal(
                team_id=team_id,
                player_id=details.get("scoringPlayerId", ""),
                situation_code=play.get("situationCode", ""),
                period=play.get("periodDescriptor", {}).get("number", 0),
                time=play.get("timeInPeriod", ""),
                x=details.get("xCoord", 0),
                y=details.get("yCoord", 0),
                url=details.get("highlightClipSharingUrl", ""),
                shot_type=details.get("shotType", ""),
                goalie=details.get("goalieInNetId", ""),
                home_team_defending_side=play.get("homeTeamDefendingSide", ""),
                team_score=details.get("homeScore", 0) if team_id == home_team else details.get("awayScore", 0),
                opponent_score=details.get("awayScore", 0) if team_id == home_team else details.get("homeScore", 0),
                game_date=data.get("gameDate", "")
            )
            goals.append(goal)

    return goals

def get_schedule_on_date(date):
    url = f"https://api-web.nhle.com/v1/schedule/{date}"
    try:
        response = requests.get(url, timeout=30)
        if response.status_code == 200:
            data = response.json()
            games = []
            for gameDay in data.get("gameWeek", []):
                for game in gameDay.get("games", []):
                    if game.get("gameType", 0) == 2:
                        games.append(game)
            return games, data.get("nextStartDate", "")
        print("Failed to fetch schedule:", response.status_code)
        return [], ""
    except requests.exceptions.Timeout:
        print(f"Timeout fetching schedule for {date}")
        return [], ""
    except requests.exceptions.RequestException as e:
        print(f"Request error for schedule {date}: {e}")
        return [], ""

def load_existing_data():
    """Load existing CSV data and return DataFrame with processed games"""
    csv_file = "nhl_goals.csv"
    if os.path.exists(csv_file):
        try:
            df = pd.read_csv(csv_file)
            print(f"Loaded existing data: {len(df)} goals")
            return df
        except Exception as e:
            print(f"Error loading existing CSV: {e}")
            return pd.DataFrame()
    else:
        print("No existing CSV found, starting fresh")
        return pd.DataFrame()

def get_processed_games(existing_df):
    """Extract set of already processed game IDs from existing data"""
    if existing_df.empty:
        return set()
    
    # We need to extract game IDs from the data
    # Since we don't store game_id directly, we'll use a combination of game_date and teams
    # This is imperfect but should catch most duplicates
    processed = set()
    for _, row in existing_df.iterrows():
        # Create a unique identifier from date and score
        identifier = f"{row['game_date']}_{row['team_score']}_{row['opponent_score']}"
        processed.add(identifier)
    return processed

def save_goals_batch(all_goals, append=False):
    """Save goals to CSV file"""
    if not all_goals:
        return
    
    csv_file = "nhl_goals.csv"
    goals_df = pd.DataFrame([goal.__dict__ for goal in all_goals])
    
    if append and os.path.exists(csv_file):
        goals_df.to_csv(csv_file, mode='a', header=False, index=False)
    else:
        goals_df.to_csv(csv_file, index=False)
    
    print(f"Saved {len(all_goals)} goals to {csv_file}")

def orchestrate_season_data_pull(season, existing_df):
    print(f"Pulling data for season {season}")

    # assumes that we should start looking for games in a season from 08/01 to 06/01 of the next year
    # the date format is 2023-11-10 and the season is 20232024
    start_date = f"{str(season)[:4]}-08-01"
    end_date = f"{str(season)[4:8]}-06-01"
    print(f"Start date: {start_date}, End date: {end_date}")
    current_date = start_date
    goals = []
    
    # Get processed games to skip
    processed_games = get_processed_games(existing_df)
    while current_date <= end_date:
        schedule, next_start_date = get_schedule_on_date(current_date)
        if not schedule:
            print(f"No games found for date {current_date}")
            # Use datetime for proper date increment
            try:
                current_dt = datetime.strptime(current_date, "%Y-%m-%d")
                current_dt += timedelta(days=1)
                current_date = current_dt.strftime("%Y-%m-%d")
            except ValueError:
                print(f"Invalid date format: {current_date}")
                break
            continue

        print(f"Found {len(schedule)} games on {current_date}")
        for game in schedule:
            game_id = game.get("id")
            if not game_id:
                print(f"Game ID not found for game on {current_date}, skipping.")
                continue
            
            # Check if this game might already be processed
            # Create identifier similar to how we check in get_processed_games
            game_date = game.get("gameDate", current_date)
            home_score = game.get("homeTeam", {}).get("score", 0)
            away_score = game.get("awayTeam", {}).get("score", 0)
            
            # Check both possible combinations since we don't know which team scored
            game_identifier1 = f"{game_date}_{home_score}_{away_score}"
            game_identifier2 = f"{game_date}_{away_score}_{home_score}"
            
            if game_identifier1 in processed_games or game_identifier2 in processed_games:
                print(f"Game {game_id} already processed, skipping.")
                continue
            
            game_goals = get_goals_for_game(game_id)
            if game_goals:
                print(f"Found {len(game_goals)} goals for game {game_id}")
                goals.extend(game_goals)
                
                # Save progress every 10 games to avoid losing data
                if len(goals) >= 50:  # Save after every 50 goals
                    save_goals_batch(goals, append=True)
                    goals = []  # Clear the list after saving

        # Use next_start_date if available, otherwise increment by 1 day
        if next_start_date:
            current_date = next_start_date
        else:
            try:
                current_dt = datetime.strptime(current_date, "%Y-%m-%d")
                current_dt += timedelta(days=1)
                current_date = current_dt.strftime("%Y-%m-%d")
            except ValueError:
                print(f"Invalid date format: {current_date}")
                break
    
    # Save any remaining goals
    if goals:
        save_goals_batch(goals, append=True)
    
    return goals

def main():
    # Load existing data to check what's already been processed
    existing_df = load_existing_data()
    
    # Process seasons sequentially to avoid overwhelming the API
    # Recent seasons (2023+) seem to have more data and cause issues when run in parallel
    total_new_goals = 0
    
    for season in seasons:
        print(f"\n--- Processing season {season} ---")
        try:
            season_goals = orchestrate_season_data_pull(season, existing_df)
            total_new_goals += len(season_goals)
            print(f"Completed season {season}: {len(season_goals)} new goals")
        except Exception as e:
            print(f"Error processing season {season}: {e}")
            continue

    print(f"\nProcessing complete!")
    print(f"Total new goals added: {total_new_goals}")
    
    # Load final CSV to get total count
    if os.path.exists("nhl_goals.csv"):
        final_df = pd.read_csv("nhl_goals.csv")
        print(f"Total goals in nhl_goals.csv: {len(final_df)}")
    
    print("File saved as nhl_goals.csv in root directory")
    print("Remember to manually move to data/ directory when ready")

if __name__ == "__main__":
    main()
