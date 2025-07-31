import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.preprocessing import StandardScaler, LabelEncoder
import hdbscan
import umap
from datetime import datetime
import os
import time
import logging
import warnings
import itertools
warnings.filterwarnings('ignore')

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

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

def perform_umap_hdbscan_clustering(df_encoded, step_name, umap_params, hdbscan_params):
    """Perform UMAP + HDBSCAN clustering with specified parameters"""
    print(f"{step_name}: Performing UMAP + HDBSCAN clustering...")
    print(f"  UMAP params: {umap_params}")
    print(f"  HDBSCAN params: {hdbscan_params}")
    
    # Scale features
    scaler = StandardScaler()
    features_scaled = scaler.fit_transform(df_encoded.values)
    
    print(f"Clustering {len(features_scaled)} goals with {features_scaled.shape[1]} features")
    
    # Apply UMAP for dimensionality reduction
    print("Applying UMAP dimensionality reduction...")
    umap_reducer = umap.UMAP(
        random_state=42,
        **umap_params
    )
    umap_features = umap_reducer.fit_transform(features_scaled)
    print(f"UMAP reduced to {umap_features.shape[1]} dimensions")
    
    # Apply HDBSCAN clustering
    print("Applying HDBSCAN clustering...")
    clusterer = hdbscan.HDBSCAN(**hdbscan_params)
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
    
    return cluster_labels, umap_features, clusterer

def evaluate_clustering_quality(cluster_labels, features):
    """Evaluate clustering quality using various metrics"""
    from sklearn.metrics import silhouette_score, calinski_harabasz_score, davies_bouldin_score
    
    unique_labels = np.unique(cluster_labels)
    n_clusters = len(unique_labels)
    
    # Skip evaluation if we have only one cluster or too few samples
    if n_clusters < 2 or len(features) < 10:
        return {
            'n_clusters': n_clusters,
            'silhouette_score': -1,
            'calinski_harabasz_score': -1,
            'davies_bouldin_score': float('inf')
        }
    
    try:
        silhouette = silhouette_score(features, cluster_labels)
        calinski_harabasz = calinski_harabasz_score(features, cluster_labels)
        davies_bouldin = davies_bouldin_score(features, cluster_labels)
        
        return {
            'n_clusters': n_clusters,
            'silhouette_score': silhouette,
            'calinski_harabasz_score': calinski_harabasz,
            'davies_bouldin_score': davies_bouldin
        }
    except Exception as e:
        logger.warning(f"Error calculating clustering metrics: {e}")
        return {
            'n_clusters': n_clusters,
            'silhouette_score': -1,
            'calinski_harabasz_score': -1,
            'davies_bouldin_score': float('inf')
        }

