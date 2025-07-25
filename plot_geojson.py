import json
import matplotlib.pyplot as plt
import numpy as np

def plot_geojson_points():
    """Plot all points from the GeoJSON file"""
    
    # Load the GeoJSON file
    with open('visualizations/nhl_constellation_map.geojson', 'r') as f:
        geojson_data = json.load(f)
    
    # Separate points by type
    galaxies = []
    constellations = []
    stars = []
    
    for feature in geojson_data['features']:
        coords = feature['geometry']['coordinates']
        point_type = feature['properties']['type']
        
        if point_type == 'galaxy':
            galaxies.append(coords)
        elif point_type == 'constellation':
            constellations.append(coords)
        elif point_type == 'star':
            stars.append(coords)
    
    # Create the plot
    fig, ax = plt.subplots(1, 1, figsize=(20, 20))
    fig.patch.set_facecolor('black')
    ax.set_facecolor('black')
    
    # Plot stars first (so they're in the background)
    if stars:
        star_x = [coord[0] for coord in stars]
        star_y = [coord[1] for coord in stars]
        ax.scatter(star_x, star_y, c='lightblue', s=2, marker='.', alpha=0.6, label=f'Stars ({len(stars)})')
    
    # Plot constellations
    if constellations:
        const_x = [coord[0] for coord in constellations]
        const_y = [coord[1] for coord in constellations]
        ax.scatter(const_x, const_y, c='gold', s=80, marker='o', alpha=0.8, 
                  edgecolor='white', linewidth=1, label=f'Constellations ({len(constellations)})')
    
    # Plot galaxies
    if galaxies:
        galaxy_x = [coord[0] for coord in galaxies]
        galaxy_y = [coord[1] for coord in galaxies]
        ax.scatter(galaxy_x, galaxy_y, c='red', s=400, marker='*', alpha=0.9, 
                  edgecolor='white', linewidth=2, label=f'Galaxies ({len(galaxies)})')
    
    # Set equal aspect ratio and limits
    ax.set_aspect('equal')
    
    # Get data bounds for proper scaling
    all_x = []
    all_y = []
    if stars:
        all_x.extend([coord[0] for coord in stars])
        all_y.extend([coord[1] for coord in stars])
    if constellations:
        all_x.extend([coord[0] for coord in constellations])
        all_y.extend([coord[1] for coord in constellations])
    if galaxies:
        all_x.extend([coord[0] for coord in galaxies])
        all_y.extend([coord[1] for coord in galaxies])
    
    if all_x and all_y:
        x_margin = (max(all_x) - min(all_x)) * 0.1
        y_margin = (max(all_y) - min(all_y)) * 0.1
        ax.set_xlim(min(all_x) - x_margin, max(all_x) + x_margin)
        ax.set_ylim(min(all_y) - y_margin, max(all_y) + y_margin)
    
    # Style the plot
    ax.set_title('NHL Constellation Map - All Points', color='white', fontsize=24, pad=20)
    ax.set_xlabel('X Coordinate', color='white', fontsize=14)
    ax.set_ylabel('Y Coordinate', color='white', fontsize=14)
    
    # Remove tick marks but keep labels
    ax.tick_params(colors='white', labelsize=10)
    
    # Add legend
    ax.legend(loc='upper right', facecolor='black', edgecolor='white', 
             labelcolor='white', fontsize=12)
    
    # Add grid for reference
    ax.grid(True, alpha=0.3, color='gray')
    
    # Add summary statistics
    stats_text = f"""
    Total Features: {len(geojson_data['features'])}
    Galaxies: {len(galaxies)}
    Constellations: {len(constellations)}  
    Stars: {len(stars)}
    
    X Range: {min(all_x):.0f} to {max(all_x):.0f}
    Y Range: {min(all_y):.0f} to {max(all_y):.0f}
    """
    
    ax.text(0.02, 0.98, stats_text, transform=ax.transAxes, 
           verticalalignment='top', color='white', fontsize=12,
           bbox=dict(boxstyle='round', facecolor='black', alpha=0.8))
    
    # Save the plot
    plt.savefig('visualizations/geojson_plot.png', dpi=300, bbox_inches='tight', 
                facecolor='black', edgecolor='none')
    plt.close()
    
    print(f"Plot saved to: visualizations/geojson_plot.png")
    print(f"Total points plotted: {len(geojson_data['features'])}")
    print(f"  - Galaxies: {len(galaxies)}")
    print(f"  - Constellations: {len(constellations)}")
    print(f"  - Stars: {len(stars)}")

if __name__ == "__main__":
    plot_geojson_points()