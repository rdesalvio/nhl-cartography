import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.preprocessing import StandardScaler, LabelEncoder
import hdbscan
import umap
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

def load_and_prepare_data():
    """Load the NHL goals dataset and prepare features for clustering"""
    print("Loading NHL goals dataset...")
    df = pd.read_csv('data/nhl_goals_with_names.csv', low_memory=False)
    df['game_date'] = pd.to_datetime(df['game_date'])
    df = df[df['game_date'] >= '2023-10-09'].copy()
    # filters out penalty shots
    df = df[df['period'] < 5].copy()
    print(f"Goals from 2023 onwards: {len(df):,}")

    # Filter out empty nets
    df = df[~df['goalie'].isna()].copy()
    print(f"Goals from 2023 onwards: {len(df):,}")
        
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
    df['score_diff'] = df['team_score'] - df['opponent_score']
    
    # Select the specified features
    feature_columns = ['x', 'y', 'period', 'period_time', 'shot_zone', 'shot_type', 'game_time',
                      'score_diff', 'situation_code', 'team_id']
    
    # Create subset with only complete data for key features
    df_subset = df[feature_columns].copy()
    
    print(f"Shape before removing missing values: {df_subset.shape}")
    
    return df_subset, df

def parse_time_to_minutes(time_str):
    """Convert time string (MM:SS) to minutes as float"""
    if pd.isna(time_str) or time_str == '':
        return 0.0
    try:
        parts = str(time_str).split(':')
        if len(parts) == 2:
            minutes = int(parts[0])
            seconds = int(parts[1])
            return minutes + seconds / 60.0
        return 0.0
    except:
        return 0.0

def encode_features(df):
    """Encode categorical features and scale numerical ones"""
    print("Encoding categorical features...")
    df_encoded = df.copy()
    
    # Encode categorical variables
    categorical_cols = ['shot_type']
    label_encoders = {}
    
    for col in categorical_cols:
        le = LabelEncoder()
        # Convert to string to ensure uniform type
        col_data = df_encoded[col].astype(str)
        df_encoded[f'{col}_encoded'] = le.fit_transform(col_data)
        label_encoders[col] = le
        print(f"  {col}: {len(le.classes_)} unique values")
    
    # Select features for clustering (use encoded versions)
    feature_cols = ['shot_zone', 'shot_type_encoded', 'game_time',
                   'score_diff', 'situation_code', 'team_id']
    
    X = df_encoded[feature_cols]
    
    # Scale features
    print("Scaling features...")
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    return X_scaled, df_encoded, label_encoders, scaler

def apply_umap_reduction(X_scaled, n_components=2, n_neighbors=8, min_dist=0.1):
    """Apply UMAP dimensionality reduction"""
    print(f"Applying UMAP reduction to {n_components}D with n_neighbors={n_neighbors}, min_dist={min_dist}...")
    
    reducer = umap.UMAP(
        n_components=15,
        n_neighbors=15,
        min_dist=0.1,
        random_state=42
    )
    
    X_umap = reducer.fit_transform(X_scaled)
    
    print(f"UMAP reduction complete. Shape: {X_scaled.shape} -> {X_umap.shape}")
    
    return X_umap, reducer

def perform_density_clustering(X_umap, min_cluster_size=300, min_samples=15):
    """Perform HDBSCAN clustering on UMAP-reduced data"""
    print(f"Performing HDBSCAN clustering on UMAP data with min_cluster_size={min_cluster_size}, min_samples={min_samples}...")
    
    clusterer = hdbscan.HDBSCAN(
        min_cluster_size=min_cluster_size,
    )
    
    cluster_labels = clusterer.fit_predict(X_umap)
    
    return clusterer, cluster_labels

def analyze_galaxy_structure(cluster_labels, df_encoded):
    """Analyze clustering results with galaxy-like structure in mind"""
    print("\n" + "="*60)
    print("UMAP + HDBSCAN GALAXY STRUCTURE ANALYSIS")
    print("="*60)
    
    unique_labels = np.unique(cluster_labels)
    n_clusters = len(unique_labels) - (1 if -1 in cluster_labels else 0)
    n_noise = list(cluster_labels).count(-1)
    
    print(f"Number of 'galaxies' (clusters): {n_clusters}")
    print(f"Number of 'dark matter' (noise points): {n_noise}")
    print(f"Percentage of goals in galaxies: {((len(cluster_labels) - n_noise) / len(cluster_labels)) * 100:.1f}%")
    
    # Galaxy size statistics
    galaxy_sizes = []
    for label in unique_labels:
        if label != -1:  # Exclude noise
            size = np.sum(cluster_labels == label)
            galaxy_sizes.append(size)
    
    if galaxy_sizes:
        print(f"\nGalaxy size statistics:")
        print(f"  Average galaxy size: {np.mean(galaxy_sizes):.1f} goals")
        print(f"  Median galaxy size: {np.median(galaxy_sizes):.1f} goals")
        print(f"  Smallest galaxy: {min(galaxy_sizes)} goals")
        print(f"  Largest galaxy: {max(galaxy_sizes)} goals")
        print(f"  Galaxy size std deviation: {np.std(galaxy_sizes):.1f}")
        
        # Classify galaxies by size
        small_galaxies = sum(1 for size in galaxy_sizes if size < 100)
        medium_galaxies = sum(1 for size in galaxy_sizes if 100 <= size < 1000)
        large_galaxies = sum(1 for size in galaxy_sizes if size >= 1000)
        
        print(f"\nGalaxy classification:")
        print(f"  Small galaxies (<100 goals): {small_galaxies}")
        print(f"  Medium galaxies (100-999 goals): {medium_galaxies}")
        print(f"  Large galaxies (≥1000 goals): {large_galaxies}")
    
    return n_clusters, n_noise, galaxy_sizes

