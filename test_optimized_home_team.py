#!/usr/bin/env python3
"""
Test the optimized home team addition logic
"""

import pandas as pd
from add_home_team_data import find_game_on_date

def test_optimized_approach():
    """Test the optimized approach with sample data"""
    print("🏒 Testing Optimized Home Team Addition")
    print("=" * 40)
    
    # Load sample data
    df = pd.read_csv('data/nhl_goals_with_names.csv', low_memory=False)
    df['game_date'] = pd.to_datetime(df['game_date'])
    
    # Get goals from a single game for testing
    sample_goals = df[df['game_date'] == '2023-01-01'].head(10)
    
    print(f"Testing with {len(sample_goals)} goals from the same game:")
    print("-" * 40)
    
    # Group by unique game (date + team)
    games_found = {}
    
    for _, goal in sample_goals.iterrows():
        game_date = goal['game_date'].strftime('%Y-%m-%d')
        team_id = goal['team_id']
        game_key = f"{game_date}_{team_id}"
        
        if game_key not in games_found:
            # Try to find the game
            game_id, home_team_id = find_game_on_date(game_date, team_id, 0, 0)
            games_found[game_key] = {
                'game_id': game_id,
                'home_team_id': home_team_id,
                'goals': []
            }
        
        games_found[game_key]['goals'].append({
            'team_name': goal['team_name'],
            'player_name': goal['player_name'],
            'team_score': goal['team_score'],
            'opponent_score': goal['opponent_score']
        })
    
    # Display results
    for game_key, game_data in games_found.items():
        print(f"Game {game_key}:")
        print(f"  Game ID: {game_data['game_id']}")
        print(f"  Home Team ID: {game_data['home_team_id']}")
        print(f"  Goals in this game: {len(game_data['goals'])}")
        
        for goal in game_data['goals'][:3]:  # Show first 3 goals
            is_home = goal['team_name'] == 'New Jersey Devils' if game_data['home_team_id'] == 1 else False
            print(f"    {goal['player_name']} ({goal['team_name']}) - {'HOME' if is_home else 'AWAY'}")
        
        print()
    
    print(f"✅ Successfully identified {len(games_found)} unique games")
    print(f"Total API calls needed: {len(games_found)} (instead of {len(sample_goals)})")

if __name__ == "__main__":
    test_optimized_approach()