def explore_hyperparameters():
    """Explore different hyperparameter combinations for the multiple rounds clustering"""
    print("🔍 HYPERPARAMETER EXPLORATION FOR MULTIPLE ROUNDS CLUSTERING")
    print("=" * 80)
    
    # Load and prepare data
    df_subset, df_original = load_and_prepare_data()
    
    # Define hyperparameter grids
    umap_param_grid = {
        'n_components': [10, 15, 20],
        'n_neighbors': [10, 15, 20],
        'min_dist': [0.05, 0.1, 0.15]
    }
    
    hdbscan_param_grid = {
        'min_cluster_size': [50, 100, 150],
        'min_samples': [None]  # Use default (min_cluster_size)
    }
    
    # Create all combinations
    umap_combinations = list(itertools.product(*umap_param_grid.values()))
    hdbscan_combinations = list(itertools.product(*hdbscan_param_grid.values()))
    
    print(f"Testing {len(umap_combinations)} UMAP × {len(hdbscan_combinations)} HDBSCAN = {len(umap_combinations) * len(hdbscan_combinations)} combinations")
    print()
    
    results = []
    total_combinations = len(umap_combinations) * len(hdbscan_combinations)
    
    for combo_idx, (umap_combo, hdbscan_combo) in enumerate(itertools.product(umap_combinations, hdbscan_combinations), 1):
        print(f"Testing combination {combo_idx}/{total_combinations}")
        
        # Create parameter dictionaries
        umap_params = dict(zip(umap_param_grid.keys(), umap_combo))
        hdbscan_params = dict(zip(hdbscan_param_grid.keys(), hdbscan_combo))
        # Remove None values
        hdbscan_params = {k: v for k, v in hdbscan_params.items() if v is not None}
        
        try:
            # Step 1: Galaxy clustering (spatial/shot features)
            galaxy_features = ['shot_zone', 'shot_type', 'situation']
            df_encoded_galaxy, _ = encode_categorical_features(df_subset, galaxy_features)
            
            galaxy_labels, galaxy_umap, galaxy_clusterer = perform_umap_hdbscan_clustering(
                df_encoded_galaxy, 
                f"Galaxy clustering {combo_idx}",
                umap_params,
                hdbscan_params
            )
            
            # Evaluate galaxy clustering
            galaxy_metrics = evaluate_clustering_quality(galaxy_labels, galaxy_umap)
            
            # Step 2: Cluster clustering within galaxies (sample approach - test on largest galaxy)
            unique_galaxies = np.unique(galaxy_labels)
            largest_galaxy_id = None
            largest_galaxy_size = 0
            
            for galaxy_id in unique_galaxies:
                galaxy_mask = galaxy_labels == galaxy_id
                galaxy_size = galaxy_mask.sum()
                if galaxy_size > largest_galaxy_size:
                    largest_galaxy_size = galaxy_size
                    largest_galaxy_id = galaxy_id
            
            cluster_metrics = {'n_clusters': 0, 'silhouette_score': -1, 'calinski_harabasz_score': -1, 'davies_bouldin_score': float('inf')}
            
            if largest_galaxy_id is not None and largest_galaxy_size >= 100:
                # Test cluster clustering on largest galaxy
                galaxy_mask = galaxy_labels == largest_galaxy_id
                galaxy_indices = np.where(galaxy_mask)[0]
                galaxy_data = df_subset.iloc[galaxy_indices]
                
                cluster_features = ['game_time', 'team_score', 'opponent_score']
                df_encoded_cluster, _ = encode_categorical_features(galaxy_data, cluster_features)
                
                if len(df_encoded_cluster) >= hdbscan_params.get('min_cluster_size', 50):
                    cluster_labels, cluster_umap, cluster_clusterer = perform_umap_hdbscan_clustering(
                        df_encoded_cluster,
                        f"Cluster clustering {combo_idx}",
                        umap_params,
                        hdbscan_params
                    )
                    cluster_metrics = evaluate_clustering_quality(cluster_labels, cluster_umap)
            
            # Store results
            result = {
                'combo_idx': combo_idx,
                'umap_params': umap_params.copy(),
                'hdbscan_params': hdbscan_params.copy(),
                'galaxy_n_clusters': galaxy_metrics['n_clusters'],
                'galaxy_silhouette': galaxy_metrics['silhouette_score'],
                'galaxy_calinski_harabasz': galaxy_metrics['calinski_harabasz_score'],
                'galaxy_davies_bouldin': galaxy_metrics['davies_bouldin_score'],
                'cluster_n_clusters': cluster_metrics['n_clusters'],
                'cluster_silhouette': cluster_metrics['silhouette_score'],
                'cluster_calinski_harabasz': cluster_metrics['calinski_harabasz_score'],
                'cluster_davies_bouldin': cluster_metrics['davies_bouldin_score'],
                'largest_galaxy_size': largest_galaxy_size
            }
            results.append(result)
            
            print(f"  Galaxy clusters: {galaxy_metrics['n_clusters']}, Silhouette: {galaxy_metrics['silhouette_score']:.3f}")
            print(f"  Largest galaxy size: {largest_galaxy_size}, Cluster sub-clusters: {cluster_metrics['n_clusters']}")
            print()
            
        except Exception as e:
            logger.error(f"Error in combination {combo_idx}: {e}")
            continue
    
    return results

