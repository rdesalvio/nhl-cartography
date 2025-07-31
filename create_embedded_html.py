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
            font-family: 'Inter', 'Segoe UI', 'Roboto', sans-serif;
            background: linear-gradient(135deg, #0a0a23 0%, #1a1a3a 50%, #0f0f2f 100%);
            color: #ffffff;
            overflow: hidden;
            font-weight: 400;
        }}
        
        #map {{
            height: 100vh;
            width: 100vw;
            background: radial-gradient(ellipse at center, #1a1a4a 0%, #0a0a2a 70%, #000015 100%);
            position: relative;
        }}
        
        /* Subtle star field effect */
        #map:before {{
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background-image: 
                radial-gradient(2px 2px at 20px 30px, #ffffff, transparent),
                radial-gradient(2px 2px at 40px 70px, rgba(255,255,255,0.8), transparent),
                radial-gradient(1px 1px at 90px 40px, rgba(255,255,255,0.6), transparent),
                radial-gradient(1px 1px at 130px 80px, rgba(255,255,255,0.4), transparent);
            background-repeat: repeat;
            background-size: 200px 100px;
            opacity: 0.1;
            pointer-events: none;
            z-index: 1;
        }}
        
        /* Futuristic glow animation */
        @keyframes neonPulse {{
            0%, 100% {{ opacity: 1; filter: brightness(1); }}
            50% {{ opacity: 0.95; filter: brightness(1.05); }}
        }}
        
        body {{
            animation: neonPulse 3s ease-in-out infinite;
        }}
        
        .ui-panel {{
            position: absolute;
            z-index: 1000;
            background: rgba(10, 15, 35, 0.95);
            border: 1px solid rgba(100, 200, 255, 0.4);
            border-radius: 12px;
            box-shadow: 
                0 8px 32px rgba(0, 0, 0, 0.4),
                0 0 20px rgba(100, 200, 255, 0.2),
                inset 0 1px 0 rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
            font-family: 'Inter', 'Segoe UI', sans-serif;
            color: #ffffff;
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
            width: 100%;
            padding: 12px 50px 12px 16px;
            background: rgba(15, 25, 45, 0.9);
            border: 1px solid rgba(100, 200, 255, 0.3);
            border-radius: 8px;
            color: #ffffff;
            font-family: 'Inter', 'Segoe UI', sans-serif;
            font-size: 14px;
            outline: none;
            transition: all 0.3s ease;
            box-sizing: border-box;
        }}
        
        .search-input:focus {{
            border-color: #64c8ff;
            box-shadow: 0 0 16px rgba(100, 200, 255, 0.3);
            background: rgba(20, 30, 50, 0.95);
        }}
        
        .search-input::placeholder {{
            color: rgba(255, 255, 255, 0.6);
            font-family: 'Inter', 'Segoe UI', sans-serif;
        }}
        
        .search-clear {{
            position: absolute;
            right: 8px;
            top: 50%;
            transform: translateY(-50%);
            width: 32px;
            height: 32px;
            background: rgba(100, 200, 255, 0.1);
            border: 1px solid rgba(100, 200, 255, 0.3);
            border-radius: 6px;
            color: #64c8ff;
            font-family: 'Inter', sans-serif;
            font-size: 14px;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 10;
            transition: all 0.2s ease;
        }}
        
        .search-clear:hover {{
            background: rgba(100, 200, 255, 0.2);
            color: #ffffff;
            box-shadow: 0 0 8px rgba(100, 200, 255, 0.4);
        }}
        
        .search-suggestions {{
            position: absolute;
            top: 100%;
            left: 0;
            right: 0;
            max-height: 250px;
            overflow-y: auto;
            background: rgba(15, 25, 45, 0.95);
            border: 1px solid rgba(100, 200, 255, 0.3);
            border-top: none;
            border-radius: 0 0 8px 8px;
            backdrop-filter: blur(10px);
            z-index: 1002;
            display: none;
            font-family: 'Inter', 'Segoe UI', sans-serif;
        }}
        
        .suggestion-item {{
            padding: 12px 16px;
            cursor: pointer;
            border-bottom: 1px solid rgba(100, 200, 255, 0.1);
            transition: all 0.2s ease;
        }}
        
        .suggestion-item:hover, .suggestion-item.highlighted {{
            background: rgba(100, 200, 255, 0.1);
            border-left: 3px solid #64c8ff;
        }}
        
        .suggestion-name {{
            color: #ffffff;
            font-weight: 600;
            font-family: 'Inter', 'Segoe UI', sans-serif;
        }}
        
        .suggestion-type {{
            color: #64c8ff;
            font-size: 12px;
            margin-left: 8px;
            font-family: 'Inter', 'Segoe UI', sans-serif;
            font-weight: 500;
        }}
        
        .suggestion-stats {{
            color: rgba(255, 255, 255, 0.7);
            font-size: 11px;
            margin-top: 4px;
            font-family: 'Inter', 'Segoe UI', sans-serif;
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
            margin: 0 0 16px 0;
            font-size: 28px;
            font-family: 'Inter', 'Segoe UI', sans-serif;
            color: #ffffff;
            font-weight: 700;
            background: linear-gradient(135deg, #64c8ff 0%, #ffffff 50%, #ff6b9d 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }}
        
        .title-panel p {{
            margin: 8px 0;
            font-size: 14px;
            font-family: 'Inter', 'Segoe UI', sans-serif;
            color: rgba(255, 255, 255, 0.8);
            font-weight: 400;
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
        
        /* Mobile responsive layout */
        @media screen and (max-width: 768px) {{
            .title-panel {{
                display: none; /* Hidden by default on mobile */
            }}
            
            /* Mobile info icon for title */
            .mobile-info-icon {{
                position: fixed;
                top: 15px;
                left: 15px;
                width: 40px;
                height: 40px;
                background: rgba(10, 15, 35, 0.95);
                border: 1px solid rgba(100, 200, 255, 0.4);
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 18px;
                color: #64c8ff;
                z-index: 1002;
                cursor: pointer;
                backdrop-filter: blur(10px);
                box-shadow: 0 4px 16px rgba(0, 0, 0, 0.3);
            }}
            
            .mobile-info-icon:hover {{
                background: rgba(100, 200, 255, 0.2);
                transform: scale(1.1);
            }}
            
            /* Mobile search icon */
            .mobile-search-icon {{
                position: fixed;
                top: 15px;
                right: 15px;
                width: 40px;
                height: 40px;
                background: rgba(10, 15, 35, 0.95);
                border: 1px solid rgba(100, 200, 255, 0.4);
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 16px;
                color: #64c8ff;
                z-index: 1002;
                cursor: pointer;
                backdrop-filter: blur(10px);
                box-shadow: 0 4px 16px rgba(0, 0, 0, 0.3);
            }}
            
            .mobile-search-icon:hover {{
                background: rgba(100, 200, 255, 0.2);
                transform: scale(1.1);
            }}
            
            .title-panel h1 {{
                font-size: 20px;
                margin-bottom: 8px;
            }}
            
            .title-panel p {{
                font-size: 12px;
                margin: 4px 0;
            }}
            
            .search-panel {{
                display: none; /* Hidden by default on mobile */
                top: 70px; /* Below mobile icons */
                left: 10px;
                right: 10px;
                width: auto;
                max-width: none;
                transform: none;
                padding: 12px;
            }}
            
            .search-panel.mobile-expanded {{
                display: block !important;
            }}
            
            .legend-panel {{
                bottom: 10px; /* Moved to bottom since zoom panel is hidden */
                left: 10px;
                right: 10px;
                max-width: none;
                padding: 12px;
            }}
            
            /* Make panels collapsible on mobile */
            .panel-title {{
                cursor: pointer;
                user-select: none;
                padding: 8px 0;
                border-bottom: 1px solid rgba(255,255,255,0.1);
                margin-bottom: 8px;
            }}
            
            .panel-title:after {{
                content: ' ▼';
                font-size: 10px;
                opacity: 0.7;
                float: right;
            }}
            
            /* Improve touch targets on mobile */
            .search-input {{
                font-size: 16px; /* Prevents zoom on iOS */
                padding: 12px;
            }}
            
            .search-clear {{
                padding: 8px;
                min-width: 40px;
                min-height: 40px;
            }}
            
            /* Hide less essential UI elements on small screens */
            .title-panel p:nth-child(n+4) {{
                display: none; /* Hide some description text */
            }}
            
            /* Make zoom controls more touch-friendly */
            .leaflet-control-zoom {{
                transform: translateY(-50%) scale(1.2) !important;
            }}
            
            .leaflet-control-home {{
                margin-top: 8px !important;
            }}
            
            .leaflet-control-home-button {{
                width: 32px !important;
                height: 32px !important;
                line-height: 30px !important;
                font-size: 18px !important;
            }}
            
            /* Hide navigation guide and view status on mobile */
            .controls-panel,
            .zoom-panel {{
                display: none !important;
            }}
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
            font-family: 'Inter', 'Segoe UI', sans-serif;
            font-weight: 600;
            margin-bottom: 16px;
            font-size: 16px;
            color: #64c8ff;
            border-bottom: 2px solid rgba(100, 200, 255, 0.3);
            padding-bottom: 8px;
            text-transform: none;
            letter-spacing: 0.5px;
        }}
        
        /* Custom marker styles - futuristic neon */
        .galaxy-marker {{
            background: radial-gradient(circle, #ff3366 20%, #ff6600 60%, #ffaa00 100%);
            border: 2px solid #ff6600;
            border-radius: 50%;
            box-shadow: 
                0 0 20px rgba(255, 102, 0, 0.8),
                0 0 40px rgba(255, 102, 0, 0.4),
                inset 0 0 10px rgba(255, 255, 255, 0.2);
            width: 100%;
            height: 100%;
            position: relative;
        }}
        
        .galaxy-marker:after {{
            content: '';
            position: absolute;
            top: 3px;
            left: 3px;
            right: 3px;
            bottom: 3px;
            border: 1px solid rgba(255, 255, 255, 0.6);
            border-radius: 50%;
        }}
        
        .cluster-marker {{
            background: radial-gradient(circle, #00f5ff 20%, #00bfff 60%, #0080ff 100%);
            border: 2px solid #00bfff;
            border-radius: 50%;
            box-shadow: 
                0 0 18px rgba(0, 191, 255, 0.8),
                0 0 35px rgba(0, 191, 255, 0.4);
            width: 100%;
            height: 100%;
        }}
        
        .solar-system-marker {{
            background: radial-gradient(circle, #ff00ff 20%, #cc00ff 60%, #9900cc 100%);
            border: 2px solid #cc00ff;
            border-radius: 50%;
            box-shadow: 
                0 0 16px rgba(204, 0, 255, 0.8),
                0 0 30px rgba(204, 0, 255, 0.4);
            width: 100%;
            height: 100%;
        }}
        
        .star-marker {{
            background: radial-gradient(circle, #00ff80 20%, #00ff41 60%, #00cc33 100%);
            border: 1px solid #00ff66;
            border-radius: 50%;
            box-shadow: 
                0 0 12px rgba(0, 255, 102, 0.8),
                0 0 24px rgba(0, 255, 102, 0.3);
            width: 100%;
            height: 100%;
            transition: all 0.2s ease;
        }}
        
        .star-marker:hover {{
            transform: scale(1.4);
            box-shadow: 
                0 0 20px rgba(0, 255, 102, 1),
                0 0 40px rgba(0, 255, 102, 0.6);
        }}
        
        .star-marker-optimized {{
            cursor: pointer;
            /* Removed transition for better performance */
        }}
        
        /* Optimized star dot styling */
        .star-dot {{
            width: 12px;
            height: 12px;
            border-radius: 50%;
            border: 1px solid rgba(255,255,255,0.6);
        }}
        
        /* Apply lightweight hover effects for all devices */
        .star-marker-optimized:hover {{
            transform: scale(1.2); /* Reduced scale for better performance */
            transition: transform 0.05s ease; /* Faster transition */
        }}
        
        @keyframes pulse {{
            from {{ transform: scale(1); }}
            to {{ transform: scale(1.1); }}
        }}
        
        .galaxy-label, .cluster-label, .solar-system-label {{
            background: rgba(10, 15, 35, 0.95);
            backdrop-filter: blur(8px);
            font-family: 'Inter', 'Segoe UI', sans-serif;
            font-weight: 600;
            padding: 8px 12px;
            border: 1px solid;
            border-radius: 6px;
            white-space: nowrap;
            transition: all 0.3s ease;
            text-align: center;
            transform: translateX(-50%);
            display: inline-block;
            cursor: pointer;
            pointer-events: none;
            z-index: 1000;
        }}
        
        .galaxy-label {{
            font-size: 13px;
            color: #ff6600;
            border-color: rgba(255, 102, 0, 0.5);
            text-shadow: 0 0 8px rgba(255, 102, 0, 0.8);
            box-shadow: 
                0 4px 16px rgba(255, 102, 0, 0.3),
                inset 0 1px 0 rgba(255, 255, 255, 0.1);
        }}
        
        .cluster-label {{
            font-size: 12px;
            color: #00bfff;
            border-color: rgba(0, 191, 255, 0.5);
            text-shadow: 0 0 8px rgba(0, 191, 255, 0.8);
            box-shadow: 
                0 4px 16px rgba(0, 191, 255, 0.3),
                inset 0 1px 0 rgba(255, 255, 255, 0.1);
        }}
        
        .solar-system-label {{
            font-size: 11px;
            color: #cc00ff;
            border-color: rgba(204, 0, 255, 0.5);
            text-shadow: 0 0 8px rgba(204, 0, 255, 0.8);
            box-shadow: 
                0 4px 16px rgba(204, 0, 255, 0.3),
                inset 0 1px 0 rgba(255, 255, 255, 0.1);
        }}
        
        /* Popup styling */
        .leaflet-popup-content-wrapper {{
            background: rgba(10, 15, 35, 0.95);
            backdrop-filter: blur(12px);
            border: 1px solid rgba(100, 200, 255, 0.4);
            border-radius: 12px;
            box-shadow: 
                0 8px 32px rgba(0, 0, 0, 0.4),
                0 0 20px rgba(100, 200, 255, 0.2),
                inset 0 1px 0 rgba(255, 255, 255, 0.1);
        }}
        
        .leaflet-popup-content {{
            color: #ffffff;
            margin: 16px;
            font-family: 'Inter', 'Segoe UI', sans-serif;
        }}
        
        .leaflet-popup-tip {{
            background: rgba(10, 15, 35, 0.95);
            border: 1px solid rgba(100, 200, 255, 0.4);
        }}
        
        .goal-info {{
            min-width: 280px;
            max-width: 350px;
        }}
        
        .goal-info h3 {{
            margin: 0 0 16px 0;
            color: #64c8ff;
            border-bottom: 2px solid rgba(100, 200, 255, 0.3);
            padding-bottom: 12px;
            font-size: 18px;
            font-family: 'Inter', 'Segoe UI', sans-serif;
            font-weight: 600;
            display: flex;
            align-items: center;
        }}
        
        .goal-info h3::before {{
            content: "⭐";
            margin-right: 8px;
            font-size: 20px;
        }}
        
        .goal-detail {{
            margin: 12px 0;
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 8px 0;
            border-bottom: 1px solid rgba(100, 200, 255, 0.1);
            font-family: 'Inter', 'Segoe UI', sans-serif;
            font-size: 13px;
        }}
        
        .goal-detail:last-child {{
            border-bottom: none;
        }}
        
        .goal-detail strong {{
            color: #64c8ff;
            font-weight: 600;
            font-family: 'Inter', 'Segoe UI', sans-serif;
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
        
        /* Move zoom controls to middle left */
        .leaflet-control-zoom {{
            top: 50% !important;
            left: 10px !important;
            transform: translateY(-50%) !important;
            margin: 0 !important;
        }}
        
        .leaflet-top.leaflet-left {{
            top: 50% !important;
            left: 10px !important;
            transform: translateY(-50%) !important;
        }}
        
        /* Home button control styling */
        .leaflet-control-home {{
            margin-top: 5px !important;
        }}
        
        .leaflet-control-home-button {{
            background-color: #fff;
            color: #333;
            text-decoration: none;
            font-size: 16px;
            line-height: 26px;
            display: block;
            text-align: center;
            width: 26px;
            height: 26px;
            border-radius: 4px;
            cursor: pointer;
        }}
        
        .leaflet-control-home-button:hover {{
            background-color: #f4f4f4;
            color: #000;
        }}
        
        /* Context info bar at bottom */
        .context-bar {{
            position: fixed;
            bottom: 0;
            left: 50%;
            transform: translateX(-50%);
            background: rgba(0, 0, 0, 0.9);
            color: white;
            padding: 10px 20px;
            border-radius: 8px 8px 0 0;
            border: 2px solid rgba(255, 255, 255, 0.3);
            border-bottom: none;
            z-index: 1000;
            font-size: 14px;
            font-weight: bold;
            text-align: center;
            transition: opacity 0.3s ease-in-out;
            opacity: 0;
            pointer-events: none;
        }}
        
        .context-bar.visible {{
            opacity: 1;
        }}
        
        .context-bar .galaxy-context {{
            color: #ff4444;
            margin-right: 15px;
        }}
        
        .context-bar .cluster-context {{
            color: #ffd700;
        }}
        
        /* Simple hover effects that work with Leaflet positioning */
        .celestial-object {{
            transition: filter 0.2s ease, opacity 0.2s ease;
            cursor: pointer;
        }}
        
        .celestial-object:hover {{
            filter: brightness(1.3) drop-shadow(0 0 8px currentColor);
            z-index: 1000 !important;
        }}
        
        .celestial-object.dimmed {{
            opacity: 0.4;
            filter: brightness(0.8);
        }}
        
        .celestial-label {{
            transition: all 0.2s ease;
            cursor: pointer;
        }}
        
        .celestial-label:hover {{
            filter: brightness(1.2) drop-shadow(0 2px 6px rgba(0,0,0,0.8));
            z-index: 10000 !important;
            position: relative !important;
        }}
        
        .celestial-label.dimmed {{
            opacity: 0.3;
            filter: brightness(0.7);
        }}
        
        /* Specific hover effects without transforms */
        .galaxy-marker:hover {{
            filter: brightness(1.4) drop-shadow(0 0 12px #ff4444) !important;
        }}
        
        .cluster-marker:hover {{
            filter: brightness(1.3) drop-shadow(0 0 10px #ffd700) !important;
        }}
        
        .solar-system-marker:hover {{
            filter: brightness(1.4) drop-shadow(0 0 15px #ffa500) !important;
        }}
        
        .solar-system-label:hover {{
            background: rgba(255, 165, 0, 0.95) !important;
            color: #000 !important;
            box-shadow: 0 3px 12px rgba(255, 165, 0, 0.6) !important;
            font-weight: bold !important;
            z-index: 10001 !important;
            position: relative !important;
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
        <div class="panel-title">🔍 Universal Search</div>
        <div class="search-container">
            <input type="text" id="player-search" class="search-input" placeholder="Search players..." autocomplete="off">
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
    </div>
    
    <div class="ui-panel legend-panel">
        <div class="panel-title">Color Legend</div>
        <div class="legend-item">
            <div class="legend-color" style="background: radial-gradient(circle, #ff3366 20%, #ff6600 60%, #ffaa00 100%); box-shadow: 0 0 10px rgba(255, 102, 0, 0.5);"></div>
            <span><strong>Galaxies</strong> - Spatial + shot type clusters</span>
        </div>
        <div class="legend-item">
            <div class="legend-color" style="background: radial-gradient(circle, #00f5ff 20%, #00bfff 60%, #0080ff 100%); box-shadow: 0 0 10px rgba(0, 191, 255, 0.5);"></div>
            <span><strong>Clusters</strong> - Game context groups</span>
        </div>
        <div class="legend-item">
            <div class="legend-color" style="background: radial-gradient(circle, #ff00ff 20%, #cc00ff 60%, #9900cc 100%); box-shadow: 0 0 10px rgba(204, 0, 255, 0.5);"></div>
            <span><strong>Solar Systems</strong> - Goalie groupings</span>
        </div>
        <div class="legend-item">
            <div class="legend-color" style="background: radial-gradient(circle, #00ff80 20%, #00ff41 60%, #00cc33 100%); box-shadow: 0 0 10px rgba(0, 255, 102, 0.5);"></div>
            <span><strong>Stars</strong> - Individual goals</span>
        </div>
    </div>
    
    <div class="ui-panel zoom-panel">
        <div class="panel-title">View Status</div>
        <div>Zoom: <span id="zoom-level" class="zoom-indicator">1.0</span></div>
        <div>Visible: <span id="visible-layers" class="visible-layers">Galaxies</span></div>
        <div>Objects: <span id="object-count" class="zoom-indicator">12</span></div>
    </div>
    
    <!-- Context bar for showing current galaxy/cluster -->
    <div id="context-bar" class="context-bar">
        <span id="galaxy-context" class="galaxy-context"></span>
        <span id="cluster-context" class="cluster-context"></span>
    </div>
    
    <div id="map"></div>
    
    <!-- Mobile Icons (only visible on mobile) -->
    <div class="mobile-info-icon" style="display: none;">ℹ</div>
    <div class="mobile-search-icon" style="display: none;">🔍</div>
    
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
            zoom: 0,
            minZoom: -1,
            maxZoom: 6,
            zoomControl: true,
            attributionControl: false,
            zoomAnimation: true,
            fadeAnimation: true
        }});
        
        // Custom Home Button Control
        L.Control.HomeButton = L.Control.extend({{
            onAdd: function(map) {{
                const container = L.DomUtil.create('div', 'leaflet-control-home leaflet-bar leaflet-control');
                const button = L.DomUtil.create('a', 'leaflet-control-home-button', container);
                
                button.innerHTML = '🏠';
                button.href = '#';
                button.title = 'Return to center';
                button.setAttribute('role', 'button');
                button.setAttribute('aria-label', 'Return to center of map');
                
                L.DomEvent.on(button, 'click', function(e) {{
                    L.DomEvent.stopPropagation(e);
                    L.DomEvent.preventDefault(e);
                    map.flyTo([0, 0], 0, {{
                        duration: 1.5
                    }});
                }});
                
                return container;
            }}
        }});
        
        // Add the home button control to the map
        map.addControl(new L.Control.HomeButton({{ position: 'topleft' }}));
        
        // URL parameter handling for sharing locations
        function parseUrlParams() {{
            const params = new URLSearchParams(window.location.search);
            const locationData = {{
                name: params.get('name'),
                type: params.get('type'),
                lat: parseFloat(params.get('lat')),
                lng: parseFloat(params.get('lng')),
                zoom: parseFloat(params.get('zoom'))
            }};
            
            if (locationData.name && locationData.type && !isNaN(locationData.lat) && !isNaN(locationData.lng) && !isNaN(locationData.zoom)) {{
                return locationData;
            }}
            return null;
        }}
        
        function updateUrl(name, type, lat, lng, zoom) {{
            const params = new URLSearchParams();
            params.set('name', name);
            params.set('type', type);
            params.set('lat', lat.toFixed(6));
            params.set('lng', lng.toFixed(6));
            params.set('zoom', zoom.toFixed(2));
            
            const newUrl = `${{window.location.pathname}}?${{params.toString()}}`;
            window.history.replaceState(null, '', newUrl);
        }}
        
        function generateShareableLink(name, type, lat, lng, zoom) {{
            const params = new URLSearchParams();
            params.set('name', name);
            params.set('type', type);
            params.set('lat', lat.toFixed(6));
            params.set('lng', lng.toFixed(6));
            params.set('zoom', zoom.toFixed(2));
            
            // Handle different URL contexts
            let baseUrl;
            if (window.location.protocol === 'file:') {{
                // For local files, use the full file path
                baseUrl = window.location.href.split('?')[0];
            }} else if (window.location.hostname === 'localhost' || window.location.hostname.includes('github.io')) {{
                // For localhost or GitHub Pages
                baseUrl = `${{window.location.origin}}${{window.location.pathname}}`;
            }} else {{
                // Default case
                baseUrl = `${{window.location.origin}}${{window.location.pathname}}`;
            }}
            
            return `${{baseUrl}}?${{params.toString()}}`;
        }}
        
        function navigateToLocation(name, type, coordinate, targetZoom) {{
            const [lat, lng] = coordinate;
            map.setView([lat, lng], targetZoom, {{animate: true, duration: 1.5}});
            updateUrl(name, type, lat, lng, targetZoom);
            
            // Show a temporary indicator and try to open the popup
            setTimeout(() => {{
                const indicator = L.marker([lat, lng], {{
                    icon: L.divIcon({{
                        className: 'navigation-indicator',
                        html: '<div style="background: #ffd700; width: 30px; height: 30px; border-radius: 50%; border: 3px solid white; animation: pulse 1s ease-in-out 3;"></div>',
                        iconSize: [30, 30],
                        iconAnchor: [15, 15]
                    }})
                }}).addTo(map);
                
                // Try to find and open the popup for the shared object
                setTimeout(() => {{
                    openPopupAtLocation(type, coordinate, name);
                }}, 500);
                
                setTimeout(() => map.removeLayer(indicator), 3000);
            }}, 1000);
        }}
        
        function openPopupAtLocation(type, coordinate, name) {{
            const [lat, lng] = coordinate;
            const targetLatLng = L.latLng(lat, lng);
            const tolerance = 0.001; // Small tolerance for coordinate matching
            
            // Find the closest marker to the shared coordinates
            let closestMarker = null;
            let minDistance = Infinity;
            
            // Check all active layers for markers near the target coordinates
            [galaxyLayer, clusterLayer, solarSystemLayer, starLayer].forEach(layer => {{
                if (map.hasLayer(layer)) {{
                    layer.eachLayer(marker => {{
                        if (marker.getLatLng) {{
                            const markerLatLng = marker.getLatLng();
                            const distance = targetLatLng.distanceTo(markerLatLng);
                            if (distance < minDistance && distance < tolerance * 111320) {{ // Convert tolerance to meters
                                minDistance = distance;
                                closestMarker = marker;
                            }}
                        }}
                    }});
                }}
            }});
            
            // Open the popup if we found a close marker
            if (closestMarker && closestMarker.getPopup) {{
                closestMarker.openPopup();
                console.log(`Opened popup for shared location: ${{name}}`);
            }} else {{
                console.log(`Could not find marker for shared location: ${{name}} at [${{lat}}, ${{lng}}]`);
            }}
        }}
        
        function showNotification(message, isSuccess = true) {{
            const notification = document.createElement('div');
            notification.style.cssText = `
                position: fixed;
                top: 20px;
                right: 20px;
                background: ${{isSuccess ? 'rgba(76, 175, 80, 0.95)' : 'rgba(244, 67, 54, 0.95)'}};
                color: white;
                padding: 12px 20px;
                border-radius: 8px;
                z-index: 15000;
                font-weight: bold;
                box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
                transform: translateX(400px);
                transition: all 0.3s ease;
                max-width: 300px;
                font-size: 14px;
            `;
            notification.textContent = message;
            document.body.appendChild(notification);
            
            // Slide in
            setTimeout(() => {{
                notification.style.transform = 'translateX(0)';
            }}, 10);
            
            // Fade out and remove
            setTimeout(() => {{
                notification.style.opacity = '0';
                notification.style.transform = 'translateX(400px)';
                setTimeout(() => {{
                    if (notification.parentNode) {{
                        document.body.removeChild(notification);
                    }}
                }}, 300);
            }}, 2500);
        }}
        
        async function copyShareLink(name, type, coordinate, zoom) {{
            const [lat, lng] = coordinate;
            const shareUrl = generateShareableLink(name, type, lat, lng, zoom);
            
            console.log('Attempting to copy URL:', shareUrl);
            
            // Method 1: Modern clipboard API
            if (navigator.clipboard) {{
                try {{
                    await navigator.clipboard.writeText(shareUrl);
                    console.log('Successfully copied using clipboard API');
                    showNotification(`📋 Link copied: ${{name}}`);
                    return;
                }} catch (err) {{
                    console.error('Clipboard API failed:', err);
                }}
            }}
            
            // Method 2: Legacy execCommand
            try {{
                const textArea = document.createElement('textarea');
                textArea.value = shareUrl;
                textArea.style.cssText = `
                    position: fixed;
                    left: -9999px;
                    top: -9999px;
                    opacity: 0;
                    pointer-events: none;
                `;
                document.body.appendChild(textArea);
                
                // Focus and select the text
                textArea.focus();
                textArea.select();
                textArea.setSelectionRange(0, textArea.value.length);
                
                const successful = document.execCommand('copy');
                document.body.removeChild(textArea);
                
                if (successful) {{
                    console.log('Successfully copied using execCommand');
                    showNotification(`📋 Link copied: ${{name}}`);
                    return;
                }} else {{
                    console.error('execCommand returned false');
                }}
            }} catch (err) {{
                console.error('execCommand failed:', err);
            }}
            
            // Method 3: Prompt user to manually copy
            try {{
                // For mobile/problematic browsers, use prompt
                if (typeof prompt !== 'undefined') {{
                    prompt('Copy this link to share:', shareUrl);
                    showNotification(`📋 Link ready to copy: ${{name}}`);
                    return;
                }}
            }} catch (err) {{
                console.error('Prompt failed:', err);
            }}
            
            // Method 4: Show modal as final fallback
            console.log('All clipboard methods failed, showing modal');
            const modal = document.createElement('div');
            modal.style.cssText = `
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background: rgba(0, 0, 0, 0.8);
                z-index: 20000;
                display: flex;
                align-items: center;
                justify-content: center;
            `;
            
            const popup = document.createElement('div');
            popup.style.cssText = `
                background: rgba(0, 0, 0, 0.95);
                color: white;
                padding: 30px;
                border-radius: 12px;
                border: 2px solid #ffd700;
                max-width: 500px;
                text-align: center;
                box-shadow: 0 10px 30px rgba(0, 0, 0, 0.7);
            `;
            
            popup.innerHTML = `
                <h3 style="color: #ffd700; margin: 0 0 15px 0;">🔗 Share Link for ${{name}}</h3>
                <p style="margin: 10px 0;">Select and copy this link to share:</p>
                <input type="text" value="${{shareUrl}}" readonly style="
                    width: 100%;
                    padding: 10px;
                    background: #1a1a1a;
                    color: white;
                    border: 1px solid #ffd700;
                    border-radius: 5px;
                    margin: 15px 0;
                    font-family: monospace;
                    font-size: 12px;
                " onclick="this.select()">
                <br>
                <button onclick="this.parentElement.parentElement.remove()" style="
                    background: #ffd700;
                    color: #000;
                    border: none;
                    padding: 10px 20px;
                    border-radius: 5px;
                    cursor: pointer;
                    font-weight: bold;
                    margin-top: 10px;
                ">Close</button>
            `;
            
            modal.appendChild(popup);
            document.body.appendChild(modal);
            
            // Auto-select the input text
            setTimeout(() => {{
                const input = popup.querySelector('input');
                if (input) {{
                    input.focus();
                    input.select();
                }}
            }}, 100);
            
            // Close on background click
            modal.onclick = (e) => {{
                if (e.target === modal) {{
                    modal.remove();
                }}
            }};
            
            showNotification('📋 Manual copy required - see popup', false);
        }}
        
        // Global function to be called from onclick handlers in popups
        window.shareLocation = function(name, type, coordinate, zoom) {{
            console.log('Share button clicked for:', name, type, coordinate, zoom);
            copyShareLink(name, type, coordinate, zoom);
        }};
        
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
        
        // Build search indexes for players, goalies, and celestial objects
        const playerIndex = new Map();
        const goalieIndex = new Map();
        const galaxyIndex = new Map();
        const clusterIndex = new Map();
        const solarSystemIndex = new Map();
        
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
            if (goalieName && goalieName !== 'Empty Net') {{
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
        
        // Index galaxies, clusters, and solar systems
        galaxies.forEach(galaxy => {{
            const stats = getHierarchicalStats(galaxy.properties.name, 'galaxy');
            galaxyIndex.set(galaxy.properties.name, {{
                name: galaxy.properties.name,
                type: 'galaxy',
                data: galaxy,
                stats: stats,
                coordinate: [galaxy.geometry.coordinates[1], galaxy.geometry.coordinates[0]]
            }});
        }});
        
        clusters.forEach(cluster => {{
            const stats = getHierarchicalStats(cluster.properties.name, 'cluster');
            clusterIndex.set(cluster.properties.name, {{
                name: cluster.properties.name,
                displayName: cluster.properties.name.split('.')[1] || cluster.properties.name,
                type: 'cluster',
                data: cluster,
                stats: stats,
                coordinate: [cluster.geometry.coordinates[1], cluster.geometry.coordinates[0]]
            }});
        }});
        
        solarSystems.forEach(solarSystem => {{
            const stats = getHierarchicalStats(solarSystem.properties.name, 'solar system');
            solarSystemIndex.set(solarSystem.properties.name, {{
                name: solarSystem.properties.name,
                displayName: solarSystem.properties.name.split('.')[2] || solarSystem.properties.name,
                type: 'solar system',
                data: solarSystem,
                stats: stats,
                coordinate: [solarSystem.geometry.coordinates[1], solarSystem.geometry.coordinates[0]]
            }});
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
        galaxyIndex.forEach(galaxy => {{
            searchData.push({{
                name: galaxy.name,
                type: 'Galaxy',
                count: galaxy.stats.stars,
                teams: `${{galaxy.stats.clusters}} clusters, ${{galaxy.stats.solarSystems}} systems`,
                data: galaxy,
                navigable: true
            }});
        }});
        clusterIndex.forEach(cluster => {{
            searchData.push({{
                name: cluster.displayName,
                fullName: cluster.name,
                type: 'Cluster',
                count: cluster.stats.stars,
                teams: `${{cluster.stats.solarSystems}} solar systems`,
                data: cluster,
                navigable: true
            }});
        }});
        solarSystemIndex.forEach(solarSystem => {{
            searchData.push({{
                name: solarSystem.displayName,
                fullName: solarSystem.name,
                type: 'Solar System',
                count: solarSystem.stats.stars,
                teams: `${{solarSystem.stats.topPlayers.size}} unique players`,
                data: solarSystem,
                navigable: true
            }});
        }});
        
        // Sort by goal count (descending)
        searchData.sort((a, b) => b.count - a.count);
        
        console.log(`Indexed ${{playerIndex.size}} players, ${{goalieIndex.size}} goalies, ${{galaxyIndex.size}} galaxies, ${{clusterIndex.size}} clusters, ${{solarSystemIndex.size}} solar systems`);
        
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
                periods: new Map(),
                shotZones: new Map(),
                situations: new Map(),
                // New stats for different hierarchy levels
                avgX: 0,
                avgY: 0,
                avgPeriod: 0,
                avgPeriodTime: 0,
                avgScoreDiff: 0,
                avgSeasonDay: 0,
                validCoords: 0,
                validPeriodData: 0,
                validScoreData: 0,
                validSeasonData: 0
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
                        if (goalieName && goalieName !== 'Empty Net') {{
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
                        
                        
                        // Collect shot zone stats
                        if (star.properties.shot_zone && star.properties.shot_zone.trim() !== '') {{
                            stats.shotZones.set(star.properties.shot_zone, (stats.shotZones.get(star.properties.shot_zone) || 0) + 1);
                        }}
                        
                        // Collect situation stats
                        if (star.properties.situation && star.properties.situation.trim() !== '') {{
                            stats.situations.set(star.properties.situation, (stats.situations.get(star.properties.situation) || 0) + 1);
                        }}
                        
                        // Galaxy-specific stats: average coordinates for zone information
                        if (star.properties.x && star.properties.y && !isNaN(star.properties.x) && !isNaN(star.properties.y)) {{
                            stats.avgX += parseFloat(star.properties.x);
                            stats.avgY += parseFloat(star.properties.y);
                            stats.validCoords++;
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
                        if (goalieName && goalieName !== 'Empty Net') {{
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
                        
                        
                        // Collect shot zone stats
                        if (star.properties.shot_zone && star.properties.shot_zone.trim() !== '') {{
                            stats.shotZones.set(star.properties.shot_zone, (stats.shotZones.get(star.properties.shot_zone) || 0) + 1);
                        }}
                        
                        // Collect situation stats
                        if (star.properties.situation && star.properties.situation.trim() !== '') {{
                            stats.situations.set(star.properties.situation, (stats.situations.get(star.properties.situation) || 0) + 1);
                        }}
                        
                        // Cluster-specific stats: period, time, score, and date averages
                        if (star.properties.period && !isNaN(star.properties.period)) {{
                            stats.avgPeriod += parseFloat(star.properties.period);
                            stats.validPeriodData++;
                        }}
                        
                        if (star.properties.period_time && !isNaN(star.properties.period_time)) {{
                            stats.avgPeriodTime += parseFloat(star.properties.period_time);
                        }}
                        
                        if (star.properties.score_diff !== undefined && !isNaN(star.properties.score_diff)) {{
                            stats.avgScoreDiff += parseFloat(star.properties.score_diff);
                            stats.validScoreData++;
                        }}
                        
                        if (star.properties.season_day && !isNaN(star.properties.season_day)) {{
                            stats.avgSeasonDay += parseFloat(star.properties.season_day);
                            stats.validSeasonData++;
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
                        if (goalieName && goalieName !== 'Empty Net') {{
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
                        
                        
                        // Collect shot zone stats
                        if (star.properties.shot_zone && star.properties.shot_zone.trim() !== '') {{
                            stats.shotZones.set(star.properties.shot_zone, (stats.shotZones.get(star.properties.shot_zone) || 0) + 1);
                        }}
                        
                        // Collect situation stats
                        if (star.properties.situation && star.properties.situation.trim() !== '') {{
                            stats.situations.set(star.properties.situation, (stats.situations.get(star.properties.situation) || 0) + 1);
                        }}
                    }}
                }});
            }}
            
            // Calculate averages
            if (stats.validCoords > 0) {{
                stats.avgX = stats.avgX / stats.validCoords;
                stats.avgY = stats.avgY / stats.validCoords;
            }}
            
            if (stats.validPeriodData > 0) {{
                stats.avgPeriod = stats.avgPeriod / stats.validPeriodData;
                stats.avgPeriodTime = stats.avgPeriodTime / stats.validPeriodData;
            }}
            
            if (stats.validScoreData > 0) {{
                stats.avgScoreDiff = stats.avgScoreDiff / stats.validScoreData;
            }}
            
            if (stats.validSeasonData > 0) {{
                stats.avgSeasonDay = stats.avgSeasonDay / stats.validSeasonData;
            }}
            
            return stats;
        }}
        
        // Function to create hierarchical popup content
        function createHierarchicalPopup(stats, coordinate) {{
            const shareButtonId = `share-btn-${{stats.name.replace(/[^a-zA-Z0-9]/g, '-')}}`;
            const targetZoom = stats.level === 'galaxy' ? 0.5 : 
                              stats.level === 'cluster' ? 2 : 
                              stats.level === 'solar system' ? 3 : 1.5;
            
            let content = `<div style="max-width: 300px;">
                <h3 style="margin: 0 0 10px 0; color: #ffd700; text-align: center;">
                    🌌 ${{stats.name}}
                </h3>
                <div style="font-size: 12px; color: #ccc; text-align: center; margin-bottom: 15px;">
                    ${{stats.level.charAt(0).toUpperCase() + stats.level.slice(1)}}
                </div>
                <div style="text-align: center; margin-bottom: 15px;">
                    <button onclick="window.shareLocation('${{stats.name.replace(/'/g, "\\'")}}', '${{stats.level}}', [${{coordinate[0]}},${{coordinate[1]}}], ${{targetZoom}})" style="
                        background: linear-gradient(45deg, #ffd700, #ffed4a);
                        color: #000;
                        border: none;
                        padding: 8px 16px;
                        border-radius: 20px;
                        font-weight: bold;
                        cursor: pointer;
                        font-size: 12px;
                        transition: transform 0.2s ease;
                    " onmouseover="this.style.transform='scale(1.05)'" onmouseout="this.style.transform='scale(1)'">
                        🔗 Share
                    </button>
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
            
            // Level-specific sections
            if (stats.level === 'galaxy') {{
                // Zone section for galaxies (most common shot zone)
                content += `<div style="background: rgba(255,255,255,0.1); padding: 10px; border-radius: 5px; margin-bottom: 10px;">
                    <strong>📍 Zone:</strong><br>`;
                
                if (stats.shotZones.size > 0) {{
                    const topZone = Array.from(stats.shotZones.entries())
                        .sort((a, b) => b[1] - a[1])[0];
                    content += `• ${{topZone[0]}} (${{topZone[1]}} goals)<br>`;
                    if (stats.shotZones.size > 1) {{
                        const secondZone = Array.from(stats.shotZones.entries())
                            .sort((a, b) => b[1] - a[1])[1];
                        content += `• ${{secondZone[0]}} (${{secondZone[1]}} goals)<br>`;
                    }}
                }} else {{
                    content += `No zone data available<br>`;
                }}
                content += `</div>`;
                
                // Situations for galaxies
                if (stats.situations.size > 0) {{
                    const topSituations = Array.from(stats.situations.entries())
                        .sort((a, b) => b[1] - a[1])
                        .slice(0, 3);
                    content += `<div style="background: rgba(255,255,255,0.1); padding: 10px; border-radius: 5px; margin-bottom: 10px;">
                        <strong>⚡ Situations:</strong><br>`;
                    topSituations.forEach(([situation, count]) => {{
                        content += `• ${{situation}}: ${{count}}<br>`;
                    }});
                    content += `</div>`;
                }}
            }} else if (stats.level === 'cluster') {{
                // Temporal/game state sections for clusters
                if (stats.validPeriodData > 0) {{
                    content += `<div style="background: rgba(255,255,255,0.1); padding: 10px; border-radius: 5px; margin-bottom: 10px;">
                        <strong>⏰ Timing:</strong><br>`;
                    content += `Average Period: ${{stats.avgPeriod.toFixed(1)}}<br>`;
                    content += `Average Period Time: ${{stats.avgPeriodTime.toFixed(1)}} min<br>`;
                    content += `</div>`;
                }}
                
                if (stats.validScoreData > 0) {{
                    content += `<div style="background: rgba(255,255,255,0.1); padding: 10px; border-radius: 5px; margin-bottom: 10px;">
                        <strong>📊 Score Context:</strong><br>`;
                    content += `Average Score Diff: ${{stats.avgScoreDiff.toFixed(1)}}<br>`;
                    content += `</div>`;
                }}
                
                if (stats.validSeasonData > 0) {{
                    const avgSeasonDay = Math.round(stats.avgSeasonDay);
                    // Convert season day back to a readable format
                    const seasonStartDate = new Date(2023, 9, 1); // October 1, 2023 (month is 0-indexed)
                    const avgDate = new Date(seasonStartDate);
                    avgDate.setDate(avgDate.getDate() + avgSeasonDay - 1);
                    
                    const monthNames = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
                    const formattedDate = `${{monthNames[avgDate.getMonth()]}} ${{avgDate.getDate()}}`;
                    
                    content += `<div style="background: rgba(255,255,255,0.1); padding: 10px; border-radius: 5px; margin-bottom: 10px;">
                        <strong>📅 Season Timing:</strong><br>`;
                    content += `Average Date: ${{formattedDate}} (Day ${{avgSeasonDay}})<br>`;
                    content += `</div>`;
                }}
                
                // Situations for clusters
                if (stats.situations.size > 0) {{
                    const topSituations = Array.from(stats.situations.entries())
                        .sort((a, b) => b[1] - a[1])
                        .slice(0, 3);
                    content += `<div style="background: rgba(255,255,255,0.1); padding: 10px; border-radius: 5px; margin-bottom: 10px;">
                        <strong>⚡ Situations:</strong><br>`;
                    topSituations.forEach(([situation, count]) => {{
                        content += `• ${{situation}}: ${{count}}<br>`;
                    }});
                    content += `</div>`;
                }}
            }} else if (stats.level === 'solar system') {{
                // Top players and goalies for solar systems
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
                
                // Situations for solar systems
                if (stats.situations.size > 0) {{
                    const topSituations = Array.from(stats.situations.entries())
                        .sort((a, b) => b[1] - a[1])
                        .slice(0, 3);
                    content += `<div style="background: rgba(255,255,255,0.1); padding: 10px; border-radius: 5px; margin-bottom: 10px;">
                        <strong>⚡ Situations:</strong><br>`;
                    topSituations.forEach(([situation, count]) => {{
                        content += `• ${{situation}}: ${{count}}<br>`;
                    }});
                    content += `</div>`;
                }}
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
        
        // Clear and add galaxies (always visible)
        galaxyLayer.clearLayers();
        galaxyLabelLayer.clearLayers();
        console.log('Creating', galaxies.length, 'galaxy markers');
        
        galaxies.forEach((galaxy, index) => {{
            const coord = [galaxy.geometry.coordinates[1], galaxy.geometry.coordinates[0]];
            
            // Get hierarchical stats for this galaxy
            const galaxyStats = getHierarchicalStats(galaxy.properties.name, 'galaxy');
            const hierarchicalPopup = createHierarchicalPopup(galaxyStats, coord);
            
            // Galaxy marker
            const marker = L.marker(coord, {{
                icon: L.divIcon({{
                    className: 'galaxy-marker',
                    iconSize: [24, 24],
                    iconAnchor: [12, 12],
                    html: `<div data-galaxy="${{galaxy.properties.name}}" title="${{galaxy.properties.name}}"></div>`
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
        
        // Cluster viewport rendering - track which ones are rendered
        let renderedClusters = new Set();
        let clusterMarkers = new Map();
        
        function renderClustersInViewport() {{
            if (map.getZoom() < 0.5) return; // Only render at appropriate zoom
            
            const bounds = map.getBounds();
            const bufferFactor = 0.05; // Very tight buffer for aggressive culling
            const expandedBounds = bounds.pad(bufferFactor);
            
            // Limit clusters to prevent performance issues
            const MAX_CLUSTERS = /Mobi|Android/i.test(navigator.userAgent) ? 150 : 300;
            
            const clustersToAdd = [];
            const clustersToRemove = [];
            
            clusters.forEach((cluster, index) => {{
                const coord = [cluster.geometry.coordinates[1], cluster.geometry.coordinates[0]];
                const isInView = expandedBounds.contains(coord);
                
                if (isInView && !renderedClusters.has(index)) {{
                    clustersToAdd.push({{cluster, index, coord}});
                }} else if (!isInView && renderedClusters.has(index)) {{
                    clustersToRemove.push(index);
                }}
            }});
            
            // Remove out-of-view clusters
            clustersToRemove.forEach(index => {{
                const markers = clusterMarkers.get(index);
                if (markers) {{
                    clusterLayer.removeLayer(markers.marker);
                    clusterLabelLayer.removeLayer(markers.label);
                    clusterMarkers.delete(index);
                    renderedClusters.delete(index);
                }}
            }});
            
            // Limit and prioritize clusters to add (closest to center first)
            if (clustersToAdd.length > MAX_CLUSTERS) {{
                const center = map.getCenter();
                clustersToAdd.sort((a, b) => {{
                    const distA = center.distanceTo(L.latLng(a.coord));
                    const distB = center.distanceTo(L.latLng(b.coord));
                    return distA - distB;
                }});
                clustersToAdd.splice(MAX_CLUSTERS);
            }}
            
            // Add new clusters in batches
            const BATCH_SIZE = 15;
            let currentBatch = 0;
            
            function addClusterBatch() {{
                const start = currentBatch * BATCH_SIZE;
                const end = Math.min(start + BATCH_SIZE, clustersToAdd.length);
                
                for (let i = start; i < end; i++) {{
                    const {{cluster, index, coord}} = clustersToAdd[i];
                    createClusterMarkers(cluster, index, coord);
                    renderedClusters.add(index);
                }}
                
                currentBatch++;
                if (end < clustersToAdd.length) {{
                    requestAnimationFrame(addClusterBatch);
                }}
            }}
            
            if (clustersToAdd.length > 0) {{
                requestAnimationFrame(addClusterBatch);
            }}
            
            console.log(`Clusters: added ${{clustersToAdd.length}}, removed ${{clustersToRemove.length}}, total: ${{renderedClusters.size}}`);
        }}
        
        function createClusterMarkers(cluster, clusterIndex, coord) {{
            
            // Get hierarchical stats for this cluster
            const clusterStats = getHierarchicalStats(cluster.properties.name, 'cluster');
            const hierarchicalPopup = createHierarchicalPopup(clusterStats, coord);
            
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
            
            // Store markers for tracking
            clusterMarkers.set(clusterIndex, {{marker, label}});
        }}
        
        // Debounced cluster rendering
        let clusterRenderTimeout;
        let isRenderingClusters = false;
        
        function debouncedRenderClusters() {{
            if (isRenderingClusters) return;
            clearTimeout(clusterRenderTimeout);
            clusterRenderTimeout = setTimeout(() => {{
                isRenderingClusters = true;
                renderClustersInViewport();
                setTimeout(() => {{ isRenderingClusters = false; }}, 50);
            }}, 100);
        }}
        
        // Solar system viewport rendering - track which ones are rendered
        let renderedSolarSystems = new Set();
        let solarSystemMarkers = new Map();
        
        function renderSolarSystemsInViewport() {{
            if (map.getZoom() < 2.5) return; // Only render at appropriate zoom
            
            const bounds = map.getBounds();
            const bufferFactor = 0.05; // Very tight buffer for aggressive culling
            const expandedBounds = bounds.pad(bufferFactor);
            
            // Limit solar systems to prevent performance issues
            const MAX_SOLAR_SYSTEMS = /Mobi|Android/i.test(navigator.userAgent) ? 200 : 400;
            
            const systemsToAdd = [];
            const systemsToRemove = [];
            
            solarSystems.forEach((solarSystem, index) => {{
                const coord = [solarSystem.geometry.coordinates[1], solarSystem.geometry.coordinates[0]];
                const isInView = expandedBounds.contains(coord);
                
                if (isInView && !renderedSolarSystems.has(index)) {{
                    systemsToAdd.push({{solarSystem, index, coord}});
                }} else if (!isInView && renderedSolarSystems.has(index)) {{
                    systemsToRemove.push(index);
                }}
            }});
            
            // Remove out-of-view systems
            systemsToRemove.forEach(index => {{
                const markers = solarSystemMarkers.get(index);
                if (markers) {{
                    solarSystemLayer.removeLayer(markers.marker);
                    solarSystemLabelLayer.removeLayer(markers.label);
                    solarSystemMarkers.delete(index);
                    renderedSolarSystems.delete(index);
                }}
            }});
            
            // Limit and prioritize systems to add (closest to center first)
            if (systemsToAdd.length > MAX_SOLAR_SYSTEMS) {{
                const center = map.getCenter();
                systemsToAdd.sort((a, b) => {{
                    const distA = center.distanceTo(L.latLng(a.coord));
                    const distB = center.distanceTo(L.latLng(b.coord));
                    return distA - distB;
                }});
                systemsToAdd.splice(MAX_SOLAR_SYSTEMS);
            }}
            
            // Add new systems in batches
            const BATCH_SIZE = 20;
            let currentBatch = 0;
            
            function addSolarSystemBatch() {{
                const start = currentBatch * BATCH_SIZE;
                const end = Math.min(start + BATCH_SIZE, systemsToAdd.length);
                
                for (let i = start; i < end; i++) {{
                    const {{solarSystem, index, coord}} = systemsToAdd[i];
                    createSolarSystemMarkers(solarSystem, index, coord);
                    renderedSolarSystems.add(index);
                }}
                
                currentBatch++;
                if (end < systemsToAdd.length) {{
                    requestAnimationFrame(addSolarSystemBatch);
                }}
            }}
            
            if (systemsToAdd.length > 0) {{
                requestAnimationFrame(addSolarSystemBatch);
            }}
            
            console.log(`Solar systems: added ${{systemsToAdd.length}}, removed ${{systemsToRemove.length}}, total: ${{renderedSolarSystems.size}}`);
        }}
        
        function createSolarSystemMarkers(solarSystem, solarSystemIndex, coord) {{
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
                const goalies = [...new Set(starsInSystem.map(s => s.properties.goalie_name).filter(g => g && g !== 'Empty Net'))];
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
            const hierarchicalPopup = createHierarchicalPopup(solarSystemStats, coord);
            
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
            
            // Store markers for tracking
            solarSystemMarkers.set(solarSystemIndex, {{marker, label}});
        }}
        
        // Debounced solar system rendering
        let solarSystemRenderTimeout;
        let isRenderingSolarSystems = false;
        
        function debouncedRenderSolarSystems() {{
            if (isRenderingSolarSystems) return;
            clearTimeout(solarSystemRenderTimeout);
            solarSystemRenderTimeout = setTimeout(() => {{
                isRenderingSolarSystems = true;
                renderSolarSystemsInViewport();
                setTimeout(() => {{ isRenderingSolarSystems = false; }}, 50);
            }}, 100);
        }}
        
        // Solar system color mapping function
        const solarSystemColors = new Map();
        function getSolarSystemColor(solarSystem) {{
            if (!solarSystemColors.has(solarSystem)) {{
                // Generate consistent color for this solar system using a hash-based approach
                let hash = 0;
                for (let i = 0; i < solarSystem.length; i++) {{
                    const char = solarSystem.charCodeAt(i);
                    hash = ((hash << 5) - hash) + char;
                    hash = hash & hash; // Convert to 32-bit integer
                }}
                
                // Convert hash to HSL color
                const hue = Math.abs(hash) % 360;
                const saturation = 70 + (Math.abs(hash) % 30); // 70-100%
                const lightness = 50 + (Math.abs(hash) % 25); // 50-75%
                
                const color = `hsl(${{hue}}, ${{saturation}}%, ${{lightness}}%)`;
                solarSystemColors.set(solarSystem, color);
            }}
            return solarSystemColors.get(solarSystem);
        }}
        
        // Optimized star rendering with viewport culling and lazy loading
        let renderedStars = new Set();
        let starMarkers = new Map();
        
        function renderStarsInViewport() {{
            if (map.getZoom() < 3.5) return; // Only render at high zoom
            
            const bounds = map.getBounds();
            const bufferFactor = 0.1; // Much smaller buffer - aggressive culling for performance
            const expandedBounds = bounds.pad(bufferFactor);
            
            // Much lower star limits to prevent performance issues
            const MAX_STARS = /Mobi|Android/i.test(navigator.userAgent) ? 300 : 500;
            
            // At high zoom levels (5+), also filter by which solar systems are in the viewport
            // This prevents showing stars from distant solar systems
            const relevantSolarSystems = new Set();
            if (map.getZoom() >= 4.5) {{
                solarSystems.forEach(system => {{
                    const solarCoord = [system.geometry.coordinates[1], system.geometry.coordinates[0]];
                    if (expandedBounds.contains(solarCoord)) {{
                        relevantSolarSystems.add(system.properties.name);
                    }}
                }});
                
                // Debug logging for the specific case mentioned
                if (relevantSolarSystems.has('solar system_341')) {{
                    console.log(`🔍 Zoom ${{map.getZoom().toFixed(1)}}: Found ${{relevantSolarSystems.size}} solar systems in viewport:`, Array.from(relevantSolarSystems).slice(0, 10));
                }}
            }}
            
            // Collect stars to add/remove in batches
            const starsToAdd = [];
            const starsToRemove = [];
            
            stars.forEach((star, index) => {{
                const coord = [star.geometry.coordinates[1], star.geometry.coordinates[0]];
                const isInView = expandedBounds.contains(coord);
                
                // Additional filtering at high zoom: only show stars from relevant solar systems
                let shouldShow = isInView;
                if (map.getZoom() >= 4.5 && relevantSolarSystems.size > 0) {{
                    const starSolarSystem = star.properties.solar_system;
                    shouldShow = isInView && relevantSolarSystems.has(starSolarSystem);
                }}
                
                if (shouldShow && !renderedStars.has(index)) {{
                    starsToAdd.push({{star, index, coord}});
                }} else if (!shouldShow && renderedStars.has(index)) {{
                    starsToRemove.push(index);
                }}
            }});
            
            // Limit stars for performance (prioritize closer stars to center)
            if (starsToAdd.length > MAX_STARS) {{
                const center = map.getCenter();
                starsToAdd.sort((a, b) => {{
                    const distA = center.distanceTo(L.latLng(a.coord));
                    const distB = center.distanceTo(L.latLng(b.coord));
                    return distA - distB;
                }});
                starsToAdd.splice(MAX_STARS);
            }}
            
            // Remove stars in batches (fast)
            starsToRemove.forEach(index => {{
                const marker = starMarkers.get(index);
                if (marker) {{
                    starLayer.removeLayer(marker);
                    starMarkers.delete(index);
                    renderedStars.delete(index);
                }}
            }});
            
            // Add stars in smaller batches to avoid blocking UI (reduced for mobile)
            const BATCH_SIZE = 25; // Reduced from 100 for better mobile performance
            let currentBatch = 0;
            
            function addStarBatch() {{
                const start = currentBatch * BATCH_SIZE;
                const end = Math.min(start + BATCH_SIZE, starsToAdd.length);
                
                for (let i = start; i < end; i++) {{
                    const {{star, index, coord}} = starsToAdd[i];
                    // Color stars by their solar system (level_2_cluster) instead of individual color
                    const solarSystem = star.properties.level_2_cluster || star.properties.deepest_cluster?.split('.')[3] || 'unknown';
                    const clusterColor = getSolarSystemColor(solarSystem);
                    
                    const marker = L.marker(coord, {{
                        icon: L.divIcon({{
                            className: 'star-marker-optimized',
                            html: `<div class="star-dot" style="background-color: ${{clusterColor}};"></div>`,
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
                                <div style="text-align: center; margin-bottom: 15px;">
                                    <button onclick="window.shareLocation('${{(props.player_name || 'Unknown Player').replace(/'/g, "\\'")}} Goal', 'star', [${{coord[0]}},${{coord[1]}}], 5)" style="
                                        background: linear-gradient(45deg, #87ceeb, #b6e5ff);
                                        color: #000;
                                        border: none;
                                        padding: 6px 12px;
                                        border-radius: 15px;
                                        font-weight: bold;
                                        cursor: pointer;
                                        font-size: 11px;
                                        transition: transform 0.2s ease;
                                    " onmouseover="this.style.transform='scale(1.05)'" onmouseout="this.style.transform='scale(1)'">
                                        🔗 Share
                                    </button>
                                </div>
                                <div class="goal-detail">
                                    <strong>Team:</strong> <span>${{props.team_name || 'Unknown'}}</span>
                                </div>
                                <div class="goal-detail">
                                    <strong>Shot Type:</strong> <span>${{props.shot_type || 'Unknown'}}</span>
                                </div>
                                <div class="goal-detail">
                                    <strong>Situation:</strong> <span>${{props.situation || 'Unknown'}}</span>
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
                                    <strong>Goalie:</strong> <span>${{props.goalie_name || 'Empty Net'}}</span>
                                </div>
                                <div class="goal-detail">
                                    <strong>Goal Location:</strong> <span>${{props.shot_zone && props.shot_zone.trim() !== '' ? (props.goal_x !== null && props.goal_y !== null ? `${{props.shot_zone}}(x: ${{props.goal_x}}, y: ${{props.goal_y}})` : props.shot_zone) : (props.goal_x !== null && props.goal_y !== null ? `(x: ${{props.goal_x}}, y: ${{props.goal_y}})` : 'Not recorded')}}</span>
                                </div>
                                <div class="goal-detail">
                                    <strong>Solar System:</strong> <span>${{props.solar_system ? props.solar_system.split('.')[2] || props.solar_system : 'Unknown'}}</span>
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
        
        // Improved debounced star rendering with throttling
        let renderTimeout;
        let isRendering = false;
        function debouncedRenderStars() {{
            if (isRendering) return; // Skip if already rendering
            clearTimeout(renderTimeout);
            renderTimeout = setTimeout(() => {{
                isRendering = true;
                renderStarsInViewport();
                setTimeout(() => {{ isRendering = false; }}, 50);
            }}, 150); // Increased debounce for mobile
        }}
        
        
        // Set initial view to show all galaxies
        const bounds = L.latLngBounds(galaxies.map(g => [g.geometry.coordinates[1], g.geometry.coordinates[0]]));
        map.fitBounds(bounds.pad(0.4));  // Increased padding for wider initial view
        
        // Track the last stable context to avoid constant changes
        let stableContext = {{ galaxy: null, cluster: null }};
        
        // Function to find the most prominent galaxy/cluster at current view
        function getCurrentContext() {{
            const center = map.getCenter();
            const zoom = map.getZoom();
            
            let currentGalaxy = null;
            let currentCluster = null;
            let minGalaxyDistance = Infinity;
            let minClusterDistance = Infinity;
            
            // Find closest galaxy - always find one, no radius limit for now
            galaxies.forEach(galaxy => {{
                const galaxyLatLng = L.latLng(galaxy.geometry.coordinates[1], galaxy.geometry.coordinates[0]);
                const distance = center.distanceTo(galaxyLatLng);
                if (distance < minGalaxyDistance) {{
                    minGalaxyDistance = distance;
                    currentGalaxy = galaxy.properties.name;
                }}
            }});
            
            // Find closest cluster if zoomed in enough
            if (zoom >= 0.5) {{
                clusters.forEach(cluster => {{
                    const clusterLatLng = L.latLng(cluster.geometry.coordinates[1], cluster.geometry.coordinates[0]);
                    const distance = center.distanceTo(clusterLatLng);
                    if (distance < minClusterDistance) {{
                        minClusterDistance = distance;
                        currentCluster = cluster.properties.name.split('.')[1] || cluster.properties.name;
                    }}
                }});
            }}
            
            // Use stable context logic only at very high zoom
            if (zoom >= 3.5) {{
                // At high zoom, prefer stable context if we have it and it's reasonably close
                if (stableContext.galaxy && minGalaxyDistance < 100000) {{ // 100km
                    currentGalaxy = stableContext.galaxy;
                }}
                if (stableContext.cluster && minClusterDistance < 50000) {{ // 50km
                    currentCluster = stableContext.cluster;
                }}
            }}
            
            // Update stable context
            if (currentGalaxy) stableContext.galaxy = currentGalaxy;
            if (currentCluster) stableContext.cluster = currentCluster;
            
            return {{ galaxy: currentGalaxy, cluster: currentCluster }};
        }}
        
        // Function to update context bar and label fading
        function updateContextAndLabels(zoom) {{
            const context = getCurrentContext();
            const contextBar = document.getElementById('context-bar');
            const galaxyContext = document.getElementById('galaxy-context');
            const clusterContext = document.getElementById('cluster-context');
            
            // Galaxy label fading and context
            if (zoom >= 2) {{
                // Completely fade out galaxy labels and show in context bar
                galaxyLabelLayer.eachLayer(layer => {{
                    if (layer.getElement()) {{
                        layer.getElement().style.opacity = 0;
                    }}
                }});
                
                if (context.galaxy) {{
                    galaxyContext.textContent = `🌌 ${{context.galaxy}}`;
                    contextBar.classList.add('visible');
                }} else {{
                    galaxyContext.textContent = '';
                }}
            }} else {{
                // Show galaxy labels normally
                const galaxyOpacity = Math.max(0.3, Math.min(1, (2.5 - zoom) / 2));
                galaxyLabelLayer.eachLayer(layer => {{
                    if (layer.getElement()) {{
                        layer.getElement().style.opacity = galaxyOpacity;
                    }}
                }});
                galaxyContext.textContent = '';
            }}
            
            // Cluster label fading and context
            if (zoom >= 3) {{
                // Completely fade out cluster labels and show in context bar
                clusterLabelLayer.eachLayer(layer => {{
                    if (layer.getElement()) {{
                        layer.getElement().style.opacity = 0;
                    }}
                }});
                
                if (context.cluster) {{
                    clusterContext.textContent = `⭐ ${{context.cluster}}`;
                    contextBar.classList.add('visible');
                }} else {{
                    clusterContext.textContent = '';
                }}
            }} else if (zoom >= 0.5) {{
                // Show cluster labels with fading
                const clusterOpacity = Math.max(0.3, Math.min(1, (3.5 - zoom) / 2));
                clusterLabelLayer.eachLayer(layer => {{
                    if (layer.getElement()) {{
                        layer.getElement().style.opacity = clusterOpacity;
                    }}
                }});
                clusterContext.textContent = '';
            }} else {{
                clusterContext.textContent = '';
            }}
            
            // Solar system label fading - don't fade at zoom 4.5+ when viewing individual stars
            const solarSystemOpacity = zoom >= 4.5 ? 0 : 1;
            solarSystemLabelLayer.eachLayer(layer => {{
                if (layer.getElement()) {{
                    layer.getElement().style.opacity = solarSystemOpacity;
                }}
            }});
            
            // Hide context bar if no context to show
            if (!galaxyContext.textContent && !clusterContext.textContent) {{
                contextBar.classList.remove('visible');
            }}
        }}
        
        // Handle zoom-based layer visibility
        function updateLayerVisibility() {{
            const zoom = map.getZoom();
            document.getElementById('zoom-level').textContent = zoom.toFixed(1);
            
            let visibleLayers = ['Galaxies'];
            let objectCount = galaxies.length;
            
            // Show/hide clusters based on zoom level (but not at highest zoom)
            if (zoom >= 0.5 && zoom < 3.5) {{
                if (!map.hasLayer(clusterLayer)) {{
                    map.addLayer(clusterLayer);
                    map.addLayer(clusterLabelLayer);
                }}
                
                // Trigger aggressive viewport-based cluster rendering
                debouncedRenderClusters();
                
                visibleLayers.push('Clusters');
                objectCount += renderedClusters.size;
            }} else {{
                if (map.hasLayer(clusterLayer)) {{
                    map.removeLayer(clusterLayer);
                    map.removeLayer(clusterLabelLayer);
                }}
            }}
            
            // Show/hide solar systems vs stars based on zoom level
            if (zoom >= 2.5 && zoom < 4.5) {{
                // Show solar systems, hide individual stars
                if (!map.hasLayer(solarSystemLayer)) {{
                    map.addLayer(solarSystemLayer);
                    map.addLayer(solarSystemLabelLayer);
                }}
                if (map.hasLayer(starLayer)) {{
                    map.removeLayer(starLayer);
                }}
                
                // Trigger aggressive viewport-based solar system rendering
                debouncedRenderSolarSystems();
                
                visibleLayers.push('Solar Systems');
                objectCount += renderedSolarSystems.size;
                
                // Control label visibility based on zoom level
                const showLabels = zoom >= 4.0; // Only show labels at zoom 4.0+
                solarSystemLabelLayer.eachLayer(layer => {{
                    if (layer.getElement()) {{
                        layer.getElement().style.display = showLabels ? 'block' : 'none';
                    }}
                }});
            }} else if (zoom >= 4.5) {{
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
            
            // Hide galaxy markers at high zoom levels to reduce clutter
            if (zoom >= 3.5) {{
                // Hide galaxy markers when viewing individual stars
                if (map.hasLayer(galaxyLayer)) {{
                    console.log('Hiding galaxy markers at zoom', zoom);
                    map.removeLayer(galaxyLayer);
                }}
            }} else {{
                // Show galaxy markers at lower zoom levels
                if (!map.hasLayer(galaxyLayer)) {{
                    console.log('Showing galaxy markers at zoom', zoom);
                    map.addLayer(galaxyLayer);
                }}
            }}
            
            // Handle label fading and context bar updates
            updateContextAndLabels(zoom);
            
            // Update UI
            document.getElementById('visible-layers').textContent = visibleLayers.join(', ');
            document.getElementById('object-count').textContent = objectCount.toLocaleString();
        }}
        
        // Add function to clean up any rogue markers
        function cleanUpRogueMarkers() {{
            // Remove any galaxy markers that might be outside our layer management
            document.querySelectorAll('.galaxy-marker').forEach(element => {{
                // Check if this marker is properly managed by our layers
                const marker = element._leaflet_pos;
                if (marker && !galaxyLayer.hasLayer(marker)) {{
                    console.log('Found and removing rogue galaxy marker');
                    element.remove();
                }}
            }});
        }}
        
        // Consolidated event handling for better performance
        map.on('zoomend', () => {{
            updateLayerVisibility();
            cleanUpRogueMarkers();
            debouncedRenderStars();
        }});
        
        map.on('moveend', () => {{
            const zoom = map.getZoom();
            updateContextAndLabels(zoom);
            debouncedRenderStars();
            debouncedRenderSolarSystems(); // Add aggressive solar system culling
            debouncedRenderClusters(); // Add aggressive cluster culling
        }});
        
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
            
            // If it's a navigable celestial object, navigate to it
            if (playerInfo.navigable) {{
                const targetZoom = playerInfo.type === 'Galaxy' ? 0.5 : 
                                   playerInfo.type === 'Cluster' ? 2 : 
                                   playerInfo.type === 'Solar System' ? 3 : 1.5;
                navigateToLocation(playerInfo.name, playerInfo.type, playerInfo.data.coordinate, targetZoom);
            }} else {{
                drawConnectionLines();
            }}
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
            
            // Find visible components containing this player/goalie with goal counts
            const visibleComponents = [];
            const componentGoalCounts = new Map(); // Track goal count per component
            
            if (zoom >= 4.5) {{
                // Individual goals level - connect rendered stars in viewport
                relevantGoals.forEach((goal, index) => {{
                    if (renderedStars.has(stars.indexOf(goal))) {{
                        const coord = [goal.geometry.coordinates[1], goal.geometry.coordinates[0]];
                        if (bounds.contains(coord)) {{
                            const coordKey = `${{coord[0]}},${{coord[1]}}`;
                            visibleComponents.push({{coord, name: `star_${{index}}`, type: 'star'}});
                            componentGoalCounts.set(coordKey, 1); // Each star represents 1 goal
                        }}
                    }}
                }});
            }} else if (zoom >= 2.5) {{
                // Solar system level - connect solar systems containing this player in viewport
                const solarSystemGoalCounts = new Map();
                relevantGoals.forEach(goal => {{
                    const solarSystemName = goal.properties.solar_system;
                    if (solarSystemName) {{
                        solarSystemGoalCounts.set(solarSystemName, (solarSystemGoalCounts.get(solarSystemName) || 0) + 1);
                    }}
                }});
                
                solarSystems.forEach(system => {{
                    if (solarSystemGoalCounts.has(system.properties.name)) {{
                        const coord = [system.geometry.coordinates[1], system.geometry.coordinates[0]];
                        if (bounds.contains(coord)) {{
                            const coordKey = `${{coord[0]}},${{coord[1]}}`;
                            visibleComponents.push({{coord, name: system.properties.name, type: 'solar_system'}});
                            componentGoalCounts.set(coordKey, solarSystemGoalCounts.get(system.properties.name));
                        }}
                    }}
                }});
            }} else if (zoom >= 0.5) {{
                // Cluster level - connect clusters containing this player in viewport
                const clusterGoalCounts = new Map();
                relevantGoals.forEach(goal => {{
                    const clusterName = goal.properties.cluster;
                    if (clusterName) {{
                        clusterGoalCounts.set(clusterName, (clusterGoalCounts.get(clusterName) || 0) + 1);
                    }}
                }});
                
                clusters.forEach(cluster => {{
                    if (clusterGoalCounts.has(cluster.properties.name)) {{
                        const coord = [cluster.geometry.coordinates[1], cluster.geometry.coordinates[0]];
                        if (bounds.contains(coord)) {{
                            const coordKey = `${{coord[0]}},${{coord[1]}}`;
                            visibleComponents.push({{coord, name: cluster.properties.name, type: 'cluster'}});
                            componentGoalCounts.set(coordKey, clusterGoalCounts.get(cluster.properties.name));
                        }}
                    }}
                }});
            }} else {{
                // Galaxy level - connect galaxies containing this player in viewport
                const galaxyGoalCounts = new Map();
                relevantGoals.forEach(goal => {{
                    const galaxyName = goal.properties.galaxy;
                    if (galaxyName) {{
                        galaxyGoalCounts.set(galaxyName, (galaxyGoalCounts.get(galaxyName) || 0) + 1);
                    }}
                }});
                
                galaxies.forEach(galaxy => {{
                    if (galaxyGoalCounts.has(galaxy.properties.name)) {{
                        const coord = [galaxy.geometry.coordinates[1], galaxy.geometry.coordinates[0]];
                        if (bounds.contains(coord)) {{
                            const coordKey = `${{coord[0]}},${{coord[1]}}`;
                            visibleComponents.push({{coord, name: galaxy.properties.name, type: 'galaxy'}});
                            componentGoalCounts.set(coordKey, galaxyGoalCounts.get(galaxy.properties.name));
                        }}
                    }}
                }});
            }}
            
            // Draw weighted lines between visible components in viewport
            if (visibleComponents.length > 1) {{
                // Find the maximum goal count for normalization
                const maxGoals = Math.max(...Array.from(componentGoalCounts.values()));
                const minGoals = Math.min(...Array.from(componentGoalCounts.values()));
                
                for (let i = 0; i < visibleComponents.length - 1; i++) {{
                    for (let j = i + 1; j < visibleComponents.length; j++) {{
                        const coord1 = visibleComponents[i].coord;
                        const coord2 = visibleComponents[j].coord;
                        const coordKey1 = `${{coord1[0]}},${{coord1[1]}}`;
                        const coordKey2 = `${{coord2[0]}},${{coord2[1]}}`;
                        
                        const goals1 = componentGoalCounts.get(coordKey1) || 1;
                        const goals2 = componentGoalCounts.get(coordKey2) || 1;
                        
                        // Determine which end has more goals
                        const maxGoalsEnd = Math.max(goals1, goals2);
                        const minGoalsEnd = Math.min(goals1, goals2);
                        const totalGoals = goals1 + goals2;
                        
                        // Calculate weights for each end (1-8 range)
                        const maxWeight = Math.max(2, Math.min(8, 2 + (maxGoalsEnd - 1) / Math.max(1, maxGoals - 1) * 6));
                        const minWeight = Math.max(1, Math.min(maxWeight - 1, 1 + (minGoalsEnd - 1) / Math.max(1, maxGoals - 1) * 3));
                        
                        // Determine coordinate order (thick end first)
                        let startCoord, endCoord, startWeight, endWeight;
                        if (goals1 >= goals2) {{
                            startCoord = coord1;
                            endCoord = coord2;
                            startWeight = maxWeight;
                            endWeight = minWeight;
                        }} else {{
                            startCoord = coord2;
                            endCoord = coord1;
                            startWeight = maxWeight;
                            endWeight = minWeight;
                        }}
                        
                        // Calculate opacity based on goal distribution balance
                        const goalBalance = minGoalsEnd / maxGoalsEnd;
                        const baseOpacity = 0.5 + (goalBalance * 0.3); // 0.5 to 0.8 based on balance
                        
                        // Choose color based on the component types and goal counts
                        let lineColor = '#64c8ff'; // Default futuristic blue
                        if (zoom < 0.5) {{
                            lineColor = '#ff6600'; // Galaxy connections - orange
                        }} else if (zoom < 2.5) {{
                            lineColor = '#00bfff'; // Cluster connections - bright blue
                        }} else if (zoom < 4.5) {{
                            lineColor = '#cc00ff'; // Solar system connections - magenta
                        }} else {{
                            lineColor = '#00ff66'; // Star connections - green
                        }}
                        
                        // Create gradient line by drawing multiple segments
                        const segments = 8; // Number of segments for smooth gradient
                        const weightDiff = startWeight - endWeight;
                        
                        for (let seg = 0; seg < segments; seg++) {{
                            const segmentStart = seg / segments;
                            const segmentEnd = (seg + 1) / segments;
                            
                            // Interpolate coordinates
                            const segStartLat = startCoord[0] + (endCoord[0] - startCoord[0]) * segmentStart;
                            const segStartLng = startCoord[1] + (endCoord[1] - startCoord[1]) * segmentStart;
                            const segEndLat = startCoord[0] + (endCoord[0] - startCoord[0]) * segmentEnd;
                            const segEndLng = startCoord[1] + (endCoord[1] - startCoord[1]) * segmentEnd;
                            
                            // Calculate weight for this segment (linear interpolation)
                            const segmentWeight = startWeight - (weightDiff * segmentStart);
                            
                            // Calculate opacity for this segment (slightly fade towards thinner end)
                            const segmentOpacity = baseOpacity * (0.8 + 0.2 * (1 - segmentStart));
                            
                            const segment = L.polyline([
                                [segStartLat, segStartLng],
                                [segEndLat, segEndLng]
                            ], {{
                                color: lineColor,
                                weight: segmentWeight,
                                opacity: segmentOpacity,
                                dashArray: segmentWeight > 3 ? 'none' : '6, 3',
                                lineCap: 'round',
                                lineJoin: 'round'
                            }});
                            connectionLines.addLayer(segment);
                        }}
                    }}
                }}
                
                console.log(`Drew ${{connectionLines.getLayers().length}} gradient connection segments for ${{selectedPlayer.name}} (viewport only)`);
                console.log(`Goal counts per component:`, Array.from(componentGoalCounts.entries()).map(([key, count]) => `${{key.split(',')[0].slice(0,6)}}: ${{count}} goals`));
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
        
        // Handle URL parameters for shared locations
        const urlLocation = parseUrlParams();
        if (urlLocation) {{
            console.log('Navigating to shared location:', urlLocation);
            setTimeout(() => {{
                navigateToLocation(urlLocation.name, urlLocation.type, [urlLocation.lat, urlLocation.lng], urlLocation.zoom);
            }}, 1000); // Wait for map to fully initialize
        }}
        
        // Mobile UI functionality
        function initMobileUI() {{
            if (window.innerWidth <= 768) {{
                // Show mobile icons
                document.querySelector('.mobile-info-icon').style.display = 'flex';
                document.querySelector('.mobile-search-icon').style.display = 'flex';
                
                // Mobile info icon click handler
                document.querySelector('.mobile-info-icon').addEventListener('click', function() {{
                    const titlePanel = document.querySelector('.title-panel');
                    const isVisible = titlePanel.style.display === 'block';
                    
                    if (isVisible) {{
                        titlePanel.style.display = 'none';
                        this.style.background = 'rgba(10, 15, 35, 0.95)';
                    }} else {{
                        titlePanel.style.display = 'block';
                        titlePanel.style.position = 'fixed';
                        titlePanel.style.top = '70px';
                        titlePanel.style.left = '10px';
                        titlePanel.style.right = '10px';
                        titlePanel.style.zIndex = '1003';
                        this.style.background = 'rgba(100, 200, 255, 0.2)';
                        
                        // Add close button
                        if (!titlePanel.querySelector('.mobile-close-btn')) {{
                            const closeBtn = document.createElement('div');
                            closeBtn.className = 'mobile-close-btn';
                            closeBtn.innerHTML = '✕';
                            closeBtn.style.cssText = `
                                position: absolute;
                                top: 10px;
                                right: 10px;
                                width: 24px;
                                height: 24px;
                                background: rgba(255, 0, 0, 0.2);
                                border-radius: 50%;
                                display: flex;
                                align-items: center;
                                justify-content: center;
                                cursor: pointer;
                                font-size: 12px;
                                color: #ff6b6b;
                            `;
                            closeBtn.onclick = () => {{
                                titlePanel.style.display = 'none';
                                document.querySelector('.mobile-info-icon').style.background = 'rgba(10, 15, 35, 0.95)';
                            }};
                            titlePanel.appendChild(closeBtn);
                        }}
                    }}
                }});
                
                // Mobile search icon click handler
                document.querySelector('.mobile-search-icon').addEventListener('click', function() {{
                    const searchPanel = document.querySelector('.search-panel');
                    const isExpanded = searchPanel.classList.contains('mobile-expanded');
                    
                    if (isExpanded) {{
                        searchPanel.classList.remove('mobile-expanded');
                        this.style.background = 'rgba(10, 15, 35, 0.95)';
                    }} else {{
                        searchPanel.classList.add('mobile-expanded');
                        this.style.background = 'rgba(100, 200, 255, 0.2)';
                        // Focus the search input
                        setTimeout(() => {{
                            const searchInput = document.getElementById('player-search');
                            if (searchInput) searchInput.focus();
                        }}, 100);
                    }}
                }});
            }} else {{
                // Hide mobile icons on desktop
                document.querySelector('.mobile-info-icon').style.display = 'none';
                document.querySelector('.mobile-search-icon').style.display = 'none';
            }}
        }}
        
        // Mobile panel collapse functionality  
        function initMobilePanelCollapse() {{
            if (window.innerWidth <= 768) {{
                const panelTitles = document.querySelectorAll('.panel-title');
                panelTitles.forEach(title => {{
                    title.addEventListener('click', function() {{
                        const panel = this.parentElement;
                        const content = Array.from(panel.children).filter(child => child !== this);
                        const isCollapsed = content[0].style.display === 'none';
                        
                        content.forEach(element => {{
                            element.style.display = isCollapsed ? 'block' : 'none';
                        }});
                        
                        // Update arrow indicator
                        this.style.opacity = isCollapsed ? '1' : '0.7';
                        const arrow = this.querySelector('::after') || this;
                        arrow.textContent = arrow.textContent.replace(isCollapsed ? '▶' : '▼', isCollapsed ? '▼' : '▶');
                    }});
                }});
                
                // Start with some panels collapsed to save space (only legend panel since controls/zoom are hidden)
                const nonEssentialPanels = ['.legend-panel'];
                nonEssentialPanels.forEach(selector => {{
                    const panel = document.querySelector(selector);
                    if (panel) {{
                        const title = panel.querySelector('.panel-title');
                        if (title) title.click();
                    }}
                }});
            }}
        }}
        
        // Initialize mobile features
        initMobileUI(); 
        initMobilePanelCollapse();
        window.addEventListener('resize', () => {{
            initMobileUI();
            initMobilePanelCollapse();
        }});
        
        console.log('NHL Constellation Map initialized successfully!');
        console.log('Zoom levels: -1 to 0 (Galaxies), 0.5+ (+ Clusters), 2.5-4.5 (+ Solar Systems), 4.5+ (+ Individual Goals)');
        console.log('🔗 Share locations by using the "Copy Share Link" button in any celestial object popup');
        console.log('🔍 Search now supports players, goalies, galaxies, clusters, and solar systems');
    </script>
</body>
</html>'''
    
    # Write the HTML file to root directory
    output_path = 'index.html'
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