import json
import os

def create_embedded_constellation_html():
    """Create an HTML file with embedded GeoJSON data in the root directory"""
    
    # Read the GeoJSON data
    geojson_path = 'visualizations/nhl_constellation_map.geojson'
    if not os.path.exists(geojson_path):
        print(f"Error: {geojson_path} not found. Run mapping.py first.")
        return
    
    with open(geojson_path, 'r') as f:
        geojson_data = json.load(f)
    
    # HTML template with embedded data
    html_content = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>NHL Constellation Map - Interactive</title>
    
    <!-- Leaflet CSS -->
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    
    <style>
        body {{
            margin: 0;
            padding: 0;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: #000;
            color: white;
            overflow: hidden;
        }}
        
        #map {{
            height: 100vh;
            width: 100vw;
            background: radial-gradient(ellipse at center, #1a1a2e 0%, #000000 100%);
        }}
        
        .ui-panel {{
            position: absolute;
            z-index: 1000;
            background: rgba(0, 0, 0, 0.85);
            border: 2px solid rgba(255, 255, 255, 0.3);
            border-radius: 8px;
            backdrop-filter: blur(10px);
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.5);
        }}
        
        .title-panel {{
            top: 20px;
            left: 20px;
            padding: 20px;
            max-width: 350px;
        }}
        
        .title-panel h1 {{
            margin: 0 0 10px 0;
            font-size: 28px;
            background: linear-gradient(45deg, #ffd700, #ff6b6b);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }}
        
        .title-panel p {{
            margin: 5px 0;
            font-size: 14px;
            color: #ccc;
        }}
        
        .controls-panel {{
            top: 20px;
            right: 20px;
            padding: 15px;
            max-width: 280px;
        }}
        
        .legend-panel {{
            bottom: 20px;
            left: 20px;
            padding: 15px;
            max-width: 320px;
        }}
        
        .zoom-panel {{
            bottom: 20px;
            right: 20px;
            padding: 12px;
            font-size: 12px;
            min-width: 150px;
        }}
        
        .legend-item {{
            display: flex;
            align-items: center;
            margin: 8px 0;
            font-size: 14px;
        }}
        
        .legend-color {{
            width: 20px;
            height: 20px;
            margin-right: 12px;
            border: 2px solid rgba(255, 255, 255, 0.5);
            border-radius: 50%;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
        }}
        
        .panel-title {{
            font-weight: bold;
            margin-bottom: 10px;
            font-size: 16px;
            color: #ffd700;
            border-bottom: 1px solid rgba(255, 215, 0, 0.3);
            padding-bottom: 5px;
        }}
        
        /* Custom marker styles */
        .galaxy-marker {{
            background: radial-gradient(circle, #ff4444 30%, #ff6666 100%);
            border: 3px solid rgba(255, 255, 255, 0.8);
            border-radius: 50%;
            box-shadow: 0 0 20px rgba(255, 68, 68, 0.6);
            animation: pulse 2s ease-in-out infinite alternate;
        }}
        
        .cluster-marker {{
            background: radial-gradient(circle, #ffd700 30%, #ffed4a 100%);
            border: 2px solid rgba(255, 255, 255, 0.7);
            border-radius: 50%;
            box-shadow: 0 0 15px rgba(255, 215, 0, 0.5);
        }}
        
        .solar-system-marker {{
            background: radial-gradient(circle, #ffa500 30%, #ffb84d 100%);
            border: 2px solid rgba(255, 255, 255, 0.6);
            border-radius: 50%;
            box-shadow: 0 0 12px rgba(255, 165, 0, 0.4);
        }}
        
        .star-marker {{
            background: radial-gradient(circle, #87ceeb 30%, #b6e5ff 100%);
            border: 1px solid rgba(255, 255, 255, 0.6);
            border-radius: 50%;
            box-shadow: 0 0 8px rgba(135, 206, 235, 0.4);
            transition: transform 0.2s ease;
        }}
        
        .star-marker:hover {{
            transform: scale(1.5);
            box-shadow: 0 0 15px rgba(135, 206, 235, 0.8);
        }}
        
        .star-marker-optimized {{
            cursor: pointer;
            transition: transform 0.1s ease;
        }}
        
        .star-marker-optimized:hover {{
            transform: scale(1.3);
        }}
        
        @keyframes pulse {{
            from {{ transform: scale(1); }}
            to {{ transform: scale(1.1); }}
        }}
        
        .galaxy-label, .cluster-label, .solar-system-label {{
            background: rgba(0, 0, 0, 0.8);
            color: white;
            padding: 4px 8px;
            border-radius: 4px;
            font-weight: bold;
            border: 1px solid rgba(255, 255, 255, 0.3);
            white-space: nowrap;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.5);
            transition: opacity 0.3s ease-in-out;
        }}
        
        .galaxy-label {{
            font-size: 14px;
            background: rgba(255, 68, 68, 0.9);
            border-color: #ff4444;
        }}
        
        .cluster-label {{
            font-size: 12px;
            background: rgba(255, 215, 0, 0.9);
            color: #000;
            border-color: #ffd700;
        }}
        
        .solar-system-label {{
            font-size: 10px;
            background: rgba(255, 165, 0, 0.9);
            color: #000;
            border-color: #ffa500;
        }}
        
        /* Popup styling */
        .leaflet-popup-content-wrapper {{
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            border: 2px solid #ffd700;
            border-radius: 12px;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.7);
        }}
        
        .leaflet-popup-content {{
            color: white;
            margin: 12px;
            font-family: 'Segoe UI', sans-serif;
        }}
        
        .leaflet-popup-tip {{
            background: #1a1a2e;
            border: 2px solid #ffd700;
        }}
        
        .goal-info {{
            min-width: 280px;
            max-width: 350px;
        }}
        
        .goal-info h3 {{
            margin: 0 0 12px 0;
            color: #ffd700;
            border-bottom: 2px solid #ffd700;
            padding-bottom: 8px;
            font-size: 18px;
            display: flex;
            align-items: center;
        }}
        
        .goal-info h3::before {{
            content: "⭐";
            margin-right: 8px;
            font-size: 20px;
        }}
        
        .goal-detail {{
            margin: 8px 0;
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 4px 0;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        }}
        
        .goal-detail:last-child {{
            border-bottom: none;
        }}
        
        .goal-detail strong {{
            color: #87ceeb;
            font-weight: 600;
            min-width: 100px;
        }}
        
        .goal-detail span {{
            text-align: right;
            flex: 1;
        }}
        
        .goal-url {{
            margin-top: 15px;
            padding-top: 15px;
            border-top: 2px solid rgba(255, 215, 0, 0.3);
            text-align: center;
        }}
        
        .goal-url a {{
            color: #87ceeb;
            text-decoration: none;
            padding: 10px 20px;
            border: 2px solid #87ceeb;
            border-radius: 25px;
            display: inline-block;
            background: linear-gradient(45deg, transparent, rgba(135, 206, 235, 0.1));
            transition: all 0.3s ease;
            font-weight: bold;
        }}
        
        .goal-url a:hover {{
            background: linear-gradient(45deg, #87ceeb, #5fa8d1);
            color: #000;
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(135, 206, 235, 0.4);
        }}
        
        .zoom-indicator {{
            font-weight: bold;
            color: #ffd700;
        }}
        
        .visible-layers {{
            color: #87ceeb;
            font-style: italic;
        }}
        
        /* Loading animation */
        .loading {{
            position: fixed;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            z-index: 2000;
            color: #ffd700;
            font-size: 18px;
            text-align: center;
        }}
        
        .spinner {{
            width: 40px;
            height: 40px;
            border: 4px solid rgba(255, 215, 0, 0.3);
            border-top: 4px solid #ffd700;
            border-radius: 50%;
            animation: spin 1s linear infinite;
            margin: 0 auto 20px;
        }}
        
        @keyframes spin {{
            0% {{ transform: rotate(0deg); }}
            100% {{ transform: rotate(360deg); }}
        }}
    </style>
</head>
<body>
    <div id="loading" class="loading">
        <div class="spinner"></div>
        <div>Loading NHL Constellation Map...</div>
    </div>

    <div class="ui-panel title-panel">
        <h1>NHL Constellation Map</h1>
        <p>🌌 Interactive visualization of NHL goal patterns</p>
        <p>📊 {len(geojson_data['features'])} total celestial objects</p>
        <p>🎯 16,221 goals from 2023+ seasons</p>
    </div>
    
    <div class="ui-panel controls-panel">
        <div class="panel-title">Navigation Guide</div>
        <p>🔍 <strong>Zoom:</strong> Mouse wheel or +/- controls</p>
        <p>🖱️ <strong>Pan:</strong> Click and drag to explore</p>
        <p>⭐ <strong>Goals:</strong> Click stars for detailed info</p>
        <p>📹 <strong>Videos:</strong> Watch NHL highlights directly</p>
    </div>
    
    <div class="ui-panel legend-panel">
        <div class="panel-title">Celestial Objects</div>
        <div class="legend-item">
            <div class="legend-color" style="background: radial-gradient(circle, #ff4444 30%, #ff6666 100%);"></div>
            <span><strong>Galaxies</strong> - Spatial clusters (12)</span>
        </div>
        <div class="legend-item">
            <div class="legend-color" style="background: radial-gradient(circle, #ffd700 30%, #ffed4a 100%);"></div>
            <span><strong>Constellations</strong> - Game context (96)</span>
        </div>
        <div class="legend-item">
            <div class="legend-color" style="background: radial-gradient(circle, #87ceeb 30%, #b6e5ff 100%);"></div>
            <span><strong>Stars</strong> - Player goals (2,767)</span>
        </div>
    </div>
    
    <div class="ui-panel zoom-panel">
        <div class="panel-title">View Status</div>
        <div>Zoom: <span id="zoom-level" class="zoom-indicator">1.0</span></div>
        <div>Visible: <span id="visible-layers" class="visible-layers">Galaxies</span></div>
        <div>Objects: <span id="object-count" class="zoom-indicator">12</span></div>
    </div>
    
    <div id="map"></div>
    
    <!-- Leaflet JavaScript -->
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    
    <script>
        // Embedded GeoJSON data
        const geojsonData = {json.dumps(geojson_data, indent=8)};
        
        // Hide loading screen once data is loaded
        document.getElementById('loading').style.display = 'none';
        
        // Custom CRS for our coordinate system
        const customCRS = L.extend({{}}, L.CRS.Simple, {{
            transformation: new L.Transformation(1, 0, -1, 0)
        }});
        
        // Initialize the map
        const map = L.map('map', {{
            crs: customCRS,
            center: [0, 0],
            zoom: 1,
            minZoom: 0,
            maxZoom: 6,
            zoomControl: true,
            attributionControl: false,
            zoomAnimation: true,
            fadeAnimation: true
        }});
        
        // Layer groups for different hierarchy levels
        const galaxyLayer = L.layerGroup();
        const galaxyLabelLayer = L.layerGroup();
        const clusterLayer = L.layerGroup();
        const clusterLabelLayer = L.layerGroup();
        const solarSystemLayer = L.layerGroup();
        const solarSystemLabelLayer = L.layerGroup();
        const starLayer = L.layerGroup();
        
        // Add base layers to map
        galaxyLayer.addTo(map);
        galaxyLabelLayer.addTo(map);
        
        console.log('Loaded', geojsonData.features.length, 'celestial objects');
        
        // Separate features by type
        const galaxies = geojsonData.features.filter(f => f.properties.type === 'galaxy');
        const clusters = geojsonData.features.filter(f => f.properties.type === 'cluster');
        const solarSystems = geojsonData.features.filter(f => f.properties.type === 'solar_system');
        const stars = geojsonData.features.filter(f => f.properties.type === 'star');
        
        console.log('Processing:', galaxies.length, 'galaxies,', clusters.length, 'clusters,', solarSystems.length, 'solar systems,', stars.length, 'stars');
        
        // Add galaxies (always visible)
        galaxies.forEach((galaxy, index) => {{
            const coord = [galaxy.geometry.coordinates[1], galaxy.geometry.coordinates[0]];
            
            // Galaxy marker
            const marker = L.marker(coord, {{
                icon: L.divIcon({{
                    className: 'galaxy-marker',
                    iconSize: [24, 24],
                    iconAnchor: [12, 12]
                }})
            }});
            
            // Galaxy label
            const label = L.marker(coord, {{
                icon: L.divIcon({{
                    className: 'galaxy-label',
                    html: galaxy.properties.name,
                    iconSize: [100, 25],
                    iconAnchor: [50, -35]
                }})
            }});
            
            marker.addTo(galaxyLayer);
            label.addTo(galaxyLabelLayer);
        }});
        
        // Add clusters (visible at medium zoom)
        clusters.forEach(cluster => {{
            const coord = [cluster.geometry.coordinates[1], cluster.geometry.coordinates[0]];
            
            const marker = L.marker(coord, {{
                icon: L.divIcon({{
                    className: 'cluster-marker',
                    iconSize: [16, 16],
                    iconAnchor: [8, 8]
                }})
            }});
            
            const label = L.marker(coord, {{
                icon: L.divIcon({{
                    className: 'cluster-label',
                    html: cluster.properties.name.split('.')[1] || 'cluster',
                    iconSize: [80, 20],
                    iconAnchor: [40, -25]
                }})
            }});
            
            marker.addTo(clusterLayer);
            label.addTo(clusterLabelLayer);
        }});
        
        // Add solar systems (visible at medium zoom as larger circles)
        solarSystems.forEach(solarSystem => {{
            const coord = [solarSystem.geometry.coordinates[1], solarSystem.geometry.coordinates[0]];
            const goalCount = solarSystem.properties.goal_count || 1;
            
            // Calculate circle size based on number of goals (min 15, max 40)
            const circleSize = Math.min(40, Math.max(15, 8 + Math.sqrt(goalCount) * 3));
            
            const marker = L.marker(coord, {{
                icon: L.divIcon({{
                    className: 'solar-system-marker',
                    iconSize: [circleSize, circleSize],
                    iconAnchor: [circleSize/2, circleSize/2],
                    html: `<div style="width: 100%; height: 100%; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 10px; font-weight: bold; color: white;">${{goalCount}}</div>`
                }})
            }});
            
            // Create popup for solar system with aggregated information
            const starsInSystem = stars.filter(star => 
                star.properties.solar_system === solarSystem.properties.name
            );
            
            let systemPopup = `
                <div class="goal-info">
                    <h3>${{solarSystem.properties.name.split('.')[2] || 'Solar System'}}</h3>
                    <div class="goal-detail">
                        <strong>Goals in System:</strong> <span>${{goalCount}}</span>
                    </div>
                    <div class="goal-detail">
                        <strong>Cluster:</strong> <span>${{solarSystem.properties.cluster.split('.')[1] || 'Unknown'}}</span>
                    </div>
                    <div class="goal-detail">
                        <strong>Galaxy:</strong> <span>${{solarSystem.properties.galaxy || 'Unknown'}}</span>
                    </div>
            `;
            
            // Add sample of goalies and players in this system
            if (starsInSystem.length > 0) {{
                const goalies = [...new Set(starsInSystem.map(s => s.properties.goalie_name).filter(g => g && g !== 'Unknown'))];
                const players = [...new Set(starsInSystem.map(s => s.properties.player_name).filter(p => p && p !== 'Unknown'))];
                
                if (goalies.length > 0) {{
                    systemPopup += `<div class="goal-detail"><strong>Goalies:</strong> <span>${{goalies.slice(0, 3).join(', ')}}${{goalies.length > 3 ? ` (+${{goalies.length - 3}} more)` : ''}}</span></div>`;
                }}
                
                if (players.length > 0) {{
                    systemPopup += `<div class="goal-detail"><strong>Top Scorers:</strong> <span>${{players.slice(0, 3).join(', ')}}${{players.length > 3 ? ` (+${{players.length - 3}} more)` : ''}}</span></div>`;
                }}
            }}
            
            systemPopup += `<div class="goal-detail"><em>Zoom in to see individual goals</em></div></div>`;
            
            marker.bindPopup(systemPopup, {{
                maxWidth: 300,
                className: 'custom-popup'
            }});
            
            const label = L.marker(coord, {{
                icon: L.divIcon({{
                    className: 'solar-system-label',
                    html: solarSystem.properties.name.split('.')[2] || 'system',
                    iconSize: [60, 16],
                    iconAnchor: [30, -20]
                }})
            }});
            
            marker.addTo(solarSystemLayer);
            label.addTo(solarSystemLabelLayer);
        }});
        
        // Optimized star rendering with viewport culling and lazy loading
        let renderedStars = new Set();
        let starMarkers = new Map();
        
        function renderStarsInViewport() {{
            if (map.getZoom() < 4) return; // Only render at high zoom
            
            const bounds = map.getBounds();
            const bufferFactor = 0.5; // Render 50% beyond viewport for smooth panning
            const expandedBounds = bounds.pad(bufferFactor);
            
            // Collect stars to add/remove in batches
            const starsToAdd = [];
            const starsToRemove = [];
            
            stars.forEach((star, index) => {{
                const coord = [star.geometry.coordinates[1], star.geometry.coordinates[0]];
                const isInView = expandedBounds.contains(coord);
                
                if (isInView && !renderedStars.has(index)) {{
                    starsToAdd.push({{star, index, coord}});
                }} else if (!isInView && renderedStars.has(index)) {{
                    starsToRemove.push(index);
                }}
            }});
            
            // Remove stars in batches (fast)
            starsToRemove.forEach(index => {{
                const marker = starMarkers.get(index);
                if (marker) {{
                    starLayer.removeLayer(marker);
                    starMarkers.delete(index);
                    renderedStars.delete(index);
                }}
            }});
            
            // Add stars in smaller batches to avoid blocking UI
            const BATCH_SIZE = 100;
            let currentBatch = 0;
            
            function addStarBatch() {{
                const start = currentBatch * BATCH_SIZE;
                const end = Math.min(start + BATCH_SIZE, starsToAdd.length);
                
                for (let i = start; i < end; i++) {{
                    const {{star, index, coord}} = starsToAdd[i];
                    const clusterColor = star.properties.cluster_color || '#87ceeb';
                    
                    const marker = L.marker(coord, {{
                        icon: L.divIcon({{
                            className: 'star-marker-optimized',
                            html: `<div style="background: ${{clusterColor}}; width: 12px; height: 12px; border-radius: 50%; border: 1px solid rgba(255,255,255,0.6);"></div>`,
                            iconSize: [12, 12],
                            iconAnchor: [6, 6]
                        }})
                    }});
                    
                    // Create popup with lazy content generation
                    function generatePopupContent() {{
                        const props = star.properties;
                        let popupContent = `
                            <div class="goal-info">
                                <h3>${{props.player_name || 'Unknown Player'}}</h3>
                                <div class="goal-detail">
                                    <strong>Team:</strong> <span>${{props.team_name || 'Unknown'}}</span>
                                </div>
                                <div class="goal-detail">
                                    <strong>Shot Type:</strong> <span>${{props.shot_type || 'Unknown'}}</span>
                                </div>
                                <div class="goal-detail">
                                    <strong>Period:</strong> <span>${{props.period || 'Unknown'}}</span>
                                </div>
                                <div class="goal-detail">
                                    <strong>Time:</strong> <span>${{props.time || 'Unknown'}}</span>
                                </div>
                                <div class="goal-detail">
                                    <strong>Score:</strong> <span>${{props.team_score || 0}} - ${{props.opponent_score || 0}}</span>
                                </div>
                                <div class="goal-detail">
                                    <strong>Date:</strong> <span>${{props.game_date || 'Unknown'}}</span>
                                </div>
                                <div class="goal-detail">
                                    <strong>Goalie:</strong> <span>${{props.goalie_name || 'Unknown'}}</span>
                                </div>
                                <div class="goal-detail">
                                    <strong>Goal Location:</strong> <span>${{props.goal_x !== null && props.goal_y !== null ? `(x: ${{props.goal_x}}, y: ${{props.goal_y}})` : 'Not recorded'}}</span>
                                </div>
                                <div class="goal-detail">
                                    <strong>Cluster:</strong> <span style="color: ${{clusterColor}}; font-weight: bold;">●</span> ${{props.goal_count || 1}} goals
                                </div>
                        `;
                        
                        if (props.url && props.url !== '' && props.url !== 'Unknown' && props.url.includes('nhl.com')) {{
                            popupContent += `
                                <div class="goal-url">
                                    <a href="${{props.url}}" target="_blank">📹 Watch Goal Video</a>
                                </div>
                            `;
                        }}
                        
                        popupContent += '</div>';
                        return popupContent;
                    }}
                    
                    // Bind popup immediately but generate content on demand
                    marker.bindPopup(generatePopupContent, {{
                        maxWidth: 400,
                        className: 'custom-popup'
                    }});
                    
                    marker.addTo(starLayer);
                    starMarkers.set(index, marker);
                    renderedStars.add(index);
                }}
                
                currentBatch++;
                
                // Continue with next batch if there are more stars to add
                if (end < starsToAdd.length) {{
                    requestAnimationFrame(addStarBatch);
                }} else if (starsToAdd.length > 0) {{
                    console.log(`Rendered ${{starsToAdd.length}} stars in batches (${{renderedStars.size}} total)`);
                }}
            }}
            
            // Start batch processing if there are stars to add
            if (starsToAdd.length > 0) {{
                requestAnimationFrame(addStarBatch);
            }}
            
            if (starsToRemove.length > 0) {{
                console.log(`Removed ${{starsToRemove.length}} stars from viewport`);
            }}
        }}
        
        // Debounced star rendering to avoid excessive calls during fast panning/zooming
        let renderTimeout;
        function debouncedRenderStars() {{
            clearTimeout(renderTimeout);
            renderTimeout = setTimeout(renderStarsInViewport, 100);
        }}
        
        // Set initial view to show all galaxies
        const bounds = L.latLngBounds(galaxies.map(g => [g.geometry.coordinates[1], g.geometry.coordinates[0]]));
        map.fitBounds(bounds.pad(0.15));
        
        // Handle zoom-based layer visibility
        function updateLayerVisibility() {{
            const zoom = map.getZoom();
            document.getElementById('zoom-level').textContent = zoom.toFixed(1);
            
            let visibleLayers = ['Galaxies'];
            let objectCount = galaxies.length;
            
            // Show/hide clusters based on zoom level
            if (zoom >= 1) {{
                if (!map.hasLayer(clusterLayer)) {{
                    map.addLayer(clusterLayer);
                    map.addLayer(clusterLabelLayer);
                }}
                visibleLayers.push('Clusters');
                objectCount += clusters.length;
            }} else {{
                if (map.hasLayer(clusterLayer)) {{
                    map.removeLayer(clusterLayer);
                    map.removeLayer(clusterLabelLayer);
                }}
            }}
            
            // Show/hide solar systems vs stars based on zoom level
            if (zoom >= 2 && zoom < 4) {{
                // Show solar systems, hide individual stars
                if (!map.hasLayer(solarSystemLayer)) {{
                    map.addLayer(solarSystemLayer);
                    map.addLayer(solarSystemLabelLayer);
                }}
                if (map.hasLayer(starLayer)) {{
                    map.removeLayer(starLayer);
                }}
                visibleLayers.push('Solar Systems');
                objectCount += solarSystems.length;
            }} else if (zoom >= 4) {{
                // Show individual stars, hide solar systems
                if (!map.hasLayer(starLayer)) {{
                    map.addLayer(starLayer);
                }}
                if (map.hasLayer(solarSystemLayer)) {{
                    map.removeLayer(solarSystemLayer);
                    map.removeLayer(solarSystemLabelLayer);
                }}
                // Render stars in viewport
                debouncedRenderStars();
                visibleLayers.push('Individual Goals');
                objectCount += renderedStars.size;
            }} else {{
                // Hide both solar systems and stars at low zoom
                if (map.hasLayer(solarSystemLayer)) {{
                    map.removeLayer(solarSystemLayer);
                    map.removeLayer(solarSystemLabelLayer);
                }}
                if (map.hasLayer(starLayer)) {{
                    map.removeLayer(starLayer);
                    // Clear all rendered stars for performance
                    starMarkers.forEach(marker => starLayer.removeLayer(marker));
                    starMarkers.clear();
                    renderedStars.clear();
                }}
            }}
            
            // Add fading effects for labels based on zoom level
            // Fade out galaxy labels as you zoom in
            const galaxyOpacity = Math.max(0.3, Math.min(1, (3 - zoom) / 2));
            galaxyLabelLayer.eachLayer(layer => {{
                if (layer.getElement()) {{
                    layer.getElement().style.opacity = galaxyOpacity;
                }}
            }});
            
            // Fade out cluster labels as you zoom in further
            const clusterOpacity = Math.max(0.3, Math.min(1, (4 - zoom) / 2));
            clusterLabelLayer.eachLayer(layer => {{
                if (layer.getElement()) {{
                    layer.getElement().style.opacity = clusterOpacity;
                }}
            }});
            
            // Fade out solar system labels when switching to individual stars
            const solarSystemOpacity = zoom >= 3.5 ? Math.max(0.2, (4 - zoom) * 2) : 1;
            solarSystemLabelLayer.eachLayer(layer => {{
                if (layer.getElement()) {{
                    layer.getElement().style.opacity = solarSystemOpacity;
                }}
            }});
            
            // Update UI
            document.getElementById('visible-layers').textContent = visibleLayers.join(', ');
            document.getElementById('object-count').textContent = objectCount.toLocaleString();
        }}
        
        // Update layer visibility on zoom changes
        map.on('zoomend', updateLayerVisibility);
        
        // Update star rendering on map moves for viewport culling
        map.on('moveend', debouncedRenderStars);
        map.on('zoomend', debouncedRenderStars);
        map.on('zoom', updateLayerVisibility);
        
        // Initial update
        updateLayerVisibility();
        
        console.log('NHL Constellation Map initialized successfully!');
        console.log('Zoom levels: 0 (Galaxies), 1+ (+ Clusters), 2-3 (+ Solar Systems), 4+ (+ Individual Goals)');
    </script>
</body>
</html>'''
    
    # Write the HTML file to root directory
    output_path = 'nhl_constellation_map.html'
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"✅ Created interactive constellation map: {output_path}")
    print(f"📊 Embedded {len(geojson_data['features'])} celestial objects")
    print(f"🌌 {len([f for f in geojson_data['features'] if f['properties']['type'] == 'galaxy'])} galaxies")
    print(f"⭐ {len([f for f in geojson_data['features'] if f['properties']['type'] == 'cluster'])} clusters") 
    print(f"🪐 {len([f for f in geojson_data['features'] if f['properties']['type'] == 'solar_system'])} solar systems")
    print(f"🌟 {len([f for f in geojson_data['features'] if f['properties']['type'] == 'star'])} stars")
    print(f"🚀 Open {output_path} in Chrome to explore!")

if __name__ == "__main__":
    create_embedded_constellation_html()