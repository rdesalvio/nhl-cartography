import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.preprocessing import StandardScaler, LabelEncoder
import hdbscan
import umap
from datetime import datetime
import os
import warnings
warnings.filterwarnings('ignore')

def get_zones(x, y):
    x = float(x)
    y = float(y)

    if x < 0:
        x = x * -1
        y = y * -1

    if 25 < x < 54 and  -42.5 < y < -37:
        return 1
    elif 25 < x < 39.5 and  -37 < y < -22:
        return 2
    elif 25 < x < 39.5 and -22 < y < 22:
        return 3
    elif 25 < x < 39.5 and 22 < y < 37:
        return 4
    elif 25 < x < 54 and 37 < y < 42.5:
        return 5
    elif 39.5 < x < 54 and -37 < y < -22:
        return 6
    elif 39.5 < x < 54 and -22 < y < 22:
        return 7
    elif 39.5 < x < 54 and 22 < y < 37:
        return 8
    elif 54 < x < 69 and -42.5 < y < -22:
        return 9
    elif 54 < x < 69 and -22 < y < -7:
        return 10
    elif 54 < x < 69 and -7 < y < 7:
        return 11
    elif 54 < x < 69 and 7 < y < 22:
        return 12
    elif 54 < x < 69 and 22 < y < 42.5:
        return 13
    
    return 14

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
    df['game_date'] = pd.to_datetime(df['game_date'])
    df = df[df['game_date'] >= '2023-10-09'].copy()

    print(f"Goals from 2023 onwards: {len(df):,}")

    # Filter out empty nets
    df = df[~df['goalie'].isna()].copy()
        
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
    df['situation_code'] = pd.to_numeric(df['situation_code'], errors='coerce')
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

        101: 1011,
        431: 1431,
        541: 1541,
        1550: 1551,
        1340: 1341,
        1350: 1351
    }
    reduced_situation_code_map = {
        1551: 0,
        1451: 2,
        1541: 1,
        1441: 0,
        431: 1,
        651: 1,
        1560: 2,
        1331: 0,
        1351: 2,
        1531: 1,
        1431: 1,
        1341: 2,
        641: 1,
        1460: 2,
        1010: 3,

        101: 3,
        431: 1,
        541: 1,
        1550: 0,
        1340: 2,
        1350: 2
    }
    df['situation_code'] = df['situation_code'].apply(lambda x: situation_code_map[x])
    df['situation'] = df.apply(lambda row: determine_situation_code(row['situation_code'], row['team_id'], row['home_team']), axis=1)
    
    # Select the specified features (excluding player_id and goalie integer IDs)
    feature_columns = ['shot_zone', 'shot_type', 'period', 'period_time', 
                      'score_diff', 'situation']
    
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

def encode_categorical_features(df):
    """Encode categorical features for clustering"""
    print("Encoding categorical features...")
    
    df_encoded = df.copy()
    categorical_columns = ['shot_type', 'situation']
    label_encoders = {}
    
    for col in categorical_columns:
        if col in df.columns:
            le = LabelEncoder()
            # Handle missing values by filling with 'unknown'
            df_encoded[col] = df_encoded[col].fillna('unknown')
            df_encoded[col] = le.fit_transform(df_encoded[col].astype(str))
            label_encoders[col] = le
    
    # Fill missing numerical values
    numerical_columns = ['x', 'y', 'period', 'period_time',  'score_diff']
    for col in numerical_columns:
        if col in df_encoded.columns:
            df_encoded[col] = df_encoded[col].fillna(df_encoded[col].median())
    
    return df_encoded, label_encoders

def perform_galaxy_clustering(df_encoded):
    """Step 1: Use UMAP + HDBSCAN to determine galaxies from base features"""
    print("Step 1: Creating galaxies using UMAP + HDBSCAN...")
    
    # Use only base features (no name similarity)
    base_features = df_encoded.values
    
    # Scale features
    scaler = StandardScaler()
    features_scaled = scaler.fit_transform(base_features)
    
    print(f"Clustering {len(features_scaled)} goals with {features_scaled.shape[1]} base features")
    
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
    
    # Apply HDBSCAN clustering to create galaxies
    print("Applying HDBSCAN clustering...")
    clusterer = hdbscan.HDBSCAN(
        min_cluster_size=100,
    )
    galaxy_labels = clusterer.fit_predict(umap_features)
    
    # Handle noise points by assigning them to the nearest galaxy
    noise_mask = galaxy_labels == -1
    if noise_mask.sum() > 0:
        print(f"  Assigning {noise_mask.sum()} noise points to galaxy 0...")
        galaxy_labels[noise_mask] = 0
    
    # Check clustering results
    unique_galaxies = np.unique(galaxy_labels)
    n_galaxies = len(unique_galaxies)
    
    print(f"Galaxy clustering results:")
    print(f"  Number of galaxies: {n_galaxies}")
    for galaxy_id in unique_galaxies:
        count = np.sum(galaxy_labels == galaxy_id)
        print(f"    Galaxy {galaxy_id}: {count} goals")
    
    return galaxy_labels

