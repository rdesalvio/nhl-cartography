import pandas as pd
import numpy as np
import json
import os
import matplotlib.pyplot as plt
from sklearn.manifold import TSNE
from sklearn.preprocessing import StandardScaler
import logging
from datetime import datetime, date

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def calculate_season_day(game_date_str):
    """Calculate days into the NHL season from October 1st start date"""
    try:
        if pd.isna(game_date_str) or game_date_str == 'Unknown':
            return None
            
        # Parse the game date
        game_date = pd.to_datetime(game_date_str).date()
        
        # Determine which season this game belongs to
        if game_date.month >= 10:  # October or later = current season year
            season_start = date(game_date.year, 10, 1)
        else:  # Before October = previous season year
            season_start = date(game_date.year - 1, 10, 1)
        
        # Calculate days into season
        days_into_season = (game_date - season_start).days + 1  # +1 to make it 1-based
        return max(1, days_into_season)  # Ensure minimum of 1
        
    except Exception as e:
        logger.warning(f"Could not calculate season day for {game_date_str}: {e}")
        return None

class StaticConstellationMapper:
    """Creates dense, night-sky-like constellation map layouts for static star chart view"""
    
    def __init__(self, output_dir="visualizations"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        
        # Dense coordinate system parameters for night sky appearance
        self.galaxy_radius = 120   # Much smaller - galaxies close together
        self.constellation_radius = 25  # Tight constellation clustering
        self.star_radius = 15      # Stars very close within constellations
        self.galaxy_separation = 30    # Minimal space between galaxy centers
        
    def load_clustering_results(self, specific_file=None):
        """Load the clustering results from the latest file"""
        try:
            if specific_file:
                file_path = f"sequential_clustering/{specific_file}"
            else:
                # Find the most recent clustering file
                clustering_files = [f for f in os.listdir("sequential_clustering") 
                                  if f.startswith("goal_hierarchy_mapping_multiple_rounds_")]
                if not clustering_files:
                    raise FileNotFoundError("No clustering files found")
                
                # Sort by modification time and get the most recent
                clustering_files.sort(key=lambda x: os.path.getmtime(f"sequential_clustering/{x}"))
                file_path = f"sequential_clustering/{clustering_files[-1]}"
            
            logger.info(f"Loading clustering results from: {file_path}")
            df = pd.read_csv(file_path)
            logger.info(f"Loaded {len(df)} clustered goals")
            return df
            
        except Exception as e:
            logger.error(f"Error loading clustering results: {e}")
            raise

    def create_dense_galaxy_layout(self, galaxies):
        """Create a dense, tightly packed layout for galaxies like a real night sky"""
        logger.info(f"Creating dense layout for {len(galaxies)} galaxies")
        
        # Use a spiral pattern to pack galaxies tightly
        galaxy_positions = {}
        
        # Calculate how many galaxies can fit in concentric rings
        rings = []
        remaining_galaxies = len(galaxies)
        ring_radius = 0
        
        while remaining_galaxies > 0:
            if ring_radius == 0:
                # Center galaxy
                galaxies_in_ring = 1
            else:
                # Calculate circumference and fit galaxies with minimal separation
                circumference = 2 * np.pi * ring_radius
                galaxies_in_ring = max(1, int(circumference / self.galaxy_separation))
            
            galaxies_in_ring = min(galaxies_in_ring, remaining_galaxies)
            rings.append((ring_radius, galaxies_in_ring))
            remaining_galaxies -= galaxies_in_ring
            ring_radius += self.galaxy_separation
        
        # Assign positions
        galaxy_idx = 0
        for ring_radius, galaxies_in_ring in rings:
            if ring_radius == 0:
                # Center galaxy
                galaxy_name = galaxies[galaxy_idx]
                galaxy_positions[galaxy_name] = (0, 0)
                galaxy_idx += 1
            else:
                # Distribute galaxies evenly around the ring
                for i in range(galaxies_in_ring):
                    angle = (2 * np.pi * i) / galaxies_in_ring
                    # Add slight random offset for more natural look
                    angle_offset = np.random.uniform(-0.1, 0.1)
                    radius_offset = np.random.uniform(-5, 5)
                    
                    x = (ring_radius + radius_offset) * np.cos(angle + angle_offset)
                    y = (ring_radius + radius_offset) * np.sin(angle + angle_offset)
                    
                    galaxy_name = galaxies[galaxy_idx]
                    galaxy_positions[galaxy_name] = (x, y)
                    galaxy_idx += 1
        
        logger.info(f"Created dense galaxy layout with {len(rings)} rings")
        return galaxy_positions

    def create_tight_constellation_positions(self, galaxy_center, constellations):
        """Create very tight positioning for constellations within a galaxy"""
        if len(constellations) == 1:
            return {constellations[0]: galaxy_center}
        
        positions = {}
        
        # Use a tight spiral or grid pattern for constellations
        if len(constellations) <= 4:
            # Small numbers: use cardinal directions
            offsets = [(0, 0), (self.constellation_radius//2, 0), 
                      (0, self.constellation_radius//2), (-self.constellation_radius//2, 0)]
        else:
            # More constellations: use tight spiral
            angles = np.linspace(0, 2*np.pi, len(constellations), endpoint=False)
            radii = np.linspace(5, self.constellation_radius, len(constellations))
            offsets = [(r * np.cos(a), r * np.sin(a)) for r, a in zip(radii, angles)]
        
        for i, constellation in enumerate(constellations):
            if i < len(offsets):
                offset_x, offset_y = offsets[i]
            else:
                # Fallback for extra constellations
                angle = np.random.uniform(0, 2*np.pi)
                radius = np.random.uniform(5, self.constellation_radius)
                offset_x = radius * np.cos(angle)
                offset_y = radius * np.sin(angle)
            
            positions[constellation] = (
                galaxy_center[0] + offset_x,
                galaxy_center[1] + offset_y
            )
        
        return positions

    def create_compact_star_positions(self, constellation_center, stars):
        """Create very compact positioning for stars within a constellation"""
        if len(stars) == 1:
            return {stars[0]: constellation_center}
        
        positions = {}
        
        # Use extremely tight clustering for realistic night sky density
        if len(stars) <= 3:
            # Very small offset for few stars
            offsets = [(0, 0), (3, 0), (0, 3)]
        elif len(stars) <= 8:
            # Tight circle pattern
            angles = np.linspace(0, 2*np.pi, len(stars), endpoint=False)
            radius = min(8, self.star_radius // 3)
            offsets = [(radius * np.cos(a), radius * np.sin(a)) for a in angles]
        else:
            # Dense spiral for many stars
            angles = np.linspace(0, 4*np.pi, len(stars))  # Multiple spiral turns
            radii = np.linspace(1, self.star_radius, len(stars))
            offsets = [(r * np.cos(a), r * np.sin(a)) for r, a in zip(radii, angles)]
        
        for i, star in enumerate(stars):
            if i < len(offsets):
                offset_x, offset_y = offsets[i]
            else:
                # Random tight positioning for overflow
                angle = np.random.uniform(0, 2*np.pi)
                radius = np.random.uniform(1, self.star_radius // 2)
                offset_x = radius * np.cos(angle)
                offset_y = radius * np.sin(angle)
            
            # Add tiny random jitter for natural appearance
            jitter_x = np.random.uniform(-1, 1)
            jitter_y = np.random.uniform(-1, 1)
            
            positions[star] = (
                constellation_center[0] + offset_x + jitter_x,
                constellation_center[1] + offset_y + jitter_y
            )
        
        return positions

    def create_static_constellation_map(self, specific_file=None):
        """Create a dense, night-sky-like constellation map optimized for static viewing"""
        try:
            # Load clustering data
            df = self.load_clustering_results(specific_file)
            
            # Set seed for reproducible but natural-looking layouts
            np.random.seed(42)
            
            logger.info("Creating dense static constellation map...")
            
            # Get unique hierarchical levels using correct column names
            galaxies = df['level_0_cluster'].unique().tolist()
            logger.info(f"Processing {len(galaxies)} galaxies for dense layout")
            
            # Create extremely tight galaxy layout
            galaxy_positions = self.create_dense_galaxy_layout(galaxies)
            
            # Process each hierarchical level with tight spacing
            geojson_features = []
            
            # 1. Process galaxies but skip adding galaxy markers for cleaner star map view
            for galaxy in galaxies:
                galaxy_data = df[df['level_0_cluster'] == galaxy]
                galaxy_center = galaxy_positions[galaxy]
                
                # Skip adding galaxy feature to avoid blue dots
                # geojson_features.append({ galaxy feature }) - REMOVED
                
                # 2. Create constellation features within this galaxy
                constellations = galaxy_data['level_1_cluster'].unique()
                constellation_positions = self.create_tight_constellation_positions(
                    galaxy_center, constellations
                )
                
                for constellation in constellations:
                    constellation_data = galaxy_data[galaxy_data['level_1_cluster'] == constellation]
                    constellation_center = constellation_positions[constellation]
                    
                    # Skip cluster markers for cleaner star map view
                    # geojson_features.append({ cluster feature }) - REMOVED
                    
                    # 3. Process solar systems
                    solar_systems = constellation_data['level_2_cluster'].unique()
                    
                    for solar_system in solar_systems:
                        solar_system_data = constellation_data[constellation_data['level_2_cluster'] == solar_system]
                        
                        # Position solar systems very close to constellation center
                        ss_offset_x = np.random.uniform(-self.star_radius//4, self.star_radius//4)
                        ss_offset_y = np.random.uniform(-self.star_radius//4, self.star_radius//4)
                        ss_center = (
                            constellation_center[0] + ss_offset_x,
                            constellation_center[1] + ss_offset_y
                        )
                        
                        # Skip solar system markers for cleaner star map view
                        # geojson_features.append({ solar_system feature }) - REMOVED
                        
                        # 4. Create individual star features (goals) - very tightly packed
                        stars_in_system = solar_system_data.index.tolist()
                        star_positions = self.create_compact_star_positions(ss_center, stars_in_system)
                        
                        for star_idx in stars_in_system:
                            goal_data = solar_system_data.loc[star_idx]
                            star_position = star_positions[star_idx]
                            
                            geojson_features.append({
                                "type": "Feature",
                                "geometry": {
                                    "type": "Point",
                                    "coordinates": [star_position[0], star_position[1]]
                                },
                                "properties": {
                                    "name": f"Goal by {str(goal_data.get('player_name', 'Unknown'))}",
                                    "type": "star",
                                    "solar_system": str(solar_system),
                                    "cluster": str(constellation),
                                    "galaxy": str(galaxy),
                                    "cluster_color": '#64c8ff',  # Default color for now
                                    "goal_count": 1,
                                    "player_name": str(goal_data.get('player_name', 'Unknown')),
                                    "team_name": str(goal_data.get('team_name', 'Unknown')),
                                    "shot_type": str(goal_data.get('shot_type', 'Unknown')),
                                    "situation_code": str(goal_data.get('situation_code', 'Unknown')),
                                    "game_date": str(goal_data.get('game_date', 'Unknown')),
                                    "url": str(goal_data.get('url', '')),
                                    "period": int(goal_data.get('period', 0)) if pd.notna(goal_data.get('period', 0)) else 0,
                                    "time": str(goal_data.get('time', '00:00')),
                                    "team_score": int(goal_data.get('team_score', 0)) if pd.notna(goal_data.get('team_score', 0)) else 0,
                                    "opponent_score": int(goal_data.get('opponent_score', 0)) if pd.notna(goal_data.get('opponent_score', 0)) else 0,
                                    "goalie_name": str(goal_data.get('goalie_name', 'Unknown')),
                                    "shot_zone": goal_data.get('shot_zone', None),
                                    "situation": goal_data.get('situation', None),
                                    "goal_x": float(goal_data.get('x', 0)) if pd.notna(goal_data.get('x')) else None,
                                    "goal_y": float(goal_data.get('y', 0)) if pd.notna(goal_data.get('y')) else None,
                                }
                            })
            
            # Create GeoJSON structure
            geojson_data = {
                "type": "FeatureCollection",
                "features": geojson_features
            }
            
            # Save to new static file
            output_file = os.path.join(self.output_dir, "nhl_constellation_map_static.geojson")
            with open(output_file, 'w') as f:
                json.dump(geojson_data, f, indent=2)
            
            logger.info(f"Dense static constellation map saved to: {output_file}")
            logger.info(f"Total features: {len(geojson_features)}")
            
            # Print statistics
            feature_counts = {}
            for feature in geojson_features:
                feature_type = feature['properties']['type']
                feature_counts[feature_type] = feature_counts.get(feature_type, 0) + 1
            
            for feature_type, count in feature_counts.items():
                logger.info(f"{feature_type.title()}s: {count}")
            
            return output_file
            
        except Exception as e:
            logger.error(f"Error creating static constellation map: {e}")
            raise

def main():
    """Create the dense static constellation map"""
    mapper = StaticConstellationMapper()
    output_file = mapper.create_static_constellation_map()
    print(f"✅ Dense static constellation map created: {output_file}")
    print("🌌 Optimized for night-sky viewing with minimal empty space")
    print("⭐ All stars visible with tight galaxy clustering")

if __name__ == "__main__":
    main()