import requests
import pandas as pd
import time
import os
from datetime import datetime
import json

def load_existing_data():
    """Load the existing goals data"""
    print("Loading existing NHL goals data...")
    df = pd.read_csv('data/nhl_goals_with_names.csv', low_memory=False)
    print(f"Loaded {len(df):,} goals")
    return df

def load_checkpoint():
    """Load checkpoint data if it exists"""
    checkpoint_file = 'home_team_checkpoint.json'
    if os.path.exists(checkpoint_file):
        try:
            with open(checkpoint_file, 'r') as f:
                checkpoint = json.load(f)
            print(f"Loaded checkpoint: {checkpoint['processed_goals']} goals processed")
            return checkpoint
        except Exception as e:
            print(f"Error loading checkpoint: {e}")
            return None
    return None

def save_checkpoint(processed_goals, game_cache, current_index):
    """Save checkpoint data"""
    checkpoint_file = 'home_team_checkpoint.json'
    checkpoint = {
        'processed_goals': processed_goals,
        'game_cache': game_cache,
        'current_index': current_index,
        'timestamp': datetime.now().isoformat()
    }
    with open(checkpoint_file, 'w') as f:
        json.dump(checkpoint, f, indent=2)
    print(f"Checkpoint saved: {processed_goals} goals processed")

def extract_game_id_from_date(game_date):
    """Extract potential game ID from date format"""
    try:
        # Convert date format from YYYY-MM-DD to YYYYMMDD
        date_obj = datetime.strptime(game_date, '%Y-%m-%d')
        return date_obj.strftime('%Y%m%d')
    except:
        return None

def get_schedule_on_date(date):
    """Get NHL schedule for a specific date"""
    url = f"https://api-web.nhle.com/v1/schedule/{date}"
    try:
        time.sleep(0.5)  # Rate limiting
        response = requests.get(url, timeout=30)
        if response.status_code == 200:
            data = response.json()
            games = []
            for gameDay in data.get("gameWeek", []):
                for game in gameDay.get("games", []):
                    if game.get("gameType", 0) == 2:  # Regular season only
                        games.append(game)
            return games
        else:
            print(f"Failed to fetch schedule for {date}: {response.status_code}")
            return []
    except Exception as e:
        print(f"Error fetching schedule for {date}: {e}")
        return []

def get_home_team_for_game(game_id, game_cache):
    """Get home team ID for a specific game, with caching"""
    
    # Check cache first
    if str(game_id) in game_cache:
        return game_cache[str(game_id)]
    
    url = f"https://api-web.nhle.com/v1/gamecenter/{game_id}/play-by-play"
    try:
        time.sleep(0.3)  # Rate limiting - be gentle with the API
        response = requests.get(url, timeout=30)
        if response.status_code == 200:
            data = response.json()
            home_team = data.get("homeTeam", {}).get("id", None)
            # Cache the result
            game_cache[str(game_id)] = home_team
            return home_team
        else:
            print(f"Failed to fetch game data for {game_id}: {response.status_code}")
            game_cache[str(game_id)] = None
            return None
    except Exception as e:
        print(f"Error fetching game data for {game_id}: {e}")
        game_cache[str(game_id)] = None
        return None

def find_game_on_date(game_date, team_id, team_score, opponent_score):
    """Find the specific game on a given date based on team participation"""
    games = get_schedule_on_date(game_date)
    
    for game in games:
        home_team_id = game.get("homeTeam", {}).get("id")
        away_team_id = game.get("awayTeam", {}).get("id")
        
        # Just check if the team was playing in this game
        # Don't match on scores since our data has progressive scores, not final scores
        if team_id == home_team_id:
            return game.get("id"), home_team_id
        elif team_id == away_team_id:
            return game.get("id"), home_team_id
    
    return None, None

def determine_season_from_date(game_date):
    """Determine NHL season from game date"""
    try:
        date_obj = datetime.strptime(game_date, '%Y-%m-%d')
        year = date_obj.year
        month = date_obj.month
        
        # NHL seasons run from October to June
        if month >= 8:  # August onwards is start of new season
            return f"{year}{year+1}"
        else:  # Before August is end of previous season
            return f"{year-1}{year}"
    except:
        return None

