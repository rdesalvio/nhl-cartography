#!/usr/bin/env python3
"""
Test script to verify the home team addition logic works correctly
Tests with just 5 goals from recent data to ensure API calls work
"""

import requests
import pandas as pd
import time
from datetime import datetime

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

def test_home_team_addition():
    """Test the home team addition logic with a small sample"""
    print("🏒 Testing Home Team Addition Logic")
    print("=" * 40)
    
    # Load sample data from 2023
    df = pd.read_csv('data/nhl_goals_with_names.csv', low_memory=False)
    df['game_date'] = pd.to_datetime(df['game_date'])
    
    # Get 5 goals from January 2023 for testing
    sample_goals = df[df['game_date'] >= '2023-01-01'].head(5)
    
    print(f"Testing with {len(sample_goals)} sample goals:")
    print("-" * 40)
    
    results = []
    
    for idx, (_, goal) in enumerate(sample_goals.iterrows()):
        game_date = goal['game_date'].strftime('%Y-%m-%d')
        team_id = goal['team_id']
        team_score = goal['team_score']
        opponent_score = goal['opponent_score']
        team_name = goal['team_name']
        
        print(f"Goal {idx + 1}: {team_name} on {game_date}")
        print(f"  Team ID: {team_id}, Score: {team_score}-{opponent_score}")
        
        # Try to find the game and get home team
        game_id, home_team_id = find_game_on_date(game_date, team_id, team_score, opponent_score)
        
        if game_id and home_team_id:
            is_home = team_id == home_team_id
            print(f"  ✅ Found game {game_id}, home team: {home_team_id}")
            print(f"  📍 {team_name} was playing {'HOME' if is_home else 'AWAY'}")
            results.append({
                'team_name': team_name,
                'game_date': game_date,
                'team_id': team_id,
                'home_team_id': home_team_id,
                'is_home': is_home,
                'game_id': game_id,
                'success': True
            })
        else:
            print(f"  ❌ Could not find game data")
            results.append({
                'team_name': team_name,
                'game_date': game_date,
                'team_id': team_id,
                'home_team_id': None,
                'is_home': None,
                'game_id': None,
                'success': False
            })
        
        print()
    
    # Summary
    successes = sum(1 for r in results if r['success'])
    print(f"=== TEST RESULTS ===")
    print(f"Successful lookups: {successes}/{len(results)}")
    print(f"Success rate: {(successes/len(results))*100:.1f}%")
    
    if successes > 0:
        print("\n✅ API calls are working correctly!")
        print("You can now run the full script: uv run add_home_team_data.py")
    else:
        print("\n❌ API calls failed. Check your internet connection or API availability.")
    
    return results

if __name__ == "__main__":
    test_home_team_addition()