def cluster_by_player_similarity(df_original, df_encoded, galaxy_labels):
    """Step 2: Within each galaxy, cluster by player name similarity (SWAPPED ORDER)"""
    print("Step 2: Creating clusters by player name similarity within galaxies...")
    
    cluster_labels = np.full(len(df_encoded), -1, dtype=int)
    cluster_id = 0
    
    unique_galaxies = np.unique(galaxy_labels)
    similarity_threshold = 0.5 
    
    for galaxy_id in unique_galaxies:
        galaxy_mask = galaxy_labels == galaxy_id
        galaxy_indices = np.where(galaxy_mask)[0]
        galaxy_original_indices = df_encoded.index[galaxy_indices]
        
        print(f"\n  Processing Galaxy {galaxy_id} ({len(galaxy_indices)} goals)...")
        
        # Get player names for this galaxy
        galaxy_players = df_original.loc[galaxy_original_indices, 'player_name'].fillna('Unknown')
        unique_players = galaxy_players.unique()
        
        print(f"    Found {len(unique_players)} unique players in galaxy")
        
        # Create similarity matrix between players
        similarity_matrix = np.zeros((len(unique_players), len(unique_players)))
        
        for i, player1 in enumerate(unique_players):
            for j, player2 in enumerate(unique_players):
                if i == j:
                    similarity_matrix[i, j] = 1.0
                else:
                    similarity = calculate_name_similarity(player1, player2)
                    similarity_matrix[i, j] = similarity
        
        # Group players by similarity threshold
        player_clusters = {}
        clustered_players = set()
        miscellaneous_players = []  # NEW: For players that don't match threshold
        
        for i, player in enumerate(unique_players):
            if player in clustered_players:
                continue
                
            # Find similar players
            similar_players = []
            for j, other_player in enumerate(unique_players):
                if similarity_matrix[i, j] >= similarity_threshold:
                    similar_players.append(other_player)
                    clustered_players.add(other_player)
            
            # Only create cluster if we have more than just the single player (similarity matches)
            if len(similar_players) > 1:
                player_clusters[cluster_id] = similar_players
                cluster_id += 1
            elif len(similar_players) == 1:  # Just the player themselves
                miscellaneous_players.append(similar_players[0])
                clustered_players.add(similar_players[0])
        
        # Create miscellaneous cluster for non-matching players
        if miscellaneous_players:
            player_clusters[cluster_id] = miscellaneous_players
            print(f"    Created miscellaneous cluster {cluster_id} with {len(miscellaneous_players)} non-matching players")
            cluster_id += 1
        
        # Assign cluster labels to goals based on their player
        for current_cluster_id, players_in_cluster in player_clusters.items():
            for player in players_in_cluster:
                player_goals_mask = galaxy_players == player
                player_goal_indices = galaxy_indices[player_goals_mask]
                cluster_labels[player_goal_indices] = current_cluster_id
        
        print(f"    Created {len(player_clusters)} player clusters")
        for cid, players in player_clusters.items():
            goal_count = np.sum(cluster_labels == cid)
            if len(players) > 10:  # Only show details for smaller clusters
                print(f"      Cluster {cid}: {len(players)} players, {goal_count} goals")
            else:
                print(f"      Cluster {cid}: {len(players)} players ({', '.join(players[:5])}{'...' if len(players) > 5 else ''}), {goal_count} goals")
    
    print(f"\nTotal clusters created: {len(np.unique(cluster_labels[cluster_labels >= 0]))}")
    return cluster_labels

def cluster_by_goalie_similarity(df_original, df_encoded, cluster_labels):
    """Step 3: Within each cluster, create solar systems by goalie name similarity (SWAPPED ORDER)"""
    print("Step 3: Creating solar systems by goalie name similarity within clusters...")
    
    solar_system_labels = np.full(len(df_encoded), -1, dtype=int)
    solar_system_id = 0
    
    unique_clusters = np.unique(cluster_labels[cluster_labels >= 0])
    similarity_threshold = 0.4  # LOWERED THRESHOLD
    
    for cluster_id in unique_clusters:
        cluster_mask = cluster_labels == cluster_id
        cluster_indices = np.where(cluster_mask)[0]
        cluster_original_indices = df_encoded.index[cluster_indices]
        
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
        miscellaneous_goalies = []  # NEW: For goalies that don't match threshold
        
        for i, goalie in enumerate(unique_goalies):
            if goalie in clustered_goalies:
                continue
                
            # Find similar goalies
            similar_goalies = []
            for j, other_goalie in enumerate(unique_goalies):
                if similarity_matrix[i, j] >= similarity_threshold:
                    similar_goalies.append(other_goalie)
                    clustered_goalies.add(other_goalie)
            
            # Only create solar system if we have more than just the single goalie (similarity matches)
            if len(similar_goalies) > 1:
                goalie_clusters[solar_system_id] = similar_goalies
                solar_system_id += 1
            elif len(similar_goalies) == 1:  # Just the goalie themselves
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
            if len(goalies) > 10:  # Only show details for smaller systems
                print(f"      Solar System {sid}: {len(goalies)} goalies, {goal_count} goals")
            else:
                print(f"      Solar System {sid}: {len(goalies)} goalies ({', '.join(goalies[:5])}{'...' if len(goalies) > 5 else ''}), {goal_count} goals")
    
    print(f"\nTotal solar systems created: {len(np.unique(solar_system_labels[solar_system_labels >= 0]))}")
    return solar_system_labels