def add_home_team_column():
    """Main function to add home_team column to the existing data"""
    
    # Load existing data
    df = load_existing_data()
    
    # Load checkpoint if exists
    checkpoint = load_checkpoint()
    if checkpoint:
        game_cache = checkpoint.get('game_cache', {})
        processed_games = set(checkpoint.get('processed_games', []))
        processed_count = checkpoint.get('processed_goals', 0)
    else:
        game_cache = {}
        processed_games = set()
        processed_count = 0
    
    # Add home_team column if it doesn't exist
    if 'home_team' not in df.columns:
        df['home_team'] = None
        print("Added home_team column")
    
    # Filter to 2009-2010 season onwards
    df['game_date'] = pd.to_datetime(df['game_date'])
    target_goals = df[df['game_date'] >= '2009-08-01'].copy()
    print(f"Found {len(target_goals):,} goals from 2009-2010 season onwards")
    
    # Group goals by game (date + team combination to identify unique games)
    games_to_process = {}
    for idx, row in target_goals.iterrows():
        if pd.notna(row.get('home_team')):
            continue  # Skip already processed goals
            
        game_date = row['game_date'].strftime('%Y-%m-%d')
        team_id = row['team_id']
        
        # Create unique game identifier
        game_key = f"{game_date}_{team_id}"
        
        if game_key not in processed_games:
            if game_key not in games_to_process:
                games_to_process[game_key] = {
                    'game_date': game_date,
                    'team_id': team_id,
                    'goal_indices': []
                }
            games_to_process[game_key]['goal_indices'].append(idx)
    
    print(f"Found {len(games_to_process)} unique games to process")
    
    batch_size = 10  # Save checkpoint every 10 games
    failed_lookups = 0
    max_failures = 20  # Stop if too many consecutive failures
    
    for game_idx, (game_key, game_info) in enumerate(games_to_process.items()):
        game_date = game_info['game_date']
        team_id = game_info['team_id']
        goal_indices = game_info['goal_indices']
        
        print(f"Processing game {game_idx + 1}/{len(games_to_process)} - Date: {game_date}, Team: {team_id} ({len(goal_indices)} goals)")
        
        # Try to find the game and get home team
        game_id, home_team_id = find_game_on_date(game_date, team_id, 0, 0)  # Scores don't matter anymore
        
        if game_id and home_team_id:
            # Update ALL goals from this game
            df.loc[goal_indices, 'home_team'] = home_team_id
            processed_count += len(goal_indices)
            processed_games.add(game_key)
            failed_lookups = 0  # Reset failure counter
            print(f"  ✅ Found home team {home_team_id} for game {game_id}, updated {len(goal_indices)} goals")
        else:
            failed_lookups += 1
            print(f"  ❌ Could not find game data for {game_date}")
            
            if failed_lookups >= max_failures:
                print(f"Too many consecutive failures ({max_failures}), stopping to avoid issues")
                break
        
        # Save checkpoint periodically
        if (game_idx + 1) % batch_size == 0:
            checkpoint_data = {
                'processed_goals': processed_count,
                'game_cache': game_cache,
                'processed_games': list(processed_games),
                'current_game': game_idx + 1
            }
            with open('home_team_checkpoint.json', 'w') as f:
                json.dump(checkpoint_data, f, indent=2)
            
            # Save intermediate results
            print(f"Saving intermediate results...")
            df.to_csv('data/nhl_goals_with_full_data_temp.csv', index=False)
            print(f"Intermediate file saved with {processed_count} updated goals")
    
    # Final save
    print(f"\nProcessing complete!")
    print(f"Successfully added home_team data for {processed_count} goals")
    
    # Save final result
    df.to_csv('data/nhl_goals_with_full_data.csv', index=False)
    print(f"Final file saved as data/nhl_goals_with_full_data.csv")
    
    # Clean up checkpoint and temp files
    if os.path.exists('home_team_checkpoint.json'):
        os.remove('home_team_checkpoint.json')
        print("Checkpoint file cleaned up")
    
    if os.path.exists('data/nhl_goals_with_full_data_temp.csv'):
        os.remove('data/nhl_goals_with_full_data_temp.csv')
        print("Temporary file cleaned up")
    
    # Summary statistics
    home_team_count = df['home_team'].notna().sum()
    total_from_2009 = len(df[df['game_date'] >= '2009-08-01'])
    
    print(f"\n=== SUMMARY ===")
    print(f"Total goals in dataset: {len(df):,}")
    print(f"Goals from 2009-2010 onwards: {total_from_2009:,}")
    print(f"Goals with home_team data: {home_team_count:,}")
    print(f"Success rate: {(home_team_count/total_from_2009)*100:.1f}%")
    
    return df

def main():
    """Main execution function"""
    print("🏒 NHL Home Team Data Addition Script")
    print("=" * 50)
    print("This script will add home_team column to nhl_goals_with_names.csv")
    print("for games from 2009-2010 season onwards.")
    print("=" * 50)
    
    try:
        df = add_home_team_column()
        print("\n✅ Script completed successfully!")
        return df
    except KeyboardInterrupt:
        print("\n\n⚠️  Script interrupted by user")
        print("Progress has been saved. You can restart the script to continue from where it left off.")
        return None
    except Exception as e:
        print(f"\n❌ Script failed with error: {e}")
        print("Check the checkpoint file to resume from where it stopped.")
        return None

if __name__ == "__main__":
    result = main()