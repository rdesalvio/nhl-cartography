"""
Sequential Hierarchical Clustering for NHL Goals Cartography

This module implements a hierarchical clustering approach where goals are clustered
sequentially by different features, creating a natural cartography-like structure
suitable for visualization as galaxies, continents, and regions.

Clustering sequence:
1. x,y coordinates (spatial regions - "continents")
2. shot_type (shot style within regions - "countries")
3. time_minutes, time_seconds (game time - "provinces")
4. team_score, opponent_score (score situation - "districts")
5. period (game period - "zones")
6. month, day (temporal patterns - "neighborhoods")
7. goalie (opponent goalie - "streets")
8. player_name (individual identity - "addresses")
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.cluster import KMeans, DBSCAN
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.metrics import silhouette_score
from scipy.spatial import ConvexHull
import json
import os
import logging
from datetime import datetime
import warnings
import time
warnings.filterwarnings('ignore')

# Set up logging first
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

# Set matplotlib style
plt.style.use('dark_background')
plt.rcParams['figure.figsize'] = (16, 12)
plt.rcParams['font.size'] = 10


class SequentialHierarchicalClusterer:
    """
    Hierarchical clustering implementation that clusters goals sequentially
    by different features to create natural cartography-like structures.
    """
    
    def __init__(self, output_dir='sequential_clustering'):
        self.output_dir = output_dir
        self.goals_df = None
        self.hierarchy = {}
        self.clustering_config = {}
        self.results = {}
        
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        # Define clustering sequence with parameters (3-level approach)
        self.clustering_sequence = [
            {
                'name': 'spatial_shot',
                'features': ['x', 'y', 'shot_type', 'team_id'],
                'method': 'mixed_clustering',
                'n_clusters': 12,
                'level_name': 'galaxy',
                'description': 'Spatial position and shot type clusters'
            },
            {
                'name': 'game_context',
                'features': ['period', 'period_time', 'team_score', 'opponent_score'],
                'method': 'kmeans',
                'n_clusters': 8,
                'level_name': 'cluster',
                'description': 'Game timing and score situation within spatial-shot clusters'
            },
            {
                'name': 'player',
                'features': ['player_name'],
                'method': 'categorical',
                'level_name': 'solar system',
                'description': 'Individual players within game context clusters'
            },
            {
                'name': 'goalie',
                'features': ['goalie'],
                'method': 'categorical',
                'level_name': 'star',
                'description': 'Individual goalies within game context clusters'
            }
        ]
        
        logger.info(f"Initialized SequentialHierarchicalClusterer")
        logger.info(f"Output directory: {output_dir}")
        
        # Track generated names to ensure uniqueness
        self.generated_names = {
            'galaxy': set(),
            'cluster': set(), 
            'solar system': set(),
            'star': set()
        }
        
        # Rate limiting for Anthropic API (much more generous limits with pro plan)
        self.last_api_call_time = 0
        self.api_rate_limit_seconds = 0.5  # Conservative 0.5 second between calls for pro plan
        
        logger.info(f"Clustering levels: {len(self.clustering_sequence)}")
        logger.info(f"API rate limit: {60/self.api_rate_limit_seconds:.0f} requests per minute")
    
    def generate_cluster_name(self, level_name, cluster_goals, features_used):
        """
        Generate a unique astronomical cluster name using AI based on cluster context.
        
        Args:
            level_name: Type of celestial object (galaxy, cluster, solar system, star)
            cluster_goals: DataFrame of goals in this cluster
            features_used: List of features used for clustering at this level
            
        Returns:
            str: Generated astronomical name
        """
        if not AI_AVAILABLE:
            # Fallback to generic naming
            base_name = f"{level_name}_{len(self.generated_names[level_name])}"
            self.generated_names[level_name].add(base_name)
            return base_name
        
        try:
            # Rate limiting: conservative delay for Anthropic API
            current_time = time.time()
            time_since_last_call = current_time - self.last_api_call_time
            
            if time_since_last_call < self.api_rate_limit_seconds:
                sleep_time = self.api_rate_limit_seconds - time_since_last_call
                logger.info(f"Rate limiting: sleeping for {sleep_time:.2f} seconds")
                time.sleep(sleep_time)
            
            # Prepare cluster context information
            context_info = []
            
            # Analyze features used for clustering
            if 'x' in features_used and 'y' in features_used:
                x_range = f"{cluster_goals['x'].min():.0f} to {cluster_goals['x'].max():.0f}"
                y_range = f"{cluster_goals['y'].min():.0f} to {cluster_goals['y'].max():.0f}" 
                context_info.append(f"Spatial coordinates: x={x_range}, y={y_range}")
            
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
            
            if 'team_name' in cluster_goals.columns:
                top_teams = cluster_goals['team_name'].value_counts().head(3)
                context_info.append(f"Primary teams: {', '.join([f'{team} ({count})' for team, count in top_teams.items()])}")
            
            # Add temporal context if available
            if 'month' in cluster_goals.columns:
                months = cluster_goals['month'].value_counts().head(2)
                month_names = {1: 'Jan', 2: 'Feb', 3: 'Mar', 4: 'Apr', 5: 'May', 6: 'Jun',
                              7: 'Jul', 8: 'Aug', 9: 'Sep', 10: 'Oct', 11: 'Nov', 12: 'Dec'}
                context_info.append(f"Peak months: {', '.join([f'{month_names.get(month, month)} ({count})' for month, count in months.items()])}")
            
            # Build the prompt (removed uniqueness checking to save context)
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
            self.last_api_call_time = time.time()
            
            generated_name = response.content[0].text.strip().replace('"', '').replace("'", "")
            
            # Ensure uniqueness
            if generated_name in self.generated_names[level_name]:
                # Add a suffix if name already exists
                counter = 1
                while f"{generated_name} {counter}" in self.generated_names[level_name]:
                    counter += 1
                generated_name = f"{generated_name} {counter}"
            
            self.generated_names[level_name].add(generated_name)
            logger.info(f"Generated {level_name} name: '{generated_name}'")
            return generated_name
            
        except Exception as e:
            logger.warning(f"Failed to generate AI name for {level_name}: {e}")
            # Fallback to generic naming
            base_name = f"{level_name}_{len(self.generated_names[level_name])}"
            self.generated_names[level_name].add(base_name)
            return base_name
    
    def load_and_prepare_data(self, csv_path='data/nhl_goals_with_names.csv'):
        """Load and prepare goal data for sequential clustering"""
        logger.info("Loading and preparing goal data...")
        
        # Load data
        df = pd.read_csv(csv_path)
        logger.info(f"Loaded {len(df)} total goals")
        
        # Filter for recent goals with coordinates (same as similarity.py)
        df['game_date'] = pd.to_datetime(df['game_date'])
        df_recent = df[df['game_date'] >= '2023-10-09'].copy()
        logger.info(f"Goals from 2023 onwards: {len(df_recent):,}")
        
        # Filter for goals with coordinates
        has_coords = ((df_recent['x'] != 0) | (df_recent['y'] != 0))
        df_coords = df_recent[has_coords].copy()
        logger.info(f"Goals with coordinates: {len(df_coords):,}")
        
        # Prepare features
        self._prepare_features(df_coords)
        
        self.goals_df = df_coords.reset_index(drop=True)
        logger.info(f"Final dataset: {len(self.goals_df)} goals ready for clustering")
        
        return self.goals_df
    
    def _prepare_features(self, df):
        """Prepare and extract features needed for clustering"""
        logger.info("Preparing clustering features...")
        
        # Parse time components if needed
        if 'time' in df.columns and 'time_seconds' not in df.columns:
            time_parts = df['time'].str.split(':')
            df['time_minutes'] = time_parts.str[0].astype(float)
            df['time_seconds'] = time_parts.str[1].astype(float)


        df['period_time'] = (df['time_minutes'] * 60) + df['time_seconds']
        
        # Extract date components if needed
        if 'month' not in df.columns:
            df['month'] = df['game_date'].dt.month
            df['day'] = df['game_date'].dt.day
        
        # Normalize coordinates to same side of ice
        df['x'] = df['x'].apply(lambda x: x if x >= 0 else -x)
        df['y'] = df['y'].apply(lambda y: y if y >= 0 else -y)
        
        # Fill missing categorical values
        categorical_features = ['shot_type', 'goalie', 'player_name', 'team']
        for feature in categorical_features:
            if feature in df.columns:
                df[feature] = df[feature].fillna('unknown')
        
        # Fill missing numerical values
        numerical_features = ['period_time', 'team_score', 'opponent_score', 'period']
        for feature in numerical_features:
            if feature in df.columns:
                df[feature] = df[feature].fillna(0)
        
        logger.info("Feature preparation complete")
    
    def perform_sequential_clustering(self, max_cluster_size=1000):
        """
        Perform sequential hierarchical clustering following the defined sequence.
        
        Args:
            max_cluster_size: Maximum size for a cluster before further subdivision
        """
        logger.info("Starting sequential hierarchical clustering...")
        
        if self.goals_df is None:
            logger.error("No data loaded. Call load_and_prepare_data() first.")
            return None
        
        # Initialize hierarchy with all goals at root
        self.hierarchy = {
            'root': {
                'goal_indices': list(range(len(self.goals_df))),
                'level': -1,
                'parent': None,
                'children': [],
                'cluster_id': 'root',
                'size': len(self.goals_df)
            }
        }
        
        # Track current clusters to process
        clusters_to_process = [('root', self.hierarchy['root'])]
        
        # Process each clustering level
        for level_idx, level_config in enumerate(self.clustering_sequence):
            logger.info(f"\nLevel {level_idx + 1}: {level_config['name']} clustering ({level_config['level_name']})")
            
            new_clusters_to_process = []
            
            # Process each cluster from previous level
            for cluster_id, cluster_info in clusters_to_process:
                goal_indices = cluster_info['goal_indices']
                
                # Skip if cluster is too small to subdivide meaningfully
                if len(goal_indices) < 10:
                    logger.info(f"  Skipping subdivision of {cluster_id} (only {len(goal_indices)} goals)")
                    continue
                
                # Skip if cluster is small enough (under max_cluster_size)
                if len(goal_indices) < max_cluster_size:
                    logger.info(f"  Skipping subdivision of {cluster_id} (under {max_cluster_size} goals)")
                    continue
                
                logger.info(f"  Clustering {cluster_id} ({len(goal_indices)} goals)")
                
                # Extract data for this cluster
                cluster_data = self.goals_df.iloc[goal_indices]
                
                # Perform clustering for this level
                sub_clusters = self._cluster_at_level(cluster_data, level_config, goal_indices, cluster_id)
                
                if sub_clusters:
                    # Add sub-clusters to hierarchy
                    for sub_cluster_id, sub_cluster_info in sub_clusters.items():
                        full_cluster_id = f"{cluster_id}.{sub_cluster_id}"
                        
                        self.hierarchy[full_cluster_id] = {
                            'goal_indices': sub_cluster_info['goal_indices'],
                            'level': level_idx,
                            'parent': cluster_id,
                            'children': [],
                            'cluster_id': full_cluster_id,
                            'size': len(sub_cluster_info['goal_indices']),
                            'cluster_center': sub_cluster_info.get('center'),
                            'level_name': level_config['level_name']
                        }
                        
                        # Update parent's children list
                        self.hierarchy[cluster_id]['children'].append(full_cluster_id)
                        
                        # Add to next level processing
                        new_clusters_to_process.append((full_cluster_id, self.hierarchy[full_cluster_id]))
                
            clusters_to_process = new_clusters_to_process
            logger.info(f"  Created {len(new_clusters_to_process)} clusters for next level")
            
            if not clusters_to_process:
                logger.info(f"  No more clusters to subdivide. Stopping at level {level_idx + 1}")
                break
        
        logger.info(f"\nSequential clustering complete!")
        logger.info(f"Total clusters created: {len(self.hierarchy)}")
        
        # Analyze results
        self._analyze_hierarchy()
        
        return self.hierarchy
    
    def _cluster_at_level(self, data, level_config, goal_indices, parent_cluster_id='root'):
        """Perform clustering at a specific level"""
        method = level_config['method']
        features = level_config['features']
        
        # Check if all features exist
        missing_features = [f for f in features if f not in data.columns]
        if missing_features:
            logger.warning(f"    Missing features {missing_features}, skipping this level")
            return None
        
        # Extract feature data
        feature_data = data[features].copy()
        
        if method == 'categorical':
            return self._categorical_clustering(feature_data, features, goal_indices, parent_cluster_id, level_config)
        elif method == 'kmeans':
            n_clusters = level_config.get('n_clusters', 5)
            return self._kmeans_clustering(feature_data, features, goal_indices, n_clusters, level_config)
        elif method == 'dbscan':
            return self._dbscan_clustering(feature_data, features, goal_indices, level_config)
        elif method == 'mixed_clustering':
            n_clusters = level_config.get('n_clusters', 8)
            return self._mixed_clustering(feature_data, features, goal_indices, n_clusters, level_config)
        else:
            logger.warning(f"    Unknown clustering method: {method}")
            return None
    
    def _categorical_clustering(self, feature_data, features, goal_indices, parent_cluster_id='root', level_config=None):
        """Cluster by categorical features using Jaccard similarity (for player_name)"""
        if len(features) != 1 or features[0] != 'player_name':
            logger.warning(f"    Categorical clustering with Jaccard similarity only supports single 'player_name' feature")
            return self._simple_categorical_clustering(feature_data, features, goal_indices, level_config)
        
        # Use Jaccard similarity for player clustering
        feature_data_reset = feature_data.reset_index(drop=True)
        player_names = feature_data_reset['player_name'].fillna('unknown').values
        unique_players = list(set(player_names))
        
        if len(unique_players) <= 1:
            logger.info(f"    Only {len(unique_players)} unique players, no clustering needed")
            return None
        
        # Calculate Jaccard similarity matrix between players
        n_players = len(unique_players)
        similarity_matrix = np.zeros((n_players, n_players))
        
        # For each pair of players, calculate Jaccard similarity based on shared characteristics
        # We'll use the other features in the dataset to determine similarity
        available_features = [col for col in feature_data.columns if col != 'player_name']
        
        for i, player1 in enumerate(unique_players):
            player1_mask = player_names == player1
            player1_goals = feature_data_reset[player1_mask]
            
            for j, player2 in enumerate(unique_players):
                if i <= j:  # Only calculate upper triangle
                    player2_mask = player_names == player2
                    player2_goals = feature_data_reset[player2_mask]
                    
                    if i == j:
                        similarity_matrix[i, j] = 1.0
                    else:
                        # Calculate name similarity using Damerau-Levenshtein distance
                        name_sim = self._calculate_player_name_similarity(
                            player1_goals, player2_goals, available_features
                        )
                        similarity_matrix[i, j] = name_sim
                        similarity_matrix[j, i] = name_sim
        
        # Use similarity threshold to create clusters
        similarity_threshold = 0.5  # Players with >30% similarity are clustered together
        clusters = {}
        clustered_players = set()
        cluster_counter = 0
        
        # Debug: log some similarity values
        logger.info(f"    Similarity matrix shape: {similarity_matrix.shape}")
        if similarity_matrix.size > 0:
            logger.info(f"    Similarity range: {similarity_matrix.min():.3f} to {similarity_matrix.max():.3f}")
            logger.info(f"    Mean similarity: {similarity_matrix.mean():.3f}")
            # Show a few sample similarities
            for i in range(min(3, len(unique_players))):
                for j in range(i+1, min(i+3, len(unique_players))):
                    if j < len(unique_players):
                        logger.info(f"    {unique_players[i]} vs {unique_players[j]}: {similarity_matrix[i,j]:.3f}")
        # First pass: Find players that have high similarity with others
        high_similarity_players = set()
        similarity_groups = []
        
        for i, player1 in enumerate(unique_players):
            if player1 in clustered_players:
                continue
                
            # Find all players similar to this one
            similar_players = [player1]
            
            for j, player2 in enumerate(unique_players):
                if i != j and player2 not in clustered_players and similarity_matrix[i, j] > similarity_threshold:
                    similar_players.append(player2)
            
            # Only create a cluster if there are multiple similar players
            if len(similar_players) > 1:
                similarity_groups.append(similar_players)
                high_similarity_players.update(similar_players)
                clustered_players.update(similar_players)
        
        # Create clusters for high-similarity groups
        for similar_players in similarity_groups:
            cluster_goal_indices = []
            for player in similar_players:
                player_mask = player_names == player
                player_indices = [goal_indices[idx] for idx in range(len(goal_indices)) if player_mask[idx]]
                cluster_goal_indices.extend(player_indices)
            
            if len(cluster_goal_indices) > 0:
                # Create unique cluster ID that includes parent cluster to avoid collisions
                if level_config and level_config.get('level_name'):
                    # Generate AI name for this cluster
                    cluster_goals_df = self.goals_df.iloc[cluster_goal_indices]
                    ai_name = self.generate_cluster_name(
                        level_config['level_name'], 
                        cluster_goals_df, 
                        features
                    )
                else:
                    # Fallback to old naming if no level_config
                    primary_player_short = similar_players[0][:12] if similar_players[0] else 'unknown'
                    parent_short = parent_cluster_id.split('.')[-1] if parent_cluster_id != 'root' else 'root'
                    ai_name = f"jaccard_{parent_short}_{cluster_counter}_{primary_player_short}"
                
                clusters[ai_name] = {
                    'goal_indices': cluster_goal_indices,
                    'center': {
                        'primary_player': similar_players[0],
                        'similar_players': similar_players,
                        'similarity_threshold': similarity_threshold
                    }
                }
                cluster_counter += 1
        
        # Create a single "miscellaneous" cluster for all remaining players (low similarity)
        remaining_players = [player for player in unique_players if player not in high_similarity_players]
        if remaining_players:
            misc_goal_indices = []
            for player in remaining_players:
                player_mask = player_names == player
                player_indices = [goal_indices[idx] for idx in range(len(goal_indices)) if player_mask[idx]]
                misc_goal_indices.extend(player_indices)
            
            if len(misc_goal_indices) > 0:
                if level_config and level_config.get('level_name'):
                    # Generate AI name for miscellaneous cluster
                    cluster_goals_df = self.goals_df.iloc[misc_goal_indices]
                    ai_name = self.generate_cluster_name(
                        level_config['level_name'], 
                        cluster_goals_df, 
                        features
                    )
                else:
                    # Fallback to old naming
                    parent_short = parent_cluster_id.split('.')[-1] if parent_cluster_id != 'root' else 'root'
                    ai_name = f"jaccard_{parent_short}_{cluster_counter}_miscellaneous"
                
                clusters[ai_name] = {
                    'goal_indices': misc_goal_indices,
                    'center': {
                        'primary_player': 'miscellaneous',
                        'similar_players': remaining_players,
                        'similarity_threshold': similarity_threshold,
                        'is_miscellaneous': True
                    }
                }
                cluster_counter += 1
        
        logger.info(f"    Created {len(clusters)} name similarity clusters for players")
        logger.info(f"    High-similarity groups: {len(similarity_groups)} (covering {len(high_similarity_players)} players)")
        logger.info(f"    Miscellaneous cluster: {len(remaining_players)} players")
        return clusters
    
    def _calculate_player_name_similarity(self, player1_goals, player2_goals, features):
        """Calculate similarity between two players using Damerau-Levenshtein distance on names"""
        if len(player1_goals) == 0 or len(player2_goals) == 0:
            return 0.0
        
        # Get the most common player name from each group (should be the same for each player's goals)
        player1_names = player1_goals['player_name'].dropna().astype(str)
        player2_names = player2_goals['player_name'].dropna().astype(str)
        
        if len(player1_names) == 0 or len(player2_names) == 0:
            return 0.0
        
        # Get the most frequent name from each group
        player1_name = player1_names.mode().iloc[0] if len(player1_names.mode()) > 0 else player1_names.iloc[0]
        player2_name = player2_names.mode().iloc[0] if len(player2_names.mode()) > 0 else player2_names.iloc[0]
        
        # Calculate Damerau-Levenshtein distance
        distance = self._damerau_levenshtein_distance(player1_name, player2_name)
        
        # Convert distance to similarity (0-1 scale, where 1 is identical)
        max_len = max(len(player1_name), len(player2_name))
        if max_len == 0:
            return 1.0
        
        similarity = 1.0 - (distance / max_len)
        return max(0.0, similarity)  # Ensure similarity is non-negative
    
    def _damerau_levenshtein_distance(self, s1, s2):
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
    
    def _simple_categorical_clustering(self, feature_data, features, goal_indices, level_config=None):
        """Fallback simple categorical clustering for non-player features"""
        clusters = {}
        feature_data_reset = feature_data.reset_index(drop=True)
        
        if len(features) == 1:
            feature = features[0]
            unique_values = feature_data_reset[feature].unique()
            
            for i, value in enumerate(unique_values):
                mask = feature_data_reset[feature] == value
                local_indices = mask[mask].index.tolist()
                cluster_goal_indices = [goal_indices[j] for j in local_indices]
                
                if len(cluster_goal_indices) > 0:
                    if level_config and level_config.get('level_name'):
                        # Generate AI name for this cluster
                        cluster_goals_df = self.goals_df.iloc[cluster_goal_indices]
                        ai_name = self.generate_cluster_name(
                            level_config['level_name'], 
                            cluster_goals_df, 
                            features
                        )
                    else:
                        # Fallback to old naming if no level_config
                        ai_name = f"cat_{i}_{str(value)[:10]}"
                    
                    clusters[ai_name] = {
                        'goal_indices': cluster_goal_indices,
                        'center': {'categorical_value': value}
                    }
        
        logger.info(f"    Created {len(clusters)} simple categorical clusters")
        return clusters
    
    def _kmeans_clustering(self, feature_data, features, goal_indices, n_clusters, level_config):
        """Cluster using K-means"""
        # Fill missing values and scale features
        feature_data_clean = feature_data.fillna(0)
        scaler = StandardScaler()
        scaled_features = scaler.fit_transform(feature_data_clean)
        
        # Adjust n_clusters if we have fewer data points
        n_clusters = min(n_clusters, len(scaled_features) // 2, len(scaled_features))
        if n_clusters < 2:
            logger.warning(f"    Not enough data for clustering ({len(scaled_features)} points)")
            return None
        
        # Perform K-means clustering
        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        cluster_labels = kmeans.fit_predict(scaled_features)
        
        # Calculate silhouette score if possible
        if len(set(cluster_labels)) > 1 and len(scaled_features) > n_clusters:
            try:
                silhouette = silhouette_score(scaled_features, cluster_labels)
                logger.info(f"    K-means silhouette score: {silhouette:.3f}")
            except:
                pass
        
        # Create cluster dictionary
        clusters = {}
        for cluster_id in range(n_clusters):
            mask = cluster_labels == cluster_id
            cluster_goal_indices = [goal_indices[i] for i in range(len(goal_indices)) if mask[i]]
            
            if len(cluster_goal_indices) > 0:
                # Calculate cluster center in original feature space
                cluster_center = feature_data_clean.iloc[mask].mean().to_dict()
                
                # Generate AI name for this cluster
                cluster_goals_df = self.goals_df.iloc[cluster_goal_indices]
                ai_name = self.generate_cluster_name(
                    level_config['level_name'], 
                    cluster_goals_df, 
                    features
                )
                
                clusters[ai_name] = {
                    'goal_indices': cluster_goal_indices,
                    'center': cluster_center
                }
        
        logger.info(f"    Created {len(clusters)} K-means clusters")
        return clusters
    
    def _dbscan_clustering(self, feature_data, features, goal_indices, level_config):
        """Cluster using DBSCAN"""
        # Scale features
        feature_data_clean = feature_data.fillna(0)
        scaler = StandardScaler()
        scaled_features = scaler.fit_transform(feature_data_clean)
        
        # DBSCAN parameters
        eps = level_config.get('eps', 0.5)
        min_samples = level_config.get('min_samples', 5)
        
        # Perform DBSCAN clustering
        dbscan = DBSCAN(eps=eps, min_samples=min_samples)
        cluster_labels = dbscan.fit_predict(scaled_features)
        
        # Create cluster dictionary
        clusters = {}
        unique_labels = set(cluster_labels)
        
        for cluster_id in unique_labels:
            if cluster_id == -1:  # Noise points
                continue
                
            mask = cluster_labels == cluster_id
            cluster_goal_indices = [goal_indices[i] for i in range(len(goal_indices)) if mask[i]]
            
            if len(cluster_goal_indices) > 0:
                cluster_center = feature_data_clean.iloc[mask].mean().to_dict()
                
                clusters[f"db{cluster_id}"] = {
                    'goal_indices': cluster_goal_indices,
                    'center': cluster_center
                }
        
        logger.info(f"    Created {len(clusters)} DBSCAN clusters ({sum(cluster_labels == -1)} noise points)")
        return clusters
    
    def _mixed_clustering(self, feature_data, features, goal_indices, n_clusters, level_config):
        """Mixed clustering for spatial coordinates and categorical features (x, y, shot_type)"""
        # Prepare all features including encoded shot_type
        spatial_data = feature_data[['x', 'y']].fillna(0).copy()
        
        # Encode shot_type as numerical feature
        shot_type_data = feature_data['shot_type'].fillna('unknown')
        label_encoder = LabelEncoder()
        encoded_shot_type = label_encoder.fit_transform(shot_type_data)
        spatial_data['shot_type_encoded'] = encoded_shot_type
        
        # Scale all features together (x, y, shot_type_encoded)
        scaler = StandardScaler()
        scaled_spatial = scaler.fit_transform(spatial_data)
        
        # Use the full n_clusters since shot_type is now encoded and included
        n_clusters = min(n_clusters, len(scaled_spatial) // 2, len(scaled_spatial))
        
        if n_clusters < 2:
            logger.warning(f"    Not enough data for mixed clustering ({len(scaled_spatial)} points)")
            return None
        
        # Perform K-means clustering on all features (x, y, shot_type_encoded)
        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        cluster_labels = kmeans.fit_predict(scaled_spatial)
        
        # Calculate silhouette score if possible
        if len(set(cluster_labels)) > 1 and len(scaled_spatial) > n_clusters:
            try:
                silhouette = silhouette_score(scaled_spatial, cluster_labels)
                logger.info(f"    Mixed clustering silhouette score: {silhouette:.3f}")
            except:
                pass
        
        # Create cluster dictionary
        clusters = {}
        for cluster_id in range(n_clusters):
            mask = cluster_labels == cluster_id
            cluster_goal_indices = [goal_indices[i] for i in range(len(goal_indices)) if mask[i]]
            
            if len(cluster_goal_indices) > 0:
                # Calculate cluster center in original feature space
                cluster_data = feature_data.iloc[mask]
                cluster_center = {
                    'x': cluster_data['x'].mean(),
                    'y': cluster_data['y'].mean(),
                    'dominant_shot_type': cluster_data['shot_type'].mode().iloc[0] if not cluster_data['shot_type'].mode().empty else 'unknown'
                }
                
                # Generate AI name for this cluster
                cluster_goals_df = self.goals_df.iloc[cluster_goal_indices]
                ai_name = self.generate_cluster_name(
                    level_config['level_name'], 
                    cluster_goals_df, 
                    features
                )
                
                clusters[ai_name] = {
                    'goal_indices': cluster_goal_indices,
                    'center': cluster_center
                }
        
        logger.info(f"    Created {len(clusters)} mixed clusters (x,y,shot_type)")
        return clusters
    
    def _analyze_hierarchy(self):
        """Analyze the created hierarchy"""
        logger.info("\nAnalyzing clustering hierarchy...")
        
        # Count clusters by level
        level_counts = {}
        level_sizes = {}
        
        for cluster_id, cluster_info in self.hierarchy.items():
            level = cluster_info['level']
            size = cluster_info['size']
            
            if level not in level_counts:
                level_counts[level] = 0
                level_sizes[level] = []
            
            level_counts[level] += 1
            level_sizes[level].append(size)
        
        # Log statistics
        for level in sorted(level_counts.keys()):
            if level == -1:
                continue  # Skip root
            
            level_name = self.clustering_sequence[level]['level_name'] if level < len(self.clustering_sequence) else f"level_{level}"
            avg_size = np.mean(level_sizes[level])
            min_size = min(level_sizes[level])
            max_size = max(level_sizes[level])
            
            logger.info(f"  Level {level} ({level_name}): {level_counts[level]} clusters, "
                       f"avg size: {avg_size:.1f}, range: [{min_size}, {max_size}]")
        
        # Store analysis results
        self.results = {
            'level_counts': level_counts,
            'level_sizes': level_sizes,
            'total_clusters': len(self.hierarchy),
            'total_goals': len(self.goals_df),
            'clustering_sequence': self.clustering_sequence
        }
    
    def create_goal_hierarchy_mapping(self):
        """Create a mapping of each goal to its full hierarchical path"""
        logger.info("Creating goal-to-hierarchy mapping...")
        
        # Create mapping dataframe
        mapping_data = []
        
        for _, goal_row in self.goals_df.iterrows():
            goal_idx = goal_row.name
            
            # Find the deepest cluster containing this goal
            deepest_cluster_id = None
            deepest_level = -1
            
            for cluster_id, cluster_info in self.hierarchy.items():
                if goal_idx in cluster_info['goal_indices']:
                    if cluster_info['level'] > deepest_level:
                        deepest_level = cluster_info['level']
                        deepest_cluster_id = cluster_id
            
            # Build hierarchical path
            hierarchy_path = []
            current_cluster = deepest_cluster_id
            
            while current_cluster and current_cluster != 'root':
                hierarchy_path.append(current_cluster.split('.')[-1])  # Get last part of cluster ID
                current_cluster = self.hierarchy[current_cluster]['parent']
            
            hierarchy_path.reverse()  # Make it root-to-leaf order
            
            # Create mapping entry
            mapping_entry = goal_row.to_dict()
            mapping_entry.update({
                'goal_index': goal_idx,
                'deepest_cluster': deepest_cluster_id,
                'hierarchy_level': deepest_level,
                'hierarchy_path': '.'.join(hierarchy_path),
                'cluster_size': self.hierarchy[deepest_cluster_id]['size'] if deepest_cluster_id else 0
            })
            
            # Add hierarchical coordinates (for cartography)
            for i, path_part in enumerate(hierarchy_path):
                mapping_entry[f'level_{i}_cluster'] = path_part
            
            mapping_data.append(mapping_entry)
        
        mapping_df = pd.DataFrame(mapping_data)
        
        # Save mapping
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        mapping_file = os.path.join(self.output_dir, f'goal_hierarchy_mapping_{timestamp}.csv')
        mapping_df.to_csv(mapping_file, index=False)
        
        logger.info(f"Saved goal hierarchy mapping to {mapping_file}")
        logger.info(f"Mapping contains {len(mapping_df)} goals with hierarchical paths")
        
        return mapping_df, mapping_file
    
    def visualize_hierarchy(self, max_levels=4, save_png=True):
        """Create visualizations of the hierarchical clustering"""
        logger.info("Creating hierarchy visualizations...")
        
        fig, axes = plt.subplots(2, 2, figsize=(20, 16))
        fig.suptitle('Sequential Hierarchical Clustering Analysis', fontsize=16, fontweight='bold')
        
        # 1. Spatial distribution by first level (continents)
        self._plot_spatial_hierarchy(axes[0, 0])
        
        # 2. Cluster size distribution by level
        self._plot_cluster_sizes_by_level(axes[0, 1])
        
        # 3. Hierarchy tree (simplified)
        self._plot_hierarchy_tree(axes[1, 0], max_levels)
        
        # 4. Feature importance by level
        self._plot_level_characteristics(axes[1, 1])
        
        plt.tight_layout()
        
        if save_png:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"sequential_clustering_analysis_{timestamp}.png"
            filepath = os.path.join(self.output_dir, filename)
            plt.savefig(filepath, dpi=300, bbox_inches='tight', 
                       facecolor='black', edgecolor='none')
            logger.info(f"Saved visualization to {filepath}")
        
        plt.show()
        return fig
    
    def visualize_complete_dataset(self, save_png=True):
        """Create comprehensive visualization showing all goals with their final cluster assignments"""
        logger.info("Creating complete dataset visualization with final clusters...")
        
        if self.goals_df is None or not self.hierarchy:
            logger.error("No data or hierarchy available for visualization")
            return None
        
        # Get final cluster assignment for each goal
        goal_cluster_map = {}
        final_clusters = {}
        
        # Find the deepest cluster for each goal
        for goal_idx in range(len(self.goals_df)):
            deepest_cluster_id = None
            deepest_level = -1
            
            for cluster_id, cluster_info in self.hierarchy.items():
                if goal_idx in cluster_info['goal_indices']:
                    if cluster_info['level'] > deepest_level:
                        deepest_level = cluster_info['level']
                        deepest_cluster_id = cluster_id
            
            goal_cluster_map[goal_idx] = deepest_cluster_id
            
            # Track final clusters
            if deepest_cluster_id not in final_clusters:
                final_clusters[deepest_cluster_id] = []
            final_clusters[deepest_cluster_id].append(goal_idx)
        
        # Create comprehensive visualization
        fig = plt.figure(figsize=(24, 18))
        gs = fig.add_gridspec(3, 3, hspace=0.3, wspace=0.3)
        fig.suptitle('Complete NHL Goals Dataset - Sequential Clustering Results', 
                    fontsize=20, fontweight='bold', color='white')
        
        # 1. Main spatial plot - all goals colored by final cluster
        ax_main = fig.add_subplot(gs[0, :2])
        self._plot_complete_spatial_clusters(ax_main, goal_cluster_map, final_clusters)
        
        # 2. Cluster size histogram
        ax_hist = fig.add_subplot(gs[0, 2])
        self._plot_final_cluster_sizes(ax_hist, final_clusters)
        
        # 3. Shot type distribution by cluster level
        ax_shot = fig.add_subplot(gs[1, 0])
        self._plot_shot_type_by_level(ax_shot, goal_cluster_map)
        
        # 4. Temporal distribution
        ax_time = fig.add_subplot(gs[1, 1])
        self._plot_temporal_distribution(ax_time, goal_cluster_map)
        
        # 5. Score situation heatmap
        ax_score = fig.add_subplot(gs[1, 2])
        self._plot_score_situation_heatmap(ax_score, goal_cluster_map)
        
        # 6. Cluster depth distribution
        ax_depth = fig.add_subplot(gs[2, 0])
        self._plot_cluster_depth_distribution(ax_depth, goal_cluster_map)
        
        # 7. Ice position heatmap
        ax_heat = fig.add_subplot(gs[2, 1])
        self._plot_ice_position_heatmap(ax_heat)
        
        # 8. Summary statistics
        ax_stats = fig.add_subplot(gs[2, 2])
        self._plot_dataset_summary(ax_stats, final_clusters, goal_cluster_map)
        
        plt.tight_layout()
        
        if save_png:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"complete_dataset_visualization_{timestamp}.png"
            filepath = os.path.join(self.output_dir, filename)
            plt.savefig(filepath, dpi=300, bbox_inches='tight', 
                       facecolor='black', edgecolor='none')
            logger.info(f"Saved complete dataset visualization to {filepath}")
        
        plt.show()
        return fig
    
    def visualize_galaxy_view(self, save_png=True):
        """Create map-like visualization showing hierarchical clusters as nested circular regions"""
        logger.info("Creating hierarchical cluster map with nested circular regions...")
        
        if self.goals_df is None or not self.hierarchy:
            logger.error("No data or hierarchy available for cluster map visualization")
            return None
        
        # Create single large plot
        fig, ax = plt.subplots(1, 1, figsize=(24, 20))
        fig.suptitle('NHL Goals Cluster Map - Hierarchical Areas View', 
                    fontsize=24, fontweight='bold', color='white', y=0.95)
        
        # Get hierarchical structure for spatial positioning
        cluster_positions = self._calculate_cluster_positions()
        
        # Check if we have cluster positions
        if not cluster_positions:
            logger.warning("No cluster positions calculated - creating fallback visualization")
            ax.text(0.5, 0.5, 'No hierarchical clusters found for visualization\nCheck clustering results', 
                   ha='center', va='center', transform=ax.transAxes, 
                   fontsize=16, color='white')
        else:
            logger.info(f"Plotting {len(cluster_positions)} cluster regions")
            
            # Plot nested circles for each level
            self._plot_nested_cluster_circles(ax, cluster_positions)
            
            # Add cluster labels and statistics
            self._add_cluster_map_labels(ax, cluster_positions)
            
            # Set plot limits based on cluster positions
            all_x = [pos['x'] for pos in cluster_positions.values()]
            all_y = [pos['y'] for pos in cluster_positions.values()]
            all_r = [pos['radius'] for pos in cluster_positions.values()]
            
            if all_x and all_y:
                margin = max(all_r) * 1.5
                x_min, x_max = min(all_x) - margin, max(all_x) + margin
                y_min, y_max = min(all_y) - margin, max(all_y) + margin
                ax.set_xlim(x_min, x_max)
                ax.set_ylim(y_min, y_max)
                logger.info(f"Set plot limits: x=({x_min:.1f}, {x_max:.1f}), y=({y_min:.1f}, {y_max:.1f})")
        
        ax.set_title(f'Hierarchical Cluster Map: {len(self.goals_df)} Goals in Nested Regions', 
                    fontsize=16, color='white', pad=20)
        ax.set_xlabel('Cluster Space X', fontsize=14, color='white')
        ax.set_ylabel('Cluster Space Y', fontsize=14, color='white')
        
        # Style the plot like a map
        ax.set_facecolor('black')
        ax.grid(True, alpha=0.2, color='white', linestyle=':')
        ax.tick_params(colors='white')
        ax.set_aspect('equal')
        
        # Add legend
        self._add_cluster_map_legend(ax)
        
        plt.tight_layout()
        
        # Force refresh
        fig.canvas.draw()
        
        if save_png:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"cluster_map_visualization_{timestamp}.png"
            filepath = os.path.join(self.output_dir, filename)
            
            # Save twice to make sure it works
            plt.savefig(filepath, dpi=300, bbox_inches='tight', 
                       facecolor='black', edgecolor='none')
            logger.info(f"Saved cluster map visualization to {filepath}")
            
            # Also save a simplified version for debugging
            debug_filename = f"cluster_map_debug_{timestamp}.png"
            debug_filepath = os.path.join(self.output_dir, debug_filename) 
            fig.savefig(debug_filepath, dpi=150, bbox_inches='tight', 
                       facecolor='black', edgecolor='none')
            logger.info(f"Saved debug version to {debug_filepath}")
        
        plt.show()
        return fig
    
    def _calculate_cluster_positions(self):
        """Calculate spatial positions for clusters to create a map-like layout"""
        cluster_positions = {}
        
        # Get level 0 clusters (galaxies)
        level_0_clusters = [cid for cid, info in self.hierarchy.items() if info['level'] == 0]
        n_level_0 = len(level_0_clusters)
        
        logger.info(f"Found {n_level_0} level 0 clusters (galaxies): {level_0_clusters}")
        
        if n_level_0 == 0:
            logger.warning("No level 0 clusters found!")
            return cluster_positions
        
        # Arrange level 0 clusters in a grid or circle pattern
        if n_level_0 <= 4:
            # Small number - arrange in a square
            grid_size = int(np.ceil(np.sqrt(n_level_0)))
            for i, cluster_id in enumerate(level_0_clusters):
                row = i // grid_size
                col = i % grid_size
                x = col * 10
                y = row * 10
                
                # Calculate radius based on cluster size
                cluster_size = self.hierarchy[cluster_id]['size']
                base_radius = np.sqrt(cluster_size) * 0.01  # Scale factor
                radius = max(2, min(4, base_radius))  # Clamp between 2 and 4
                
                cluster_positions[cluster_id] = {
                    'x': x, 'y': y, 'radius': radius, 'level': 0,
                    'size': cluster_size, 'children': []
                }
        else:
            # Larger number - arrange in a circle
            angle_step = 2 * np.pi / n_level_0
            circle_radius = max(8, n_level_0 * 1.5)  # Adjust circle size based on number of clusters
            
            for i, cluster_id in enumerate(level_0_clusters):
                angle = i * angle_step
                x = circle_radius * np.cos(angle)
                y = circle_radius * np.sin(angle)
                
                cluster_size = self.hierarchy[cluster_id]['size']
                base_radius = np.sqrt(cluster_size) * 0.01
                radius = max(2, min(4, base_radius))
                
                cluster_positions[cluster_id] = {
                    'x': x, 'y': y, 'radius': radius, 'level': 0,
                    'size': cluster_size, 'children': []
                }
        
        # Position level 1 clusters (constellations) within their parent galaxies
        level_1_clusters = [cid for cid, info in self.hierarchy.items() if info['level'] == 1]
        
        for cluster_id in level_1_clusters:
            parent_id = self.hierarchy[cluster_id]['parent']
            if parent_id in cluster_positions:
                parent_pos = cluster_positions[parent_id]
                
                # Get siblings (other level 1 clusters with same parent)
                siblings = [cid for cid in level_1_clusters 
                           if self.hierarchy[cid]['parent'] == parent_id]
                
                if len(siblings) == 1:
                    # Only child - place at center with smaller radius
                    x = parent_pos['x']
                    y = parent_pos['y']
                else:
                    # Multiple children - arrange in circle within parent
                    sibling_index = siblings.index(cluster_id)
                    angle_step = 2 * np.pi / len(siblings)
                    angle = sibling_index * angle_step
                    inner_radius = parent_pos['radius'] * 0.6  # 60% of parent radius
                    
                    x = parent_pos['x'] + inner_radius * np.cos(angle)
                    y = parent_pos['y'] + inner_radius * np.sin(angle)
                
                cluster_size = self.hierarchy[cluster_id]['size']
                # Child radius should be smaller than parent
                base_radius = np.sqrt(cluster_size) * 0.008
                radius = max(0.5, min(parent_pos['radius'] * 0.4, base_radius))
                
                cluster_positions[cluster_id] = {
                    'x': x, 'y': y, 'radius': radius, 'level': 1,
                    'size': cluster_size, 'parent': parent_id, 'children': []
                }
                
                # Add to parent's children list
                parent_pos['children'].append(cluster_id)
        
        # Position level 2 clusters (stars) within their parent constellations
        level_2_clusters = [cid for cid, info in self.hierarchy.items() if info['level'] == 2]
        
        for cluster_id in level_2_clusters:
            parent_id = self.hierarchy[cluster_id]['parent']
            if parent_id in cluster_positions:
                parent_pos = cluster_positions[parent_id]
                
                # Get siblings
                siblings = [cid for cid in level_2_clusters 
                           if self.hierarchy[cid]['parent'] == parent_id]
                
                if len(siblings) == 1:
                    x = parent_pos['x']
                    y = parent_pos['y']
                else:
                    # Arrange in circle within parent constellation
                    sibling_index = siblings.index(cluster_id)
                    angle_step = 2 * np.pi / len(siblings)
                    angle = sibling_index * angle_step
                    inner_radius = parent_pos['radius'] * 0.5
                    
                    x = parent_pos['x'] + inner_radius * np.cos(angle)
                    y = parent_pos['y'] + inner_radius * np.sin(angle)
                
                cluster_size = self.hierarchy[cluster_id]['size']
                base_radius = np.sqrt(cluster_size) * 0.005
                radius = max(0.2, min(parent_pos['radius'] * 0.3, base_radius))
                
                cluster_positions[cluster_id] = {
                    'x': x, 'y': y, 'radius': radius, 'level': 2,
                    'size': cluster_size, 'parent': parent_id
                }
                
                parent_pos['children'].append(cluster_id)
        
        logger.info(f"Final cluster positions calculated: {len(cluster_positions)} total clusters")
        for level in [0, 1, 2]:
            level_clusters = [cid for cid, pos in cluster_positions.items() if pos['level'] == level]
            logger.info(f"  Level {level}: {len(level_clusters)} clusters")
        
        return cluster_positions
    
    def _plot_nested_cluster_circles(self, ax, cluster_positions):
        """Plot nested circles representing the hierarchical clusters"""
        logger.info(f"Starting to plot circles for {len(cluster_positions)} clusters")
        
        # Color schemes for different levels
        level_colors = {
            0: plt.cm.Set3(np.linspace(0, 1, 12)),      # Galaxies - bright colors
            1: plt.cm.Pastel1(np.linspace(0, 1, 9)),    # Constellations - pastel colors  
            2: plt.cm.Set2(np.linspace(0, 1, 8))        # Stars - muted colors
        }
        
        circles_plotted = 0
        
        # Plot clusters by level (largest first)
        for level in [0, 1, 2]:
            level_clusters = [(cid, pos) for cid, pos in cluster_positions.items() 
                             if pos['level'] == level]
            
            logger.info(f"Plotting {len(level_clusters)} circles for level {level}")
            
            for i, (cluster_id, pos) in enumerate(level_clusters):
                # Choose color
                color_idx = i % len(level_colors[level])
                color = level_colors[level][color_idx]
                
                # Set alpha and line width based on level
                if level == 0:  # Galaxy - outermost
                    alpha = 0.4
                    linewidth = 3
                    linestyle = '-'
                elif level == 1:  # Constellation - middle
                    alpha = 0.6
                    linewidth = 2
                    linestyle = '--'
                else:  # Stars - innermost
                    alpha = 0.8
                    linewidth = 1
                    linestyle = ':'
                
                # Draw circle
                circle = plt.Circle((pos['x'], pos['y']), pos['radius'],
                                  facecolor=color, alpha=alpha,
                                  edgecolor='white', linewidth=linewidth,
                                  linestyle=linestyle)
                ax.add_patch(circle)
                circles_plotted += 1
                
                # Debug: Log first few circles
                if circles_plotted <= 5:
                    logger.info(f"  Circle {circles_plotted}: pos=({pos['x']:.1f}, {pos['y']:.1f}), radius={pos['radius']:.2f}, color={color[:3]}")
                
                # Add size annotation in center of cluster
                if pos['size'] > 50:  # Only label larger clusters
                    ax.annotate(f"{pos['size']}", 
                               (pos['x'], pos['y']), 
                               ha='center', va='center',
                               fontsize=10, color='white', weight='bold',
                               bbox=dict(boxstyle='round,pad=0.2', facecolor='black', alpha=0.7))
        
        logger.info(f"Successfully plotted {circles_plotted} circles")
    
    def _add_cluster_map_labels(self, ax, cluster_positions):
        """Add labels and information to the cluster map"""
        # Label major galaxies (level 0)
        level_0_clusters = [(cid, pos) for cid, pos in cluster_positions.items() 
                           if pos['level'] == 0]
        
        # Sort by size and label the largest ones
        level_0_clusters.sort(key=lambda x: x[1]['size'], reverse=True)
        
        for i, (cluster_id, pos) in enumerate(level_0_clusters[:6]):  # Label top 6 galaxies
            # Get dominant characteristics for this galaxy
            galaxy_goals = self.goals_df.iloc[self.hierarchy[cluster_id]['goal_indices']]
            
            # Find most common shot type
            if 'shot_type' in galaxy_goals.columns:
                shot_types = galaxy_goals['shot_type'].value_counts()
                dominant_shot = shot_types.index[0] if len(shot_types) > 0 else 'Mixed'
            else:
                dominant_shot = 'Mixed'
            
            # Position label outside the circle
            label_x = pos['x'] + pos['radius'] + 0.5
            label_y = pos['y'] + pos['radius'] + 0.5
            
            label = f"Galaxy {i+1}\n{dominant_shot}\n{pos['size']} goals\n{len(pos.get('children', []))} regions"
            
            ax.annotate(label, (label_x, label_y),
                       fontsize=10, color='white', weight='bold',
                       bbox=dict(boxstyle='round,pad=0.3', facecolor='black', alpha=0.7),
                       ha='left', va='bottom')
    
    def _add_cluster_map_legend(self, ax):
        """Add legend explaining the cluster map visualization"""
        legend_text = """CLUSTER MAP LEGEND

