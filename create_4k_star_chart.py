#!/usr/bin/env python3
"""
4K Star Chart Generator for NHL Goal Data
Creates a high-resolution astronomical-style star chart with fisheye projection
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import matplotlib.patheffects as path_effects
import matplotlib.font_manager as fm
from matplotlib.colors import LinearSegmentedColormap
import os
import json
from scipy.spatial import ConvexHull
from sklearn.preprocessing import MinMaxScaler
import logging
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class StarChartGenerator:
    """Generates high-resolution star charts from NHL goal clustering data"""
    
    def __init__(self, width=2880, height=2880, dpi=200):
        """Initialize with square dimensions for better chart layout"""
        self.width = width
        self.height = height
        self.dpi = dpi
        
        # Calculate figure size in inches for matplotlib
        self.fig_width = width / dpi
        self.fig_height = height / dpi
        
        # Star chart parameters
        self.center_x = 0
        self.center_y = 0
        self.radius = 100  # Chart radius
        
        # Color schemes for different elements
        self.bg_color = '#0a0f23'  # Deep space blue
        self.star_color = '#ffffff'
        self.galaxy_colors = [
            '#ff6b6b', '#4ecdc4', '#45b7d1', '#96ceb4', '#ffeaa7',
            '#dda0dd', '#98d8c8', '#ffd93d', '#ff9ff3', '#74b9ff'
        ]
        
        # Register custom font
        self.custom_font = self.register_custom_font()
    
    def register_custom_font(self):
        """Register the custom PlaywriteAUQLD font"""
        font_path = 'Beholden-Bold.ttf'
        
        if os.path.exists(font_path):
            try:
                # Register the font with matplotlib
                fm.fontManager.addfont(font_path)
                
                # Get the font name from the file
                prop = fm.FontProperties(fname=font_path)
                font_name = prop.get_name()
                
                logger.info(f"Successfully registered custom font: {font_name}")
                return font_name
            except Exception as e:
                logger.warning(f"Failed to register custom font {font_path}: {e}")
                return 'DejaVu Serif'  # Fallback
        else:
            logger.warning(f"Custom font file {font_path} not found, using fallback")
            return 'DejaVu Serif'  # Fallback
        
    def load_clustering_data(self, specific_file=None):
        """Load the latest clustering results"""
        try:
            if specific_file:
                file_path = f"sequential_clustering/{specific_file}"
            else:
                # Find the most recent clustering file
                clustering_files = [f for f in os.listdir("sequential_clustering") 
                                  if f.startswith("goal_hierarchy_mapping_multiple_rounds_")]
                if not clustering_files:
                    raise FileNotFoundError("No clustering files found")
                
                clustering_files.sort(key=lambda x: os.path.getmtime(f"sequential_clustering/{x}"))
                file_path = f"sequential_clustering/{clustering_files[-1]}"
            
            logger.info(f"Loading clustering data from: {file_path}")
            df = pd.read_csv(file_path)
            logger.info(f"Loaded {len(df)} clustered goals")
            return df
            
        except Exception as e:
            logger.error(f"Error loading clustering data: {e}")
            raise
    
    def apply_fisheye_projection(self, x, y):
        """Apply fisheye projection to coordinates"""
        # Convert to polar coordinates
        r = np.sqrt(x**2 + y**2)
        theta = np.arctan2(y, x)
        
        # Apply fisheye distortion
        # Normalize radius to [0, 1] range
        max_r = self.radius
        r_norm = r / max_r
        
        # Apply fisheye transformation (stronger curve for outer regions)
        r_fisheye = np.sin(r_norm * np.pi / 2) * max_r * 0.9
        
        # Convert back to cartesian
        x_fisheye = r_fisheye * np.cos(theta)
        y_fisheye = r_fisheye * np.sin(theta)
        
        return x_fisheye, y_fisheye
    
    def create_galaxy_layout(self, galaxies):
        """Create spiral galaxy layout similar to mapping_static.py"""
        galaxy_positions = {}
        
        # Use spiral pattern to distribute galaxies
        rings = []
        remaining_galaxies = len(galaxies)
        ring_radius = 0
        galaxy_separation = 25
        
        while remaining_galaxies > 0:
            if ring_radius == 0:
                galaxies_in_ring = 1
            else:
                circumference = 2 * np.pi * ring_radius
                galaxies_in_ring = max(1, int(circumference / galaxy_separation))
            
            galaxies_in_ring = min(galaxies_in_ring, remaining_galaxies)
            rings.append((ring_radius, galaxies_in_ring))
            remaining_galaxies -= galaxies_in_ring
            ring_radius += galaxy_separation
        
        # Assign positions
        galaxy_idx = 0
        for ring_radius, galaxies_in_ring in rings:
            if ring_radius == 0:
                galaxy_name = galaxies[galaxy_idx]
                galaxy_positions[galaxy_name] = (0, 0)
                galaxy_idx += 1
            else:
                for i in range(galaxies_in_ring):
                    angle = (2 * np.pi * i) / galaxies_in_ring
                    # Add slight random offset
                    angle_offset = np.random.uniform(-0.1, 0.1)
                    radius_offset = np.random.uniform(-3, 3)
                    
                    x = (ring_radius + radius_offset) * np.cos(angle + angle_offset)
                    y = (ring_radius + radius_offset) * np.sin(angle + angle_offset)
                    
                    galaxy_name = galaxies[galaxy_idx]
                    galaxy_positions[galaxy_name] = (x, y)
                    galaxy_idx += 1
        
        return galaxy_positions
    
    def create_constellation_positions(self, galaxy_center, constellations):
        """Create constellation positions within galaxy"""
        if len(constellations) == 1:
            return {constellations[0]: galaxy_center}
        
        positions = {}
        constellation_radius = 15
        
        if len(constellations) <= 4:
            offsets = [(0, 0), (constellation_radius//2, 0), 
                      (0, constellation_radius//2), (-constellation_radius//2, 0)]
        else:
            angles = np.linspace(0, 2*np.pi, len(constellations), endpoint=False)
            radii = np.linspace(3, constellation_radius, len(constellations))
            offsets = [(r * np.cos(a), r * np.sin(a)) for r, a in zip(radii, angles)]
        
        for i, constellation in enumerate(constellations):
            if i < len(offsets):
                offset_x, offset_y = offsets[i]
            else:
                angle = np.random.uniform(0, 2*np.pi)
                radius = np.random.uniform(3, constellation_radius)
                offset_x = radius * np.cos(angle)
                offset_y = radius * np.sin(angle)
            
            positions[constellation] = (
                galaxy_center[0] + offset_x,
                galaxy_center[1] + offset_y
            )
        
        return positions
    
    def create_star_positions(self, constellation_center, stars):
        """Create tight star positions within constellation"""
        if len(stars) == 1:
            return {stars[0]: constellation_center}
        
        positions = {}
        star_radius = 8
        
        if len(stars) <= 3:
            offsets = [(0, 0), (2, 0), (0, 2)]
        elif len(stars) <= 8:
            angles = np.linspace(0, 2*np.pi, len(stars), endpoint=False)
            radius = min(5, star_radius // 2)
            offsets = [(radius * np.cos(a), radius * np.sin(a)) for a in angles]
        else:
            angles = np.linspace(0, 4*np.pi, len(stars))
            radii = np.linspace(1, star_radius, len(stars))
            offsets = [(r * np.cos(a), r * np.sin(a)) for r, a in zip(radii, angles)]
        
        for i, star in enumerate(stars):
            if i < len(offsets):
                offset_x, offset_y = offsets[i]
            else:
                angle = np.random.uniform(0, 2*np.pi)
                radius = np.random.uniform(1, star_radius // 2)
                offset_x = radius * np.cos(angle)
                offset_y = radius * np.sin(angle)
            
            # Add tiny jitter
            jitter_x = np.random.uniform(-0.5, 0.5)
            jitter_y = np.random.uniform(-0.5, 0.5)
            
            positions[star] = (
                constellation_center[0] + offset_x + jitter_x,
                constellation_center[1] + offset_y + jitter_y
            )
        
        return positions
    
    def create_galaxy_boundary(self, galaxy_points, alpha=0.3):
        """Create convex hull boundary for galaxy shading"""
        if len(galaxy_points) < 3:
            return None
        
        try:
            hull = ConvexHull(galaxy_points)
            hull_points = np.array(galaxy_points)[hull.vertices]
            return hull_points
        except:
            return None
    
    
    def convert_to_roman(self, num):
        """Convert number to Roman numerals for classical styling"""
        if num >= 4000:
            return str(num)  # Too large for practical Roman numerals
        
        values = [1000, 900, 500, 400, 100, 90, 50, 40, 10, 9, 5, 4, 1]
        literals = ['M', 'CM', 'D', 'CD', 'C', 'XC', 'L', 'XL', 'X', 'IX', 'V', 'IV', 'I']
        
        result = ''
        for i in range(len(values)):
            count = num // values[i]
            if count:
                result += literals[i] * count
                num -= values[i] * count
        return result
    
    def calculate_star_brightness(self, star_density, max_density):
        """Calculate star brightness based on local density"""
        # Normalize density to 0-1 range
        normalized = star_density / max_density if max_density > 0 else 0
        
        # Apply power curve for more dramatic brightness differences
        brightness = np.power(normalized, 0.5)  # Square root for gentler curve
        
        # Ensure minimum brightness
        return max(0.3, brightness)
    
    def create_4k_star_chart(self, specific_file=None):
        """Create the main 4K star chart"""
        try:
            # Load data
            df = self.load_clustering_data(specific_file)
            
            # Set random seed for reproducibility
            np.random.seed(42)
            
            logger.info("Creating 4K star chart...")
            
            # Create figure with high DPI and proper centering
            plt.style.use('dark_background')
            fig, ax = plt.subplots(figsize=(self.fig_width, self.fig_height), dpi=self.dpi)
            fig.patch.set_facecolor(self.bg_color)
            ax.set_facecolor(self.bg_color)
            
            # Position the subplot to maximize chart size while preserving title space
            # Reduce top margin to minimize gap between title and chart
            plt.subplots_adjust(left=0.01, right=0.99, top=0.85, bottom=0.01)
            
            # Remove axes and set equal aspect ratio
            ax.set_xlim(-self.radius, self.radius)
            ax.set_ylim(-self.radius, self.radius)
            ax.set_aspect('equal')
            ax.axis('off')
            
            # Get galaxy layout
            galaxies = df['level_0_cluster'].unique().tolist()
            galaxy_positions = self.create_galaxy_layout(galaxies)
            
            # Store all star positions and data
            all_stars = []
            galaxy_star_groups = {}
            
            # Process each galaxy
            for i, galaxy in enumerate(galaxies):
                galaxy_data = df[df['level_0_cluster'] == galaxy]
                galaxy_center = galaxy_positions[galaxy]
                galaxy_color = self.galaxy_colors[i % len(self.galaxy_colors)]
                
                # Get constellations in this galaxy
                constellations = galaxy_data['level_1_cluster'].unique()
                constellation_positions = self.create_constellation_positions(galaxy_center, constellations)
                
                galaxy_points = []
                
                # Process each constellation
                for constellation in constellations:
                    constellation_data = galaxy_data[galaxy_data['level_1_cluster'] == constellation]
                    constellation_center = constellation_positions[constellation]
                    
                    # Get solar systems
                    solar_systems = constellation_data['level_2_cluster'].unique()
                    
                    for solar_system in solar_systems:
                        solar_system_data = constellation_data[constellation_data['level_2_cluster'] == solar_system]
                        
                        # Position solar system near constellation center
                        ss_offset_x = np.random.uniform(-3, 3)
                        ss_offset_y = np.random.uniform(-3, 3)
                        ss_center = (
                            constellation_center[0] + ss_offset_x,
                            constellation_center[1] + ss_offset_y
                        )
                        
                        # Create star positions
                        stars_in_system = solar_system_data.index.tolist()
                        star_positions = self.create_star_positions(ss_center, stars_in_system)
                        
                        # Store star data
                        for star_idx in stars_in_system:
                            star_pos = star_positions[star_idx]
                            goal_data = solar_system_data.loc[star_idx]
                            
                            # Apply fisheye projection
                            x_fisheye, y_fisheye = self.apply_fisheye_projection(star_pos[0], star_pos[1])
                            
                            star_info = {
                                'x': x_fisheye,
                                'y': y_fisheye,
                                'galaxy': galaxy,
                                'galaxy_color': galaxy_color,
                                'player_name': goal_data.get('player_name', 'Unknown'),
                                'team_name': goal_data.get('team_name', 'Unknown')
                            }
                            
                            all_stars.append(star_info)
                            galaxy_points.append((x_fisheye, y_fisheye))
                
                # Store galaxy points for boundary creation
                if galaxy_points:
                    galaxy_star_groups[galaxy] = {
                        'points': galaxy_points,
                        'color': galaxy_color
                    }
            
            # Calculate star densities for brightness (optimized)
            logger.info("Calculating star densities...")
            
            # Use galaxy-based density instead of distance-based for performance
            galaxy_counts = {}
            for star in all_stars:
                galaxy = star['galaxy']
                galaxy_counts[galaxy] = galaxy_counts.get(galaxy, 0) + 1
            
            max_galaxy_size = max(galaxy_counts.values()) if galaxy_counts else 1
            
            star_densities = []
            for star in all_stars:
                galaxy_size = galaxy_counts[star['galaxy']]
                # Normalize by galaxy size
                density = galaxy_size / max_galaxy_size
                star_densities.append(density)
            
            max_density = max(star_densities) if star_densities else 1
            
            # Draw galaxy boundaries (shaded regions) using fisheye-projected points
            logger.info("Drawing galaxy boundaries...")
            galaxy_info = {}
            for galaxy, data in galaxy_star_groups.items():
                # Use the already fisheye-projected points for boundary calculation
                boundary = self.create_galaxy_boundary(data['points'])
                if boundary is not None:
                    # Points are already fisheye-projected, so use them directly
                    polygon = patches.Polygon(boundary, 
                                            facecolor=data['color'], 
                                            alpha=0.15, 
                                            edgecolor=data['color'], 
                                            linewidth=1, 
                                            linestyle='--')
                    ax.add_patch(polygon)
                    
                    # Calculate galaxy properties for name placement
                    points_array = np.array(data['points'])
                    centroid_x = np.mean(points_array[:, 0])
                    centroid_y = np.mean(points_array[:, 1])
                    
                    # Calculate galaxy size (bounding box)
                    min_x, max_x = np.min(points_array[:, 0]), np.max(points_array[:, 0])
                    min_y, max_y = np.min(points_array[:, 1]), np.max(points_array[:, 1])
                    width = max_x - min_x
                    height = max_y - min_y
                    galaxy_size = min(width, height)  # Use smaller dimension
                    
                    galaxy_info[galaxy] = {
                        'centroid': (centroid_x, centroid_y),
                        'color': data['color'],
                        'size': galaxy_size,
                        'bounds': (min_x, max_x, min_y, max_y),
                        'boundary': boundary,
                        'bounding_center': ((min_x + max_x) / 2, (min_y + max_y) / 2)
                    }
            
            # Draw stars efficiently
            logger.info(f"Drawing {len(all_stars)} stars...")
            
            # Prepare data for vectorized plotting
            x_coords = [star['x'] for star in all_stars]
            y_coords = [star['y'] for star in all_stars]
            
            # Calculate brightness and sizes
            brightnesses = [self.calculate_star_brightness(star_densities[i], max_density) 
                          for i in range(len(all_stars))]
            sizes = [1.0 + brightness * 3.0 for brightness in brightnesses]
            alphas = [0.6 + brightness * 0.4 for brightness in brightnesses]
            
            # Draw all stars at once for better performance
            ax.scatter(x_coords, y_coords, s=sizes, c=self.star_color, 
                      alpha=0.8, marker='*', edgecolors='none')
            
            # Add galaxy labels using custom font
            logger.info("Adding galaxy labels...")
            for galaxy, info in galaxy_info.items():
                center_x, center_y = info['bounding_center']
                galaxy_color = info['color']
                galaxy_size = info['size']
                
                # Scale font size based on galaxy size (smaller range for labels)
                font_size = max(8, min(14, int(galaxy_size * 0.3)))
                
                # Create clean galaxy name (remove cluster prefix if present)
                galaxy_name = str(galaxy).replace('cluster_', '').upper()
                
                # Add text with custom font
                ax.text(center_x, center_y, galaxy_name,
                       fontsize=font_size,
                       color='white',
                       fontweight='bold',
                       fontfamily=self.custom_font,
                       ha='center',
                       va='center',
                       alpha=0.9,
                       path_effects=[
                           path_effects.withStroke(linewidth=2, foreground='black', alpha=0.8)
                       ])
            
            # Add circular boundary for fisheye effect
            circle = patches.Circle((0, 0), self.radius * 0.9, 
                                  fill=False, edgecolor='white', 
                                  alpha=0.3, linewidth=2)
            ax.add_patch(circle)
            
            # Add coordinate grid lines like real star charts
            for angle in np.linspace(0, 2*np.pi, 12, endpoint=False):  # 12 radial lines
                x_line = [0, self.radius * 0.9 * np.cos(angle)]
                y_line = [0, self.radius * 0.9 * np.sin(angle)]
                ax.plot(x_line, y_line, color='white', alpha=0.1, linewidth=0.5)
            
            # Add concentric circles
            for r in np.linspace(0.3, 0.9, 4):  # 4 circles at different radii
                circle_grid = patches.Circle((0, 0), self.radius * r, 
                                           fill=False, edgecolor='white', 
                                           alpha=0.1, linewidth=0.5)
                ax.add_patch(circle_grid)
            
            # Classical old world map style title
            title_text = 'NHL STAR CHART'
            
            # Main title with custom font - positioned lower to avoid cutoff
            plt.figtext(0.5, 0.92, title_text, 
                       ha='center', fontsize=50, color='#daa520',  # Goldenrod
                       fontweight='normal', fontfamily=self.custom_font,
                       alpha=1.0,
                       path_effects=[
                           path_effects.withStroke(linewidth=2, foreground='#2f1b14', alpha=0.8)
                       ])
            
            # Classical subtitle in English
            subtitle_text = f'{len(all_stars)} Goals From 2023+ Seasons • {len(galaxies)} Galaxies'
            
            # Subtitle with aged manuscript styling - positioned lower
            plt.figtext(0.5, 0.88, subtitle_text, 
                       ha='center', fontsize=25, color='#cd853f',  # Peru
                       fontweight='normal', fontfamily=self.custom_font,
                       alpha=0.9,
                       path_effects=[
                           path_effects.withStroke(linewidth=1, foreground='#2f1b14', alpha=0.6)
                       ])
            
            # Classical attribution in English
            plt.figtext(0.98, 0.02, 'NHL CARTOGRAPHY PROJECT', 
                       ha='right', fontsize=10, color='#cd853f',
                       fontweight='normal', fontfamily=self.custom_font,
                       alpha=0.8,
                       path_effects=[
                           path_effects.withStroke(linewidth=1, foreground='#2f1b14', alpha=0.5)
                       ])
            
            # Save the chart with tight bounding box to prevent cutoff
            output_path = f'nhl_star_chart_4k_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png'
            plt.savefig(output_path, dpi=self.dpi, bbox_inches='tight', pad_inches=0.1,
                       facecolor=self.bg_color, edgecolor='none')
            
            logger.info(f"4K star chart saved to: {output_path}")
            
            # Also save a web-friendly version
            web_output_path = f'nhl_star_chart_web_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png'
            plt.savefig(web_output_path, dpi=150, bbox_inches='tight', pad_inches=0.1,
                       facecolor=self.bg_color, edgecolor='none')
            
            logger.info(f"Web version saved to: {web_output_path}")
            
            plt.close()
            
            return output_path, web_output_path
            
        except Exception as e:
            logger.error(f"Error creating star chart: {e}")
            raise

def main():
    """Generate the 4K star chart"""
    import sys
    
    # Check for high-quality flag
    high_quality = '--high-quality' in sys.argv or '--hq' in sys.argv
    
    if high_quality:
        print("🎨 Generating HIGH QUALITY version (300 DPI)...")
        generator = StarChartGenerator(dpi=300)
    else:
        print("🎨 Generating STANDARD version (200 DPI)...")
        generator = StarChartGenerator(dpi=200)
    
    try:
        output_4k, output_web = generator.create_4k_star_chart()
        print(f"✅ 4K Star Chart created successfully!")
        print(f"🌌 4K Version: {output_4k}")
        print(f"🌐 Web Version: {output_web}")
        print(f"⭐ High-resolution astronomical-style visualization complete")
        
        if high_quality:
            print(f"🖼️  High-quality 300 DPI version ready for printing!")
        else:
            print(f"💡 Tip: Use --high-quality flag for 300 DPI print version")
        
    except Exception as e:
        print(f"❌ Error creating star chart: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())