def create_goal_hierarchy_mapping_FIXED(galaxy_labels, cluster_labels, solar_system_labels, df_encoded, df_original):
    """Create goal hierarchy mapping with proper star assignments"""
    print("Creating goal hierarchy mapping with FIXED star assignments...")
    
    # Create mapping data
    mapping_data = []
    
    # Group goals by solar system to assign relative star IDs
    goals_by_solar_system = {}
    for i in range(len(df_encoded)):
        solar_system_id = solar_system_labels[i]
        if solar_system_id not in goals_by_solar_system:
            goals_by_solar_system[solar_system_id] = []
        goals_by_solar_system[solar_system_id].append(i)
    
    for i in range(len(df_encoded)):
        # Get the original goal data
        original_idx = df_encoded.index[i]
        goal_row = df_original.loc[original_idx]
        
        # Get hierarchical assignments
        galaxy_id = galaxy_labels[i]
        cluster_id = cluster_labels[i] 
        solar_system_id = solar_system_labels[i]
        
        # FIXED: Assign star ID relative to solar system
        goals_in_same_system = goals_by_solar_system[solar_system_id]
        star_id = goals_in_same_system.index(i)  # 0-based index within this solar system
        
        # Create hierarchical path components
        galaxy_name = f"galaxy_{galaxy_id}"
        cluster_name = f"cluster_{cluster_id}"
        solar_system_name = f"solar system_{solar_system_id}"
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
        'shot_type', 'goalie', 'home_team_defending_side', 'score_diff',
        'game_date', 'team_name', 'player_name', 'goalie_name', 'time_minutes', 'time_seconds',
        'period_time', 'month', 'day', 'home_team'
    ]
    
    hierarchy_columns = [
        'goal_index', 'deepest_cluster', 'hierarchy_level', 'hierarchy_path', 'cluster_size',
        'level_0_cluster', 'level_1_cluster', 'level_2_cluster', 'level_3_cluster'
    ]
    
    # Reorder columns to match format
    available_base_columns = [col for col in base_columns if col in mapping_df.columns]
    column_order = available_base_columns + hierarchy_columns
    mapping_df = mapping_df[column_order]
    
    return mapping_df

def main():
    """Main function to run the FINAL hierarchical clustering"""
    print("=== FINAL UMAP + HDBSCAN + NAME SIMILARITY CLUSTERING ===")
    print("Galaxies: UMAP+HDBSCAN | Clusters: Player similarity | Solar Systems: Goalie similarity")
    print("Threshold: 0.4 | Non-matching names grouped into miscellaneous units")
    
    # Create output directory
    os.makedirs('sequential_clustering', exist_ok=True)
    
    # Load and prepare data
    df_subset, df_original = load_and_prepare_data()
    
    # Encode categorical features
    df_encoded, label_encoders = encode_categorical_features(df_subset)
    
    # Step 1: Create galaxies using UMAP + HDBSCAN
    galaxy_labels = perform_galaxy_clustering(df_encoded)

    # Step 3: Within each cluster, create solar systems by GOALIE name similarity (SWAPPED)
    cluster_labels = cluster_by_goalie_similarity(df_original, df_encoded, galaxy_labels)
    
    # Step 2: Within each galaxy, cluster by PLAYER name similarity (SWAPPED)
    solar_system_labels = cluster_by_player_similarity(df_original, df_encoded, cluster_labels)
    
    # Create goal hierarchy mapping with FIXED star assignments
    mapping_df = create_goal_hierarchy_mapping_FIXED(galaxy_labels, cluster_labels, solar_system_labels, df_encoded, df_original)
    
    # Save the output
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f'sequential_clustering/goal_hierarchy_mapping_umap_hdbscan_FINAL_{timestamp}.csv'
    mapping_df.to_csv(output_file, index=False)
    
    print(f"\n✅ FINAL hierarchical clustering complete!")
    print(f"Output file: {output_file}")
    print(f"Total goals processed: {len(mapping_df):,}")
    
    # Final statistics
    n_galaxies = len(np.unique(galaxy_labels))
    n_clusters = len(np.unique(cluster_labels[cluster_labels >= 0]))
    n_solar_systems = len(np.unique(solar_system_labels[solar_system_labels >= 0]))
    
    print(f"\n=== FINAL HIERARCHY ===")
    print(f"Galaxies: {n_galaxies}")
    print(f"Clusters (player similarity): {n_clusters}")
    print(f"Solar Systems (goalie similarity): {n_solar_systems}")
    print(f"Stars: {len(mapping_df)}")
    
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