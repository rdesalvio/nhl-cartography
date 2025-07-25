import json

def create_standalone_html():
    """Create a standalone HTML file with embedded GeoJSON data"""
    
    # Read the GeoJSON data
    with open('visualizations/nhl_constellation_map.geojson', 'r') as f:
        geojson_data = json.load(f)
    
    # HTML template with embedded data
    html_content = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>NHL Constellation Map</title>
    
    <!-- Leaflet CSS -->
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    
    <style>
        body {
            margin: 0;
            padding: 0;
            font-family: 'Arial', sans-serif;
            background: #000;
            color: white;
        }
        
        #map {
            height: 100vh;
            width: 100vw;
            background: #000;
        }
        
        .title {
            position: absolute;
            top: 20px;
            left: 20px;
            z-index: 1000;
            background: rgba(0, 0, 0, 0.8);
            padding: 15px;
            border-radius: 8px;
            border: 2px solid #fff;
            max-width: 300px;
        }
        
        .controls {
            position: absolute;
            top: 20px;
            right: 20px;
            z-index: 1000;
            background: rgba(0, 0, 0, 0.8);
            padding: 15px;
            border-radius: 8px;
            border: 2px solid #fff;
            max-width: 250px;
        }
        
        .legend {
            position: absolute;
            bottom: 20px;
            left: 20px;
            z-index: 1000;
            background: rgba(0, 0, 0, 0.8);
            padding: 15px;
            border-radius: 8px;
            border: 2px solid #fff;
            max-width: 300px;
        }
        
        .legend-item {
            display: flex;
            align-items: center;
            margin: 5px 0;
        }
        
        .legend-color {
            width: 20px;
            height: 20px;
            margin-right: 10px;
            border: 1px solid #fff;
            border-radius: 50%;
        }
        
        .galaxy-marker {
            background: #ff4444;
            border: 2px solid white;
            border-radius: 50%;
            width: 20px;
            height: 20px;
        }
        
        .constellation-marker {
            background: #ffd700;
            border: 2px solid white;
            border-radius: 50%;
            width: 15px;
            height: 15px;
        }
        
        .star-marker {
            background: #87ceeb;
            border: 1px solid white;
            border-radius: 50%;
            width: 8px;
            height: 8px;
        }
        
        .galaxy-label {
            background: rgba(255, 68, 68, 0.9);
            color: white;
            padding: 4px 8px;
            border-radius: 4px;
            font-weight: bold;
            font-size: 12px;
            border: 1px solid white;
            white-space: nowrap;
        }
        
        .constellation-label {
            background: rgba(255, 215, 0, 0.9);
            color: black;
            padding: 2px 6px;
            border-radius: 3px;
            font-size: 10px;
            border: 1px solid white;
            white-space: nowrap;
        }
        
        .leaflet-popup-content-wrapper {
            background: #000;
            border: 2px solid #fff;
            border-radius: 8px;
        }
        
        .leaflet-popup-content {
            color: white;
            margin: 8px;
        }
        
        .goal-info {
            min-width: 250px;
        }
        
        .goal-info h3 {
            margin: 0 0 10px 0;
            color: #ffd700;
            border-bottom: 1px solid #ffd700;
            padding-bottom: 5px;
        }
        
        .goal-detail {
            margin: 5px 0;
            display: flex;
            justify-content: space-between;
        }
        
        .goal-detail strong {
            color: #87ceeb;
        }
        
        .goal-url {
            margin-top: 10px;
            padding-top: 10px;
            border-top: 1px solid #fff;
        }
        
        .goal-url a {
            color: #87ceeb;
            text-decoration: none;
            padding: 5px 10px;
            border: 1px solid #87ceeb;
            border-radius: 4px;
            display: inline-block;
        }
        
        .goal-url a:hover {
            background: #87ceeb;
            color: #000;
        }
        
        .zoom-info {
            position: absolute;
            bottom: 20px;
            right: 20px;
            z-index: 1000;
            background: rgba(0, 0, 0, 0.8);
            padding: 10px;
            border-radius: 8px;
            border: 2px solid #fff;
            font-size: 12px;
        }
    </style>