def analyze_hyperparameter_results(results):
    """Analyze and visualize hyperparameter exploration results"""
    print("\n" + "="*80)
    print("HYPERPARAMETER EXPLORATION RESULTS ANALYSIS")
    print("="*80)
    
    if not results:
        print("No valid results to analyze!")
        return
    
    # Convert to DataFrame for easier analysis
    df_results = pd.DataFrame(results)
    
    # Print summary statistics
    print(f"Total valid combinations tested: {len(df_results)}")
    print()
    
    # Find best combinations by different criteria
    valid_galaxy_results = df_results[df_results['galaxy_silhouette'] > -1]
    valid_cluster_results = df_results[df_results['cluster_silhouette'] > -1]
    
    if len(valid_galaxy_results) > 0:
        print("TOP 5 COMBINATIONS BY GALAXY CLUSTERING QUALITY:")
        print("-" * 50)
        
        # Sort by galaxy silhouette score
        top_galaxy = valid_galaxy_results.nlargest(5, 'galaxy_silhouette')
        
        for idx, row in top_galaxy.iterrows():
            print(f"Rank {idx+1}:")
            print(f"  UMAP params: {row['umap_params']}")
            print(f"  HDBSCAN params: {row['hdbscan_params']}")
            print(f"  Galaxy clusters: {row['galaxy_n_clusters']}")
            print(f"  Galaxy silhouette: {row['galaxy_silhouette']:.4f}")
            print(f"  Galaxy Calinski-Harabasz: {row['galaxy_calinski_harabasz']:.2f}")
            print(f"  Galaxy Davies-Bouldin: {row['galaxy_davies_bouldin']:.4f}")
            print()
    
    if len(valid_cluster_results) > 0:
        print("TOP 5 COMBINATIONS BY CLUSTER CLUSTERING QUALITY:")
        print("-" * 50)
        
        # Sort by cluster silhouette score
        top_cluster = valid_cluster_results.nlargest(5, 'cluster_silhouette')
        
        for idx, row in top_cluster.iterrows():
            print(f"Rank {idx+1}:")
            print(f"  UMAP params: {row['umap_params']}")
            print(f"  HDBSCAN params: {row['hdbscan_params']}")
            print(f"  Cluster sub-clusters: {row['cluster_n_clusters']}")
            print(f"  Cluster silhouette: {row['cluster_silhouette']:.4f}")
            print(f"  Cluster Calinski-Harabasz: {row['cluster_calinski_harabasz']:.2f}")
            print(f"  Cluster Davies-Bouldin: {row['cluster_davies_bouldin']:.4f}")
            print(f"  Largest galaxy size: {row['largest_galaxy_size']}")
            print()
    
    # Create visualizations
    create_hyperparameter_visualizations(df_results)
    
    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f'hyperparameter_exploration_results_{timestamp}.csv'
    df_results.to_csv(output_file, index=False)
    print(f"Detailed results saved to: {output_file}")
    
    return df_results

