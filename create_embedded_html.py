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
        
        .search-panel {{
            top: 20px;
            left: 50%;
            transform: translateX(-50%);
            padding: 15px;
            width: 350px;
            max-width: 90vw;
            z-index: 1001;
        }}
        
        .search-container {{
            position: relative;
        }}
        
        .search-input {{
            width: calc(100% - 24px);
            padding: 10px 40px 10px 12px;
            background: rgba(20, 20, 30, 0.9);
            border: 2px solid rgba(255, 255, 255, 0.3);
            border-radius: 6px;
            color: white;
            font-size: 14px;
            outline: none;
            transition: border-color 0.3s ease;
            box-sizing: border-box;
        }}
        
        .search-input:focus {{
            border-color: #ffd700;
            box-shadow: 0 0 10px rgba(255, 215, 0, 0.3);
        }}
        
        .search-clear {{
            position: absolute;
            right: 10px;
            top: 50%;
            transform: translateY(-50%);
            background: none;
            border: none;
            color: #ffd700;
            font-size: 16px;
            cursor: pointer;
            padding: 2px;
        }}
        
        .search-suggestions {{
            position: absolute;
            top: 100%;
            left: 0;
            right: 0;
            max-height: 200px;
            overflow-y: auto;
            background: rgba(10, 10, 20, 0.95);
            border: 1px solid rgba(255, 255, 255, 0.3);
            border-top: none;
            border-radius: 0 0 6px 6px;
            z-index: 1002;
            display: none;
        }}
        
        .suggestion-item {{
            padding: 10px 12px;
            cursor: pointer;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
            transition: background-color 0.2s ease;
        }}
        
        .suggestion-item:hover, .suggestion-item.highlighted {{
            background: rgba(255, 215, 0, 0.2);
        }}
        
        .suggestion-name {{
            color: white;
            font-weight: bold;
        }}
        
        .suggestion-type {{
            color: #ffd700;
            font-size: 12px;
            margin-left: 8px;
        }}
        
        .suggestion-stats {{
            color: #aaa;
            font-size: 11px;
            margin-top: 2px;
        }}
        
        .search-active-indicator {{
            margin-top: 10px;
            padding: 8px;
            background: rgba(255, 215, 0, 0.1);
            border: 1px solid rgba(255, 215, 0, 0.3);
            border-radius: 4px;
            color: #ffd700;
            font-size: 12px;
            display: none;
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
            text-align: center;
            transform: translateX(-50%);
            display: inline-block;
            cursor: pointer;
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
    
    <div class="ui-panel search-panel">
        <h3 style="margin: 0 0 10px 0; color: #ffd700; font-size: 16px;">🔍 Player Search</h3>
        <div class="search-container">
            <input type="text" id="player-search" class="search-input" placeholder="Search players and goalies..." autocomplete="off">
            <button id="search-clear" class="search-clear" style="display: none;">✕</button>
            <div id="search-suggestions" class="search-suggestions"></div>
        </div>
        <div id="search-active" class="search-active-indicator">
            <div>🎯 <span id="selected-player"></span> selected</div>
            <div style="margin-top: 4px; font-size: 10px;">Lines connect visible elements</div>
        </div>
    </div>
    
    <div class="ui-panel controls-panel">
        <div class="panel-title">Navigation Guide</div>
        <p>🔍 <strong>Zoom:</strong> Mouse wheel or +/- controls</p>
        <p>🖱️ <strong>Pan:</strong> Click and drag to explore</p>
        <p>⭐ <strong>Goals:</strong> Click stars for detailed info</p>
        <p>📹 <strong>Videos:</strong> Watch NHL highlights directly</p>
    </div>
    
    <div class="ui-panel legend-panel">
        <div class="panel-title">Color Legend</div>
        <div class="legend-item">
            <div class="legend-color" style="background: radial-gradient(circle, #ff4444 30%, #ff6666 100%);"></div>
            <span><strong>Galaxies</strong> - Spatial + shot type clusters</span>
        </div>
        <div class="legend-item">
            <div class="legend-color" style="background: radial-gradient(circle, #ffd700 30%, #ffed4a 100%);"></div>
            <span><strong>Clusters</strong> - Game context groups</span>
        </div>
        <div class="legend-item">
            <div class="legend-color" style="background: radial-gradient(circle, #ffa500 30%, #ffb84d 100%);"></div>
            <span><strong>Solar Systems</strong> - Goalie groupings</span>
        </div>
        <div class="legend-item">
            <div class="legend-color" style="background: radial-gradient(circle, #87ceeb 30%, #b6e5ff 100%);"></div>
            <span><strong>Stars</strong> - Individual goals</span>
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
            zoom: 0.5,
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
        
        // Build search indexes for players and goalies
        const playerIndex = new Map();
        const goalieIndex = new Map();
        
        stars.forEach(star => {{
            const props = star.properties;
            const playerName = props.player_name;
            const goalieName = props.goalie_name;
            
            // Index players
            if (playerName && playerName !== 'Unknown') {{
                if (!playerIndex.has(playerName)) {{
                    playerIndex.set(playerName, {{
                        name: playerName,
                        type: 'player',
                        goals: [],
                        teams: new Set()
                    }});
                }}
                const playerData = playerIndex.get(playerName);
                playerData.goals.push(star);
                if (props.team_name && props.team_name !== 'Unknown') {{
                    playerData.teams.add(props.team_name);
                }}
            }}
            
            // Index goalies
            if (goalieName && goalieName !== 'Unknown') {{
                if (!goalieIndex.has(goalieName)) {{
                    goalieIndex.set(goalieName, {{
                        name: goalieName,
                        type: 'goalie',
                        goalsAgainst: [],
                        teams: new Set()
                    }});
                }}
                const goalieData = goalieIndex.get(goalieName);
                goalieData.goalsAgainst.push(star);
            }}
        }});
        
        // Build combined search list
        const searchData = [];
        playerIndex.forEach(player => {{
            searchData.push({{
                name: player.name,
                type: 'Player',
                count: player.goals.length,
                teams: Array.from(player.teams).join(', '),
                data: player
            }});
        }});
        goalieIndex.forEach(goalie => {{
            searchData.push({{
                name: goalie.name,
                type: 'Goalie',
                count: goalie.goalsAgainst.length,
                teams: 'Multiple teams',
                data: goalie
            }});
        }});
        
        // Sort by goal count (descending)
        searchData.sort((a, b) => b.count - a.count);
        
        console.log(`Indexed ${{playerIndex.size}} players and ${{goalieIndex.size}} goalies`);
        
        // Function to get hierarchical statistics for celestial objects
        function getHierarchicalStats(objectName, level) {{
            let stats = {{
                name: objectName,
                level: level,
                clusters: 0,
                solarSystems: 0,
                stars: 0,
                totalGoals: 0,
                topPlayers: new Map(),
                topGoalies: new Map(),
                teams: new Set(),
                shotTypes: new Map(),
                periods: new Map()
            }};
            
            if (level === 'galaxy') {{
                // Count clusters, solar systems, and stars within this galaxy
                clusters.forEach(cluster => {{
                    if (cluster.properties.name.startsWith(objectName + '.')) {{
                        stats.clusters++;
                    }}
                }});
                
                solarSystems.forEach(system => {{
                    if (system.properties.name.startsWith(objectName + '.')) {{
                        stats.solarSystems++;
                    }}
                }});
                
                stars.forEach(star => {{
                    if (star.properties.galaxy === objectName) {{
                        stats.stars++;
                        stats.totalGoals++;
                        
                        // Collect player stats
                        const playerName = star.properties.player_name;
                        if (playerName && playerName !== 'unknown') {{
                            stats.topPlayers.set(playerName, (stats.topPlayers.get(playerName) || 0) + 1);
                        }}
                        
                        // Collect goalie stats
                        const goalieName = star.properties.goalie_name;
                        if (goalieName && goalieName !== 'unknown') {{
                            stats.topGoalies.set(goalieName, (stats.topGoalies.get(goalieName) || 0) + 1);
                        }}
                        
                        // Collect team stats
                        if (star.properties.team_name) {{
                            stats.teams.add(star.properties.team_name);
                        }}
                        
                        // Collect shot type stats
                        if (star.properties.shot_type) {{
                            stats.shotTypes.set(star.properties.shot_type, (stats.shotTypes.get(star.properties.shot_type) || 0) + 1);
                        }}
                        
                        // Collect period stats
                        if (star.properties.period) {{
                            stats.periods.set(star.properties.period, (stats.periods.get(star.properties.period) || 0) + 1);
                        }}
                    }}
                }});
            }} else if (level === 'cluster') {{
                // Count solar systems and stars within this cluster
                solarSystems.forEach(system => {{
                    if (system.properties.name.startsWith(objectName + '.')) {{
                        stats.solarSystems++;
                    }}
                }});
                
                stars.forEach(star => {{
                    if (star.properties.cluster === objectName) {{
                        stats.stars++;
                        stats.totalGoals++;
                        
                        // Collect same stats as galaxy level
                        const playerName = star.properties.player_name;
                        if (playerName && playerName !== 'unknown') {{
                            stats.topPlayers.set(playerName, (stats.topPlayers.get(playerName) || 0) + 1);
                        }}
                        
                        const goalieName = star.properties.goalie_name;
                        if (goalieName && goalieName !== 'unknown') {{
                            stats.topGoalies.set(goalieName, (stats.topGoalies.get(goalieName) || 0) + 1);
                        }}
                        
                        if (star.properties.team_name) {{
                            stats.teams.add(star.properties.team_name);
                        }}
                        
                        if (star.properties.shot_type) {{
                            stats.shotTypes.set(star.properties.shot_type, (stats.shotTypes.get(star.properties.shot_type) || 0) + 1);
                        }}
                        
                        if (star.properties.period) {{
                            stats.periods.set(star.properties.period, (stats.periods.get(star.properties.period) || 0) + 1);
                        }}
                    }}
                }});
            }} else if (level === 'solar system') {{
                // Count stars within this solar system
                stars.forEach(star => {{
                    if (star.properties.solar_system === objectName) {{
                        stats.stars++;
                        stats.totalGoals++;
                        
                        // Collect same stats
                        const playerName = star.properties.player_name;
                        if (playerName && playerName !== 'unknown') {{
                            stats.topPlayers.set(playerName, (stats.topPlayers.get(playerName) || 0) + 1);
                        }}
                        
                        const goalieName = star.properties.goalie_name;
                        if (goalieName && goalieName !== 'unknown') {{
                            stats.topGoalies.set(goalieName, (stats.topGoalies.get(goalieName) || 0) + 1);
                        }}
                        
                        if (star.properties.team_name) {{
                            stats.teams.add(star.properties.team_name);
                        }}
                        
                        if (star.properties.shot_type) {{
                            stats.shotTypes.set(star.properties.shot_type, (stats.shotTypes.get(star.properties.shot_type) || 0) + 1);
                        }}
                        
                        if (star.properties.period) {{
                            stats.periods.set(star.properties.period, (stats.periods.get(star.properties.period) || 0) + 1);
                        }}
                    }}
                }});
            }}
            
            return stats;
        }}
        
        // Function to create hierarchical popup content
        function createHierarchicalPopup(stats) {{
            let content = `<div style="max-width: 300px;">
                <h3 style="margin: 0 0 10px 0; color: #ffd700; text-align: center;">
                    🌌 ${{stats.name}}
                </h3>
                <div style="font-size: 12px; color: #ccc; text-align: center; margin-bottom: 15px;">
                    ${{stats.level.charAt(0).toUpperCase() + stats.level.slice(1)}}
                </div>`;
            
            // Hierarchical composition
            content += `<div style="background: rgba(255,255,255,0.1); padding: 10px; border-radius: 5px; margin-bottom: 10px;">
                <strong>📊 Composition:</strong><br>`;
            
            if (stats.level === 'galaxy') {{
                content += `🌟 Clusters: ${{stats.clusters}}<br>`;
                content += `🪐 Solar Systems: ${{stats.solarSystems}}<br>`;
            }} else if (stats.level === 'cluster') {{
                content += `🪐 Solar Systems: ${{stats.solarSystems}}<br>`;
            }}
            content += `⭐ Stars (Goals): ${{stats.stars}}<br>`;
            content += `</div>`;
            
            // Top players
            if (stats.topPlayers.size > 0) {{
                const topPlayers = Array.from(stats.topPlayers.entries())
                    .sort((a, b) => b[1] - a[1])
                    .slice(0, 3);
                content += `<div style="background: rgba(255,255,255,0.1); padding: 10px; border-radius: 5px; margin-bottom: 10px;">
                    <strong>🏒 Top Scorers:</strong><br>`;
                topPlayers.forEach(([player, count]) => {{
                    content += `• ${{player}}: ${{count}} goals<br>`;
                }});
                content += `</div>`;
            }}
            
            // Top goalies
            if (stats.topGoalies.size > 0) {{
                const topGoalies = Array.from(stats.topGoalies.entries())
                    .sort((a, b) => b[1] - a[1])
                    .slice(0, 3);
                content += `<div style="background: rgba(255,255,255,0.1); padding: 10px; border-radius: 5px; margin-bottom: 10px;">
                    <strong>🥅 Most Scored On:</strong><br>`;
                topGoalies.forEach(([goalie, count]) => {{
                    content += `• ${{goalie}}: ${{count}} goals<br>`;
                }});
                content += `</div>`;
            }}
            
            // Teams involved
            if (stats.teams.size > 0) {{
                content += `<div style="background: rgba(255,255,255,0.1); padding: 10px; border-radius: 5px; margin-bottom: 10px;">
                    <strong>🏒 Teams:</strong><br>`;
                const teamList = Array.from(stats.teams).slice(0, 5).join(', ');
                content += `${{teamList}}${{stats.teams.size > 5 ? ` (+${{stats.teams.size - 5}} more)` : ''}}<br>`;
                content += `</div>`;
            }}
            
            // Shot types
            if (stats.shotTypes.size > 0) {{
                const topShotTypes = Array.from(stats.shotTypes.entries())
                    .sort((a, b) => b[1] - a[1])
                    .slice(0, 3);
                content += `<div style="background: rgba(255,255,255,0.1); padding: 10px; border-radius: 5px;">
                    <strong>🎯 Shot Types:</strong><br>`;
                topShotTypes.forEach(([shotType, count]) => {{
                    content += `• ${{shotType}}: ${{count}}<br>`;
                }});
                content += `</div>`;
            }}
            
            content += `</div>`;
            return content;
        }}
        
        // Add galaxies (always visible)
        galaxies.forEach((galaxy, index) => {{
            const coord = [galaxy.geometry.coordinates[1], galaxy.geometry.coordinates[0]];
            
            // Get hierarchical stats for this galaxy
            const galaxyStats = getHierarchicalStats(galaxy.properties.name, 'galaxy');
            const hierarchicalPopup = createHierarchicalPopup(galaxyStats);
            
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
                    iconSize: null,
                    iconAnchor: [0, -35]
                }})
            }});
            
            // Bind hierarchical popup to both marker and label
            marker.bindPopup(hierarchicalPopup, {{
                maxWidth: 350,
                className: 'custom-popup'
            }});
            label.bindPopup(hierarchicalPopup, {{
                maxWidth: 350,
                className: 'custom-popup'
            }});
            
            marker.addTo(galaxyLayer);
            label.addTo(galaxyLabelLayer);
        }});
        
        // Add clusters (visible at medium zoom)
        clusters.forEach(cluster => {{
            const coord = [cluster.geometry.coordinates[1], cluster.geometry.coordinates[0]];
            
            // Get hierarchical stats for this cluster
            const clusterStats = getHierarchicalStats(cluster.properties.name, 'cluster');
            const hierarchicalPopup = createHierarchicalPopup(clusterStats);
            
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
                    iconSize: null,
                    iconAnchor: [0, -25]
                }})
            }});
            
            // Bind hierarchical popup to both marker and label
            marker.bindPopup(hierarchicalPopup, {{
                maxWidth: 350,
                className: 'custom-popup'
            }});
            label.bindPopup(hierarchicalPopup, {{
                maxWidth: 350,
                className: 'custom-popup'
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
            
            // Get hierarchical stats for this solar system
            const solarSystemStats = getHierarchicalStats(solarSystem.properties.name, 'solar system');
            const hierarchicalPopup = createHierarchicalPopup(solarSystemStats);
            
            marker.bindPopup(hierarchicalPopup, {{
                maxWidth: 350,
                className: 'custom-popup'
            }});
            
            const label = L.marker(coord, {{
                icon: L.divIcon({{
                    className: 'solar-system-label',
                    html: solarSystem.properties.name.split('.')[2] || 'system',
                    iconSize: null,
                    iconAnchor: [0, -20]
                }})
            }});
            
            // Bind hierarchical popup to label as well
            label.bindPopup(hierarchicalPopup, {{
                maxWidth: 350,
                className: 'custom-popup'
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
        map.fitBounds(bounds.pad(0.3));
        
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
        
        // Search functionality
        let selectedPlayer = null;
        let connectionLines = L.layerGroup().addTo(map);
        
        const searchInput = document.getElementById('player-search');
        const searchSuggestions = document.getElementById('search-suggestions');
        const searchClear = document.getElementById('search-clear');
        const searchActive = document.getElementById('search-active');
        const selectedPlayerSpan = document.getElementById('selected-player');
        
        let currentSuggestions = [];
        let highlightedIndex = -1;
        
        function showSuggestions(query) {{
            if (!query || query.length < 2) {{
                searchSuggestions.style.display = 'none';
                return;
            }}
            
            const filtered = searchData.filter(item => 
                item.name.toLowerCase().includes(query.toLowerCase())
            ).slice(0, 10); // Limit to 10 suggestions
            
            if (filtered.length === 0) {{
                searchSuggestions.style.display = 'none';
                return;
            }}
            
            currentSuggestions = filtered;
            highlightedIndex = -1;
            
            searchSuggestions.innerHTML = filtered.map((item, index) => `
                <div class="suggestion-item" data-index="${{index}}">
                    <div class="suggestion-name">${{item.name}}<span class="suggestion-type">${{item.type}}</span></div>
                    <div class="suggestion-stats">${{item.count}} goals • ${{item.teams}}</div>
                </div>
            `).join('');
            
            searchSuggestions.style.display = 'block';
            
            // Add click handlers
            searchSuggestions.querySelectorAll('.suggestion-item').forEach((item, index) => {{
                item.addEventListener('click', () => selectPlayer(filtered[index]));
            }});
        }}
        
        function selectPlayer(playerInfo) {{
            selectedPlayer = playerInfo;
            searchInput.value = playerInfo.name;
            searchSuggestions.style.display = 'none';
            searchClear.style.display = 'block';
            searchActive.style.display = 'block';
            selectedPlayerSpan.textContent = `${{playerInfo.name}} (${{playerInfo.type}})`;
            
            drawConnectionLines();
        }}
        
        function clearSearch() {{
            selectedPlayer = null;
            searchInput.value = '';
            searchSuggestions.style.display = 'none';
            searchClear.style.display = 'none';
            searchActive.style.display = 'none';
            connectionLines.clearLayers();
        }}
        
        function drawConnectionLines() {{
            connectionLines.clearLayers();
            
            if (!selectedPlayer) return;
            
            const zoom = map.getZoom();
            const bounds = map.getBounds();
            const relevantGoals = selectedPlayer.data.type === 'player' ? 
                selectedPlayer.data.goals : selectedPlayer.data.goalsAgainst;
            
            // Find visible components containing this player/goalie (viewport-only)
            const visibleComponents = [];
            
            if (zoom >= 4) {{
                // Individual goals level - connect rendered stars in viewport
                relevantGoals.forEach((goal, index) => {{
                    if (renderedStars.has(stars.indexOf(goal))) {{
                        const coord = [goal.geometry.coordinates[1], goal.geometry.coordinates[0]];
                        if (bounds.contains(coord)) {{
                            visibleComponents.push(coord);
                        }}
                    }}
                }});
            }} else if (zoom >= 2) {{
                // Solar system level - connect solar systems containing this player in viewport
                const solarSystemsWithPlayer = new Set();
                relevantGoals.forEach(goal => {{
                    const solarSystemName = goal.properties.solar_system;
                    if (solarSystemName) {{
                        solarSystemsWithPlayer.add(solarSystemName);
                    }}
                }});
                
                solarSystems.forEach(system => {{
                    if (solarSystemsWithPlayer.has(system.properties.name)) {{
                        const coord = [system.geometry.coordinates[1], system.geometry.coordinates[0]];
                        if (bounds.contains(coord)) {{
                            visibleComponents.push(coord);
                        }}
                    }}
                }});
            }} else if (zoom >= 1) {{
                // Cluster level - connect clusters containing this player in viewport
                const clustersWithPlayer = new Set();
                relevantGoals.forEach(goal => {{
                    const clusterName = goal.properties.cluster;
                    if (clusterName) {{
                        clustersWithPlayer.add(clusterName);
                    }}
                }});
                
                clusters.forEach(cluster => {{
                    if (clustersWithPlayer.has(cluster.properties.name)) {{
                        const coord = [cluster.geometry.coordinates[1], cluster.geometry.coordinates[0]];
                        if (bounds.contains(coord)) {{
                            visibleComponents.push(coord);
                        }}
                    }}
                }});
            }} else {{
                // Galaxy level - connect galaxies containing this player in viewport
                const galaxiesWithPlayer = new Set();
                relevantGoals.forEach(goal => {{
                    const galaxyName = goal.properties.galaxy;
                    if (galaxyName) {{
                        galaxiesWithPlayer.add(galaxyName);
                    }}
                }});
                
                galaxies.forEach(galaxy => {{
                    if (galaxiesWithPlayer.has(galaxy.properties.name)) {{
                        const coord = [galaxy.geometry.coordinates[1], galaxy.geometry.coordinates[0]];
                        if (bounds.contains(coord)) {{
                            visibleComponents.push(coord);
                        }}
                    }}
                }});
            }}
            
            // Draw lines between visible components in viewport
            if (visibleComponents.length > 1) {{
                for (let i = 0; i < visibleComponents.length - 1; i++) {{
                    for (let j = i + 1; j < visibleComponents.length; j++) {{
                        const line = L.polyline([visibleComponents[i], visibleComponents[j]], {{
                            color: '#ffd700',
                            weight: 2,
                            opacity: 0.6,
                            dashArray: '5, 10'
                        }});
                        connectionLines.addLayer(line);
                    }}
                }}
                
                console.log(`Drew ${{connectionLines.getLayers().length}} connection lines for ${{selectedPlayer.name}} (viewport only)`);
            }}
        }}
        
        // Search input handlers
        searchInput.addEventListener('input', (e) => {{
            const query = e.target.value;
            showSuggestions(query);
            if (query) {{
                searchClear.style.display = 'block';
            }} else {{
                searchClear.style.display = 'none';
                clearSearch();
            }}
        }});
        
        searchInput.addEventListener('keydown', (e) => {{
            if (e.key === 'ArrowDown') {{
                e.preventDefault();
                highlightedIndex = Math.min(highlightedIndex + 1, currentSuggestions.length - 1);
                updateHighlight();
            }} else if (e.key === 'ArrowUp') {{
                e.preventDefault();
                highlightedIndex = Math.max(highlightedIndex - 1, -1);
                updateHighlight();
            }} else if (e.key === 'Enter') {{
                e.preventDefault();
                if (highlightedIndex >= 0 && currentSuggestions[highlightedIndex]) {{
                    selectPlayer(currentSuggestions[highlightedIndex]);
                }}
            }} else if (e.key === 'Escape') {{
                searchSuggestions.style.display = 'none';
            }}
        }});
        
        function updateHighlight() {{
            const items = searchSuggestions.querySelectorAll('.suggestion-item');
            items.forEach((item, index) => {{
                item.classList.toggle('highlighted', index === highlightedIndex);
            }});
        }}
        
        searchClear.addEventListener('click', clearSearch);
        
        // Hide suggestions when clicking outside
        document.addEventListener('click', (e) => {{
            if (!e.target.closest('.search-container')) {{
                searchSuggestions.style.display = 'none';
            }}
        }});
        
        // Redraw lines when zoom/pan changes
        map.on('zoomend moveend', () => {{
            if (selectedPlayer) {{
                drawConnectionLines();
            }}
        }});
        
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