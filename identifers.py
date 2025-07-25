import requests
import pandas as pd
import tqdm
import time
import random
import os

def load_player_cache(cache_file='data/player_cache.csv'):
    """Load existing player name cache from CSV file"""
    if os.path.exists(cache_file):
        try:
            cache_df = pd.read_csv(cache_file)
            # Convert to dictionary for fast lookup
            player_cache = dict(zip(cache_df['player_id'], cache_df['full_name']))
            print(f"Loaded {len(player_cache)} players from cache: {cache_file}")
            return player_cache
        except Exception as e:
            print(f"Error loading player cache: {e}")
            return {}
    else:
        print(f"No player cache found at {cache_file}, starting fresh")
        return {}

def save_player_cache(player_names, cache_file='data/player_cache.csv'):
    """Save player names to CSV cache file"""
    try:
        # Create data directory if it doesn't exist
        os.makedirs(os.path.dirname(cache_file), exist_ok=True)
        
        # Convert dictionary to DataFrame
        cache_df = pd.DataFrame([
            {'player_id': player_id, 'full_name': name}
            for player_id, name in player_names.items()
        ])
        
        # Sort by player_id for consistent ordering
        cache_df = cache_df.sort_values('player_id')
        
        # Save to CSV
        cache_df.to_csv(cache_file, index=False)
        print(f"Saved {len(player_names)} players to cache: {cache_file}")
    except Exception as e:
        print(f"Error saving player cache: {e}")

# curl -X GET "https://api.nhle.com/stats/rest/en/team"
def get_teams():
    url = "https://api.nhle.com/stats/rest/en/team"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        # Convert the 'data' field to a DataFrame
        # data['data'] is a list of dictionaries, each representing a team
        # We can directly convert it to a DataFrame
        teams_df = pd.DataFrame(data['data'])
        return teams_df
    else:
        raise Exception(f"Failed to fetch teams: {response.status_code}")
    
# curl -X GET "https://api-web.nhle.com/v1/player/8478402/landing"
def get_players(player_id):
    url = f"https://api-web.nhle.com/v1/player/{int(player_id)}/landing"
    retries = 4
    for _ in range(retries):
        try:
            response = requests.get(url, timeout=10)
        except requests.RequestException as e:
            print(f"Request error for player {player_id}: {e}. Retrying...")
            time.sleep(random.uniform(3, 6))
            continue
        if response.status_code == 200:
            data = response.json()
            # "firstName":{"default":"Connor"},"lastName":{"default":"McDavid"}
            return pd.DataFrame([{
            'id': player_id,
            'fullName': f"{data['firstName']['default']} {data['lastName']['default']}"
        }])
        elif response.status_code == 404:
            print(f"Player {player_id} not found (404).")
            return pd.DataFrame()
        else:
            print(f"Error fetching player {player_id}: {response.status_code}. Retrying...")
            time.sleep(random.uniform(3, 6))
    print(f"Failed to fetch player {player_id} after {retries} retries.")
    return pd.DataFrame()

if __name__ == "__main__":
    print("Fetching team data...")
    teams = get_teams()
    df = pd.read_csv('nhl_goals.csv')
    print(f"Loaded {len(df)} goals")
    print(teams.head())
    
    # Update df with team names using the 'team_id' from the teams DataFrame
    df = df.merge(teams[['id', 'fullName']], left_on='team_id', right_on='id', how='left')
    df.rename(columns={'fullName': 'team_name'}, inplace=True)
    df.drop(columns=['id'], inplace=True)  # Drop the 'id' column as it's no longer needed
    

    # Get unique player IDs (including goalies)
    players = set(df['player_id'].unique())
    goalies = set(df['goalie'].dropna().unique())
    all_player_ids = players.union(goalies)
    print(f"Found {len(all_player_ids)} unique players needed")
    
    # Load existing player cache
    player_names = load_player_cache()
    
    # Find players we still need to fetch
    cached_players = set(player_names.keys())
    players_to_fetch = all_player_ids - cached_players
    
    print(f"Players already cached: {len(cached_players)}")
    print(f"Players to fetch: {len(players_to_fetch)}")
    
    # Only fetch players we don't have cached
    if players_to_fetch:
        print(f"Fetching {len(players_to_fetch)} new players...")
        new_player_names = {}
        failed_players = []
        
        for i, player_id in enumerate(tqdm.tqdm(players_to_fetch, desc="Fetching new player names")):
            try:
                # Add delay between requests to be respectful
                if i > 0:
                    time.sleep(random.uniform(0.3, 0.7))  # 300-700ms between requests
                
                player_df = get_players(player_id)
                if not player_df.empty:
                    player_name = player_df['fullName'].iloc[0]
                    new_player_names[player_id] = player_name
                else:
                    failed_players.append(player_id)
                    
            except Exception as e:
                print(f"Error fetching player {player_id}: {e}")
                failed_players.append(player_id)

            # Save progress every 20 players to avoid losing work
            if (i + 1) % 20 == 0:
                # Merge new names with existing cache and save
                updated_cache = {**player_names, **new_player_names}
                save_player_cache(updated_cache)
                success_rate = ((i + 1 - len(failed_players)) / (i + 1)) * 100
                print(f"Progress: {i + 1}/{len(players_to_fetch)} new players processed, {success_rate:.1f}% success rate")
        
        # Merge new names with existing cache
        player_names.update(new_player_names)
        
        # Save final cache
        save_player_cache(player_names)
        
        # Final statistics for new fetches
        success_count = len(new_player_names)
        total_fetch_count = len(players_to_fetch)
        print(f"\nNew fetch results:")
        print(f"  Successfully fetched: {success_count}/{total_fetch_count} players ({success_count/total_fetch_count*100:.1f}%)")
        print(f"  Failed to fetch: {len(failed_players)} players")
        
        if failed_players:
            print(f"  Failed player IDs: {failed_players[:10]}{'...' if len(failed_players) > 10 else ''}")
    else:
        print("All players already cached! No API requests needed.")

    # Update df with player names (from cache and newly fetched)
    df['player_name'] = df['player_id'].map(player_names)
    df['goalie_name'] = df['goalie'].map(player_names)  # Map goalie names as well
    
    # Report coverage statistics
    total_coverage = len([pid for pid in all_player_ids if pid in player_names])
    print(f"\nFinal player name coverage:")
    print(f"  Total unique players needed: {len(all_player_ids)}")
    print(f"  Players with names: {total_coverage}/{len(all_player_ids)} ({total_coverage/len(all_player_ids)*100:.1f}%)")
    
    # Report missing names in final dataset
    missing_players = df['player_name'].isna().sum()
    missing_goalies = df['goalie_name'].isna().sum()
    print(f"\nMissing names in final dataset:")
    print(f"  Player names: {missing_players}/{len(df)} goals ({missing_players/len(df)*100:.1f}%)")
    print(f"  Goalie names: {missing_goalies}/{len(df)} goals ({missing_goalies/len(df)*100:.1f}%)")
    
    df.to_csv('nhl_goals_with_names.csv', index=False)
    print("Identifiers updated and saved to nhl_goals_with_names.csv")