⭕ Large circles = Galaxies (Level 0)
   Spatial + shot type clusters
   
⭕ Medium circles = Constellations (Level 1)  
   Game context clusters within galaxies
   
⭕ Small circles = Stars (Level 2)
   Player clusters within constellations

Circle size ∝ Number of goals in cluster
Numbers show exact goal count

Line styles:
─── Galaxy boundaries
- - - Constellation boundaries  
··· Star boundaries"""
        
        ax.text(0.02, 0.02, legend_text, transform=ax.transAxes, 
               fontsize=11, color='white', weight='bold',
               verticalalignment='bottom',
               bbox=dict(boxstyle='round,pad=0.5', facecolor='black', alpha=0.8))
    
    def _get_hierarchical_assignments(self):
        """Get the hierarchical cluster assignment for each goal"""
        goal_assignments = {}
        
        for goal_idx in range(len(self.goals_df)):
            assignment = {'level_0': None, 'level_1': None, 'level_2': None}
            
            # Find clusters containing this goal at each level
            for cluster_id, cluster_info in self.hierarchy.items():
                if goal_idx in cluster_info['goal_indices'] and cluster_info['level'] >= 0:
                    level = cluster_info['level']
                    if level < 3:  # Only track first 3 levels
                        assignment[f'level_{level}'] = cluster_id
            
            goal_assignments[goal_idx] = assignment
        
        return goal_assignments
    
    def _plot_galaxy_background(self, ax, goal_assignments, level_0_color_map):
        """Plot level 0 clusters as galaxy background regions"""
        level_0_centers = {}
        level_0_goals = {}
        
        # Group goals by level 0 cluster
        for goal_idx, assignment in goal_assignments.items():
            l0_cluster = assignment['level_0']
            if l0_cluster:
                if l0_cluster not in level_0_goals:
                    level_0_goals[l0_cluster] = []
                level_0_goals[l0_cluster].append(goal_idx)
        
        # Plot background regions for each galaxy
        for l0_cluster, goal_indices in level_0_goals.items():
            if len(goal_indices) < 3:  # Need at least 3 points for a meaningful region
                continue
                
            cluster_goals = self.goals_df.iloc[goal_indices]
            x_coords = cluster_goals['x'].values
            y_coords = cluster_goals['y'].values
            
            # Calculate convex hull or approximate boundary
            try:
                points = np.column_stack([x_coords, y_coords])
                hull = ConvexHull(points)
                hull_points = points[hull.vertices]
                
                # Plot filled polygon for galaxy region
                galaxy_color = level_0_color_map.get(l0_cluster, (0.3, 0.3, 0.3))
                polygon = plt.Polygon(hull_points, alpha=0.15, 
                                    facecolor=galaxy_color[:3], 
                                    edgecolor=galaxy_color[:3], 
                                    linewidth=2, linestyle='--')
                ax.add_patch(polygon)
                
                # Store center for labeling
                center_x, center_y = np.mean(x_coords), np.mean(y_coords)
                level_0_centers[l0_cluster] = (center_x, center_y)
                
            except:
                # Fallback to simple circle
                center_x, center_y = np.mean(x_coords), np.mean(y_coords)
                radius = np.std(x_coords) + np.std(y_coords)
                
                galaxy_color = level_0_color_map.get(l0_cluster, (0.3, 0.3, 0.3))
                circle = plt.Circle((center_x, center_y), radius, 
                                  alpha=0.1, facecolor=galaxy_color[:3], 
                                  edgecolor=galaxy_color[:3], linewidth=2)
                ax.add_patch(circle)
                level_0_centers[l0_cluster] = (center_x, center_y)
        
        return level_0_centers
    
    def _plot_constellation_regions(self, ax, goal_assignments, level_1_color_map):
        """Plot level 1 clusters as constellation regions"""
        level_1_goals = {}
        
        # Group goals by level 1 cluster
        for goal_idx, assignment in goal_assignments.items():
            l1_cluster = assignment['level_1']
            if l1_cluster:
                if l1_cluster not in level_1_goals:
                    level_1_goals[l1_cluster] = []
                level_1_goals[l1_cluster].append(goal_idx)
        
        # Plot constellation regions
        for l1_cluster, goal_indices in level_1_goals.items():
            if len(goal_indices) < 2:
                continue
                
            cluster_goals = self.goals_df.iloc[goal_indices]
            x_coords = cluster_goals['x'].values
            y_coords = cluster_goals['y'].values
            
            # Plot constellation as connected dots
            constellation_color = level_1_color_map.get(l1_cluster, (0.7, 0.7, 0.7, 0.8))
            
            # Draw connecting lines between nearby points in constellation
            if len(goal_indices) > 1:
                ax.scatter(x_coords, y_coords, 
                          c=[constellation_color[:3]], 
                          s=30, alpha=0.6, edgecolors='white', linewidth=0.5)
    
    def _plot_individual_stars(self, ax, goal_assignments, level_0_color_map, level_1_color_map):
        """Plot individual goals as stars"""
        for goal_idx in range(len(self.goals_df)):
            goal = self.goals_df.iloc[goal_idx]
            assignment = goal_assignments[goal_idx]
            
            # Determine point color based on hierarchy
            if assignment['level_1']:
                color = level_1_color_map.get(assignment['level_1'], (1, 1, 1, 0.8))
            elif assignment['level_0']:
                color = level_0_color_map.get(assignment['level_0'], (0.8, 0.8, 0.8))
            else:
                color = (0.5, 0.5, 0.5, 0.5)
            
            # Determine point size based on clustering level
            if assignment['level_2']:  # Deepest level - smallest stars
                size = 15
                alpha = 0.9
            elif assignment['level_1']:  # Middle level
                size = 25
                alpha = 0.8
            else:  # Top level only
                size = 40
                alpha = 0.7
            
            ax.scatter(goal['x'], goal['y'], c=[color[:3]], s=size, 
                      alpha=alpha, edgecolors='white', linewidth=0.3)
    
    def _add_galaxy_labels(self, ax, goal_assignments, level_0_color_map):
        """Add labels for major galaxy clusters"""
        level_0_stats = {}
        
        # Calculate statistics for each level 0 cluster
        for goal_idx, assignment in goal_assignments.items():
            l0_cluster = assignment['level_0']
            if l0_cluster:
                if l0_cluster not in level_0_stats:
                    level_0_stats[l0_cluster] = {'goals': [], 'center_x': 0, 'center_y': 0}
                level_0_stats[l0_cluster]['goals'].append(goal_idx)
        
        # Add labels for largest galaxies
        sorted_galaxies = sorted(level_0_stats.items(), key=lambda x: len(x[1]['goals']), reverse=True)
        
        for i, (l0_cluster, stats) in enumerate(sorted_galaxies[:8]):  # Label top 8 galaxies
            goal_indices = stats['goals']
            cluster_goals = self.goals_df.iloc[goal_indices]
            
            center_x = cluster_goals['x'].mean()
            center_y = cluster_goals['y'].mean()
            
            # Get dominant shot type for this galaxy
            shot_types = cluster_goals['shot_type'].value_counts()
            dominant_shot = shot_types.index[0] if len(shot_types) > 0 else 'Mixed'
            
            label = f"Galaxy {i+1}\n{dominant_shot}\n({len(goal_indices)} goals)"
            
            ax.annotate(label, (center_x, center_y), 
                       xytext=(10, 10), textcoords='offset points',
                       fontsize=10, color='white', weight='bold',
                       bbox=dict(boxstyle='round,pad=0.3', facecolor='black', alpha=0.7),
                       ha='left')
    
    def _add_galaxy_legend(self, ax, level_0_color_map, level_1_color_map):
        """Add legend explaining the galaxy visualization"""
        legend_text = """GALAXY MAP LEGEND
        
