"""
This file contains the code for fetching embedding vectors for the players, goalies, and team names.
The embedding data is saved to a cache file for later use using the corresponding id as the lookup
"""
import pandas as pd
import tqdm
from google import genai
from google.genai import types
import os


class EmbeddingWrapper:
    def __init__(self, embedding_model="models/embedding-001"):
        self.embedding_model = embedding_model
        self.client = genai.Client(api_key="AIzaSyAmtDYAEyzOzB40VHR76sGEFMrH2h5GLQ4")
        

    def get_embedding(self, text: list[str]) -> types.EmbedContentResponse:
        response = self.client.models.embed_content(
            model=self.embedding_model,
            contents=text,
            config=types.EmbedContentConfig(task_type="SEMANTIC_SIMILARITY")
        )
        return response

def get_embeddings_for_players(embedding_client: EmbeddingWrapper, players: pd.DataFrame, cache_file='data/player_embeddings.csv'):
    embeddings = {}
    embeddings_df = pd.DataFrame()
    if os.path.exists(cache_file):
        existing_df = pd.read_csv(cache_file, index_col='player_id')
        embeddings_df = pd.concat([existing_df, embeddings_df])

    # group embedding requests in batch of 50
    for i in tqdm.tqdm(range(0, len(players), 50)):
        batch = players.iloc[i:i+50]
        # remove any existing embeddings for these players
        batch = batch[~batch['player_id'].isin(embeddings_df.index)]
        batch.dropna(subset=['player_id'], inplace=True)
        if len(batch) == 0:
            continue

        player_names = batch['player_name'].tolist()
        player_ids = batch['player_id'].tolist()
        try:
            print(f"Getting embeddings for players: {player_names}")
            response = embedding_client.get_embedding(player_names)
            for idx, embedding in enumerate(response.embeddings):
                embeddings[player_ids[idx]] = str(embedding.values)
        except Exception as e:
            print(f"Error fetching embeddings for players {player_ids}: {e}")

        # Save embeddings to cache file
        if embeddings:
            embeddings_df = pd.DataFrame.from_dict(embeddings, orient='index', columns=['embedding'])
            embeddings_df.index.name = 'player_id'
            embeddings_df = embeddings_df.reset_index()
            embeddings_df.to_csv(cache_file, index=False)
            print(f"Saved {len(embeddings)} player embeddings to {cache_file}")
        else:
            print("No embeddings fetched, nothing to save.")
    return embeddings

def get_embeddings_for_teams(embedding_client: EmbeddingWrapper, teams: pd.DataFrame, cache_file='data/team_embeddings.csv'):
    embeddings = {}
    embeddings_df = pd.DataFrame()
    if os.path.exists(cache_file):
        existing_df = pd.read_csv(cache_file, index_col='team_id')
        embeddings_df = pd.concat([existing_df, embeddings_df])

    # group embedding requests in batch of 50
    for i in tqdm.tqdm(range(0, len(teams), 50)):
        batch = teams.iloc[i:i+50]
        # remove any existing embeddings for these teams
        batch = batch[~batch['team_id'].isin(embeddings_df.index)]
        batch.dropna(subset=['team_id'], inplace=True)
        if len(batch) == 0:
            continue

        team_names = batch['team_name'].tolist()
        team_ids = batch['team_id'].tolist()
        try:
            print(f"Getting embeddings for teams: {team_names}")
            response = embedding_client.get_embedding(team_names)
            for idx, embedding in enumerate(response.embeddings):
                embeddings[team_ids[idx]] = str(embedding.values)
        except Exception as e:
            print(f"Error fetching embeddings for teams {team_ids}: {e}")

        # Save embeddings to cache file
        if embeddings:
            embeddings_df = pd.DataFrame.from_dict(embeddings, orient='index', columns=['embedding'])
            embeddings_df.index.name = 'team_id'
            embeddings_df = embeddings_df.reset_index()
            embeddings_df.to_csv(cache_file, index=False)
            print(f"Saved {len(embeddings)} team embeddings to {cache_file}")
        else:
            print("No embeddings fetched, nothing to save.")
    return embeddings

if __name__ == "__main__":
    data = pd.read_csv('data/nhl_goals_with_names.csv')
    players = data[['player_id', 'player_name']].drop_duplicates()
    goalies = data[['goalie', 'goalie_name']].drop_duplicates()
    teams = data[['team_id', 'team_name']].drop_duplicates()

    all_players = pd.concat([players, goalies.rename(columns={'goalie': 'player_id', 'goalie_name': 'player_name'})])
    all_players = all_players.drop_duplicates(subset='player_id')

    print(f"Total unique players and goalies: {len(all_players)}")
    embedding_wrapper = EmbeddingWrapper()
    get_embeddings_for_players(embedding_wrapper, all_players)
    print("Player embeddings fetched and saved.")

    get_embeddings_for_teams(embedding_wrapper, teams)
    print("Team embeddings fetched and saved.")