def create_umap_hdbscan_visualizations(X_umap, cluster_labels, df_encoded, clusterer, reducer):
    """Create comprehensive visualizations of UMAP + HDBSCAN clustering"""
    print("\nCreating UMAP + HDBSCAN visualizations...")
    
    plt.style.use('default')
    fig = plt.figure(figsize=(20, 16))
    
    unique_labels = np.unique(cluster_labels)
    n_clusters = len(unique_labels) - (1 if -1 in cluster_labels else 0)
    
    # Use a colormap that works well for many clusters
    if n_clusters > 0:
        colors = plt.cm.tab20(np.linspace(0, 1, min(n_clusters, 20)))
        if n_clusters > 20:
            colors = plt.cm.nipy_spectral(np.linspace(0, 1, n_clusters))
    else:
        colors = ['black']
    
    # 1. UMAP embedding with HDBSCAN clusters
    ax1 = plt.subplot(3, 4, 1)
    
    # Plot noise first
    if -1 in cluster_labels:
        mask = cluster_labels == -1
        plt.scatter(X_umap[mask, 0], X_umap[mask, 1], c='lightgray', alpha=0.3, s=1, label='Noise')
    
    # Plot clusters
    color_idx = 0
    for label in unique_labels:
        if label != -1:
            mask = cluster_labels == label
            color = colors[color_idx % len(colors)]
            plt.scatter(X_umap[mask, 0], X_umap[mask, 1], c=[color], alpha=0.8, s=3, 
                       label=f'Galaxy {label}' if color_idx < 10 else "")
            color_idx += 1
    
    plt.title(f'UMAP + HDBSCAN Galaxies\n({n_clusters} galaxies found)')
    plt.xlabel('UMAP Dimension 1')
    plt.ylabel('UMAP Dimension 2')
    if n_clusters <= 10:
        plt.legend(fontsize=8, markerscale=3)
    
    # 2. UMAP colored by original features
    feature_plots = [
        ('period', 'Period'),
        ('shot_type_encoded', 'Shot Type'),
        ('score_diff', 'Team Score'),
        ('x', 'X Coordinate'),
        ('y', 'Y Coordinate')
    ]
    
    for i, (feature, title) in enumerate(feature_plots):
        ax = plt.subplot(3, 4, i + 2)
        if feature in df_encoded.columns:
            feature_data = df_encoded[feature]
            scatter = plt.scatter(X_umap[:, 0], X_umap[:, 1], 
                                c=feature_data, cmap='viridis', alpha=0.6, s=1)
            plt.title(f'UMAP colored by {title}')
            plt.xlabel('UMAP Dimension 1')
            plt.ylabel('UMAP Dimension 2')
            plt.colorbar(scatter, ax=ax)
    
    # 7. Galaxy size distribution
    ax7 = plt.subplot(3, 4, 8)
    galaxy_sizes = [np.sum(cluster_labels == label) for label in unique_labels if label != -1]
    
    if galaxy_sizes:
        plt.hist(galaxy_sizes, bins=min(20, len(galaxy_sizes)), alpha=0.7, edgecolor='black')
        plt.xlabel('Galaxy Size')
        plt.ylabel('Frequency')
        plt.title('Galaxy Size Distribution')
        plt.axvline(np.mean(galaxy_sizes), color='red', linestyle='--', 
                   label=f'Mean: {np.mean(galaxy_sizes):.0f}')
        plt.legend()
    
    # 8. Cluster stability (if available)
    ax8 = plt.subplot(3, 4, 9)
    if hasattr(clusterer, 'cluster_persistence_'):
        persistence = clusterer.cluster_persistence_
        valid_clusters = [i for i in range(len(persistence)) if persistence[i] > 0]
        plt.bar(valid_clusters, [persistence[i] for i in valid_clusters])
        plt.title('Cluster Persistence')
        plt.xlabel('Cluster ID')
        plt.ylabel('Persistence')
    else:
        plt.text(0.5, 0.5, 'Cluster persistence\nnot available', 
                ha='center', va='center', transform=ax8.transAxes)
        plt.title('Cluster Stability')
    
    # 10. Spatial distribution (if coordinates available)
    ax10 = plt.subplot(3, 4, 11)
    has_coords = (~df_encoded['x'].isna() & ~df_encoded['y'].isna()).sum() > 0
    if has_coords:
        scatter = plt.scatter(df_encoded['x'], df_encoded['y'], 
                            c=cluster_labels, cmap='nipy_spectral', alpha=0.6, s=2)
        plt.title('Spatial Distribution of Galaxies')
        plt.xlabel('X Coordinate')
        plt.ylabel('Y Coordinate')
    else:
        plt.text(0.5, 0.5, 'No spatial coordinates available', 
                ha='center', va='center', transform=ax10.transAxes)
        plt.title('Spatial Distribution (No Data)')
    
    # 11. UMAP parameters and results summary
    ax11 = plt.subplot(3, 4, 12)
    summary_text = f"""
    UMAP + HDBSCAN Results:
    
    UMAP Parameters:
    • n_components: {reducer.n_components}
    • n_neighbors: {reducer.n_neighbors}
    • min_dist: {reducer.min_dist}
    
    HDBSCAN Results:
    • Galaxies found: {n_clusters}
    • Goals clustered: {len(cluster_labels) - list(cluster_labels).count(-1):,}
    • Noise points: {list(cluster_labels).count(-1):,}
    • Clustering rate: {((len(cluster_labels) - list(cluster_labels).count(-1)) / len(cluster_labels) * 100):.1f}%
    """
    
    plt.text(0.05, 0.95, summary_text, fontsize=10, transform=ax11.transAxes, 
             verticalalignment='top', fontfamily='monospace')
    plt.axis('off')
    plt.title('Summary')
    
    plt.tight_layout()
    plt.savefig('umap_hdbscan_galaxy_analysis.png', dpi=300, bbox_inches='tight')
    plt.show()

