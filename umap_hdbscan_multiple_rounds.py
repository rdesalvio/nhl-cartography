import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.preprocessing import StandardScaler, LabelEncoder
import hdbscan
import umap
from datetime import datetime
import os
import time
import logging
import warnings
warnings.filterwarnings('ignore')

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# AI for dynamic cluster naming
try:
    import anthropic
    # API key will be read from environment variable ANTHROPIC_API_KEY
    anthropic_client = anthropic.Anthropic()
    AI_AVAILABLE = True
    logger.info("Anthropic Claude API configured successfully")
except ImportError:
    AI_AVAILABLE = False
    logger.warning("Anthropic API not available - using generic names")
except Exception as e:
    AI_AVAILABLE = False
    logger.warning(f"Failed to configure Anthropic API: {e} - using generic names")

# Global variables for naming system
generated_names = {
    'galaxy': set(),
    'cluster': set(),
    'solar system': set(),  
    'star': set()
}

# Rate limiting for Anthropic API
last_api_call_time = 0
api_rate_limit_seconds = 0.5  # Conservative 0.5 second between calls

def generate_cluster_name(level_name, cluster_goals, features_used):
    """
    Generate a unique astronomical cluster name using AI based on cluster context.
    
    Args:
        level_name: Type of celestial object (galaxy, cluster, solar system, star)
        cluster_goals: DataFrame of goals in this cluster
        features_used: List of features used for clustering at this level
        
    Returns:
        str: Generated astronomical name
    """
    global last_api_call_time, generated_names
    
    if not AI_AVAILABLE:
        # Fallback to generic naming
        base_name = f"{level_name}_{len(generated_names[level_name])}"
        generated_names[level_name].add(base_name)
        return base_name
    
    try:
        # Rate limiting: conservative delay for Anthropic API
        current_time = time.time()
        time_since_last_call = current_time - last_api_call_time
        
        if time_since_last_call < api_rate_limit_seconds:
            sleep_time = api_rate_limit_seconds - time_since_last_call
            logger.info(f"Rate limiting: sleeping for {sleep_time:.2f} seconds")
            time.sleep(sleep_time)
        
        # Prepare cluster context information
        context_info = []
        
        # Analyze features used for clustering
        if 'shot_zone' in features_used:
            shot_zones = cluster_goals['shot_zone'].value_counts().head(3)
            context_info.append(f"Common shot zones: {', '.join([f'{zone} ({count})' for zone, count in shot_zones.items()])}")

        if 'situation' in features_used:
            situations = cluster_goals['situation'].value_counts().head(3)
            context_info.append(f"Common situations: {', '.join([f'{situation} ({count})' for situation, count in situations.items()])}")
        
        if 'shot_type' in features_used:
            shot_types = cluster_goals['shot_type'].value_counts().head(3)
            context_info.append(f"Common shot types: {', '.join([f'{shot} ({count})' for shot, count in shot_types.items()])}")
        
        if 'period' in features_used:
            periods = cluster_goals['period'].value_counts().head(3)
            context_info.append(f"Game periods: {', '.join([f'Period {period} ({count})' for period, count in periods.items()])}")
        
        if 'team_score' in features_used or 'opponent_score' in features_used:
            avg_team_score = cluster_goals['team_score'].mean()
            avg_opp_score = cluster_goals['opponent_score'].mean()
            context_info.append(f"Average score context: {avg_team_score:.1f} - {avg_opp_score:.1f}")
        
        if 'player_name' in features_used:
            top_players = cluster_goals['player_name'].value_counts().head(3)
            context_info.append(f"Top players: {', '.join([f'{player} ({count})' for player, count in top_players.items()])}")
        
        if 'goalie' in features_used or 'goalie_name' in features_used:
            goalie_col = 'goalie_name' if 'goalie_name' in cluster_goals.columns else 'goalie'
            top_goalies = cluster_goals[goalie_col].value_counts().head(3)
            context_info.append(f"Goalies faced: {', '.join([f'{goalie} ({count})' for goalie, count in top_goalies.items()])}")
        
        # Build the prompt
        context_str = '; '.join(context_info)
        
        prompt = f"""You are tasked with creating a {level_name} name for a project which maps all of the goals scored in the NHL into a constellation map. The name should make sense based on the attributes of the goals contained in the cluster and should resemble names used in astronomy for our real universe.

Some context for the goals in this grouping are: {context_str}.

Please provide only the name (2-3 words maximum), no explanation. The name should be evocative of the goal characteristics and follow astronomical naming conventions."""
        
        # Generate name using Claude
        response = anthropic_client.messages.create(
            model="claude-3-5-haiku-20241022",
            max_tokens=50,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        
        # Update last API call time for rate limiting
        last_api_call_time = time.time()
        
        generated_name = response.content[0].text.strip().replace('"', '').replace("'", "")
        
        # Ensure uniqueness
        if generated_name in generated_names[level_name]:
            # Add a suffix if name already exists
            counter = 1
            while f"{generated_name} {counter}" in generated_names[level_name]:
                counter += 1
            generated_name = f"{generated_name} {counter}"
        
        generated_names[level_name].add(generated_name)
        logger.info(f"Generated {level_name} name: '{generated_name}'")
        return generated_name
        
    except Exception as e:
        logger.warning(f"Failed to generate AI name for {level_name}: {e}")
        # Fallback to generic naming
        base_name = f"{level_name}_{len(generated_names[level_name])}"
        generated_names[level_name].add(base_name)
        return base_name

def get_zones(x, y):
    x = float(x)
    y = float(y)

    if 25 < x <= 54 and  -42.5 < y < -22:
        return "Right Point"
    elif 25 < x <= 54 and 22 < y < 42.5:
        return "Left Point"
    elif 25 < x <= 54 and -22 <= y <= 22:
        return "Point"
    elif 54 < x < 89 and 7 < y < 42.5:
        return 'Left Faceoff Circle'
    elif 54 < x < 89 and -42.5 < y < -7:
        return 'Right Faceoff Circle'
    elif 54 < x < 89 and -7 <= y <= 7:
        return 'Slot'
    elif x >= 89:
        return 'Behind Net'
    return "Not In OZ"

def determine_situation_code(code, player_team, home_team):
    is_home = player_team == home_team

    # grab middle 2 characters
    code_string = str(code)
    if len(code_string) == 4:
        code_string = code_string[1:3]
    else:
        code_string = code_string[0:2]

    situation = ""
    if is_home:
        situation = f"{code_string[1]}v{code_string[0]}"
    else:
        situation = f"{code_string[0]}v{code_string[1]}"

    # small check for 0v1
    if situation == "0v1":
        return "1v0"
    
    return situation

def load_and_prepare_data():
    """Load the NHL goals dataset and prepare features for clustering"""
    print("Loading NHL goals dataset...")
    df = pd.read_csv('data/nhl_goals_with_full_data.csv', low_memory=False)

    df.dropna(subset=["shot_type"], inplace=True)
    shot_type_cleanup = {
        "backhand": "Backhand",
        "tip-in": "Tip-In",
        "slap": "Slap Shot",
        "wrist": "Wrist Shot",
        "snap": "Snap Shot",
        "wrap-around": "Wrap Around",
        "deflected": "Deflected",
        "bat": "Bat",
        "poke": "Poke",
        "between-legs": "Between Legs",
        "cradle": "Cradle",
    }
    
    df['shot_type'] = df['shot_type'].apply(lambda x: shot_type_cleanup[x])
    df['game_date'] = pd.to_datetime(df['game_date'])
    df = df[df['game_date'] >= '2023-10-09'].copy()

    df['month'] = df['game_date'].dt.month
    df['day'] = df['game_date'].dt.day
    
    # Calculate season day (days since October 1st start of season)
    def calculate_season_day(game_date):
        """Calculate days into the NHL season from October 1st start date"""
        if pd.isna(game_date):
            return None
            
        # Determine which season this game belongs to
        if game_date.month >= 10:  # October or later = current season year
            season_start = pd.Timestamp(year=game_date.year, month=10, day=1)
        else:  # Before October = previous season year
            season_start = pd.Timestamp(year=game_date.year - 1, month=10, day=1)
        
        # Calculate days into season
        days_into_season = (game_date - season_start).days + 1  # +1 to make it 1-based
        return max(1, days_into_season)  # Ensure minimum of 1
    
    df['season_day'] = df['game_date'].apply(calculate_season_day)

    print(f"Goals from 2023 onwards: {len(df):,}")

    # Filter out empty nets
    #df = df[~df['goalie'].isna()].copy()
        
    # Normalize coordinates to same side of ice
    df['x'] = pd.to_numeric(df['x'], errors='coerce')
    df['y'] = pd.to_numeric(df['y'], errors='coerce')
    df['y'] = np.where(df['x'] < 0, df['y'] * -1, df['y'])
    df['x'] = np.where(df['x'] < 0, df['x'] * -1, df['x'])

    df['shot_zone'] = df.apply(lambda x: get_zones(x['x'], x['y']), axis=1)

    print(f"Dataset shape: {df.shape}")
    
    # Parse time to get period_time in minutes
    df['period_time'] = df['time'].apply(parse_time_to_minutes)
    df['game_time'] = (df['period_time'] + (df['period'] * 20)) // 60
    
    df['score_diff'] = (df['team_score']-1) - df['opponent_score']

    # subtract 1 from team score since the nhl api counts the goal in the event
    df['team_score'] = df['team_score']-1
    df['situation_code'] = pd.to_numeric(df['situation_code'], errors='coerce')

    df['goalie'] = df['goalie'].fillna("Empty")
    # flatten situation code
    situation_code_map = {
        1551: 1551,
        1451: 1451,
        1541: 1541,
        1441: 1441,
        431: 1431,
        651: 1651,
        1560: 1561,
        1331: 1331,
        1351: 1351,
        1531: 1531,
        1431: 1431,
        1341: 1341,
        641: 1641,
        1460: 1461,
        1010: 1011,

        551: 1551,
        1450: 1451,
        101: 1011,
        431: 1431,
        541: 1541,
        1550: 1551,
        1340: 1341,
        1350: 1351
    }
    df['situation_code'] = df['situation_code'].apply(lambda x: situation_code_map[x])
    df['situation'] = df.apply(lambda row: determine_situation_code(row['situation_code'], row['team_id'], row['home_team']), axis=1)
    
    # Select the specified features (excluding player_id and goalie integer IDs)
    feature_columns = ['shot_zone', 'shot_type', 'game_time', 'team_score', 'opponent_score',
                      'score_diff', 'situation', 'month', 'day', 'season_day']
    
    # Create subset with only complete data for key features
    df_subset = df[feature_columns].copy()

    print(f"Shape after removing missing critical values: {df_subset.shape}")
    print(f"subset columns: {df_subset.columns}")
    
    return df_subset, df

def parse_time_to_minutes(time_str):
    """Parse time string (MM:SS) to minutes as float"""
    try:
        if pd.isna(time_str):
            return 0.0
        minutes, seconds = map(int, str(time_str).split(':'))
        return minutes + seconds / 60.0
    except (ValueError, AttributeError):
        return 0.0

def damerau_levenshtein_distance(s1, s2):
    """Calculate Damerau-Levenshtein distance between two strings"""
    len1, len2 = len(s1), len(s2)
    
    # Create a dictionary for character frequencies
    da = {}
    for char in s1 + s2:
        da[char] = 0
    
    # Create the distance matrix
    h = [[0 for _ in range(len2 + 2)] for _ in range(len1 + 2)]
    
    maxdist = len1 + len2
    h[0][0] = maxdist
    
    for i in range(0, len1 + 1):
        h[i + 1][0] = maxdist
        h[i + 1][1] = i
    for j in range(0, len2 + 1):
        h[0][j + 1] = maxdist
        h[1][j + 1] = j
    
    for i in range(1, len1 + 1):
        db = 0
        for j in range(1, len2 + 1):
            k = da[s2[j - 1]]
            l = db
            if s1[i - 1] == s2[j - 1]:
                cost = 0
                db = j
            else:
                cost = 1
            h[i + 1][j + 1] = min(
                h[i][j] + cost,  # substitution
                h[i + 1][j] + 1,  # insertion
                h[i][j + 1] + 1,  # deletion
                h[k][l] + (i - k - 1) + 1 + (j - l - 1)  # transposition
            )
        da[s1[i - 1]] = i
    
    return h[len1 + 1][len2 + 1]

def calculate_name_similarity(name1, name2):
    """Calculate similarity between two names using Damerau-Levenshtein distance"""
    if pd.isna(name1) or pd.isna(name2):
        return 0.0
    
    name1, name2 = str(name1), str(name2)
    distance = damerau_levenshtein_distance(name1, name2)
    
    # Convert distance to similarity (0-1 scale, where 1 is identical)
    max_len = max(len(name1), len(name2))
    if max_len == 0:
        return 1.0
    
    similarity = 1.0 - (distance / max_len)
    return max(0.0, similarity)  # Ensure similarity is non-negative

def encode_categorical_features(df, feature_subset):
    """Encode categorical features for clustering"""
    print(f"Encoding categorical features for {feature_subset}...")
    
    df_encoded = df.copy()
    
    # Determine which categorical columns are in this subset
    categorical_columns = ['shot_zone']
    if 'shot_type' in feature_subset:
        categorical_columns.append('shot_type')
    if 'situation' in feature_subset:
        categorical_columns.append('situation')
    
    label_encoders = {}
    
    for col in categorical_columns:
        if col in df.columns:
            le = LabelEncoder()
            # Handle missing values by filling with 'unknown'
            df_encoded[col] = df_encoded[col].fillna('unknown')
            df_encoded[col] = le.fit_transform(df_encoded[col].astype(str))
            label_encoders[col] = le
    
    # Fill missing numerical values for columns in this subset
    numerical_columns = ['game_time', 'score_diff', 'month', 'day', 'season_day']
    for col in numerical_columns:
        if col in df_encoded.columns and col in feature_subset:
            df_encoded[col] = df_encoded[col].fillna(df_encoded[col].median())
    
    # Return only the columns we're using for this clustering step
    return df_encoded[feature_subset], label_encoders

def perform_umap_hdbscan_clustering(df_encoded, step_name, min_cluster_size=100):
    """Perform UMAP + HDBSCAN clustering on the given features"""
    print(f"{step_name}: Performing UMAP + HDBSCAN clustering...")
    
    # Scale features
    scaler = StandardScaler()
    features_scaled = scaler.fit_transform(df_encoded.values)
    
    print(f"Clustering {len(features_scaled)} goals with {features_scaled.shape[1]} features")
    
    # Apply UMAP for dimensionality reduction
    print("Applying UMAP dimensionality reduction...")
    umap_reducer = umap.UMAP(
        n_components=15,
        n_neighbors=15,
        min_dist=0.1,
        random_state=42
    )
    umap_features = umap_reducer.fit_transform(features_scaled)
    print(f"UMAP reduced to {umap_features.shape[1]} dimensions")
    
    # Apply HDBSCAN clustering
    print("Applying HDBSCAN clustering...")
    clusterer = hdbscan.HDBSCAN(
        min_cluster_size=min_cluster_size,
    )
    cluster_labels = clusterer.fit_predict(umap_features)
    
    # Handle noise points by assigning them to cluster 0
    noise_mask = cluster_labels == -1
    if noise_mask.sum() > 0:
        print(f"  Assigning {noise_mask.sum()} noise points to cluster 0...")
        cluster_labels[noise_mask] = 0
    
    # Check clustering results
    unique_clusters = np.unique(cluster_labels)
    n_clusters = len(unique_clusters)
    
    print(f"{step_name} clustering results:")
    print(f"  Number of clusters: {n_clusters}")
    for cluster_id in unique_clusters:
        count = np.sum(cluster_labels == cluster_id)
        print(f"    Cluster {cluster_id}: {count} goals")
    
    return cluster_labels

def perform_galaxy_clustering(df_subset):
    """Step 1: Create galaxies using shot_zone and shot_type"""
    print("Step 1: Creating galaxies using shot_zone and shot_type...")
    
    # Use only spatial/shot features for galaxies
    galaxy_features = ['shot_zone', 'shot_type', 'situation']
    df_encoded, _ = encode_categorical_features(df_subset, galaxy_features)
    
    galaxy_labels = perform_umap_hdbscan_clustering(
        df_encoded, 
        "Galaxy clustering",
        min_cluster_size=100
    )
    
    return galaxy_labels

def perform_cluster_clustering(df_subset, galaxy_labels):
    """Step 2: Within each galaxy, create clusters using temporal/game state features"""
    print("Step 2: Creating clusters using period, period_time, score_diff, and situation...")
    
    # Use temporal/game state features for clusters
    cluster_features = ['game_time', 'team_score', 'opponent_score']
    
    cluster_labels = np.full(len(df_subset), -1, dtype=int)
    cluster_id = 0
    
    unique_galaxies = np.unique(galaxy_labels)
    
    for galaxy_id in unique_galaxies:
        galaxy_mask = galaxy_labels == galaxy_id
        galaxy_indices = np.where(galaxy_mask)[0]
        
        print(f"\n  Processing Galaxy {galaxy_id} ({len(galaxy_indices)} goals)...")
        
        if len(galaxy_indices) < 50:  # Skip very small galaxies
            cluster_labels[galaxy_indices] = cluster_id
            print(f"    Galaxy too small, assigning all to cluster {cluster_id}")
            cluster_id += 1
            continue
        
        # Get data for this galaxy only
        galaxy_data = df_subset.iloc[galaxy_indices]
        df_encoded, _ = encode_categorical_features(galaxy_data, cluster_features)
        
        # Perform clustering within this galaxy
        galaxy_cluster_labels = perform_umap_hdbscan_clustering(
            df_encoded,
            f"Galaxy {galaxy_id} cluster clustering",
            min_cluster_size=30  # Smaller min size since we're working within galaxies
        )
        
        # Map local cluster labels to global cluster labels
        unique_galaxy_clusters = np.unique(galaxy_cluster_labels)
        for local_cluster_id in unique_galaxy_clusters:
            local_cluster_mask = galaxy_cluster_labels == local_cluster_id
            global_indices = galaxy_indices[local_cluster_mask]
            cluster_labels[global_indices] = cluster_id
            cluster_id += 1
        
        print(f"    Created {len(unique_galaxy_clusters)} clusters in galaxy {galaxy_id}")
    
    print(f"\nTotal clusters created: {len(np.unique(cluster_labels[cluster_labels >= 0]))}")
    return cluster_labels

def cluster_by_goalie_similarity(df_original, df_subset, cluster_labels):
    """Step 3: Within each cluster, create solar systems by goalie name similarity"""
    print("Step 3: Creating solar systems by goalie name similarity within clusters...")
    
    solar_system_labels = np.full(len(df_subset), -1, dtype=int)
    solar_system_id = 0
    
    unique_clusters = np.unique(cluster_labels[cluster_labels >= 0])
    similarity_threshold = 0.4
    
    for cluster_id in unique_clusters:
        cluster_mask = cluster_labels == cluster_id
        cluster_indices = np.where(cluster_mask)[0]
        cluster_original_indices = df_subset.index[cluster_indices]
        
        print(f"\n  Processing Cluster {cluster_id} ({len(cluster_indices)} goals)...")
        
        # Get goalie names for this cluster
        cluster_goalies = df_original.loc[cluster_original_indices, 'goalie_name'].fillna('Empty Net')
        unique_goalies = cluster_goalies.unique()
        
        print(f"    Found {len(unique_goalies)} unique goalies in cluster")
        
        # Create similarity matrix between goalies
        similarity_matrix = np.zeros((len(unique_goalies), len(unique_goalies)))
        
        for i, goalie1 in enumerate(unique_goalies):
            for j, goalie2 in enumerate(unique_goalies):
                if i == j:
                    similarity_matrix[i, j] = 1.0
                else:
                    similarity = calculate_name_similarity(goalie1, goalie2)
                    similarity_matrix[i, j] = similarity
        
        # Group goalies by similarity threshold
        goalie_clusters = {}
        clustered_goalies = set()
        miscellaneous_goalies = []
        
        for i, goalie in enumerate(unique_goalies):
            if goalie in clustered_goalies:
                continue
                
            # Find similar goalies
            similar_goalies = []
            for j, other_goalie in enumerate(unique_goalies):
                if similarity_matrix[i, j] >= similarity_threshold:
                    similar_goalies.append(other_goalie)
                    clustered_goalies.add(other_goalie)
            
            # Only create solar system if we have more than just the single goalie
            if len(similar_goalies) > 1:
                goalie_clusters[solar_system_id] = similar_goalies
                solar_system_id += 1
            elif len(similar_goalies) == 1:
                miscellaneous_goalies.append(similar_goalies[0])
                clustered_goalies.add(similar_goalies[0])
        
        # Create miscellaneous solar system for non-matching goalies
        if miscellaneous_goalies:
            goalie_clusters[solar_system_id] = miscellaneous_goalies
            print(f"    Created miscellaneous solar system {solar_system_id} with {len(miscellaneous_goalies)} non-matching goalies")
            solar_system_id += 1
        
        # Assign solar system labels to goals based on their goalie
        for current_system_id, goalies_in_system in goalie_clusters.items():
            for goalie in goalies_in_system:
                goalie_goals_mask = cluster_goalies == goalie
                goalie_goal_indices = cluster_indices[goalie_goals_mask]
                solar_system_labels[goalie_goal_indices] = current_system_id
        
        print(f"    Created {len(goalie_clusters)} solar systems")
        for sid, goalies in goalie_clusters.items():
            goal_count = np.sum(solar_system_labels == sid)
            if len(goalies) > 10:
                print(f"      Solar System {sid}: {len(goalies)} goalies, {goal_count} goals")
            else:
                print(f"      Solar System {sid}: {len(goalies)} goalies ({', '.join(goalies[:5])}{'...' if len(goalies) > 5 else ''}), {goal_count} goals")
    
    print(f"\nTotal solar systems created: {len(np.unique(solar_system_labels[solar_system_labels >= 0]))}")
    return solar_system_labels

def cluster_by_player_similarity(df_original, df_subset, cluster_labels):
    """Step 3: Within each cluster, create solar systems by player name similarity"""
    print("Step 3: Creating solar systems by player name similarity within clusters...")
    
    solar_system_labels = np.full(len(df_subset), -1, dtype=int)
    solar_system_id = 0
    
    unique_clusters = np.unique(cluster_labels[cluster_labels >= 0])
    similarity_threshold = 0.4
    
    for cluster_id in unique_clusters:
        cluster_mask = cluster_labels == cluster_id
        cluster_indices = np.where(cluster_mask)[0]
        cluster_original_indices = df_subset.index[cluster_indices]
        
        print(f"\n  Processing Cluster {cluster_id} ({len(cluster_indices)} goals)...")
        
        # Get goalie names for this cluster
        cluster_players = df_original.loc[cluster_original_indices, 'player_name']
        unique_players = cluster_players.unique()
        
        print(f"    Found {len(unique_players)} unique players in cluster")
        
        # Create similarity matrix between goalies
        similarity_matrix = np.zeros((len(unique_players), len(unique_players)))
        
        for i, player1 in enumerate(unique_players):
            for j, player2 in enumerate(unique_players):
                if i == j:
                    similarity_matrix[i, j] = 1.0
                else:
                    similarity = calculate_name_similarity(player1, player2)
                    similarity_matrix[i, j] = similarity
        
        # Group goalies by similarity threshold
        player_clusters = {}
        clustered_players = set()
        miscellaneous_players = []
        
        for i, player in enumerate(unique_players):
            if player in clustered_players:
                continue
                
            # Find similar goalies
            similar_players = []
            for j, other_player in enumerate(unique_players):
                if similarity_matrix[i, j] >= similarity_threshold:
                    similar_players.append(other_player)
                    clustered_players.add(other_player)
            
            # Only create solar system if we have more than just the single goalie
            if len(similar_players) > 1:
                player_clusters[solar_system_id] = similar_players
                solar_system_id += 1
            elif len(similar_players) == 1:
                miscellaneous_players.append(similar_players[0])
                clustered_players.add(similar_players[0])
        
        # Create miscellaneous solar system for non-matching goalies
        if miscellaneous_players:
            player_clusters[solar_system_id] = miscellaneous_players
            print(f"    Created miscellaneous solar system {solar_system_id} with {len(miscellaneous_players)} non-matching player")
            solar_system_id += 1
        
        # Assign solar system labels to goals based on their goalie
        for current_system_id, players_in_system in player_clusters.items():
            for player in players_in_system:
                player_goals_mask = cluster_players == player
                player_goal_indices = cluster_indices[player_goals_mask]
                solar_system_labels[player_goal_indices] = current_system_id
        
        print(f"    Created {len(player_clusters)} solar systems")
        for sid, players in player_clusters.items():
            goal_count = np.sum(solar_system_labels == sid)
            if len(players) > 10:
                print(f"      Solar System {sid}: {len(players)} players, {goal_count} goals")
            else:
                print(f"      Solar System {sid}: {len(players)} players ({', '.join(players[:5])}{'...' if len(players) > 5 else ''}), {goal_count} goals")
    
    print(f"\nTotal solar systems created: {len(np.unique(solar_system_labels[solar_system_labels >= 0]))}")
    return solar_system_labels

def create_goal_hierarchy_mapping_FIXED(galaxy_labels, cluster_labels, solar_system_labels, df_subset, df_original):
    """Create goal hierarchy mapping with proper star assignments and AI-generated names"""
    print("Creating goal hierarchy mapping with FIXED star assignments and AI naming...")
    
    # Generate names for each unique cluster at each level
    galaxy_names = {}
    cluster_names = {}
    solar_system_names = {}
    
    # Generate galaxy names
    unique_galaxies = np.unique(galaxy_labels)
    for galaxy_id in unique_galaxies:
        galaxy_mask = galaxy_labels == galaxy_id
        galaxy_goals = df_original.loc[df_subset.index[galaxy_mask]]
        features_used = ['shot_zone', 'shot_type', 'situation']  # Features used for galaxy clustering
        galaxy_names[galaxy_id] = generate_cluster_name('galaxy', galaxy_goals, features_used)
    
    # Generate cluster names  
    unique_clusters = np.unique(cluster_labels[cluster_labels >= 0])
    for cluster_id in unique_clusters:
        cluster_mask = cluster_labels == cluster_id
        cluster_goals = df_original.loc[df_subset.index[cluster_mask]]
        features_used = ['game_time', 'team_score', 'opponent_score']  # Features used for cluster clustering
        cluster_names[cluster_id] = generate_cluster_name('cluster', cluster_goals, features_used)
    
    # Generate solar system names
    unique_solar_systems = np.unique(solar_system_labels[solar_system_labels >= 0])
    for solar_system_id in unique_solar_systems:
        solar_system_mask = solar_system_labels == solar_system_id
        solar_system_goals = df_original.loc[df_subset.index[solar_system_mask]]
        features_used = ['goalie_name']  # Features used for solar system clustering
        solar_system_names[solar_system_id] = generate_cluster_name('solar system', solar_system_goals, features_used)
    
    # Create mapping data
    mapping_data = []
    
    # Group goals by solar system to assign relative star IDs
    goals_by_solar_system = {}
    for i in range(len(df_subset)):
        solar_system_id = solar_system_labels[i]
        if solar_system_id not in goals_by_solar_system:
            goals_by_solar_system[solar_system_id] = []
        goals_by_solar_system[solar_system_id].append(i)
    
    for i in range(len(df_subset)):
        # Get the original goal data
        original_idx = df_subset.index[i]
        goal_row = df_original.loc[original_idx]
        
        # Get hierarchical assignments
        galaxy_id = galaxy_labels[i]
        cluster_id = cluster_labels[i] 
        solar_system_id = solar_system_labels[i]
        
        # FIXED: Assign star ID relative to solar system
        goals_in_same_system = goals_by_solar_system[solar_system_id]
        star_id = goals_in_same_system.index(i)  # 0-based index within this solar system
        
        # Create hierarchical path components using AI-generated names
        galaxy_name = galaxy_names[galaxy_id]
        cluster_name = cluster_names[cluster_id]
        solar_system_name = solar_system_names[solar_system_id]
        star_name = f"star_{star_id}"  # Now relative to solar system!
        
        # Create full hierarchy path
        hierarchy_path = f"root.{galaxy_name}.{cluster_name}.{solar_system_name}.{star_name}"
        
        # Calculate cluster size (goals in same solar system)
        cluster_size = len(goals_in_same_system)
        
        # Create mapping entry matching sequential_clustering format
        mapping_entry = goal_row.to_dict()
        mapping_entry.update({
            'goal_index': original_idx,
            'deepest_cluster': hierarchy_path,
            'hierarchy_level': 3,  # 4 levels: galaxy, cluster, solar system, star
            'hierarchy_path': hierarchy_path,
            'cluster_size': cluster_size,
            'level_0_cluster': galaxy_name,
            'level_1_cluster': cluster_name,
            'level_2_cluster': solar_system_name,
            'level_3_cluster': star_name
        })
        
        mapping_data.append(mapping_entry)
    
    # Create DataFrame
    mapping_df = pd.DataFrame(mapping_data)
    
    # Ensure proper column order to match sequential_clustering output
    base_columns = [
        'team_id', 'player_id', 'period', 'time', 'situation', 'situation_code', 'x', 'y', 'url',
        'shot_type', 'goalie', 'home_team_defending_side', 'score_diff', 'shot_zone', 'team_score', 'opponent_score',
        'game_date', 'team_name', 'player_name', 'goalie_name', 'time_minutes', 'time_seconds',
        'period_time', 'month', 'day', 'season_day', 'home_team'
    ]
    
    hierarchy_columns = [
        'goal_index', 'deepest_cluster', 'hierarchy_level', 'hierarchy_path', 'cluster_size',
        'level_0_cluster', 'level_1_cluster', 'level_2_cluster', 'level_3_cluster'
    ]
    
    # Reorder columns to match format
    available_base_columns = [col for col in base_columns if col in mapping_df.columns]
    column_order = available_base_columns + hierarchy_columns
    mapping_df = mapping_df[column_order]

    # clean up data
    mapping_df['goalie_name'] = mapping_df['goalie_name'].fillna("Empty Net")
    
    return mapping_df

def main():
    """Main function to run the MULTIPLE ROUNDS hierarchical clustering"""
    print("=== MULTIPLE ROUNDS UMAP + HDBSCAN CLUSTERING ===")
    print("Round 1 - Galaxies: shot_zone, shot_type")
    print("Round 2 - Clusters: period, period_time, score_diff, situation (within galaxies)")
    print("Round 3 - Solar Systems: goalie name similarity (within clusters)")
    
    # Create output directory
    os.makedirs('sequential_clustering', exist_ok=True)
    
    # Load and prepare data
    df_subset, df_original = load_and_prepare_data()
    
    # Step 1: Create galaxies using spatial/shot features
    galaxy_labels = perform_galaxy_clustering(df_subset)
    
    # Step 2: Within each galaxy, create clusters using temporal/game state features
    cluster_labels = perform_cluster_clustering(df_subset, galaxy_labels)
    
    # Step 3: Within each cluster, create solar systems by goalie name similarity
    solar_system_labels = cluster_by_goalie_similarity(df_original, df_subset, cluster_labels)
    #solar_system_labels = cluster_by_player_similarity(df_original, df_subset, cluster_labels)
    
    # Create goal hierarchy mapping with FIXED star assignments
    mapping_df = create_goal_hierarchy_mapping_FIXED(galaxy_labels, cluster_labels, solar_system_labels, df_subset, df_original)
    
    # Save the output
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f'sequential_clustering/goal_hierarchy_mapping_multiple_rounds_{timestamp}.csv'
    mapping_df.to_csv(output_file, index=False)
    
    print(f"\n✅ MULTIPLE ROUNDS hierarchical clustering complete!")
    print(f"Output file: {output_file}")
    print(f"Total goals processed: {len(mapping_df):,}")
    
    # Final statistics
    n_galaxies = len(np.unique(galaxy_labels))
    n_clusters = len(np.unique(cluster_labels[cluster_labels >= 0]))
    n_solar_systems = len(np.unique(solar_system_labels[solar_system_labels >= 0]))
    
    print(f"\n=== FINAL HIERARCHY ===")
    print(f"Galaxies (spatial/shot): {n_galaxies}")
    print(f"Clusters (temporal/game state): {n_clusters}")
    print(f"Solar Systems (goalie similarity): {n_solar_systems}")
    print(f"Stars: {len(mapping_df)}")
    
    # Show sample AI-generated names
    print(f"\n=== SAMPLE AI-GENERATED NAMES ===")
    sample_galaxies = mapping_df['level_0_cluster'].unique()[:3]
    sample_clusters = mapping_df['level_1_cluster'].unique()[:3]
    sample_solar_systems = mapping_df['level_2_cluster'].unique()[:3]
    
    print("Sample Galaxies:", ", ".join(sample_galaxies))
    print("Sample Clusters:", ", ".join(sample_clusters))
    print("Sample Solar Systems:", ", ".join(sample_solar_systems))
    
    # Verify the fix
    print(f"\n=== VERIFICATION ===")
    sample_systems = mapping_df.groupby('level_2_cluster')
    
    for system_name, system_goals in list(sample_systems)[:3]:
        stars_in_system = system_goals['level_3_cluster'].tolist()
        print(f"{system_name}: {stars_in_system[:5]}...")  # Show first 5 stars
        
        # Check if stars start from 0 and are sequential
        star_numbers = [int(star.split('_')[1]) for star in stars_in_system]
        expected = list(range(len(star_numbers)))
        if star_numbers == expected:
            print(f"  ✅ Fixed: Stars are {expected[:5]}...")
        else:
            print(f"  ❌ Still broken: Stars are {star_numbers[:5]}...")
    
    return mapping_df

if __name__ == "__main__":
    result = main()