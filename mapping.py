import pandas as pd
import numpy as np
import json
import os
import matplotlib.pyplot as plt
from sklearn.manifold import TSNE
from sklearn.preprocessing import StandardScaler
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ConstellationMapper:
    """Creates constellation map layouts from clustering results"""
    
    def __init__(self, output_dir="visualizations"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        
        # Coordinate system parameters
        self.galaxy_radius = 1000  # Max radius for galaxy distribution
        self.constellation_radius = 75  # Max radius for constellations within galaxy (reduced from 120)
        self.star_radius = 45  # Max radius for stars within constellation (reduced from 80)
        
    def load_clustering_results(self, specific_file=None):
        """Load the clustering results from sequential_clustering output"""
        try:
            data_dir = "sequential_clustering"
            
            if specific_file:
                # Use specific file if provided
                mapping_path = specific_file
                if not os.path.exists(mapping_path):
                    mapping_path = os.path.join(data_dir, specific_file)
            else:
                # Look for the most recent clustering results
                mapping_files = [f for f in os.listdir(data_dir) if f.startswith("goal_hierarchy_mapping_")]
                
                if not mapping_files:
                    raise FileNotFoundError("No clustering results found. Run sequential_clustering.py first.")
                
                # Get the most recent file
                latest_file = sorted(mapping_files)[-1]
                mapping_path = os.path.join(data_dir, latest_file)
            
            logger.info(f"Loading clustering results from: {mapping_path}")
            self.df = pd.read_csv(mapping_path)
            
            # Load original data to get missing score information
            try:
                original_data = pd.read_csv('data/nhl_goals_with_names.csv', low_memory=False)
                logger.info(f"Loaded original data for score information")
                
                # Add missing score columns if they don't exist
                if 'team_score' not in self.df.columns and 'team_score' in original_data.columns:
                    # Create a mapping from goal_index to scores
                    if 'goal_index' in self.df.columns:
                        score_mapping = original_data.set_index(original_data.index)[['team_score', 'opponent_score']]
                        self.df = self.df.merge(score_mapping, left_on='goal_index', right_index=True, how='left')
                        logger.info(f"Added team_score and opponent_score columns from original data")
                    else:
                        logger.warning("No goal_index column found, cannot merge score data")
            except Exception as e:
                logger.warning(f"Could not load original score data: {e}")
            
            # Debug: Print data structure info
            logger.info(f"Data columns: {list(self.df.columns)}")
            logger.info(f"Level 0 clusters (Galaxies): {self.df['level_0_cluster'].nunique()}")
            logger.info(f"Level 1 clusters (Clusters): {self.df['level_1_cluster'].nunique()}")
            logger.info(f"Level 2 clusters (Solar Systems): {self.df['level_2_cluster'].nunique()}")
            if 'level_3_cluster' in self.df.columns:
                logger.info(f"Level 3 clusters (Stars): {self.df['level_3_cluster'].nunique() if self.df['level_3_cluster'].notna().any() else 0}")
            
            # Sample data
            logger.info("Sample data:")
            available_levels = [col for col in ['level_0_cluster', 'level_1_cluster', 'level_2_cluster', 'level_3_cluster'] if col in self.df.columns]
            logger.info(self.df[available_levels].head(10))
            
            # Load hierarchy structure
            hierarchy_files = [f for f in os.listdir(data_dir) if f.startswith("hierarchy_")]
            if hierarchy_files:
                hierarchy_file = sorted(hierarchy_files)[-1]
                hierarchy_path = os.path.join(data_dir, hierarchy_file)
                with open(hierarchy_path, 'r') as f:
                    self.hierarchy = json.load(f)
            else:
                self.hierarchy = {}
            
            logger.info(f"Loaded {len(self.df)} goal mappings")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load clustering results: {e}")
            return False
    
    def create_spiral_galaxy_layout(self):
        """Create spiral galaxy layout for top-level clusters"""
        logger.info("Creating spiral galaxy layout...")
        
        # Get unique galaxies (level 0 clusters - the mixed clusters)
        galaxies = self.df['level_0_cluster'].unique()
        galaxy_positions = {}
        
        # Parameters for spiral galaxy
        n_arms = 3  # Number of spiral arms
        arm_separation = 2 * np.pi / n_arms
        arm_width = 0.5  # Spread along each arm
        
        for i, galaxy in enumerate(galaxies):
            # Distribute galaxies along spiral arms
            arm_index = i % n_arms
            position_on_arm = (i // n_arms) * 0.3 + 0.2  # Position along arm length
            
            # Calculate spiral coordinates
            theta = arm_index * arm_separation + position_on_arm * 2 * np.pi
            radius = position_on_arm * self.galaxy_radius
            
            # Add some randomness for natural look
            theta += np.random.normal(0, arm_width)
            radius += np.random.normal(0, radius * 0.1)
            
            x = radius * np.cos(theta)
            y = radius * np.sin(theta)
            
            galaxy_positions[galaxy] = {'x': x, 'y': y, 'arm': arm_index}
        
        self.galaxy_positions = galaxy_positions
        logger.info(f"Positioned {len(galaxies)} galaxies in spiral layout")
        
    def create_cluster_positions(self):
        """Use t-SNE to position clusters within each galaxy"""
        logger.info("Creating cluster positions using t-SNE...")
        
        cluster_positions = {}
        
        for galaxy, galaxy_pos in self.galaxy_positions.items():
            # Get clusters (level 1 clusters) within this galaxy
            galaxy_data = self.df[self.df['level_0_cluster'] == galaxy]
            clusters_raw = galaxy_data['level_1_cluster'].unique()
            
            # Create unique cluster names by combining galaxy + cluster
            clusters = [f"{galaxy}.{cluster}" for cluster in clusters_raw]
            
            if len(clusters) <= 1:
                # Single cluster - place at galaxy center
                for cluster in clusters:
                    cluster_positions[cluster] = {
                        'x': galaxy_pos['x'],
                        'y': galaxy_pos['y'],
                        'galaxy': galaxy
                    }
                continue
            
            # Create features for t-SNE based on cluster metadata
            cluster_features = []
            for i, cluster in enumerate(clusters):
                cluster_raw_name = clusters_raw[i]
                cluster_data = galaxy_data[galaxy_data['level_1_cluster'] == cluster_raw_name]
                
                # Features: size, average period, score patterns, etc.
                features = [
                    len(cluster_data),  # Number of goals in cluster
                    cluster_data['period'].mean() if 'period' in cluster_data.columns else 2.0,
                    cluster_data['team_score'].mean() if 'team_score' in cluster_data.columns else 1.0,
                    cluster_data['opponent_score'].mean() if 'opponent_score' in cluster_data.columns else 1.0,
                    len(cluster_data['level_2_cluster'].unique()),  # Number of solar systems
                ]
                cluster_features.append(features)
            
            # Apply t-SNE if we have enough clusters
            if len(clusters) >= 2:
                scaler = StandardScaler()
                features_scaled = scaler.fit_transform(cluster_features)
                
                # Use t-SNE for 2D positioning
                perplexity = min(5, len(clusters) - 1)
                tsne = TSNE(n_components=2, perplexity=perplexity, random_state=42)
                positions_2d = tsne.fit_transform(features_scaled)
                
                # Scale positions to fit within galaxy region with minimum separation
                max_abs = np.max(np.abs(positions_2d))
                if max_abs > 0:
                    positions_2d = positions_2d * self.constellation_radius / max_abs
                else:
                    # Failsafe: if t-SNE produces identical positions, create manual spacing
                    logger.warning(f"t-SNE produced identical positions for {len(clusters)} clusters in galaxy {galaxy}. Using manual spacing.")
                    for i, cluster in enumerate(clusters):
                        angle = (2 * np.pi * i) / len(clusters)
                        radius = self.constellation_radius * 0.7
                        positions_2d[i] = [radius * np.cos(angle), radius * np.sin(angle)]
                
                # Ensure minimum separation between clusters and offset by galaxy center
                min_separation = 10.0  # Minimum distance between cluster centers
                for i, cluster in enumerate(clusters):
                    base_x = galaxy_pos['x'] + positions_2d[i, 0]
                    base_y = galaxy_pos['y'] + positions_2d[i, 1]
                    
                    # Check for conflicts with existing clusters and adjust if necessary
                    final_x, final_y = base_x, base_y
                    for existing_cluster, existing_pos in cluster_positions.items():
                        if existing_pos['galaxy'] == galaxy:
                            distance = np.sqrt((final_x - existing_pos['x'])**2 + (final_y - existing_pos['y'])**2)
                            if distance < min_separation:
                                # Push this cluster away from the existing one
                                angle = np.arctan2(final_y - existing_pos['y'], final_x - existing_pos['x'])
                                final_x = existing_pos['x'] + min_separation * np.cos(angle)
                                final_y = existing_pos['y'] + min_separation * np.sin(angle)
                    
                    cluster_positions[cluster] = {
                        'x': final_x,
                        'y': final_y,
                        'galaxy': galaxy
                    }
            else:
                # Fallback for single cluster
                cluster_positions[clusters[0]] = {
                    'x': galaxy_pos['x'],
                    'y': galaxy_pos['y'],
                    'galaxy': galaxy
                }
        
        self.cluster_positions = cluster_positions
        logger.info(f"Positioned {len(cluster_positions)} clusters")
    
    def create_solar_system_positions(self):
        """Position solar systems within each cluster"""
        logger.info("Creating solar system positions...")
        
        solar_system_positions = {}
        
        for cluster, cluster_pos in self.cluster_positions.items():
            # Parse cluster name to get galaxy and raw cluster name
            galaxy_name, cluster_raw_name = cluster.split('.', 1)
            
            # Get all goals within this cluster
            cluster_data = self.df[(self.df['level_0_cluster'] == galaxy_name) & 
                                  (self.df['level_1_cluster'] == cluster_raw_name)]
            
            # Group by solar system (level 2)
            solar_systems = cluster_data.groupby('level_2_cluster')
            
            # Position solar systems around cluster center
            num_solar_systems = len(solar_systems)
            if num_solar_systems == 0:
                continue
                
            for sys_idx, (solar_system_raw_name, system_goals) in enumerate(solar_systems):
                # Position the center of this solar system within cluster area
                if num_solar_systems == 1:
                    # Single solar system - place at cluster center
                    system_center_x = cluster_pos['x']
                    system_center_y = cluster_pos['y']
                else:
                    # Multiple solar systems - distribute in a circular pattern with moderate spacing
                    max_radius = self.constellation_radius * 0.6  # Reduced from 0.8 for closer spacing
                    
                    # Use structured circular positioning with better layering
                    angle = (2 * np.pi * sys_idx) / num_solar_systems
                    radius = max_radius * (0.4 + 0.6 * (sys_idx % 2))  # Two clear layers
                    
                    system_center_x = cluster_pos['x'] + radius * np.cos(angle)
                    system_center_y = cluster_pos['y'] + radius * np.sin(angle)
                
                # Create solar system entry
                solar_system_name = f"{cluster}.{solar_system_raw_name}"
                solar_system_positions[solar_system_name] = {
                    'x': system_center_x,
                    'y': system_center_y,
                    'cluster': cluster,
                    'galaxy': cluster_pos['galaxy'],
                    'goal_count': len(system_goals)
                }
        
        self.solar_system_positions = solar_system_positions
        logger.info(f"Positioned {len(solar_system_positions)} solar systems")
    
    def create_star_positions(self):
        """Create tightly clustered star positions around solar system labels"""
        logger.info("Creating tight star clusters around solar system centers...")
        
        star_positions = {}
        goal_positions = {}
        
        # Generate color palette for clusters
        import colorsys
        def generate_cluster_color(cluster_index, total_clusters):
            hue = (cluster_index * 137.508) % 360  # Golden angle for good distribution
            saturation = 0.7 + 0.3 * (cluster_index % 3) / 3  # Vary saturation
            lightness = 0.5 + 0.3 * ((cluster_index * 7) % 4) / 4  # Vary lightness
            rgb = colorsys.hls_to_rgb(hue/360, lightness, saturation)
            return f"#{int(rgb[0]*255):02x}{int(rgb[1]*255):02x}{int(rgb[2]*255):02x}"
        
        cluster_index = 0
        
        for solar_system, system_pos in self.solar_system_positions.items():
            # Parse solar system name to get hierarchy
            parts = solar_system.split('.')
            galaxy_name = parts[0]
            cluster_raw_name = parts[1]
            system_raw_name = parts[2]
            
            # Get all goals within this solar system
            system_data = self.df[(self.df['level_0_cluster'] == galaxy_name) & 
                                 (self.df['level_1_cluster'] == cluster_raw_name) &
                                 (self.df['level_2_cluster'] == system_raw_name)]
            
            # Check if there are level 3 clusters (player clusters)
            if 'level_3_cluster' in self.df.columns and system_data['level_3_cluster'].notna().any():
                # Group by star cluster (level 3 - player clusters)
                star_clusters = system_data.groupby('level_3_cluster')
            else:
                # No level 3 clustering - treat the whole solar system as one star cluster
                star_clusters = [(system_raw_name, system_data)]
            
            # Position star clusters very close to solar system center for tight clustering
            num_star_clusters = len(star_clusters)
            if num_star_clusters == 0:
                continue
                
            for star_idx, (star_raw_name, star_goals) in enumerate(star_clusters):
                # Position star clusters in a very tight formation around solar system center
                if num_star_clusters == 1:
                    # Single cluster - place exactly at solar system center
                    cluster_center_x = system_pos['x']
                    cluster_center_y = system_pos['y']
                else:
                    # Multiple clusters - use very small radius to keep them close to solar system label
                    # Dramatically reduced radius for tight clustering
                    max_radius = 3.0  # Much smaller than before (was self.star_radius * 0.9 ≈ 40)
                    
                    # Simple circular distribution with minimal spread
                    angle = (2 * np.pi * star_idx) / num_star_clusters
                    # Use single ring with tight spacing - no dual ring system
                    radius = max_radius
                    
                    cluster_center_x = system_pos['x'] + radius * np.cos(angle)
                    cluster_center_y = system_pos['y'] + radius * np.sin(angle)
                
                # Generate color for this cluster
                total_possible_clusters = len(self.df['level_2_cluster'].unique()) * 2  # Estimate
                cluster_color = generate_cluster_color(cluster_index, total_possible_clusters)
                cluster_index += 1
                
                # Create star cluster entry
                star_name = f"{solar_system}.{star_raw_name}" if star_raw_name != system_raw_name else solar_system
                star_positions[star_name] = {
                    'x': cluster_center_x,
                    'y': cluster_center_y,
                    'solar_system': solar_system,
                    'cluster': system_pos['cluster'],
                    'galaxy': system_pos['galaxy'],
                    'cluster_color': cluster_color,
                    'goal_count': len(star_goals)
                }
                
                # Position individual goals with minimal jitter to maintain tight clustering
                for goal_idx, (_, goal) in enumerate(star_goals.iterrows()):
                    # Extremely minimal jitter to keep stars visually together
                    # This ensures stars appear as a tight cluster around the solar system label
                    jitter_radius = 0.3  # Much smaller jitter (was 0.8)
                    jitter_angle = np.random.uniform(0, 2 * np.pi)
                    jitter_distance = np.random.uniform(0, jitter_radius)
                    
                    goal_x = cluster_center_x + jitter_distance * np.cos(jitter_angle)
                    goal_y = cluster_center_y + jitter_distance * np.sin(jitter_angle)
                    
                    goal_id = goal['goal_index']
                    goal_positions[goal_id] = {
                        'x': goal_x,
                        'y': goal_y,
                        'star_cluster': star_name,
                        'solar_system': solar_system,
                        'cluster': system_pos['cluster'],
                        'galaxy': system_pos['galaxy'],
                        'cluster_color': cluster_color,
                        'goal_data': goal
                    }
        
        self.star_positions = star_positions
        self.goal_positions = goal_positions
        logger.info(f"Positioned {len(star_positions)} tight star clusters with {len(goal_positions)} individual goals")
    
    def create_geojson(self):
        """Convert positions to GeoJSON format"""
        logger.info("Creating GeoJSON...")
        
        features = []
        
        # Add galaxies
        for galaxy, pos in self.galaxy_positions.items():
            feature = {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [pos['x'], pos['y']]
                },
                "properties": {
                    "name": galaxy,
                    "type": "galaxy",
                    "arm": pos['arm']
                }
            }
            features.append(feature)
        
        # Add clusters
        for cluster, pos in self.cluster_positions.items():
            feature = {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [pos['x'], pos['y']]
                },
                "properties": {
                    "name": cluster,
                    "type": "cluster",
                    "galaxy": pos['galaxy']
                }
            }
            features.append(feature)
        
        # Add solar systems
        for solar_system, pos in self.solar_system_positions.items():
            feature = {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [pos['x'], pos['y']]
                },
                "properties": {
                    "name": solar_system,
                    "type": "solar_system",
                    "cluster": pos['cluster'],
                    "galaxy": pos['galaxy'],
                    "goal_count": pos['goal_count']
                }
            }
            features.append(feature)
        
        # Add individual goals (now positioned together by cluster)
        for goal_id, goal_pos in self.goal_positions.items():
            goal_data = goal_pos['goal_data']
            
            feature = {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [goal_pos['x'], goal_pos['y']]
                },
                "properties": {
                    "name": f"goal_{goal_id}",
                    "type": "star",
                    "solar_system": goal_pos['solar_system'],
                    "level_2_cluster": goal_data.get('level_2_cluster', goal_pos['solar_system']),
                    "cluster": goal_pos['cluster'],
                    "galaxy": goal_pos['galaxy'],
                    "star_cluster": goal_pos['star_cluster'],
                    "cluster_color": goal_pos['cluster_color'],
                    "goal_count": self.star_positions[goal_pos['star_cluster']]['goal_count'],
                    "player_name": str(goal_data.get('player_name', 'Unknown')),
                    "team_name": str(goal_data.get('team_name', 'Unknown')),
                    "shot_type": str(goal_data.get('shot_type', 'Unknown')),
                    "situation_code": str(goal_data.get('situation_code', 'Unknown')),
                    "game_date": str(goal_data.get('game_date', 'Unknown')),
                    "url": str(goal_data.get('url', '')),
                    "period": int(goal_data.get('period', 0)) if goal_data.get('period') is not None else 0,
                    "time": str(goal_data.get('time', 'Unknown')),
                    "team_score": int(goal_data.get('team_score', 0)) if goal_data.get('team_score') is not None else 0,
                    "opponent_score": int(goal_data.get('opponent_score', 0)) if goal_data.get('opponent_score') is not None else 0,
                    "goalie_name": str(goal_data.get('goalie_name', 'Empty Net')),
                    "goal_x": goal_data.get('x', None),
                    "goal_y": goal_data.get('y', None)
                }
            }
            features.append(feature)
        
        geojson = {
            "type": "FeatureCollection",
            "features": features
        }
        
        # Save GeoJSON
        geojson_path = os.path.join(self.output_dir, "nhl_constellation_map.geojson")
        with open(geojson_path, 'w') as f:
            json.dump(geojson, f, indent=2)
        
        logger.info(f"GeoJSON saved to: {geojson_path}")
        return geojson
    
    def visualize_constellation_map(self):
        """Create a visualization of the constellation map"""
        logger.info("Creating constellation map visualization...")
        
        # Debug: Print counts
        logger.info(f"Galaxies to plot: {len(self.galaxy_positions)}")
        logger.info(f"Clusters to plot: {len(self.cluster_positions)}")
        logger.info(f"Solar Systems to plot: {len(self.solar_system_positions)}")
        logger.info(f"Stars to plot: {len(self.star_positions)}")
        
        fig, ax = plt.subplots(1, 1, figsize=(20, 20))
        fig.patch.set_facecolor('black')
        ax.set_facecolor('black')
        
        # Plot galaxies
        galaxy_colors = ['red', 'blue', 'green']
        
        for i, (galaxy, pos) in enumerate(self.galaxy_positions.items()):
            color = galaxy_colors[pos['arm'] % len(galaxy_colors)]
            ax.scatter(pos['x'], pos['y'], c=color, s=500, marker='*', 
                      alpha=0.8, edgecolor='white', linewidth=2, 
                      label=f'Galaxy Arm {pos["arm"]}' if i < 3 else "")
        
        # Plot clusters
        if self.cluster_positions:
            cluster_x = [pos['x'] for pos in self.cluster_positions.values()]
            cluster_y = [pos['y'] for pos in self.cluster_positions.values()]
            ax.scatter(cluster_x, cluster_y, c='gold', s=100, marker='o', alpha=0.7, 
                      edgecolor='white', linewidth=1, label='Clusters')
        
        # Plot solar systems
        if self.solar_system_positions:
            system_x = [pos['x'] for pos in self.solar_system_positions.values()]
            system_y = [pos['y'] for pos in self.solar_system_positions.values()]
            ax.scatter(system_x, system_y, c='orange', s=50, marker='s', alpha=0.6, 
                      edgecolor='white', linewidth=0.5, label='Solar Systems')
        
        # Plot individual goals (sample for performance if too many)
        if self.goal_positions:
            goal_positions_list = list(self.goal_positions.values())
            if len(goal_positions_list) > 2000:
                # Sample for visualization performance
                import random
                goal_positions_list = random.sample(goal_positions_list, 2000)
                logger.info(f"Sampling 2000 goals from {len(self.goal_positions)} for visualization")
            
            goal_x = [pos['x'] for pos in goal_positions_list]
            goal_y = [pos['y'] for pos in goal_positions_list]
            
            # Debug: Check goal coordinate ranges
            logger.info(f"Goal X range: {min(goal_x):.2f} to {max(goal_x):.2f}")
            logger.info(f"Goal Y range: {min(goal_y):.2f} to {max(goal_y):.2f}")
            logger.info(f"Plotting {len(goal_x)} goals")
            
            # Make goals more visible
            ax.scatter(goal_x, goal_y, c='lightblue', s=15, marker='o', alpha=0.8, 
                      edgecolor='white', linewidth=0.3, label='Goals')
        
        # Draw connections from galaxies to their clusters
        for cluster, cluster_pos in self.cluster_positions.items():
            galaxy_pos = self.galaxy_positions[cluster_pos['galaxy']]
            ax.plot([galaxy_pos['x'], cluster_pos['x']], [galaxy_pos['y'], cluster_pos['y']], 
                   'white', alpha=0.2, linewidth=0.5)
        
        # Draw connections from clusters to their solar systems
        for solar_system, system_pos in self.solar_system_positions.items():
            cluster_pos = self.cluster_positions[system_pos['cluster']]
            ax.plot([cluster_pos['x'], system_pos['x']], [cluster_pos['y'], system_pos['y']], 
                   'yellow', alpha=0.1, linewidth=0.3)
        
        ax.set_xlim(-self.galaxy_radius * 1.1, self.galaxy_radius * 1.1)
        ax.set_ylim(-self.galaxy_radius * 1.1, self.galaxy_radius * 1.1)
        ax.set_aspect('equal')
        ax.set_title('NHL Goal Constellation Map', color='white', fontsize=24, pad=20)
        
        # Remove axes for cleaner look
        ax.set_xticks([])
        ax.set_yticks([])
        
        # Add legend
        ax.legend(loc='upper right', facecolor='black', edgecolor='white', 
                 labelcolor='white', fontsize=12)
        
        # Add summary text
        summary_text = f"""
        Galaxies: {len(self.galaxy_positions)}
        Clusters: {len(self.cluster_positions)}
        Solar Systems: {len(self.solar_system_positions)}
        Stars: {len(self.star_positions)}
        Total Goals: {len(self.df)}
        """
        ax.text(0.02, 0.98, summary_text, transform=ax.transAxes, 
               verticalalignment='top', color='white', fontsize=14,
               bbox=dict(boxstyle='round', facecolor='black', alpha=0.7))
        
        # Save visualization
        viz_path = os.path.join(self.output_dir, "nhl_constellation_map.png")
        plt.savefig(viz_path, dpi=300, bbox_inches='tight', facecolor='black')
        plt.close()
        
        logger.info(f"Visualization saved to: {viz_path}")
    
    def run_complete_mapping(self, specific_file=None):
        """Run the complete constellation mapping process"""
        logger.info("Starting NHL constellation mapping...")
        
        # Load data
        if not self.load_clustering_results(specific_file):
            return None
        
        # Create layouts
        self.create_spiral_galaxy_layout()
        self.create_cluster_positions()
        self.create_solar_system_positions()
        self.create_star_positions()
        
        # Generate outputs
        geojson = self.create_geojson()
        self.visualize_constellation_map()
        
        logger.info("Constellation mapping complete!")
        return {
            'geojson': geojson,
            'galaxy_count': len(self.galaxy_positions),
            'cluster_count': len(self.cluster_positions),
            'solar_system_count': len(self.solar_system_positions),
            'star_count': len(self.star_positions)
        }

def main():
    """Run the constellation mapping"""
    import sys
    
    # Check for command line argument
    specific_file = sys.argv[1] if len(sys.argv) > 1 else None
    
    mapper = ConstellationMapper()
    results = mapper.run_complete_mapping(specific_file)
    
    if results:
        print(f"\nNHL Constellation Mapping Complete!")
        print(f"Galaxies: {results['galaxy_count']}")
        print(f"Clusters: {results['cluster_count']}")
        print(f"Solar Systems: {results['solar_system_count']}")
        print(f"Stars: {results['star_count']}")
        print(f"Files saved to: {mapper.output_dir}/")
    else:
        print("Mapping failed. Please check the logs.")

if __name__ == "__main__":
    main()