</head>
<body>
    <div class="title">
        <h1>NHL Constellation Map</h1>
        <p>Interactive visualization of NHL goal patterns as astronomical objects</p>
    </div>
    
    <div class="controls">
        <h3>Navigation</h3>
        <p>🔍 Zoom to explore galaxies, constellations, and stars</p>
        <p>🖱️ Hover over stars for goal details</p>
        <p>📹 Click links to watch goal videos</p>
    </div>
    
    <div class="legend">
        <h3>Legend</h3>
        <div class="legend-item">
            <div class="legend-color" style="background: #ff4444;"></div>
            <span>Galaxies (12)</span>
        </div>
        <div class="legend-item">
            <div class="legend-color" style="background: #ffd700;"></div>
            <span>Constellations (96)</span>
        </div>
        <div class="legend-item">
            <div class="legend-color" style="background: #87ceeb;"></div>
            <span>Stars (10,417)</span>
        </div>
    </div>
    
    <div class="zoom-info">
        <div>Zoom Level: <span id="zoom-level">1</span></div>
        <div>Visible: <span id="visible-layers">Galaxies</span></div>
    </div>
    
    <div id="map"></div>
    
    <!-- Leaflet JavaScript -->
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    
    <script>
        // Embedded GeoJSON data
        const geojsonData = ''' + json.dumps(geojson_data, indent=8) + ''';
        
        // Custom CRS for our coordinate system
        const customCRS = L.extend({}, L.CRS.Simple, {
            transformation: new L.Transformation(1, 0, -1, 0)
        });
        
        // Initialize the map
        const map = L.map('map', {
            crs: customCRS,
            center: [0, 0],
            zoom: 1,
            minZoom: 0,
            maxZoom: 10,
            zoomControl: true,
            attributionControl: false
        });
        
        // Set black background
        map.getContainer().style.background = '#000';
        
        // Layer groups for different zoom levels
        const galaxyLayer = L.layerGroup();
        const constellationLayer = L.layerGroup();
        const starLayer = L.layerGroup();
        
        // Add layers to map
        galaxyLayer.addTo(map);
        
        console.log('Loaded', geojsonData.features.length, 'features');
        
        // Separate features by type
        const galaxies = geojsonData.features.filter(f => f.properties.type === 'galaxy');
        const constellations = geojsonData.features.filter(f => f.properties.type === 'constellation');
        const stars = geojsonData.features.filter(f => f.properties.type === 'star');
        
        console.log('Galaxies:', galaxies.length, 'Constellations:', constellations.length, 'Stars:', stars.length);
        
        // Add galaxies (always visible)
        galaxies.forEach(galaxy => {
            const marker = L.marker([galaxy.geometry.coordinates[1], galaxy.geometry.coordinates[0]], {
                icon: L.divIcon({
                    className: 'galaxy-marker',
                    iconSize: [20, 20],
                    iconAnchor: [10, 10]
                })
            });
            
            // Galaxy label
            const label = L.marker([galaxy.geometry.coordinates[1], galaxy.geometry.coordinates[0]], {
                icon: L.divIcon({
                    className: 'galaxy-label',
                    html: galaxy.properties.name,
                    iconSize: [80, 20],
                    iconAnchor: [40, -30]
                })
            });
            
            marker.addTo(galaxyLayer);
            label.addTo(galaxyLayer);
        });
        
        // Add constellations (visible at higher zoom)
        constellations.forEach(constellation => {
            const marker = L.marker([constellation.geometry.coordinates[1], constellation.geometry.coordinates[0]], {
                icon: L.divIcon({
                    className: 'constellation-marker',
                    iconSize: [15, 15],
                    iconAnchor: [7, 7]
                })
            });
            
            const label = L.marker([constellation.geometry.coordinates[1], constellation.geometry.coordinates[0]], {
                icon: L.divIcon({
                    className: 'constellation-label',
                    html: constellation.properties.name.split('.')[1], // Show only constellation part
                    iconSize: [60, 16],
                    iconAnchor: [30, -20]
                })
            });
            
            marker.addTo(constellationLayer);
            label.addTo(constellationLayer);
        });
        
        // Add stars (visible at highest zoom)
        stars.forEach(star => {
            const marker = L.marker([star.geometry.coordinates[1], star.geometry.coordinates[0]], {
                icon: L.divIcon({
                    className: 'star-marker',
                    iconSize: [8, 8],
                    iconAnchor: [4, 4]
                })
            });
            
            // Create popup with goal information
            const props = star.properties;
            let popupContent = `
                <div class="goal-info">
                    <h3>⭐ ${props.player_name}</h3>
                    <div class="goal-detail">
                        <strong>Team:</strong> <span>${props.team_name}</span>
                    </div>
                    <div class="goal-detail">
                        <strong>Shot Type:</strong> <span>${props.shot_type}</span>
                    </div>
                    <div class="goal-detail">
                        <strong>Period:</strong> <span>${props.period}</span>
                    </div>
                    <div class="goal-detail">
                        <strong>Time:</strong> <span>${props.time}</span>
                    </div>
                    <div class="goal-detail">
                        <strong>Score:</strong> <span>${props.team_score} - ${props.opponent_score}</span>
                    </div>
                    <div class="goal-detail">
                        <strong>Date:</strong> <span>${props.game_date}</span>
                    </div>
                    <div class="goal-detail">
                        <strong>Goals in cluster:</strong> <span>${props.goal_count}</span>
                    </div>
            `;
            
            if (props.url && props.url !== '' && props.url !== 'Unknown') {
                popupContent += `
                    <div class="goal-url">
                        <a href="${props.url}" target="_blank">📹 Watch Goal Video</a>
                    </div>
                `;
            }
            
            popupContent += '</div>';
            
            marker.bindPopup(popupContent);
            marker.addTo(starLayer);
        });
        
        // Set initial view to show all galaxies
        const bounds = L.latLngBounds(galaxies.map(g => [g.geometry.coordinates[1], g.geometry.coordinates[0]]));
        map.fitBounds(bounds.pad(0.1));
        
        // Handle zoom-based layer visibility
        function updateLayerVisibility() {
            const zoom = map.getZoom();
            document.getElementById('zoom-level').textContent = zoom.toFixed(1);
            
            let visibleLayers = [];
            
            // Always show galaxies
            visibleLayers.push('Galaxies');
            
            if (zoom >= 3) {
                // Medium zoom: show constellations
                if (!map.hasLayer(constellationLayer)) {
                    map.addLayer(constellationLayer);
                }
                visibleLayers.push('Constellations');
            } else {
                // Low zoom: hide constellations
                if (map.hasLayer(constellationLayer)) {
                    map.removeLayer(constellationLayer);
                }
            }
            
            if (zoom >= 5) {
                // High zoom: show stars
                if (!map.hasLayer(starLayer)) {
                    map.addLayer(starLayer);
                }
                visibleLayers.push('Stars');
            } else {
                // Low zoom: hide stars
                if (map.hasLayer(starLayer)) {
                    map.removeLayer(starLayer);
                }
            }
            
            document.getElementById('visible-layers').textContent = visibleLayers.join(', ');
        }
        
        // Update layer visibility on zoom
        map.on('zoomend', updateLayerVisibility);
        map.on('zoom', updateLayerVisibility);
        updateLayerVisibility();
        
        console.log('Map initialized successfully');
    </script>
</body>
</html>'''
    
    # Write the standalone HTML file
    with open('visualizations/constellation_map_standalone.html', 'w') as f:
        f.write(html_content)
    
    print("Created standalone HTML file: visualizations/constellation_map_standalone.html")
    print("This file contains all data embedded and should work when opened directly in a browser.")

if __name__ == "__main__":
    create_standalone_html()