● Large background regions = Galaxies (spatial + shot type)
● Medium clusters = Constellations (game context)  
● Individual points = Stars (individual goals)

Point size indicates clustering depth:
○ Large = Galaxy level only
● Medium = Constellation level  
● Small = Player level (individual stars)"""
        
        ax.text(0.02, 0.98, legend_text, transform=ax.transAxes, 
               fontsize=11, color='white', weight='bold',
               verticalalignment='top',
               bbox=dict(boxstyle='round,pad=0.5', facecolor='black', alpha=0.8))
    
    def _plot_complete_spatial_clusters(self, ax, goal_cluster_map, final_clusters):
        """Plot all goals spatially colored by their final cluster"""
        if 'x' not in self.goals_df.columns or 'y' not in self.goals_df.columns:
            ax.text(0.5, 0.5, 'No coordinate data available', ha='center', va='center', 
                   transform=ax.transAxes, fontsize=14, color='white')
            ax.set_title('Spatial Distribution - Final Clusters')
            return
        
        # Get unique final clusters and assign colors
        unique_clusters = list(final_clusters.keys())
        n_clusters = len(unique_clusters)
        
        # Use a combination of colormaps for better distinction
        if n_clusters <= 20:
            colors = plt.cm.tab20(np.linspace(0, 1, n_clusters))
        elif n_clusters <= 50:
            colors1 = plt.cm.tab20(np.linspace(0, 1, 20))
            colors2 = plt.cm.Set3(np.linspace(0, 1, n_clusters - 20))
            colors = np.vstack([colors1, colors2])
        else:
            colors = plt.cm.viridis(np.linspace(0, 1, n_clusters))
        
        cluster_colors = {cluster_id: colors[i] for i, cluster_id in enumerate(unique_clusters)}
        
        # Plot each cluster
        for i, (cluster_id, goal_indices) in enumerate(final_clusters.items()):
            cluster_goals = self.goals_df.iloc[goal_indices]
            
            if len(cluster_goals) > 0:
                # Determine point size based on cluster size
                if len(cluster_goals) > 500:
                    point_size = 8
                    alpha = 0.4
                elif len(cluster_goals) > 100:
                    point_size = 12
                    alpha = 0.6
                else:
                    point_size = 20
                    alpha = 0.8
                
                ax.scatter(cluster_goals['x'], cluster_goals['y'], 
                          c=[cluster_colors[cluster_id]], 
                          s=point_size, alpha=alpha,
                          label=f'{cluster_id.split(".")[-1] if cluster_id and "." in cluster_id else (cluster_id or "unknown")} (n={len(cluster_goals)})' if i < 10 else "")
        
        ax.set_title(f'All {len(self.goals_df)} Goals - Final Cluster Assignment\n{n_clusters} Final Clusters')
        ax.set_xlabel('X Coordinate (Ice Position)')
        ax.set_ylabel('Y Coordinate (Ice Position)')
        ax.grid(True, alpha=0.3)
        
        # Show legend for top 10 clusters only
        if n_clusters <= 10:
            ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=8)
        
        # Add rink outline for context
        self._add_rink_outline(ax)
    
    def _add_rink_outline(self, ax):
        """Add basic hockey rink outline for spatial context"""
        # Simplified rink outline - just the basic boundaries
        # NHL rink is 200ft x 85ft, coordinates vary by data source
        x_coords = self.goals_df['x']
        y_coords = self.goals_df['y']
        
        x_min, x_max = x_coords.min(), x_coords.max()
        y_min, y_max = y_coords.min(), y_coords.max()
        
        # Add boundary rectangle
        ax.axhline(y=0, color='white', linestyle='--', alpha=0.3, linewidth=1)
        ax.axvline(x=0, color='white', linestyle='--', alpha=0.3, linewidth=1)
        
        # Add center line and face-off circles (approximate)
        ax.axvline(x=(x_min + x_max) / 2, color='white', linestyle=':', alpha=0.2)
    
    def _plot_final_cluster_sizes(self, ax, final_clusters):
        """Plot histogram of final cluster sizes"""
        cluster_sizes = [len(goals) for goals in final_clusters.values()]
        
        ax.hist(cluster_sizes, bins=20, color='cyan', alpha=0.7, edgecolor='white')
        ax.set_title('Final Cluster Size Distribution')
        ax.set_xlabel('Cluster Size (# of goals)')
        ax.set_ylabel('Number of Clusters')
        ax.set_yscale('log')
        ax.grid(True, alpha=0.3)
        
        # Add statistics
        mean_size = np.mean(cluster_sizes)
        median_size = np.median(cluster_sizes)
        ax.axvline(mean_size, color='red', linestyle='--', alpha=0.8, label=f'Mean: {mean_size:.1f}')
        ax.axvline(median_size, color='orange', linestyle='--', alpha=0.8, label=f'Median: {median_size:.1f}')
        ax.legend()
    
    def _plot_shot_type_by_level(self, ax, goal_cluster_map):
        """Plot shot type distribution by cluster level"""
        if 'shot_type' not in self.goals_df.columns:
            ax.text(0.5, 0.5, 'No shot type data', ha='center', va='center', 
                   transform=ax.transAxes, fontsize=12, color='white')
            return
        
        # Get cluster levels for each goal
        goal_levels = []
        for goal_idx in range(len(self.goals_df)):
            cluster_id = goal_cluster_map.get(goal_idx, 'root')
            if cluster_id and cluster_id in self.hierarchy:
                level = self.hierarchy[cluster_id]['level']
            else:
                level = -1
            goal_levels.append(level)
        
        # Create shot type vs level crosstab
        df_plot = pd.DataFrame({
            'shot_type': self.goals_df['shot_type'],
            'level': goal_levels
        })
        
        crosstab = pd.crosstab(df_plot['shot_type'], df_plot['level'])
        crosstab_pct = crosstab.div(crosstab.sum(axis=0), axis=1) * 100
        
        # Plot stacked bar chart
        crosstab_pct.plot(kind='bar', stacked=True, ax=ax, colormap='viridis')
        ax.set_title('Shot Type Distribution by Cluster Level')
        ax.set_xlabel('Shot Type')
        ax.set_ylabel('Percentage')
        ax.legend(title='Cluster Level', bbox_to_anchor=(1.05, 1))
        plt.setp(ax.get_xticklabels(), rotation=45, ha='right')
    
    def _plot_temporal_distribution(self, ax, goal_cluster_map):
        """Plot temporal distribution of goals by cluster"""
        if 'game_date' not in self.goals_df.columns:
            ax.text(0.5, 0.5, 'No date data', ha='center', va='center', 
                   transform=ax.transAxes, fontsize=12, color='white')
            return
        
        # Get month for each goal
        months = pd.to_datetime(self.goals_df['game_date']).dt.month
        
        # Get cluster levels
        goal_levels = []
        for goal_idx in range(len(self.goals_df)):
            cluster_id = goal_cluster_map.get(goal_idx, 'root')
            if cluster_id and cluster_id in self.hierarchy:
                level = self.hierarchy[cluster_id]['level']
            else:
                level = -1
            goal_levels.append(level)
        
        # Create temporal plot
        df_plot = pd.DataFrame({
            'month': months,
            'level': goal_levels
        })
        
        for level in sorted(df_plot['level'].unique()):
            if level >= 0:
                level_data = df_plot[df_plot['level'] == level]
                month_counts = level_data['month'].value_counts().sort_index()
                ax.plot(month_counts.index, month_counts.values, 
                       marker='o', label=f'Level {level}', alpha=0.7)
        
        ax.set_title('Temporal Distribution by Cluster Level')
        ax.set_xlabel('Month')
        ax.set_ylabel('Number of Goals')
        ax.legend()
        ax.grid(True, alpha=0.3)
    
    def _plot_score_situation_heatmap(self, ax, goal_cluster_map):
        """Plot score situation heatmap"""
        if 'team_score' not in self.goals_df.columns or 'opponent_score' not in self.goals_df.columns:
            ax.text(0.5, 0.5, 'No score data', ha='center', va='center', 
                   transform=ax.transAxes, fontsize=12, color='white')
            return
        
        # Create score situation matrix
        max_score = 8  # Limit to reasonable range
        score_matrix = np.zeros((max_score + 1, max_score + 1))
        
        for _, row in self.goals_df.iterrows():
            team_score = min(int(row['team_score']), max_score)
            opp_score = min(int(row['opponent_score']), max_score)
            score_matrix[team_score, opp_score] += 1
        
        # Create heatmap
        im = ax.imshow(score_matrix, cmap='YlOrRd', aspect='auto')
        ax.set_title('Goals by Score Situation')
        ax.set_xlabel('Opponent Score')
        ax.set_ylabel('Team Score (before goal)')
        
        # Add colorbar
        plt.colorbar(im, ax=ax, label='Number of Goals')
        
        # Add text annotations for high-value cells
        for i in range(score_matrix.shape[0]):
            for j in range(score_matrix.shape[1]):
                if score_matrix[i, j] > score_matrix.max() * 0.1:
                    ax.text(j, i, f'{int(score_matrix[i, j])}', 
                           ha='center', va='center', color='black', fontsize=8)
    
    def _plot_cluster_depth_distribution(self, ax, goal_cluster_map):
        """Plot distribution of cluster depths (levels)"""
        goal_levels = []
        for goal_idx in range(len(self.goals_df)):
            cluster_id = goal_cluster_map.get(goal_idx, 'root')
            if cluster_id and cluster_id in self.hierarchy:
                level = self.hierarchy[cluster_id]['level']
            else:
                level = -1
            goal_levels.append(max(0, level))  # Convert -1 to 0
        
        level_counts = pd.Series(goal_levels).value_counts().sort_index()
        
        bars = ax.bar(level_counts.index, level_counts.values, color='lightblue', alpha=0.7)
        ax.set_title('Goals by Final Cluster Depth')
        ax.set_xlabel('Cluster Level (Depth)')
        ax.set_ylabel('Number of Goals')
        
        # Add value labels on bars
        for bar, count in zip(bars, level_counts.values):
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 50, 
                   str(count), ha='center', va='bottom', fontweight='bold')
        
        ax.grid(True, alpha=0.3)
    
    def _plot_ice_position_heatmap(self, ax):
        """Plot 2D heatmap of goal positions on ice"""
        if 'x' not in self.goals_df.columns or 'y' not in self.goals_df.columns:
            ax.text(0.5, 0.5, 'No coordinate data', ha='center', va='center', 
                   transform=ax.transAxes, fontsize=12, color='white')
            return
        
        # Create 2D histogram
        h, xedges, yedges = np.histogram2d(self.goals_df['x'], self.goals_df['y'], bins=30)
        
        # Plot heatmap
        im = ax.imshow(h.T, origin='lower', extent=[xedges[0], xedges[-1], yedges[0], yedges[-1]], 
                      cmap='hot', aspect='auto')
        ax.set_title('Goal Position Heatmap')
        ax.set_xlabel('X Coordinate')
        ax.set_ylabel('Y Coordinate')
        
        plt.colorbar(im, ax=ax, label='Goal Density')
    
    def _plot_dataset_summary(self, ax, final_clusters, goal_cluster_map):
        """Plot summary statistics of the complete dataset"""
        ax.axis('off')
        
        # Calculate statistics
        total_goals = len(self.goals_df)
        total_clusters = len(final_clusters)
        avg_cluster_size = total_goals / total_clusters if total_clusters > 0 else 0
        
        # Cluster level distribution
        level_counts = {}
        for goal_idx in range(len(self.goals_df)):
            cluster_id = goal_cluster_map.get(goal_idx, 'root')
            if cluster_id and cluster_id in self.hierarchy:
                level = self.hierarchy[cluster_id]['level']
            else:
                level = -1
            level_counts[level] = level_counts.get(level, 0) + 1
        
        # Date range
        date_range = f"{self.goals_df['game_date'].min()} to {self.goals_df['game_date'].max()}"
        
        # Create summary text
        summary_text = f"""DATASET SUMMARY
        