def create_hyperparameter_visualizations(df_results):
    """Create visualizations of hyperparameter exploration results"""
    print("Creating hyperparameter exploration visualizations...")
    
    plt.style.use('default')
    fig, axes = plt.subplots(2, 3, figsize=(18, 12))
    fig.suptitle('Hyperparameter Exploration Results', fontsize=16)
    
    # Filter valid results
    valid_results = df_results[df_results['galaxy_silhouette'] > -1]
    
    if len(valid_results) == 0:
        plt.text(0.5, 0.5, 'No valid results to visualize', 
                ha='center', va='center', transform=fig.transFigure, fontsize=16)
        plt.tight_layout()
        plt.savefig('hyperparameter_exploration_results.png', dpi=300, bbox_inches='tight')
        plt.show()
        return
    
    # 1. Galaxy clusters vs UMAP n_components
    ax = axes[0, 0]
    umap_n_components = [params['n_components'] for params in valid_results['umap_params']]
    ax.scatter(umap_n_components, valid_results['galaxy_n_clusters'], alpha=0.6)
    ax.set_xlabel('UMAP n_components')
    ax.set_ylabel('Number of Galaxy Clusters')
    ax.set_title('Galaxy Clusters vs UMAP Components')
    
    # 2. Galaxy silhouette vs UMAP n_neighbors
    ax = axes[0, 1]
    umap_n_neighbors = [params['n_neighbors'] for params in valid_results['umap_params']]
    ax.scatter(umap_n_neighbors, valid_results['galaxy_silhouette'], alpha=0.6)
    ax.set_xlabel('UMAP n_neighbors')
    ax.set_ylabel('Galaxy Silhouette Score')
    ax.set_title('Galaxy Quality vs UMAP Neighbors')
    
    # 3. Galaxy clusters vs HDBSCAN min_cluster_size
    ax = axes[0, 2]
    hdbscan_min_size = [params['min_cluster_size'] for params in valid_results['hdbscan_params']]
    ax.scatter(hdbscan_min_size, valid_results['galaxy_n_clusters'], alpha=0.6)
    ax.set_xlabel('HDBSCAN min_cluster_size')
    ax.set_ylabel('Number of Galaxy Clusters')
    ax.set_title('Galaxy Clusters vs HDBSCAN Min Size')
    
    # 4. Silhouette distribution
    ax = axes[1, 0]
    ax.hist(valid_results['galaxy_silhouette'], bins=20, alpha=0.7, edgecolor='black')
    ax.set_xlabel('Galaxy Silhouette Score')
    ax.set_ylabel('Frequency')
    ax.set_title('Distribution of Galaxy Silhouette Scores')
    
    # 5. Parameter correlation heatmap
    ax = axes[1, 1]
    # Create correlation matrix for numeric parameters
    param_data = []
    for _, row in valid_results.iterrows():
        param_row = [
            row['umap_params']['n_components'],
            row['umap_params']['n_neighbors'],
            row['umap_params']['min_dist'],
            row['hdbscan_params']['min_cluster_size'],
            row['galaxy_silhouette'],
            row['galaxy_n_clusters']
        ]
        param_data.append(param_row)
    
    param_df = pd.DataFrame(param_data, columns=[
        'UMAP_n_comp', 'UMAP_n_neigh', 'UMAP_min_dist', 
        'HDBSCAN_min_size', 'Silhouette', 'N_Clusters'
    ])
    
    corr_matrix = param_df.corr()
    sns.heatmap(corr_matrix, annot=True, cmap='coolwarm', center=0, ax=ax)
    ax.set_title('Parameter Correlation Matrix')
    
    # 6. Best parameter combinations
    ax = axes[1, 2]
    top_5 = valid_results.nlargest(5, 'galaxy_silhouette').reset_index()
    y_pos = range(len(top_5))
    ax.barh(y_pos, top_5['galaxy_silhouette'])
    ax.set_yticks(y_pos)
    ax.set_yticklabels([f"Combo {row['combo_idx']}" for _, row in top_5.iterrows()])
    ax.set_xlabel('Galaxy Silhouette Score')
    ax.set_title('Top 5 Parameter Combinations')
    
    plt.tight_layout()
    plt.savefig('hyperparameter_exploration_results.png', dpi=300, bbox_inches='tight')
    plt.show()
    
    print("Visualizations saved as 'hyperparameter_exploration_results.png'")

def main():
    """Main execution function for hyperparameter exploration"""
    print("🔍 NHL GOAL CLUSTERING - HYPERPARAMETER EXPLORATION 🔍")
    print("=" * 80)
    print("Exploring optimal UMAP + HDBSCAN parameters for multiple rounds clustering")
    print("=" * 80)
    
    # Run hyperparameter exploration
    results = explore_hyperparameters()
    
    # Analyze results
    df_results = analyze_hyperparameter_results(results)
    
    print(f"\n" + "="*80)
    print("🔍 HYPERPARAMETER EXPLORATION COMPLETE 🔍")
    print("="*80)
    print(f"Tested {len(results)} parameter combinations")
    print("Check 'hyperparameter_exploration_results.png' for visualizations")
    print("Check CSV file for detailed numerical results")

if __name__ == "__main__":
    main()