def print_galaxy_details(cluster_labels, df_encoded, top_n=5):
    """Print detailed information about the most interesting galaxies"""
    print(f"\n" + "="*60)
    print(f"TOP {top_n} LARGEST GALAXIES - DETAILED ANALYSIS")
    print("="*60)
    
    unique_labels = np.unique(cluster_labels)
    galaxy_info = []
    
    for label in unique_labels:
        if label != -1:  # Skip noise
            mask = cluster_labels == label
            size = np.sum(mask)
            galaxy_data = df_encoded[mask]
            
            # Calculate galaxy characteristics
            most_common_period = galaxy_data['period'].mode().iloc[0] if len(galaxy_data['period'].mode()) > 0 else 'N/A'
            most_common_shot = galaxy_data['shot_type'].mode().iloc[0] if len(galaxy_data['shot_type'].mode()) > 0 else 'N/A'
            avg_score = galaxy_data['score_diff'].mean()
            avg_period_time = galaxy_data['period_time'].mean()
            
            
            galaxy_info.append({
                'label': label,
                'size': size,
                'most_common_period': most_common_period,
                'most_common_shot': most_common_shot,
                'avg_score': avg_score,
                'avg_period_time': avg_period_time,
            })
    
    # Sort by size
    galaxy_info.sort(key=lambda x: x['size'], reverse=True)
    
    for i, info in enumerate(galaxy_info[:top_n]):
        print(f"\n🌌 Galaxy {info['label']} (Rank #{i+1}):")
        print(f"    Size: {info['size']:,} goals")
        print(f"    Common period: {info['most_common_period']}")
        print(f"    Common shot type: {info['most_common_shot']}")
        print(f"    Avg game time: {info['avg_period_time']:.1f} minutes into period")
        print(f"    Score context: {info['avg_score']:.1f}")

def main():
    """Main execution function for UMAP + HDBSCAN galaxy exploration"""
    print("🌌 NHL GOAL GALAXY EXPLORATION: UMAP + HDBSCAN 🌌")
    print("=" * 60)
    print("Using UMAP dimensionality reduction + HDBSCAN clustering")
    print("=" * 60)
    
    # Load and prepare data
    df_subset, df_original = load_and_prepare_data()
    
    # Encode features
    X_scaled, df_encoded, label_encoders, scaler = encode_features(df_subset)
    
    # Apply UMAP reduction
    X_umap, reducer = apply_umap_reduction(X_scaled)
    
    # Perform clustering on UMAP-reduced data
    clusterer, cluster_labels = perform_density_clustering(X_umap, min_cluster_size=15, min_samples=5)
    
    # Analyze galaxy structure
    n_clusters, n_noise, galaxy_sizes = analyze_galaxy_structure(cluster_labels, df_encoded)
    
    # Create comprehensive visualizations
    create_umap_hdbscan_visualizations(X_umap, cluster_labels, df_encoded, clusterer, reducer)
    
    # Print detailed galaxy information
    print_galaxy_details(cluster_labels, df_encoded)
    
    print(f"\n" + "="*60)
    print("🌌 UMAP + HDBSCAN GALAXY EXPLORATION COMPLETE 🌌")
    print("="*60)
    print(f"Discovered {n_clusters} distinct goal galaxies")
    print(f"Processed {len(cluster_labels):,} total goals")
    print(f"Successfully clustered: {len(cluster_labels) - n_noise:,} goals")
    print(f"Results saved as 'umap_hdbscan_galaxy_analysis.png'")

if __name__ == "__main__":
    main()