Total Goals: {total_goals:,}
Final Clusters: {total_clusters}
Avg Cluster Size: {avg_cluster_size:.1f}

CLUSTER LEVELS:"""
        
        y_pos = 0.85
        ax.text(0.1, y_pos, summary_text, transform=ax.transAxes, 
               fontsize=12, color='white', fontweight='bold', verticalalignment='top')
        
        y_pos -= 0.35
        for level in sorted(level_counts.keys()):
            if level >= 0:
                level_name = self.clustering_sequence[level]['level_name'] if level < len(self.clustering_sequence) else f"level_{level}"
                count = level_counts[level]
                pct = count / total_goals * 100
                ax.text(0.1, y_pos, f"L{level} ({level_name}): {count:,} ({pct:.1f}%)", 
                       transform=ax.transAxes, fontsize=10, color='white')
                y_pos -= 0.08
        
        # Add date range
        ax.text(0.1, 0.1, f"Date Range:\n{date_range}", transform=ax.transAxes, 
               fontsize=10, color='white', fontweight='bold')
        
        ax.set_title('Summary Statistics', fontweight='bold', color='white')
    
    def _plot_spatial_hierarchy(self, ax):
        """Plot spatial distribution colored by top-level clusters"""
        if 'x' not in self.goals_df.columns or 'y' not in self.goals_df.columns:
            ax.text(0.5, 0.5, 'No coordinate data available', ha='center', va='center', 
                   transform=ax.transAxes, fontsize=14, color='white')
            ax.set_title('Spatial Hierarchy')
            return
        
        # Get first level clusters (spatial continents)
        first_level_clusters = [cid for cid, info in self.hierarchy.items() 
                               if info['level'] == 0]
        
        colors = plt.cm.tab10(np.linspace(0, 1, len(first_level_clusters)))
        
        for i, cluster_id in enumerate(first_level_clusters[:10]):  # Show top 10
            cluster_info = self.hierarchy[cluster_id]
            goal_indices = cluster_info['goal_indices']
            cluster_goals = self.goals_df.iloc[goal_indices]
            
            ax.scatter(cluster_goals['x'], cluster_goals['y'], 
                      c=[colors[i]], label=f'{cluster_id} (n={len(goal_indices)})',
                      alpha=0.7, s=15)
        
        ax.set_title('Spatial Hierarchy - Level 1 (Continents)')
        ax.set_xlabel('X Coordinate')
        ax.set_ylabel('Y Coordinate')
        ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=8)
        ax.grid(True, alpha=0.3)
    
    def _plot_cluster_sizes_by_level(self, ax):
        """Plot cluster size distribution by hierarchy level"""
        if not self.results:
            return
        
        level_sizes = self.results['level_sizes']
        levels = sorted([l for l in level_sizes.keys() if l >= 0])
        
        # Create box plot data
        box_data = []
        labels = []
        
        for level in levels:
            if level < len(self.clustering_sequence):
                level_name = self.clustering_sequence[level]['level_name']
                labels.append(f"L{level}\n{level_name}")
                box_data.append(level_sizes[level])
        
        if box_data:
            bp = ax.boxplot(box_data, labels=labels, patch_artist=True)
            
            # Color boxes
            colors = plt.cm.viridis(np.linspace(0, 1, len(box_data)))
            for patch, color in zip(bp['boxes'], colors):
                patch.set_facecolor(color)
                patch.set_alpha(0.7)
        
        ax.set_title('Cluster Size Distribution by Level')
        ax.set_ylabel('Cluster Size (# of goals)')
        ax.set_yscale('log')
        ax.grid(True, alpha=0.3)
    
    def _plot_hierarchy_tree(self, ax, max_levels):
        """Plot simplified hierarchy tree"""
        ax.text(0.5, 0.5, f'Hierarchy Tree\n\n{len(self.hierarchy)} total clusters\n'
                         f'across {max([info["level"] for info in self.hierarchy.values() if info["level"] >= 0]) + 1} levels\n\n'
                         f'Clustering sequence:\n' + 
                         '\n'.join([f'{i+1}. {config["level_name"]} ({config["name"]})' 
                                   for i, config in enumerate(self.clustering_sequence[:max_levels])]),
               ha='center', va='center', transform=ax.transAxes, 
               fontsize=10, color='white')
        ax.set_title('Clustering Hierarchy Overview')
        ax.axis('off')
    
    def _plot_level_characteristics(self, ax):
        """Plot characteristics of each clustering level"""
        if not self.clustering_sequence:
            return
        
        # Show clustering method distribution
        methods = [config['method'] for config in self.clustering_sequence]
        method_counts = pd.Series(methods).value_counts()
        
        colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4']
        wedges, texts, autotexts = ax.pie(method_counts.values, labels=method_counts.index, 
                                         colors=colors[:len(method_counts)], autopct='%1.0f%%',
                                         startangle=90)
        
        ax.set_title('Clustering Methods Used')
        
        # Adjust text color for dark theme
        for text in texts + autotexts:
            text.set_color('white')
    
    def save_results(self):
        """Save all results to files"""
        logger.info("Saving clustering results...")
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save hierarchy structure
        hierarchy_file = os.path.join(self.output_dir, f'hierarchy_{timestamp}.json')
        with open(hierarchy_file, 'w') as f:
            # Convert numpy types to Python types for JSON serialization
            hierarchy_json = {}
            for cluster_id, cluster_info in self.hierarchy.items():
                hierarchy_json[cluster_id] = {
                    'goal_indices': cluster_info['goal_indices'],
                    'level': int(cluster_info['level']),
                    'parent': cluster_info['parent'],
                    'children': cluster_info['children'],
                    'cluster_id': cluster_info['cluster_id'],
                    'size': int(cluster_info['size']),
                    'level_name': cluster_info.get('level_name', 'unknown')
                }
            json.dump(hierarchy_json, f, indent=2)
        
        logger.info(f"Saved hierarchy to {hierarchy_file}")
        
        # Save clustering configuration
        config_file = os.path.join(self.output_dir, f'clustering_config_{timestamp}.json')
        with open(config_file, 'w') as f:
            json.dump({
                'clustering_sequence': self.clustering_sequence,
                'results': self.results,
                'timestamp': timestamp
            }, f, indent=2)
        
        logger.info(f"Saved configuration to {config_file}")
        
        return hierarchy_file, config_file
    
    def run_complete_analysis(self, csv_path='data/nhl_goals_with_names.csv', max_cluster_size=500):
        """Run complete sequential clustering analysis"""
        logger.info("Running complete sequential clustering analysis...")
        
        # Load and prepare data
        self.load_and_prepare_data(csv_path)
        
        # Perform sequential clustering
        self.perform_sequential_clustering(max_cluster_size=max_cluster_size)
        
        # Create goal mapping
        mapping_df, mapping_file = self.create_goal_hierarchy_mapping()
        
        # Create visualizations
        self.visualize_hierarchy(save_png=True)
        
        # Create complete dataset visualization
        self.visualize_complete_dataset(save_png=True)
        
        # Create galaxy visualization
        self.visualize_galaxy_view(save_png=True)
        
        # Save results
        hierarchy_file, config_file = self.save_results()
        
        logger.info("Complete sequential clustering analysis finished!")
        logger.info(f"Results saved to: {self.output_dir}")
        
        return {
            'hierarchy': self.hierarchy,
            'mapping_df': mapping_df,
            'mapping_file': mapping_file,
            'hierarchy_file': hierarchy_file,
            'config_file': config_file
        }


def main():
    """Run the complete sequential clustering analysis"""
    clusterer = SequentialHierarchicalClusterer()
    
    # Run complete analysis
    results = clusterer.run_complete_analysis(max_cluster_size=50)
    
    if results:
        print(f"\nSequential Clustering Analysis Complete!")
        print(f"Results saved to: {clusterer.output_dir}")
        print(f"Total clusters created: {len(clusterer.hierarchy)}")
        print(f"Goal mapping saved to: {results['mapping_file']}")
        print(f"Hierarchy structure saved to: {results['hierarchy_file']}")
    else:
        print("Sequential clustering analysis failed!")


if __name__ == "__main__":
    main()