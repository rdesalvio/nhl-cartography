import json
import os

def create_embedded_constellation_html():
    """Create an HTML file with embedded GeoJSON data in the root directory"""
    
    # Read both GeoJSON files - static for star map, original for free roam
    static_path = 'visualizations/nhl_constellation_map_static.geojson'
    original_path = 'visualizations/nhl_constellation_map.geojson'
    
    if not os.path.exists(static_path):
        print(f"Error: {static_path} not found. Run mapping_static.py first.")
        return
        
    if not os.path.exists(original_path):
        print(f"Error: {original_path} not found. Run mapping.py first.")
        return
    
    with open(static_path, 'r') as f:
        static_geojson_data = json.load(f)
        
    with open(original_path, 'r') as f:
        original_geojson_data = json.load(f)
    
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
        
        /* Mobile icons - always available but controlled by JavaScript */
        .mobile-info-icon {{
            position: fixed;
            top: 15px;
            left: 15px;
            width: 40px;
            height: 40px;
            background: rgba(10, 15, 35, 0.95);
            border: 1px solid rgba(100, 200, 255, 0.4);
            border-radius: 50%;
            display: none; /* Hidden by default, shown by JavaScript */
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
        
        .mobile-search-icon {{
            position: fixed;
            top: 15px;
            right: 15px;
            width: 40px;
            height: 40px;
            background: rgba(10, 15, 35, 0.95);
            border: 1px solid rgba(100, 200, 255, 0.4);
            border-radius: 50%;
            display: none; /* Hidden by default, shown by JavaScript */
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
        
        /* View Mode Toggle */
        .view-mode-toggle {{
            position: absolute;
            top: 20px;
            right: 20px;
            z-index: 1000;
            background: rgba(10, 15, 35, 0.95);
            border: 1px solid rgba(100, 200, 255, 0.4);
            border-radius: 8px;
            padding: 8px 16px;
            font-size: 14px;
            color: #64c8ff;
            cursor: pointer;
            transition: all 0.3s ease;
            box-shadow: 0 4px 16px rgba(0, 0, 0, 0.3);
            backdrop-filter: blur(10px);
        }}
        
        .view-mode-toggle:hover {{
            background: rgba(100, 200, 255, 0.2);
            transform: scale(1.05);
        }}
        
        /* Filter Panel for Star Map Mode */
        .filter-panel {{
            position: absolute;
            top: 20px;
            left: 20px;
            z-index: 1000;
            background: rgba(10, 15, 35, 0.95);
            border: 1px solid rgba(100, 200, 255, 0.4);
            border-radius: 12px;
            padding: 20px;
            min-width: 280px;
            max-width: 320px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
            backdrop-filter: blur(10px);
            display: none;
        }}
        
        .filter-panel.show {{
            display: block;
        }}
        
        .filter-section {{
            margin-bottom: 16px;
        }}
        
        .filter-label {{
            display: block;
            font-size: 14px;
            color: #64c8ff;
            margin-bottom: 8px;
            font-weight: 500;
        }}
        
        .filter-options {{
            display: flex;
            flex-wrap: wrap;
            gap: 6px;
        }}
        
        .filter-option {{
            background: rgba(100, 200, 255, 0.1);
            border: 1px solid rgba(100, 200, 255, 0.3);
            border-radius: 6px;
            padding: 4px 8px;
            font-size: 12px;
            color: rgba(255, 255, 255, 0.8);
            cursor: pointer;
            transition: all 0.3s ease;
            user-select: none;
        }}
        
        .filter-option.selected {{
            background: rgba(100, 200, 255, 0.3);
            border-color: rgba(100, 200, 255, 0.6);
            color: #ffffff;
        }}
        
        .filter-option:hover {{
            background: rgba(100, 200, 255, 0.2);
        }}
        
        .draw-constellation-btn {{
            width: 100%;
            background: linear-gradient(135deg, #1e40af 0%, #3b82f6 100%);
            border: none;
            border-radius: 8px;
            padding: 12px;
            color: white;
            font-size: 14px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
            margin-top: 16px;
        }}
        
        .draw-constellation-btn:hover {{
            transform: scale(1.02);
            box-shadow: 0 6px 20px rgba(59, 130, 246, 0.4);
        }}
        
        .draw-constellation-btn:disabled {{
            opacity: 0.5;
            cursor: not-allowed;
            transform: none;
        }}
        
        /* Star Map Mode Styles */
        .star-map-mode {{
            display: none;
        }}
        
        .star-map-mode.active {{
            display: block;
        }}
        
        .free-roam-mode {{
            display: block;
        }}
        
        .free-roam-mode.hidden {{
            display: none;
        }}
        
        /* Galaxy Area Shading */
        .galaxy-area {{
            fill-opacity: 0.1;
            stroke-opacity: 0.2;
            stroke-width: 2;
        }}
        
        .galaxy-label-static {{
            font-size: 16px;
            fill: rgba(255, 255, 255, 0.9);
            text-anchor: middle;
            dominant-baseline: middle;
            font-weight: 600;
            text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.8);
            pointer-events: none;
        }}
        
        /* Galaxy hover tooltip */
        .galaxy-tooltip {{
            background: rgba(10, 15, 35, 0.95);
            border: 1px solid rgba(255, 215, 0, 0.6);
            border-radius: 6px;
            color: #ffd700;
            font-size: 12px;
            font-weight: 500;
            padding: 4px 8px;
            text-align: center;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.4);
        }}

        /* Welcome Information Modal */
        .welcome-modal {{
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.8);
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 2000;
            backdrop-filter: blur(10px);
        }}
        
        .welcome-content {{
            background: linear-gradient(135deg, rgba(10, 15, 35, 0.95) 0%, rgba(15, 20, 45, 0.95) 100%);
            border: 2px solid rgba(100, 200, 255, 0.3);
            border-radius: 16px;
            padding: 30px;
            max-width: 600px;
            max-height: 80vh;
            margin: 20px;
            position: relative;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5);
            overflow-y: auto;
            
            /* Hide scrollbar while keeping scroll functionality */
            scrollbar-width: none; /* Firefox */
            -ms-overflow-style: none; /* Internet Explorer/Edge */
        }}
        
        /* Hide scrollbar for WebKit browsers (Chrome, Safari) */
        .welcome-content::-webkit-scrollbar {{
            display: none;
        }}
        
        .welcome-close {{
            position: absolute;
            top: 15px;
            right: 15px;
            width: 40px;
            height: 40px;
            background: rgba(255, 0, 0, 0.3);
            border: 2px solid rgba(255, 102, 102, 0.6);
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 18px;
            color: #ff6666;
            cursor: pointer;
            transition: all 0.3s ease;
            z-index: 2001;
            touch-action: manipulation;
        }}
        
        .welcome-close:hover {{
            background: rgba(255, 0, 0, 0.4);
            transform: scale(1.1);
        }}
        
        .welcome-title {{
            color: #64c8ff;
            font-size: 24px;
            margin-bottom: 20px;
            text-align: center;
            font-weight: 600;
        }}
        
        .welcome-text {{
            color: rgba(255, 255, 255, 0.9);
            line-height: 1.6;
            margin-bottom: 16px;
            font-size: 15px;
        }}
        
        .welcome-text:last-child {{
            margin-bottom: 0;
        }}
        
        /* Desktop info button in search panel */
        .desktop-info-btn {{
            float: right;
            cursor: pointer;
            opacity: 0.7;
            font-size: 14px;
            padding: 2px 6px;
            border-radius: 50%;
            background: rgba(100, 200, 255, 0.2);
            transition: all 0.3s ease;
        }}
        
        .desktop-info-btn:hover {{
            opacity: 1;
            background: rgba(100, 200, 255, 0.4);
            transform: scale(1.1);
        }}
        
        /* Mobile responsive layout */
        @media screen and (max-width: 768px), 
               screen and (max-height: 768px) and (hover: none) and (pointer: coarse) {{
            .title-panel {{
                display: none; /* Hidden by default on mobile */
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
                display: none !important; /* Hide legend panel on mobile */
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
            
            /* Welcome modal adjustments for mobile */
            .welcome-modal {{
                padding: 0; /* Remove padding that was causing offset */
                align-items: center; /* Center horizontally */
                justify-content: center; /* Center both ways */
                padding-top: 20px; /* Only top spacing */
                padding-bottom: 20px; /* Bottom spacing for browser UI */
            }}
            
            .welcome-content {{
                margin: 15px; /* Margin instead of modal padding for proper centering */
                padding: 50px 20px 60px 20px; /* Large top padding for close button, extra bottom for browser UI */
                max-height: 70vh; /* Further reduced height */
                font-size: 14px;
                width: calc(100vw - 30px); /* Full viewport width minus margins */
                max-width: calc(100vw - 30px); /* Ensure it doesn't exceed viewport */
                box-sizing: border-box; /* Include padding in width calculation */
            }}
            
            .welcome-title {{
                font-size: 18px;
                margin-bottom: 16px;
                margin-top: 0; /* Remove top margin since we have padding */
                line-height: 1.3;
                text-align: center;
            }}
            
            .welcome-text {{
                font-size: 13px;
                margin-bottom: 12px;
                line-height: 1.4;
            }}
            
            /* Make close button smaller and better positioned on mobile */
            .welcome-close {{
                width: 30px;
                height: 30px;
                top: 8px;
                right: 8px;
                font-size: 14px;
                font-weight: bold;
            }}
            
            /* Hide desktop info button on mobile */
            .desktop-info-btn {{
                display: none;
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

    <div class="ui-panel search-panel">
        <div class="panel-title">
            🔍 Universal Search
            <span class="desktop-info-btn" onclick="showWelcomeModal()" title="Show welcome information">ℹ️</span>
        </div>
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
    
    <div class="ui-panel controls-panel free-roam-mode">
        <div class="panel-title">Navigation Guide</div>
        <p>🔍 <strong>Zoom:</strong> Mouse wheel or +/- controls</p>
        <p>🖱️ <strong>Pan:</strong> Click and drag to explore</p>
        <p>⭐ <strong>Goals:</strong> Click stars for detailed info</p>
    </div>
    
    <div class="ui-panel legend-panel free-roam-mode">
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
            <span><strong>Solar Systems</strong> - Goalscorer + Goaltender groups</span>
        </div>
    </div>
    
    <div class="ui-panel zoom-panel free-roam-mode">
        <div class="panel-title">View Status</div>
        <div>Zoom: <span id="zoom-level" class="zoom-indicator">1.0</span></div>
        <div>Visible: <span id="visible-layers" class="visible-layers">Galaxies</span></div>
        <div>Objects: <span id="object-count" class="zoom-indicator">12</span></div>
    </div>
    
    <!-- Context bar for showing current galaxy/cluster -->
    <div id="context-bar" class="context-bar free-roam-mode">
        <span id="galaxy-context" class="galaxy-context"></span>
        <span id="cluster-context" class="cluster-context"></span>
    </div>
    
    <div id="map"></div>
    
    <!-- View Mode Toggle Button -->
    <button class="view-mode-toggle" onclick="toggleViewMode()">
        <span id="view-mode-text">Free Roam Mode</span>
    </button>
    
    <!-- Filter Panel for Star Map Mode -->
    <div class="filter-panel star-map-mode" id="filter-panel">
        <h3 style="margin-top: 0; color: #64c8ff; font-size: 16px;">Constellation Filters</h3>
        
        <div class="filter-section">
            <label class="filter-label">Shot Type</label>
            <div class="filter-options" id="shot-type-filters"></div>
        </div>
        
        <div class="filter-section">
            <label class="filter-label">Situation</label>
            <div class="filter-options" id="situation-filters"></div>
        </div>
        
        <div class="filter-section">
            <label class="filter-label">Period</label>
            <div class="filter-options" id="period-filters"></div>
        </div>
        
        <div class="filter-section">
            <label class="filter-label">Goal Zone</label>
            <div class="filter-options" id="zone-filters"></div>
        </div>
        
        <button class="draw-constellation-btn" onclick="drawConstellation()" id="draw-btn" disabled>
            Draw Constellation
        </button>
    </div>
    
    <!-- Mobile Icons (only visible on mobile) -->
    <div class="mobile-info-icon" style="display: none;">ℹ</div>
    <div class="mobile-search-icon" style="display: none;">🔍</div>
    
    <!-- Welcome Information Modal -->
    <div id="welcome-modal" class="welcome-modal">
        <div class="welcome-content">
            <div class="welcome-close" onclick="closeWelcomeModal()">✕</div>
            <div class="welcome-title">🌌 Welcome to the NHL Star Chart</div>
            <div class="welcome-text">
                Explore NHL goal data as never before! This interactive visualization maps over 16,000 goals from the 2023 NHL season+ into cosmic formations. You have two ways to explore:
            </div>
            <div class="welcome-text">
                <strong>📍 Star Map Mode (Default):</strong> View all goals as a static star chart with galaxy regions subtly shaded. Search for any player and use the filter panel to customize which goals to include, then draw their constellation connecting related goal clusters. Perfect for analyzing specific players or creating custom star patterns.
            </div>
            <div class="welcome-text">
                <strong>🚀 Free Roam Mode:</strong> Switch to the traditional zoomable exploration where you can navigate between galaxies, clusters, solar systems, and individual stars. Zoom in and out to discover the hierarchical structure of goal data and click objects to see detailed information.
            </div>
            <div class="welcome-text">
                <strong>⭐ What You'll Find:</strong> Goals are clustered by location on ice, shot type, game context, and player similarity. Similar goals form "galaxies" - grouped together like stellar formations. The names of all celestial features are determined by the goals they contain.
            </div>
            <div class="welcome-text">
                <strong>🔍 How to Use:</strong> In Star Map mode, search for a player, adjust filters (shot type, period, etc.), and click "Draw Constellation" to see their connected goals. Switch to Free Roam mode using the top-right button to explore by zooming and panning through the cosmic structure.
            </div>
            <div class="welcome-text">
                <strong>🔍 How to Interpret:</strong> Think of this map as a star chart where every NHL goal becomes a star, and similar goals
                naturally cluster together to form cosmic neighborhoods.

                <p><strong>What Makes Goals Similar?</strong><br>
                Goals are grouped based on hockey situations:
                <ul>
                    <li><strong>Where the shot came from</strong> - Goals from the slot vs. the point vs. faceoff circles</li>
                    <li><strong>How it was scored</strong> - Wrist shots, slap shots, deflections, etc.</li>
                    <li><strong>Game situation</strong> - Power play, penalty kill, even strength, empty net</li>
                    <li><strong>When it happened</strong> - Early in periods vs. late, different periods</li>
                    <li><strong>Who scored and who got beat</strong> - Similar players tend to score similar goals</li>
                </ul>
                </p>

                <p><strong>Reading the Map:</strong><br>
                The map has three levels, just like looking at the night sky with different telescopes:</p>

                <ul>
                    <li><strong>🌌 Galaxies (Red)</strong> - Broad categories like "slot shots at even strength" or "point shots on the power
                play"</li>
                    <li><strong>⭐ Clusters (Blue)</strong> - More specific situations like "first goals in the game scored in the first" or "goals in a 1-goal game scored in the 3rd period"</li>
                    <li><strong>🪐 Solar Systems (Purple)</strong> - Very specific scenarios, often involving the same goalie getting beat in
                similar ways</li>
                </ul>

                <p><strong>What This Tells You:</strong><br>
                • <em>Large formations</em> = Common NHL scoring situations<br>
                • <em>Pattern formation</em> = Some goalies get beat in similar ways which can be seen at solar system</p>
                • <em>Isolated stars</em> = Rare or spectacular goals</p>

                <p>Use the search to find your favorite player and see their "constellation" - the pattern of how and where they typically
                score!</p>
            </div>
            <div class="welcome-text">
                <strong>📚 About:</strong> This project is inspired by the fabulous <a href="https://anvaka.github.io/map-of-github">Map Of Github</a>. The code to generate this project can be found on it's github repository <a href="https://github.com/rdesalvio/nhl-cartography">nhl-cartography</a>
            </div>
        </div>
    </div>

    <!-- Leaflet JavaScript -->
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    
    <script>
        // Embedded GeoJSON data - static for star map, original for free roam
        
        // Hide loading screen once data is loaded
        document.getElementById('loading').style.display = 'none';
        
        // Welcome modal functions - defined early for immediate access
        window.closeWelcomeModal = function() {{
            console.log('Attempting to close welcome modal');
            const modal = document.getElementById('welcome-modal');
            if (modal) {{
                modal.style.display = 'none';
                localStorage.setItem('nhl-constellation-welcomed', 'true');
                console.log('Welcome modal closed successfully');
            }} else {{
                console.log('Modal element not found');
            }}
        }};
        
        function showWelcomeModal() {{
            const modal = document.getElementById('welcome-modal');
            if (modal) {{
                modal.style.display = 'flex';
                console.log('Welcome modal shown');
            }}
        }}
        
        // Set up modal event listeners after DOM is ready
        document.addEventListener('DOMContentLoaded', function() {{
            const modal = document.getElementById('welcome-modal');
            const closeBtn = document.querySelector('.welcome-close');
            
            if (modal && closeBtn) {{
                // Close button click
                closeBtn.addEventListener('click', closeWelcomeModal);
                closeBtn.addEventListener('touchstart', function(e) {{
                    e.preventDefault();
                    closeWelcomeModal();
                }});
                
                // Click outside to close
                modal.addEventListener('click', function(e) {{
                    if (e.target === modal) {{
                        closeWelcomeModal();
                    }}
                }});
                
                console.log('Modal event listeners attached');
            }}
        }});
        
        
        
        // Custom CRS for our coordinate system
        const customCRS = L.extend({{}}, L.CRS.Simple, {{
            transformation: new L.Transformation(1, 0, -1, 0)
        }});
        
        // Embedded GeoJSON data
        const STAR_MAP_DATA = {json.dumps(static_geojson_data)};
        const FREE_ROAM_DATA = {json.dumps(original_geojson_data)};
        
        // Extract different feature types for dual-mode system
        const stars = STAR_MAP_DATA.features.filter(f => f.properties.type === 'star');
        const galaxies = STAR_MAP_DATA.features.filter(f => f.properties.type === 'galaxy');
        const clusters = STAR_MAP_DATA.features.filter(f => f.properties.type === 'cluster');
        const solarSystems = STAR_MAP_DATA.features.filter(f => f.properties.type === 'solar_system');
        
        // Original hierarchical data for free roam mode
        const originalGalaxies = FREE_ROAM_DATA.features.filter(f => f.properties.type === 'galaxy');
        const originalClusters = FREE_ROAM_DATA.features.filter(f => f.properties.type === 'cluster');
        const originalSolarSystems = FREE_ROAM_DATA.features.filter(f => f.properties.type === 'solar_system');
        const originalStars = FREE_ROAM_DATA.features.filter(f => f.properties.type === 'star');
        
        // Initialize current mode before map creation
        let currentMode = 'star-map'; // Default to star map mode
        
        console.log('Data loaded:', {{
            starMapMode: {{ stars: stars.length, galaxies: galaxies.length, clusters: clusters.length, solarSystems: solarSystems.length }},
            freeRoamMode: {{ stars: originalStars.length, galaxies: originalGalaxies.length, clusters: originalClusters.length, solarSystems: originalSolarSystems.length }}
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
            fadeAnimation: true,
            closePopupOnClick: false  // Prevent closing popups when clicking on map
        }});
        
        // Global popup management
        let currentOpenPopup = null;
        let popupPersistenceEnabled = false;
        let storedPopupData = null;
        let isAutoMoving = false;
        
        // Override default popup behavior for better control
        const originalOpenPopup = map.openPopup;
        map.openPopup = function(popup, latlng, options) {{
            // Close any existing popup first to prevent multiple popups
            if (map._popup) {{
                map._explicitClose = true;
                map.closePopup();
                map._explicitClose = false;
            }}
            
            // Store reference to current popup
            const result = originalOpenPopup.call(this, popup, latlng, options);
            currentOpenPopup = map._popup;
            
            // Enable persistence in free roam mode and store popup data
            if (currentMode === 'free-roam') {{
                popupPersistenceEnabled = true;
                if (currentOpenPopup) {{
                    storedPopupData = {{
                        content: currentOpenPopup.getContent(),
                        latLng: currentOpenPopup.getLatLng(),
                        options: currentOpenPopup.options
                    }};
                }}
            }} else {{
                popupPersistenceEnabled = false;
                storedPopupData = null;
            }}
            
            return result;
        }};
        
        // Handle popup closing with persistence in free roam mode
        const originalClosePopup = map.closePopup;
        map.closePopup = function(popup) {{
            // In free roam mode, only allow explicit closes (user action)
            if (currentMode === 'free-roam' && popupPersistenceEnabled && !this._explicitClose) {{
                // Store the popup data before it gets closed
                if (map._popup && !storedPopupData) {{
                    storedPopupData = {{
                        content: map._popup.getContent(),
                        latLng: map._popup.getLatLng(),
                        options: map._popup.options
                    }};
                }}
                return this; // Ignore automatic close requests
            }}
            
            // Clear our references on explicit close
            if (this._explicitClose) {{
                currentOpenPopup = null;
                popupPersistenceEnabled = false;
                storedPopupData = null;
            }}
            
            return originalClosePopup.apply(this, arguments);
        }};
        
        // Handle map movement and popup restoration in free roam mode
        map.on('movestart autopanstart', function(e) {{
            if (currentMode === 'free-roam' && map._popup) {{
                isAutoMoving = true;
                // Store popup data if not already stored
                if (!storedPopupData) {{
                    storedPopupData = {{
                        content: map._popup.getContent(),
                        latLng: map._popup.getLatLng(),
                        options: map._popup.options
                    }};
                }}
            }}
        }});
        
        map.on('moveend autopanend', function(e) {{
            if (currentMode === 'free-roam' && isAutoMoving && storedPopupData) {{
                // Restore popup after auto-panning completes
                setTimeout(() => {{
                    if (storedPopupData && (!map._popup || !map._popup.isOpen())) {{
                        const popup = L.popup(storedPopupData.options)
                            .setLatLng(storedPopupData.latLng)
                            .setContent(storedPopupData.content);
                        map.openPopup(popup);
                    }}
                    isAutoMoving = false;
                }}, 150);
            }} else {{
                isAutoMoving = false;
            }}
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
        
        // Use static data for initial star map mode
        let currentGeojsonData = STAR_MAP_DATA;
        
        console.log('Loaded', currentGeojsonData.features.length, 'celestial objects');
        
        // Note: galaxies, clusters, solarSystems, stars already defined above from STAR_MAP_DATA
        
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
                // Trigger collision detection after batch rendering completes
                setTimeout(() => debouncedCollisionDetection(), 400);
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
                // Trigger collision detection after batch rendering completes
                setTimeout(() => debouncedCollisionDetection(), 500);
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
        
        // Label collision detection system
        function detectLabelCollisions() {{
            const currentZoom = map.getZoom();
            
            // Only apply collision detection at solar system zoom level (2.5 - 4.5)
            if (currentZoom < 2.5 || currentZoom >= 4.5) {{
                // At other zoom levels, just show all labels normally
                [galaxyLabelLayer, clusterLabelLayer, solarSystemLabelLayer].forEach(layer => {{
                    layer.eachLayer(label => {{
                        const element = label.getElement();
                        if (element) {{
                            element.style.display = 'block';
                        }}
                    }});
                }});
                return;
            }}
            
            const labels = [];
            const minDistance = 60; // Minimum distance between labels in pixels
            
            // At solar system zoom level, only collect solar system labels for collision detection
            [solarSystemLabelLayer].forEach((layer, layerIndex) => {{
                layer.eachLayer(label => {{
                    const element = label.getElement();
                    if (element && element.style.display !== 'none') {{
                        const bounds = element.getBoundingClientRect();
                        const mapBounds = map.getContainer().getBoundingClientRect();
                        
                        // Calculate position relative to map
                        const centerX = bounds.left + bounds.width/2 - mapBounds.left;
                        const centerY = bounds.top + bounds.height/2 - mapBounds.top;
                        
                        // At solar system zoom level, all labels have same base priority
                        let priority = 10;
                        let size = 40;
                        
                        // Add distance from center as secondary priority
                        const mapCenter = {{
                            x: map.getContainer().clientWidth / 2,
                            y: map.getContainer().clientHeight / 2
                        }};
                        const distanceFromCenter = Math.sqrt(
                            Math.pow(centerX - mapCenter.x, 2) + 
                            Math.pow(centerY - mapCenter.y, 2)
                        );
                        priority += Math.max(0, 50 - distanceFromCenter / 10);
                        
                        labels.push({{
                            element,
                            x: centerX,
                            y: centerY,
                            width: bounds.width || size,
                            height: bounds.height || 20,
                            priority,
                            layerType: 2 // Solar system layer
                        }});
                    }}
                }});
            }});
            
            // Sort by priority (highest first)
            labels.sort((a, b) => b.priority - a.priority);
            
            // Track occupied areas
            const occupiedAreas = [];
            
            // Check each label for collisions
            labels.forEach(label => {{
                let hasCollision = false;
                
                for (const occupied of occupiedAreas) {{
                    const dx = Math.abs(label.x - occupied.x);
                    const dy = Math.abs(label.y - occupied.y);
                    
                    // Check if labels would overlap
                    if (dx < (label.width + occupied.width) / 2 + minDistance / 2 &&
                        dy < (label.height + occupied.height) / 2 + minDistance / 2) {{
                        hasCollision = true;
                        break;
                    }}
                }}
                
                if (hasCollision) {{
                    // Hide this label due to collision
                    label.element.style.display = 'none';
                }} else {{
                    // Show this label and mark area as occupied
                    label.element.style.display = 'block';
                    occupiedAreas.push({{
                        x: label.x,
                        y: label.y,
                        width: label.width,
                        height: label.height
                    }});
                }}
            }});
            
            console.log(`Solar system label collision detection: ${{occupiedAreas.length}} labels visible, ${{labels.length - occupiedAreas.length}} hidden due to collisions`);
        }}
        
        // Debounced collision detection
        let collisionTimeout;
        function debouncedCollisionDetection() {{
            clearTimeout(collisionTimeout);
            collisionTimeout = setTimeout(detectLabelCollisions, 200);
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
        
        
        // Set initial view to show all galaxies (fallback to stars if no galaxies)
        if (galaxies.length > 0) {{
            const bounds = L.latLngBounds(galaxies.map(g => [g.geometry.coordinates[1], g.geometry.coordinates[0]]));
            map.fitBounds(bounds.pad(0.4));  // Increased padding for wider initial view
        }} else {{
            // Use star bounds as fallback for initial view
            const starBounds = L.latLngBounds(stars.map(s => [s.geometry.coordinates[1], s.geometry.coordinates[0]]));
            map.fitBounds(starBounds.pad(0.4));
        }}
        
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
                
                // Trigger collision detection for cluster labels
                setTimeout(() => debouncedCollisionDetection(), 300);
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
                
                // Trigger collision detection after visibility changes
                if (showLabels) {{
                    debouncedCollisionDetection();
                }}
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
            debouncedCollisionDetection(); // Detect and resolve label collisions
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
            
            // Handle different behaviors based on current mode
            if (currentMode === 'star-map') {{
                // In star map mode, enable constellation drawing for players
                if (playerInfo.type === 'Player' || playerInfo.type === 'Goalie') {{
                    searchPlayerStarMap(playerInfo.name);
                    console.log(`Selected ${{playerInfo.name}} for constellation in Star Map mode`);
                }} else {{
                    // For celestial objects in star map mode, just show info
                    console.log(`Selected celestial object ${{playerInfo.name}} in Star Map mode`);
                }}
            }} else {{
                // In free roam mode, use existing navigation behavior
                if (playerInfo.navigable) {{
                    const targetZoom = playerInfo.type === 'Galaxy' ? 0.5 : 
                                       playerInfo.type === 'Cluster' ? 2 : 
                                       playerInfo.type === 'Solar System' ? 3 : 1.5;
                    navigateToLocation(playerInfo.name, playerInfo.type, playerInfo.data.coordinate, targetZoom);
                }} else {{
                    drawConnectionLines();
                }}
            }}
        }}
        
        function clearSearch() {{
            selectedPlayer = null;
            searchInput.value = '';
            searchSuggestions.style.display = 'none';
            searchClear.style.display = 'none';
            searchActive.style.display = 'none';
            
            // Clear constellation in star map mode
            if (currentMode === 'star-map' && constellationLayer) {{
                constellationLayer.clearLayers();
            }}
            
            // Update filters and disable draw button
            if (currentMode === 'star-map') {{
                updateActiveFilters();
            }}
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
        
        // Simple and reliable mobile detection
        function isMobileDevice() {{
            // Check user agent for mobile devices
            const userAgent = navigator.userAgent;
            const isMobileUA = /Android|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(userAgent);
            
            // Check if it's a touch device
            const isTouchDevice = ('ontouchstart' in window) || (navigator.maxTouchPoints > 0);
            
            // Force mobile for any touch device or known mobile UA
            const isMobile = isMobileUA || isTouchDevice;
            
            console.log(`Simple mobile detection: UA=${{isMobileUA}}, Touch=${{isTouchDevice}}, Final=${{isMobile}}`);
            console.log(`UserAgent: ${{userAgent}}`);
            
            return isMobile;
        }}
        
        // Mobile UI functionality
        function initMobileUI() {{
            const infoIcon = document.querySelector('.mobile-info-icon');
            const searchIcon = document.querySelector('.mobile-search-icon');
            
            if (!infoIcon || !searchIcon) {{
                console.log('Mobile icons not found in DOM');
                return;
            }}
            
            if (isMobileDevice()) {{
                console.log('Showing mobile icons');
                // Show mobile icons
                infoIcon.style.display = 'flex';
                searchIcon.style.display = 'flex';
                
                // Mobile info icon click handler (only add if not already added)
                if (!infoIcon.hasAttribute('data-listener-added')) {{
                    infoIcon.setAttribute('data-listener-added', 'true');
                    infoIcon.addEventListener('click', function() {{
                        showWelcomeModal();
                    }});
                }}
                
                // Mobile search icon click handler (only add if not already added)
                if (!searchIcon.hasAttribute('data-listener-added')) {{
                    searchIcon.setAttribute('data-listener-added', 'true');
                    searchIcon.addEventListener('click', function() {{
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
                }}
            }} else {{
                console.log('Hiding mobile icons (desktop detected)');
                // Hide mobile icons on desktop
                infoIcon.style.display = 'none';
                searchIcon.style.display = 'none';
            }}
        }}
        
        // Mobile panel collapse functionality  
        function initMobilePanelCollapse() {{
            if (isMobileDevice()) {{
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
        
        // Initialize mobile features - defer on mobile for better performance
        if (isMobileDevice()) {{
            setTimeout(() => {{
                console.log('Initializing mobile UI after delay');
                initMobileUI(); 
                initMobilePanelCollapse();
            }}, 1000);
        }} else {{
            initMobileUI(); 
            initMobilePanelCollapse();
        }}
        
        // Handle both resize and orientation changes with debouncing
        let orientationTimeout;
        function handleOrientationChange() {{
            clearTimeout(orientationTimeout);
            orientationTimeout = setTimeout(() => {{
                console.log('Orientation/resize change detected, reinitializing mobile UI');
                // Only reinitialize if on mobile to reduce unnecessary processing
                if (isMobileDevice()) {{
                    initMobileUI();
                    initMobilePanelCollapse();
                }}
            }}, 200); // Slightly longer debounce for better performance
        }}
        
        window.addEventListener('resize', handleOrientationChange);
        window.addEventListener('orientationchange', handleOrientationChange);
        
        // Additional check after orientation change completes
        window.addEventListener('orientationchange', () => {{
            setTimeout(() => {{
                console.log('Post-orientation change check');
                initMobileUI();
            }}, 500);
        }});
        
        console.log('NHL Constellation Map initialized successfully!');
        console.log('Zoom levels: -1 to 0 (Galaxies), 0.5+ (+ Clusters), 2.5-4.5 (+ Solar Systems), 4.5+ (+ Individual Goals)');
        console.log('🔗 Share locations by using the "Copy Share Link" button in any celestial object popup');
        console.log('🔍 Search now supports players, goalies, galaxies, clusters, and solar systems');
        
        // Dual-Mode System: Star Map (default) and Free Roam
        // currentMode already declared above before map initialization
        let starMapLayer = null;
        let galaxyShadeLayer = null;
        let constellationLayer = null;
        let activeFilters = {{}};
        
        function initDualModeSystem() {{
            console.log('Initializing dual-mode system');
            
            // Hide ALL free roam layers before initializing star map
            if (galaxyLayer) map.removeLayer(galaxyLayer);
            if (galaxyLabelLayer) map.removeLayer(galaxyLabelLayer);
            if (clusterLayer) map.removeLayer(clusterLayer);
            if (clusterLabelLayer) map.removeLayer(clusterLabelLayer);
            if (solarSystemLayer) map.removeLayer(solarSystemLayer);
            if (solarSystemLabelLayer) map.removeLayer(solarSystemLabelLayer);
            if (starLayer) map.removeLayer(starLayer);
            
            // Initialize star map mode as default
            initStarMapMode();
            
            // Build filter options from data
            buildFilterOptions();
            
            // Hide free roam elements initially
            toggleElementsByClass('free-roam-mode', false);
            toggleElementsByClass('star-map-mode', true);
            
            console.log('Star Map mode activated as default - all free roam labels hidden');
        }}
        
        function toggleViewMode() {{
            if (currentMode === 'star-map') {{
                switchToFreeRoamMode();
            }} else {{
                switchToStarMapMode();
            }}
        }}
        
        function switchToStarMapMode() {{
            currentMode = 'star-map';
            document.getElementById('view-mode-text').textContent = 'Free Roam Mode';
            
            // Close any open popups when switching modes
            if (map._popup) {{
                map._explicitClose = true;
                map.closePopup();
                map._explicitClose = false;
            }}
            
            // Hide free roam elements, show star map elements
            toggleElementsByClass('free-roam-mode', false);
            toggleElementsByClass('star-map-mode', true);
            
            // Hide ALL original free roam layers for clean star map view
            if (galaxyLayer) map.removeLayer(galaxyLayer);
            if (galaxyLabelLayer) map.removeLayer(galaxyLabelLayer);
            if (clusterLayer) map.removeLayer(clusterLayer);
            if (clusterLabelLayer) map.removeLayer(clusterLabelLayer);
            if (solarSystemLayer) map.removeLayer(solarSystemLayer);
            if (solarSystemLabelLayer) map.removeLayer(solarSystemLabelLayer);
            if (starLayer) map.removeLayer(starLayer);
            
            // Clear any rendered viewport elements from free roam mode
            if (typeof renderedClusters !== 'undefined') renderedClusters.clear();
            if (typeof renderedSolarSystems !== 'undefined') renderedSolarSystems.clear();
            if (typeof renderedStars !== 'undefined') renderedStars.clear();
            if (typeof clusterMarkers !== 'undefined') clusterMarkers.clear();
            if (typeof solarSystemMarkers !== 'undefined') solarSystemMarkers.clear();
            if (typeof starMarkers !== 'undefined') starMarkers.clear();
            
            // Initialize star map if not already done
            if (!starMapLayer) {{
                initStarMapMode();
            }} else {{
                // Re-add star map layers
                map.addLayer(starMapLayer);
                map.addLayer(galaxyShadeLayer);
                map.addLayer(constellationLayer);
            }}
            
            // Reset map to show all stars
            map.setView([0, 0], -0.5);
            console.log('Switched to Star Map mode');
        }}
        
        function initializeFreeRoamRendering() {{
            // Override the existing render functions to use original hierarchical data
            // Store references to star map render functions
            const starMapRenderStars = window.debouncedRenderStars;
            const starMapRenderClusters = window.debouncedRenderClusters;
            const starMapRenderSolarSystems = window.debouncedRenderSolarSystems;
            
            // Create free roam specific render functions that work with the original data
            window.debouncedRenderStars = function() {{
                if (currentMode !== 'free-roam') return starMapRenderStars();
                
                if (isRendering) return;
                clearTimeout(renderTimeout);
                renderTimeout = setTimeout(() => {{
                    isRendering = true;
                    renderFreeRoamStarsInViewport();
                    setTimeout(() => {{ isRendering = false; }}, 50);
                }}, 150);
            }};
            
            window.debouncedRenderClusters = function() {{
                if (currentMode !== 'free-roam') return starMapRenderClusters();
                
                if (isRenderingClusters) return;
                clearTimeout(clusterRenderTimeout);
                clusterRenderTimeout = setTimeout(() => {{
                    isRenderingClusters = true;
                    renderFreeRoamClustersInViewport();
                    setTimeout(() => {{ isRenderingClusters = false; }}, 50);
                }}, 100);
            }};
            
            window.debouncedRenderSolarSystems = function() {{
                if (currentMode !== 'free-roam') return starMapRenderSolarSystems();
                
                if (isRenderingSolarSystems) return;
                clearTimeout(solarSystemRenderTimeout);
                solarSystemRenderTimeout = setTimeout(() => {{
                    isRenderingSolarSystems = true;
                    renderFreeRoamSolarSystemsInViewport();
                    setTimeout(() => {{ isRenderingSolarSystems = false; }}, 50);
                }}, 100);
            }};
        }}
        
        function generateSolarSystemColor(solarSystemName) {{
            // Generate consistent color based on solar system name using hash
            if (!solarSystemName) return '#64c8ff'; // Default color
            
            // Create a simple hash from the solar system name
            let hash = 0;
            for (let i = 0; i < solarSystemName.length; i++) {{
                const char = solarSystemName.charCodeAt(i);
                hash = ((hash << 5) - hash) + char;
                hash = hash & hash; // Convert to 32-bit integer
            }}
            
            // Use hash to generate HSL color with good saturation and lightness
            const hue = Math.abs(hash) % 360;
            const saturation = 65 + (Math.abs(hash) % 30); // 65-95% saturation
            const lightness = 50 + (Math.abs(hash) % 25); // 50-75% lightness
            
            return `hsl(${{hue}}, ${{saturation}}%, ${{lightness}}%)`;
        }}
        
        function renderFreeRoamStarsInViewport() {{
            if (map.getZoom() < 4.5) return;
            
            const bounds = map.getBounds();
            const expandedBounds = bounds.pad(0.1);
            
            // Clear existing stars
            starLayer.clearLayers();
            renderedStars.clear();
            
            let starCount = 0;
            const MAX_STARS = /Mobi|Android/i.test(navigator.userAgent) ? 500 : 1000;
            
            for (const star of originalStars) {{
                if (starCount >= MAX_STARS) break;
                
                const coords = star.geometry.coordinates;
                const latLng = L.latLng(coords[1], coords[0]);
                
                if (expandedBounds.contains(latLng)) {{
                    // Generate consistent color based on solar system
                    const solarSystemName = star.properties.solar_system;
                    const solarSystemColor = generateSolarSystemColor(solarSystemName);
                    
                    const marker = L.circleMarker(latLng, {{
                        radius: 6,  // Increased from 4 to 6 for even better clickability
                        fillColor: solarSystemColor,
                        color: 'white',
                        weight: 1.5,  // Slightly thicker border
                        opacity: 1.0,
                        fillOpacity: 0.9
                    }});
                    
                    marker.bindPopup(createDetailedStarPopup(star), {{
                        maxWidth: 450,
                        className: 'custom-popup',
                        closeOnEscapeKey: true,
                        autoPan: true
                    }});
                    starLayer.addLayer(marker);
                    renderedStars.add(star.properties.name);
                    starCount++;
                }}
            }}
        }}
        
        function renderFreeRoamClustersInViewport() {{
            if (map.getZoom() < 1.5) return;
            
            const bounds = map.getBounds();
            const expandedBounds = bounds.pad(0.1);
            
            // Clear existing clusters
            clusterLayer.clearLayers();
            clusterLabelLayer.clearLayers();
            renderedClusters.clear();
            
            let clusterCount = 0;
            const MAX_CLUSTERS = /Mobi|Android/i.test(navigator.userAgent) ? 50 : 100;
            
            for (const cluster of originalClusters) {{
                if (clusterCount >= MAX_CLUSTERS) break;
                
                const coords = cluster.geometry.coordinates;
                const latLng = L.latLng(coords[1], coords[0]);
                
                if (expandedBounds.contains(latLng)) {{
                    const marker = L.circleMarker(latLng, {{
                        radius: 8,  // Increased from 6 to 8 for better clickability
                        fillColor: '#ffd700',
                        color: 'white',
                        weight: 2,  // Thicker border
                        opacity: 1.0,
                        fillOpacity: 0.8
                    }});
                    
                    marker.bindPopup(createHierarchicalPopup(calculateClusterStats(cluster), coords), {{
                        maxWidth: 400,
                        className: 'custom-popup',
                        closeOnEscapeKey: true,
                        autoPan: true
                    }});
                    clusterLayer.addLayer(marker);
                    
                    // Add cluster label if zoom is high enough
                    if (map.getZoom() >= 2.0) {{
                        const label = L.marker(latLng, {{
                            icon: L.divIcon({{
                                className: 'cluster-label',
                                html: cluster.properties.name.split('.')[1] || 'cluster',
                                iconSize: null,
                                iconAnchor: [0, -25]
                            }})
                        }});
                        
                        // Add popup to cluster label with high-level cluster information
                        label.bindPopup(createHierarchicalPopup(calculateClusterStats(cluster), coords), {{
                            maxWidth: 400,
                            className: 'custom-popup',
                            closeOnEscapeKey: true,
                            autoPan: true
                        }});
                        
                        clusterLabelLayer.addLayer(label);
                    }}
                    
                    renderedClusters.add(cluster.properties.name);
                    clusterCount++;
                }}
            }}
        }}
        
        function renderFreeRoamSolarSystemsInViewport() {{
            if (map.getZoom() < 2.5) return;
            
            const bounds = map.getBounds();
            const expandedBounds = bounds.pad(0.1);
            
            // Clear existing solar systems
            solarSystemLayer.clearLayers();
            solarSystemLabelLayer.clearLayers();
            renderedSolarSystems.clear();
            
            let solarSystemCount = 0;
            const MAX_SOLAR_SYSTEMS = /Mobi|Android/i.test(navigator.userAgent) ? 200 : 400;
            
            for (const solarSystem of originalSolarSystems) {{
                if (solarSystemCount >= MAX_SOLAR_SYSTEMS) break;
                
                const coords = solarSystem.geometry.coordinates;
                const latLng = L.latLng(coords[1], coords[0]);
                
                if (expandedBounds.contains(latLng)) {{
                    // Generate consistent color based on solar system name (same as stars)
                    const solarSystemColor = generateSolarSystemColor(solarSystem.properties.name);
                    
                    const marker = L.circleMarker(latLng, {{
                        radius: 6,  // Increased from 4 to 6 for better clickability
                        fillColor: solarSystemColor,
                        color: 'white',
                        weight: 2,  // Thicker border
                        opacity: 1.0,
                        fillOpacity: 0.8
                    }});
                    
                    marker.bindPopup(createHierarchicalPopup(calculateSolarSystemStats(solarSystem), coords), {{
                        maxWidth: 400,
                        className: 'custom-popup',
                        closeOnEscapeKey: true,
                        autoPan: true
                    }});
                    solarSystemLayer.addLayer(marker);
                    
                    // Add label if zoom is high enough
                    if (map.getZoom() >= 4.0) {{
                        const label = L.marker(latLng, {{
                            icon: L.divIcon({{
                                className: 'solar-system-label',
                                html: solarSystem.properties.name.split('.')[2] || 'system',
                                iconSize: null,
                                iconAnchor: [0, -20]
                            }})
                        }});
                        
                        // Add popup to solar system label with high-level system information
                        label.bindPopup(createHierarchicalPopup(calculateSolarSystemStats(solarSystem), coords), {{
                            maxWidth: 400,
                            className: 'custom-popup',
                            closeOnEscapeKey: true,
                            autoPan: true
                        }});
                        
                        solarSystemLabelLayer.addLayer(label);
                    }}
                    
                    renderedSolarSystems.add(solarSystem.properties.name);
                    solarSystemCount++;
                }}
            }}
        }}
        
        function createDetailedStarPopup(star) {{
            const props = star.properties;
            
            // Format the game information
            const playerInfo = props.player_name && props.player_name !== 'Unknown' ? props.player_name : 'Unknown Player';
            const teamInfo = props.team_name && props.team_name !== 'Unknown' ? props.team_name : 'Unknown Team';
            const shotType = props.shot_type && props.shot_type !== 'Unknown' ? props.shot_type : 'Unknown';
            const goalie = props.goalie_name && props.goalie_name !== 'Unknown' ? props.goalie_name : 'Empty Net';
            const period = props.period || 'Unknown';
            const time = props.time && props.time !== 'Unknown' ? props.time : 'Unknown';
            const gameDate = props.game_date && props.game_date !== 'Unknown' ? props.game_date : 'Unknown';
            const teamScore = props.team_score !== undefined ? props.team_score : 'Unknown';
            const opponentScore = props.opponent_score !== undefined ? props.opponent_score : 'Unknown';
            
            // Coordinates
            const goalX = props.goal_x !== undefined && props.goal_x !== null ? props.goal_x.toFixed(1) : 'N/A';
            const goalY = props.goal_y !== undefined && props.goal_y !== null ? props.goal_y.toFixed(1) : 'N/A';
            
            let popupContent = `
                <div style="max-width: 440px; font-family: 'Inter', sans-serif; line-height: 1.5;">
                    <h3 style="margin: 0 0 20px 0; color: #ffd700; text-align: center; font-size: 19px; font-weight: 600;">
                        ⭐ Goal Details
                    </h3>
                    
                    <div style="background: rgba(255,255,255,0.1); padding: 18px; border-radius: 8px; margin-bottom: 16px;">
                        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; font-size: 15px;">
                            <div style="line-height: 1.6;"><strong style="color: #64c8ff;">🏒 Player:</strong><br><span style="margin-top: 6px; display: block;">${{playerInfo}}</span></div>
                            <div style="line-height: 1.6;"><strong style="color: #64c8ff;">🏴 Team:</strong><br><span style="margin-top: 6px; display: block;">${{teamInfo}}</span></div>
                        </div>
                    </div>
                    
                    <div style="background: rgba(255,255,255,0.1); padding: 18px; border-radius: 8px; margin-bottom: 16px;">
                        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; font-size: 15px;">
                            <div style="line-height: 1.6;"><strong style="color: #64c8ff;">📊 Score:</strong><br><span style="margin-top: 6px; display: block;">${{teamScore}} - ${{opponentScore}}</span></div>
                            <div style="line-height: 1.6;"><strong style="color: #64c8ff;">🎯 Shot Type:</strong><br><span style="margin-top: 6px; display: block;">${{shotType}}</span></div>
                        </div>
                        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; font-size: 15px; margin-top: 14px;">
                            <div style="line-height: 1.6;"><strong style="color: #64c8ff;">🥅 Goaltender:</strong><br><span style="margin-top: 6px; display: block;">${{goalie}}</span></div>
                            <div style="line-height: 1.6;"><strong style="color: #64c8ff;">⏰ Time:</strong><br><span style="margin-top: 6px; display: block;">P${{period}} - ${{time}}</span></div>
                        </div>
                    </div>
                    
                    <div style="background: rgba(255,255,255,0.1); padding: 18px; border-radius: 8px; margin-bottom: 16px;">
                        <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 16px; font-size: 15px;">
                            <div style="line-height: 1.6;"><strong style="color: #64c8ff;">📍 X:</strong><br><span style="margin-top: 6px; display: block;">${{goalX}}</span></div>
                            <div style="line-height: 1.6;"><strong style="color: #64c8ff;">📍 Y:</strong><br><span style="margin-top: 6px; display: block;">${{goalY}}</span></div>
                            <div style="line-height: 1.6;"><strong style="color: #64c8ff;">📅 Date:</strong><br><span style="margin-top: 6px; display: block; font-size: 13px;">${{gameDate}}</span></div>
                        </div>
                    </div>`;
            
            // Add video link if available
            if (props.url && props.url.trim() !== '' && props.url !== 'Unknown') {{
                popupContent += `
                    <div style="text-align: center; margin-top: 15px;">
                        <a href="${{props.url}}" target="_blank" style="
                            display: inline-block;
                            background: linear-gradient(45deg, #ff4444, #ff6666);
                            color: white;
                            padding: 10px 20px;
                            border-radius: 25px;
                            text-decoration: none;
                            font-weight: bold;
                            font-size: 14px;
                            transition: transform 0.2s ease, box-shadow 0.2s ease;
                            box-shadow: 0 4px 15px rgba(255, 68, 68, 0.3);
                        " onmouseover="this.style.transform='scale(1.05)'; this.style.boxShadow='0 6px 20px rgba(255, 68, 68, 0.5)';" 
                           onmouseout="this.style.transform='scale(1)'; this.style.boxShadow='0 4px 15px rgba(255, 68, 68, 0.3)';">
                            🎥 Watch Goal Highlight
                        </a>
                    </div>`;
            }}
            
            popupContent += '</div>';
            
            return popupContent;
        }}
        
        function calculateGalaxyStats(galaxy) {{
            // Calculate comprehensive stats for galaxy popup
            const galaxyStars = originalStars.filter(star => 
                star.properties.galaxy === galaxy.properties.name
            );
            
            let stats = {{
                name: galaxy.properties.name,
                level: 'galaxy',
                clusters: new Set(galaxyStars.map(star => star.properties.cluster)).size,
                solarSystems: new Set(galaxyStars.map(star => star.properties.solar_system)).size,
                stars: galaxyStars.length,
                totalGoals: galaxyStars.length,
                topPlayers: new Map(),
                topGoalies: new Map(),
                teams: new Set(),
                shotTypes: new Map(),
                periods: new Map(),
                shotZones: new Map(),
                situations: new Map(),
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
            
            // Calculate detailed stats from all stars in this galaxy
            galaxyStars.forEach(star => {{
                // Shot zones
                if (star.properties.shot_zone && star.properties.shot_zone.trim() !== '') {{
                    stats.shotZones.set(star.properties.shot_zone, (stats.shotZones.get(star.properties.shot_zone) || 0) + 1);
                }}
                
                // Shot types
                if (star.properties.shot_type) {{
                    stats.shotTypes.set(star.properties.shot_type, (stats.shotTypes.get(star.properties.shot_type) || 0) + 1);
                }}
                
                // Periods
                if (star.properties.period) {{
                    stats.periods.set(star.properties.period, (stats.periods.get(star.properties.period) || 0) + 1);
                }}
                
                // Teams
                if (star.properties.team_name) {{
                    stats.teams.add(star.properties.team_name);
                }}
                
                // Top players
                if (star.properties.player_name && star.properties.player_name !== 'Unknown') {{
                    stats.topPlayers.set(star.properties.player_name, (stats.topPlayers.get(star.properties.player_name) || 0) + 1);
                }}
                
                // Top goalies
                if (star.properties.goalie_name && star.properties.goalie_name !== 'Unknown' && star.properties.goalie_name !== 'Empty Net') {{
                    stats.topGoalies.set(star.properties.goalie_name, (stats.topGoalies.get(star.properties.goalie_name) || 0) + 1);
                }}
            }});
            
            return stats;
        }}
        
        function calculateClusterStats(cluster) {{
            // Calculate full stats for cluster popup using the same structure as getHierarchicalStats
            let stats = {{
                name: cluster.properties.name,
                level: 'cluster',
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
            
            // Get all stars in this cluster
            const clusterStars = originalStars.filter(star => 
                star.properties.cluster === cluster.properties.name
            );
            
            stats.stars = clusterStars.length;
            stats.totalGoals = clusterStars.length;
            stats.solarSystems = new Set(clusterStars.map(star => star.properties.solar_system)).size;
            
            // Calculate comprehensive stats from the stars
            clusterStars.forEach(star => {{
                // Shot zones
                if (star.properties.shot_zone && star.properties.shot_zone.trim() !== '') {{
                    stats.shotZones.set(star.properties.shot_zone, (stats.shotZones.get(star.properties.shot_zone) || 0) + 1);
                }}
                
                // Shot types
                if (star.properties.shot_type) {{
                    stats.shotTypes.set(star.properties.shot_type, (stats.shotTypes.get(star.properties.shot_type) || 0) + 1);
                }}
                
                // Periods
                if (star.properties.period) {{
                    stats.periods.set(star.properties.period, (stats.periods.get(star.properties.period) || 0) + 1);
                }}
                
                // Teams
                if (star.properties.team_name) {{
                    stats.teams.add(star.properties.team_name);
                }}
                
                // Top players in this cluster
                if (star.properties.player_name && star.properties.player_name !== 'Unknown') {{
                    stats.topPlayers.set(star.properties.player_name, (stats.topPlayers.get(star.properties.player_name) || 0) + 1);
                }}
                
                // Top goalies faced in this cluster
                if (star.properties.goalie_name && star.properties.goalie_name !== 'Unknown' && star.properties.goalie_name !== 'Empty Net') {{
                    stats.topGoalies.set(star.properties.goalie_name, (stats.topGoalies.get(star.properties.goalie_name) || 0) + 1);
                }}
                
                // Situations
                if (star.properties.situation_code && star.properties.situation_code.trim() !== '') {{
                    stats.situations.set(star.properties.situation_code, (stats.situations.get(star.properties.situation_code) || 0) + 1);
                }}
            }});
            
            return stats;
        }}
        
        function calculateSolarSystemStats(solarSystem) {{
            // Calculate full stats for solar system popup using the same structure as getHierarchicalStats
            let stats = {{
                name: solarSystem.properties.name,
                level: 'solar system',
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
            
            // Get all stars in this solar system
            const systemStars = originalStars.filter(star => 
                star.properties.solar_system === solarSystem.properties.name
            );
            
            stats.stars = systemStars.length;
            stats.totalGoals = systemStars.length;
            
            // Calculate comprehensive stats from the stars
            systemStars.forEach(star => {{
                // Shot zones
                if (star.properties.shot_zone && star.properties.shot_zone.trim() !== '') {{
                    stats.shotZones.set(star.properties.shot_zone, (stats.shotZones.get(star.properties.shot_zone) || 0) + 1);
                }}
                
                // Shot types
                if (star.properties.shot_type) {{
                    stats.shotTypes.set(star.properties.shot_type, (stats.shotTypes.get(star.properties.shot_type) || 0) + 1);
                }}
                
                // Periods
                if (star.properties.period) {{
                    stats.periods.set(star.properties.period, (stats.periods.get(star.properties.period) || 0) + 1);
                }}
                
                // Teams
                if (star.properties.team_name) {{
                    stats.teams.add(star.properties.team_name);
                }}
                
                // Top players in this solar system
                if (star.properties.player_name && star.properties.player_name !== 'Unknown') {{
                    stats.topPlayers.set(star.properties.player_name, (stats.topPlayers.get(star.properties.player_name) || 0) + 1);
                }}
                
                // Top goalies faced in this solar system
                if (star.properties.goalie_name && star.properties.goalie_name !== 'Unknown' && star.properties.goalie_name !== 'Empty Net') {{
                    stats.topGoalies.set(star.properties.goalie_name, (stats.topGoalies.get(star.properties.goalie_name) || 0) + 1);
                }}
                
                // Situations
                if (star.properties.situation_code && star.properties.situation_code.trim() !== '') {{
                    stats.situations.set(star.properties.situation_code, (stats.situations.get(star.properties.situation_code) || 0) + 1);
                }}
            }});
            
            return stats;
        }}
        
        function switchToFreeRoamMode() {{
            currentMode = 'free-roam';
            document.getElementById('view-mode-text').textContent = 'Star Map Mode';
            
            // Close any open popups when switching modes
            if (map._popup) {{
                map._explicitClose = true;
                map.closePopup();
                map._explicitClose = false;
            }}
            
            // Show free roam elements, hide star map elements
            toggleElementsByClass('free-roam-mode', true);
            toggleElementsByClass('star-map-mode', false);
            
            // Clear star map layers
            if (starMapLayer) {{
                map.removeLayer(starMapLayer);
            }}
            if (galaxyShadeLayer) {{
                map.removeLayer(galaxyShadeLayer);
            }}
            if (constellationLayer) {{
                map.removeLayer(constellationLayer);
            }}
            
            // Use embedded original GeoJSON data for free roam mode
            console.log('Switching to original GeoJSON for free roam mode...');
            
            const originalFeatures = FREE_ROAM_DATA.features;
            
            // Note: originalGalaxies, originalClusters, originalSolarSystems, originalStars already defined globally above
            
            // Update global variables temporarily for free roam mode
            window.freeRoamGalaxies = originalGalaxies;
            window.freeRoamClusters = originalClusters;
            window.freeRoamSolarSystems = originalSolarSystems;
            window.freeRoamStars = originalStars;
            
            // Restore galaxy layers with original data
            galaxyLayer.clearLayers();
            galaxyLabelLayer.clearLayers();
            
            // Re-create galaxy markers and labels from original data
            originalGalaxies.forEach(galaxy => {{
                const coord = [galaxy.geometry.coordinates[1], galaxy.geometry.coordinates[0]];
                
                const marker = L.marker(coord, {{
                    icon: L.divIcon({{
                        className: 'galaxy-marker',
                        iconSize: [24, 24],
                        iconAnchor: [12, 12],
                        html: `<div data-galaxy="${{galaxy.properties.name}}" title="${{galaxy.properties.name}}"></div>`
                    }})
                }});
                
                const label = L.marker(coord, {{
                    icon: L.divIcon({{
                        className: 'galaxy-label',
                        html: galaxy.properties.name,
                        iconSize: null,
                        iconAnchor: [0, -35]
                    }})
                }});
                
                // Add popup to galaxy label with high-level galaxy information
                label.bindPopup(createHierarchicalPopup(calculateGalaxyStats(galaxy), coord), {{
                    maxWidth: 400,
                    className: 'custom-popup',
                    closeOnEscapeKey: true,
                    autoPan: true
                }});
                
                galaxyLayer.addLayer(marker);
                galaxyLabelLayer.addLayer(label);
            }});
            
            // Add layers back to map
            map.addLayer(galaxyLayer);
            map.addLayer(galaxyLabelLayer);
            
            // Re-initialize zoom-based rendering with original data
            initializeFreeRoamRendering();
            
            // Set appropriate zoom for galaxy overview
            const bounds = L.latLngBounds(originalGalaxies.map(g => [g.geometry.coordinates[1], g.geometry.coordinates[0]]));
            map.fitBounds(bounds.pad(0.4));
            
            console.log('Free roam mode initialized with original data:', {{
                galaxies: originalGalaxies.length,
                clusters: originalClusters.length,
                solarSystems: originalSolarSystems.length,
                stars: originalStars.length
            }});
            
            console.log('Switched to Free Roam mode');
        }}
        
        function toggleElementsByClass(className, show) {{
            const elements = document.querySelectorAll(`.${{className}}`);
            elements.forEach(el => {{
                if (show) {{
                    el.style.display = el.dataset.originalDisplay || 'block';
                    el.classList.add('show');
                    el.classList.remove('hidden');
                }} else {{
                    if (!el.dataset.originalDisplay) {{
                        el.dataset.originalDisplay = getComputedStyle(el).display;
                    }}
                    el.style.display = 'none';
                    el.classList.remove('show');
                    el.classList.add('hidden');
                }}
            }});
        }}
        
        function initStarMapMode() {{
            console.log('Initializing Star Map mode');
            
            // Create star map layer group
            starMapLayer = L.layerGroup();
            galaxyShadeLayer = L.layerGroup();
            constellationLayer = L.layerGroup();
            
            // Add all stars to the map at once
            renderAllStars();
            
            // Add galaxy shading and labels
            renderGalaxyAreas();
            
            // Add layers to map
            map.addLayer(starMapLayer);
            map.addLayer(galaxyShadeLayer);
            map.addLayer(constellationLayer);
            
            // Set static view to show entire star field
            if (stars.length > 0) {{
                const allStarBounds = L.latLngBounds(stars.map(s => [s.geometry.coordinates[1], s.geometry.coordinates[0]]));
                map.fitBounds(allStarBounds.pad(0.1));
            }} else {{
                // Fallback if no stars
                map.setView([0, 0], 2);
            }}
            
            console.log(`Star Map initialized with ${{stars.length}} stars`);
        }}
        
        function renderAllStars() {{
            console.log('Rendering all stars for static map');
            
            stars.forEach(star => {{
                const coord = [star.geometry.coordinates[1], star.geometry.coordinates[0]];
                
                // Create star marker
                const marker = L.circleMarker(coord, {{
                    radius: 2,
                    fillColor: star.properties.cluster_color || '#64c8ff',
                    color: 'none',
                    fillOpacity: 0.8,
                    weight: 0
                }});
                
                // Add popup with goal details
                const popupContent = `
                    <div class="custom-popup">
                        <h3>${{star.properties.player_name}}</h3>
                        <p><strong>Team:</strong> ${{star.properties.team_name}}</p>
                        <p><strong>Shot Type:</strong> ${{star.properties.shot_type}}</p>
                        <p><strong>Period:</strong> ${{star.properties.period}}</p>
                        <p><strong>Time:</strong> ${{star.properties.time}}</p>
                        <p><strong>Date:</strong> ${{star.properties.game_date}}</p>
                        ${{star.properties.url ? `<p><a href="${{star.properties.url}}" target="_blank">🎥 Watch Goal</a></p>` : ''}}
                    </div>
                `;
                
                marker.bindPopup(popupContent);
                starMapLayer.addLayer(marker);
            }});
        }}
        
        function renderGalaxyAreas() {{
            console.log('Rendering galaxy areas and smart labels');
            
            // Group stars by galaxy to calculate bounds and counts
            const galaxyGroups = {{}};
            stars.forEach(star => {{
                const galaxyName = star.properties.galaxy;
                if (!galaxyGroups[galaxyName]) {{
                    galaxyGroups[galaxyName] = {{
                        stars: [],
                        color: star.properties.cluster_color || '#64c8ff'
                    }};
                }}
                galaxyGroups[galaxyName].stars.push(star);
            }});
            
            // Render each galaxy area with hover functionality
            Object.entries(galaxyGroups).forEach(([galaxyName, group]) => {{
                const coords = group.stars.map(s => [s.geometry.coordinates[1], s.geometry.coordinates[0]]);
                
                if (coords.length > 2) {{
                    // Create convex hull for galaxy boundary
                    const hull = getConvexHull(coords);
                    
                    if (hull.length > 2) {{
                        // Create polygon for galaxy area with hover tooltip
                        const galaxyPolygon = L.polygon(hull, {{
                            color: group.color,
                            fillColor: group.color,
                            className: 'galaxy-area'
                        }});
                        
                        // Add hover tooltip showing galaxy name and star count
                        galaxyPolygon.bindTooltip(`${{galaxyName}}<br>${{group.stars.length}} goals`, {{
                            permanent: false,
                            direction: 'center',
                            className: 'galaxy-tooltip'
                        }});
                        
                        galaxyShadeLayer.addLayer(galaxyPolygon);
                    }}
                }}
            }});
            
            // Smart galaxy label rendering with overlap prevention
            renderSmartGalaxyLabels(galaxyGroups);
        }}
        
        function renderSmartGalaxyLabels(galaxyGroups) {{
            console.log('Rendering smart galaxy labels with overlap prevention');
            
            // Calculate label data for all galaxies
            const labelData = Object.entries(galaxyGroups).map(([galaxyName, group]) => {{
                const coords = group.stars.map(s => [s.geometry.coordinates[1], s.geometry.coordinates[0]]);
                const center = getPolygonCenter(coords);
                const starCount = group.stars.length;
                const fontSize = Math.max(12, Math.min(24, 12 + Math.log(starCount) * 2));
                
                return {{
                    name: galaxyName,
                    center: center,
                    starCount: starCount,
                    fontSize: fontSize,
                    bounds: calculateTextBounds(center, galaxyName, fontSize)
                }};
            }});
            
            // Sort by star count (larger galaxies get priority)
            labelData.sort((a, b) => b.starCount - a.starCount);
            
            const renderedLabels = [];
            const labelSpacing = 20; // Minimum pixels between labels
            
            labelData.forEach(labelInfo => {{
                let canRender = true;
                
                // Check for overlaps with already rendered labels
                for (const rendered of renderedLabels) {{
                    if (labelsOverlap(labelInfo.bounds, rendered.bounds, labelSpacing)) {{
                        canRender = false;
                        break;
                    }}
                }}
                
                if (canRender) {{
                    // Create and add the label
                    const galaxyLabel = L.marker(labelInfo.center, {{
                        icon: L.divIcon({{
                            className: 'galaxy-label-static',
                            html: labelInfo.name,
                            iconSize: null,
                            iconAnchor: [0, 0]
                        }})
                    }});
                    
                    // Apply dynamic font size
                    galaxyLabel.on('add', function() {{
                        const labelElement = this.getElement();
                        if (labelElement) {{
                            labelElement.style.fontSize = `${{labelInfo.fontSize}}px`;
                        }}
                    }});
                    
                    galaxyShadeLayer.addLayer(galaxyLabel);
                    renderedLabels.push(labelInfo);
                }}
            }});
            
            console.log(`Rendered ${{renderedLabels.length}} non-overlapping galaxy labels out of ${{labelData.length}} total galaxies`);
        }}
        
        function calculateTextBounds(center, text, fontSize) {{
            // Approximate text bounds based on font size and text length
            const charWidth = fontSize * 0.6; // Rough character width
            const textWidth = text.length * charWidth;
            const textHeight = fontSize * 1.2; // Line height
            
            return {{
                left: center[1] - textWidth / 2,
                right: center[1] + textWidth / 2,
                top: center[0] - textHeight / 2,
                bottom: center[0] + textHeight / 2
            }};
        }}
        
        function labelsOverlap(bounds1, bounds2, spacing) {{
            // Check if two label bounds overlap with spacing buffer
            return !(bounds1.right + spacing < bounds2.left || 
                    bounds2.right + spacing < bounds1.left || 
                    bounds1.bottom + spacing < bounds2.top || 
                    bounds2.bottom + spacing < bounds1.top);
        }}
        
        function getConvexHull(points) {{
            // Simple convex hull algorithm (gift wrapping)
            if (points.length < 3) return points;
            
            // Find the leftmost point
            let leftmost = 0;
            for (let i = 1; i < points.length; i++) {{
                if (points[i][1] < points[leftmost][1] || 
                    (points[i][1] === points[leftmost][1] && points[i][0] < points[leftmost][0])) {{
                    leftmost = i;
                }}
            }}
            
            const hull = [];
            let current = leftmost;
            
            do {{
                hull.push(points[current]);
                let next = (current + 1) % points.length;
                
                for (let i = 0; i < points.length; i++) {{
                    if (orientation(points[current], points[i], points[next]) === 2) {{
                        next = i;
                    }}
                }}
                
                current = next;
            }} while (current !== leftmost);
            
            return hull;
        }}
        
        function orientation(p, q, r) {{
            const val = (q[0] - p[0]) * (r[1] - q[1]) - (q[1] - p[1]) * (r[0] - q[0]);
            if (val === 0) return 0;
            return val > 0 ? 1 : 2;
        }}
        
        function getPolygonCenter(coords) {{
            let lat = 0, lng = 0;
            coords.forEach(coord => {{
                lat += coord[0];
                lng += coord[1];
            }});
            return [lat / coords.length, lng / coords.length];
        }}
        
        function createDynamicConstellation(clusterCenters) {{
            const points = clusterCenters.map(c => ({{ 
                x: c.center[1], y: c.center[0], cluster: c 
            }}));
            
            // Analyze the spatial distribution to choose constellation pattern
            const analysis = analyzeClusterDistribution(points);
            
            if (analysis.pattern === 'linear') {{
                // Create a snake-like pattern following the linear arrangement
                return createLinearConstellation(points);
            }} else if (analysis.pattern === 'branched') {{
                // Create a tree-like or cross pattern
                return createBranchedConstellation(points);
            }} else if (analysis.pattern === 'clustered') {{
                // Create grouped sub-constellations
                return createClusteredConstellation(points);
            }} else {{
                // Default to enhanced circular/polygonal pattern
                return createPolygonalConstellation(points);
            }}
        }}
        
        function analyzeClusterDistribution(points) {{
            if (points.length < 4) {{
                return {{ pattern: 'simple' }};
            }}
            
            // Calculate distances and spread
            const distances = [];
            const center = {{ 
                x: points.reduce((sum, p) => sum + p.x, 0) / points.length,
                y: points.reduce((sum, p) => sum + p.y, 0) / points.length
            }};
            
            points.forEach(p => {{
                distances.push(distance(p, center));
            }});
            
            const avgDistance = distances.reduce((sum, d) => sum + d, 0) / distances.length;
            const maxDistance = Math.max(...distances);
            const minDistance = Math.min(...distances);
            
            // Check for linear arrangement
            const isLinear = checkLinearArrangement(points);
            if (isLinear) {{
                return {{ pattern: 'linear' }};
            }}
            
            // Check for branched pattern (points far from center)
            const farPoints = distances.filter(d => d > avgDistance * 1.5).length;
            if (farPoints >= 2 && points.length >= 5) {{
                return {{ pattern: 'branched' }};
            }}
            
            // Check for clustered groups
            const spreadRatio = maxDistance / (minDistance + 0.1);
            if (spreadRatio > 3 && points.length >= 6) {{
                return {{ pattern: 'clustered' }};
            }}
            
            return {{ pattern: 'polygonal' }};
        }}
        
        function createLinearConstellation(points) {{
            // Sort points to create a flowing line
            const sorted = [...points].sort((a, b) => a.x - b.x);
            const coords = sorted.map(p => [p.y, p.x]);
            coords.push(sorted[0] && [sorted[0].y, sorted[0].x]); // Close if enough spread
            
            return {{ type: 'outline', coords }};
        }}
        
        function createBranchedConstellation(points) {{
            // Find central point and create branches
            const center = points.reduce((avg, p) => ({{
                x: avg.x + p.x / points.length,
                y: avg.y + p.y / points.length
            }}), {{ x: 0, y: 0 }});
            
            const centralPoint = points.reduce((closest, p) => 
                distance(p, center) < distance(closest, center) ? p : closest
            );
            
            // Create lines from center to other significant points
            const lines = [];
            const sortedByDistance = [...points]
                .filter(p => p !== centralPoint)
                .sort((a, b) => distance(b, center) - distance(a, center));
            
            // Connect to 3-4 furthest points to create branches
            const branchCount = Math.min(4, Math.max(2, Math.floor(points.length / 2)));
            for (let i = 0; i < branchCount; i++) {{
                if (sortedByDistance[i]) {{
                    lines.push({{
                        coords: [[centralPoint.y, centralPoint.x], [sortedByDistance[i].y, sortedByDistance[i].x]],
                        weight: 4 - i * 0.5 // Thicker lines for primary branches
                    }});
                }}
            }}
            
            return {{ type: 'lines', lines }};
        }}
        
        function createClusteredConstellation(points) {{
            // Create interconnected clusters
            const lines = [];
            
            // Sort by distance from center
            const center = {{ 
                x: points.reduce((sum, p) => sum + p.x, 0) / points.length,
                y: points.reduce((sum, p) => sum + p.y, 0) / points.length
            }};
            
            const sorted = [...points].sort((a, b) => distance(a, center) - distance(b, center));
            
            // Connect each point to 1-2 nearest neighbors
            sorted.forEach((point, i) => {{
                const nearestNeighbors = sorted
                    .filter((p, j) => j !== i)
                    .sort((a, b) => distance(point, a) - distance(point, b))
                    .slice(0, 2);
                
                nearestNeighbors.forEach(neighbor => {{
                    lines.push({{
                        coords: [[point.y, point.x], [neighbor.y, neighbor.x]],
                        weight: 3
                    }});
                }});
            }});
            
            // Remove duplicate lines
            const uniqueLines = lines.filter((line, i) => {{
                return !lines.slice(0, i).some(existing => 
                    (existing.coords[0][0] === line.coords[1][0] && existing.coords[0][1] === line.coords[1][1] &&
                     existing.coords[1][0] === line.coords[0][0] && existing.coords[1][1] === line.coords[0][1])
                );
            }});
            
            return {{ type: 'lines', lines: uniqueLines.slice(0, points.length) }};
        }}
        
        function createPolygonalConstellation(points) {{
            // Enhanced polygonal approach - not just convex hull
            if (points.length === 3) {{
                const coords = points.map(p => [p.y, p.x]);
                coords.push(coords[0]); // Close triangle
                return {{ type: 'outline', coords }};
            }}
            
            // For 4+ points, create more interesting shapes
            const sorted = [...points].sort((a, b) => {{
                const centerX = points.reduce((sum, p) => sum + p.x, 0) / points.length;
                const centerY = points.reduce((sum, p) => sum + p.y, 0) / points.length;
                
                const angleA = Math.atan2(a.y - centerY, a.x - centerX);
                const angleB = Math.atan2(b.y - centerY, b.x - centerX);
                return angleA - angleB;
            }});
            
            const coords = sorted.map(p => [p.y, p.x]);
            coords.push(sorted[0] && [sorted[0].y, sorted[0].x]); // Close shape
            
            return {{ type: 'outline', coords }};
        }}
        
        function checkLinearArrangement(points) {{
            if (points.length < 4) return false;
            
            // Check if points roughly form a line
            const sorted = [...points].sort((a, b) => a.x - b.x);
            let linearScore = 0;
            
            for (let i = 1; i < sorted.length - 1; i++) {{
                const prev = sorted[i - 1];
                const curr = sorted[i];
                const next = sorted[i + 1];
                
                // Calculate how much the middle point deviates from the line
                const expectedY = prev.y + (next.y - prev.y) * (curr.x - prev.x) / (next.x - prev.x);
                const deviation = Math.abs(curr.y - expectedY);
                const maxDeviation = Math.abs(next.y - prev.y) * 0.3; // Allow 30% deviation
                
                if (deviation <= maxDeviation) {{
                    linearScore++;
                }}
            }}
            
            return linearScore >= (sorted.length - 2) * 0.6; // 60% of points should be roughly linear
        }}
        
        function crossProduct(o, a, b) {{
            return (a.x - o.x) * (b.y - o.y) - (a.y - o.y) * (b.x - o.x);
        }}
        
        function distance(a, b) {{
            return Math.sqrt((a.x - b.x) ** 2 + (a.y - b.y) ** 2);
        }}
        
        // Filter and Constellation Drawing System
        function buildFilterOptions() {{
            console.log('Building filter options from data');
            
            // Extract unique values for each filter category
            const filterData = {{
                shotTypes: new Set(),
                situations: new Set(),
                periods: new Set(),
                zones: new Set()
            }};
            
            stars.forEach(star => {{
                if (star.properties.shot_type) filterData.shotTypes.add(star.properties.shot_type);
                if (star.properties.situation_code) filterData.situations.add(star.properties.situation_code);
                if (star.properties.period) filterData.periods.add(star.properties.period.toString());
                if (star.properties.goal_x !== undefined && star.properties.goal_y !== undefined) {{
                    const zone = getGoalZone(star.properties.goal_x, star.properties.goal_y);
                    if (zone) filterData.zones.add(zone);
                }}
            }});
            
            // Build filter UI
            buildFilterSection('shot-type-filters', Array.from(filterData.shotTypes).sort());
            buildFilterSection('situation-filters', Array.from(filterData.situations).sort());
            buildFilterSection('period-filters', Array.from(filterData.periods).sort((a, b) => parseInt(a) - parseInt(b)));
            buildFilterSection('zone-filters', Array.from(filterData.zones).sort());
            
            // Initialize all filters as selected
            initializeFilters();
            
            console.log('Filter options built:', {{
                shotTypes: filterData.shotTypes.size,
                situations: filterData.situations.size,
                periods: filterData.periods.size,
                zones: filterData.zones.size
            }});
        }}
        
        function getGoalZone(x, y) {{
            // Simple zone classification based on coordinates
            if (!x || !y) return null;
            
            const absX = Math.abs(x);
            const absY = Math.abs(y);
            
            if (absX < 20 && absY < 15) return 'Slot';
            if (absX < 30 && absY < 20) return 'Near';
            if (absX > 50) return 'Long Range';
            if (absY > 30) return 'Wide Angle';
            return 'Mid Range';
        }}
        
        function buildFilterSection(containerId, options) {{
            const container = document.getElementById(containerId);
            if (!container) return;
            
            container.innerHTML = '';
            
            options.forEach(option => {{
                const filterElement = document.createElement('div');
                filterElement.className = 'filter-option selected';
                filterElement.textContent = option;
                filterElement.dataset.value = option;
                
                filterElement.addEventListener('click', function() {{
                    this.classList.toggle('selected');
                    updateActiveFilters();
                }});
                
                container.appendChild(filterElement);
            }});
        }}
        
        function initializeFilters() {{
            // Set all filter options as selected by default
            const allOptions = document.querySelectorAll('.filter-option');
            allOptions.forEach(option => {{
                option.classList.add('selected');
            }});
            
            updateActiveFilters();
        }}
        
        function updateActiveFilters() {{
            activeFilters = {{
                shotTypes: getSelectedValues('shot-type-filters'),
                situations: getSelectedValues('situation-filters'),
                periods: getSelectedValues('period-filters'),
                zones: getSelectedValues('zone-filters')
            }};
            
            // Enable/disable draw button based on whether a player is selected
            const drawBtn = document.getElementById('draw-btn');
            if (selectedPlayer && Object.values(activeFilters).some(arr => arr.length > 0)) {{
                drawBtn.disabled = false;
            }} else {{
                drawBtn.disabled = true;
            }}
            
            console.log('Active filters updated:', activeFilters);
        }}
        
        function getSelectedValues(containerId) {{
            const container = document.getElementById(containerId);
            if (!container) return [];
            
            const selectedOptions = container.querySelectorAll('.filter-option.selected');
            return Array.from(selectedOptions).map(option => option.dataset.value);
        }}
        
        function drawConstellation() {{
            if (!selectedPlayer || currentMode !== 'star-map') return;
            
            console.log(`Drawing constellation for ${{selectedPlayer.name}} with filters:`, activeFilters);
            
            // Clear existing constellation
            constellationLayer.clearLayers();
            
            // Filter goals based on active filters
            const filteredGoals = stars.filter(star => {{
                if (star.properties.player_name !== selectedPlayer.name) return false;
                
                // Apply filters
                if (activeFilters.shotTypes.length > 0 && !activeFilters.shotTypes.includes(star.properties.shot_type)) return false;
                if (activeFilters.situations.length > 0 && !activeFilters.situations.includes(star.properties.situation_code)) return false;
                if (activeFilters.periods.length > 0 && !activeFilters.periods.includes(star.properties.period.toString())) return false;
                
                if (activeFilters.zones.length > 0) {{
                    const zone = getGoalZone(star.properties.goal_x, star.properties.goal_y);
                    if (!activeFilters.zones.includes(zone)) return false;
                }}
                
                return true;
            }});
            
            if (filteredGoals.length === 0) {{
                console.log('No goals match the current filters');
                return;
            }}
            
            // Group goals by cluster for smoother constellation lines
            const clusterGroups = {{}};
            filteredGoals.forEach(goal => {{
                const clusterName = goal.properties.cluster;
                if (!clusterGroups[clusterName]) {{
                    clusterGroups[clusterName] = {{
                        goals: [],
                        center: null,
                        goalCount: 0
                    }};
                }}
                clusterGroups[clusterName].goals.push(goal);
                clusterGroups[clusterName].goalCount++;
            }});
            
            // Calculate cluster centers
            Object.values(clusterGroups).forEach(cluster => {{
                const coords = cluster.goals.map(g => [g.geometry.coordinates[1], g.geometry.coordinates[0]]);
                cluster.center = getPolygonCenter(coords);
            }});
            
            // Draw constellation outline connecting clusters in order
            const clusterCenters = Object.values(clusterGroups);
            
            if (clusterCenters.length > 1) {{
                // Sort clusters by goal count (highest first) for consistent ordering
                clusterCenters.sort((a, b) => b.goalCount - a.goalCount);
                
                const maxGoals = clusterCenters[0].goalCount;
                
                if (clusterCenters.length === 2) {{
                    // Simple line between two clusters
                    const line = L.polyline([clusterCenters[0].center, clusterCenters[1].center], {{
                        color: '#ffd700',
                        weight: 4,
                        opacity: 0.8,
                        className: 'constellation-line'
                    }});
                    constellationLayer.addLayer(line);
                }} else if (clusterCenters.length >= 3) {{
                    // Create dynamic constellation shape based on cluster distribution
                    const constellationShape = createDynamicConstellation(clusterCenters);
                    
                    if (constellationShape.type === 'lines') {{
                        // Draw individual connecting lines for complex patterns
                        constellationShape.lines.forEach(line => {{
                            const polyline = L.polyline(line.coords, {{
                                color: '#ffd700',
                                weight: line.weight,
                                opacity: 0.8,
                                className: 'constellation-line'
                            }});
                            constellationLayer.addLayer(polyline);
                        }});
                    }} else {{
                        // Draw closed outline shape
                        const constellation = L.polyline(constellationShape.coords, {{
                            color: '#ffd700',
                            weight: 3,
                            opacity: 0.8,
                            className: 'constellation-line'
                        }});
                        constellationLayer.addLayer(constellation);
                    }}
                }}
                
                // Highlight all cluster centers
                clusterCenters.forEach((cluster, index) => {{
                    const size = index === 0 ? 6 : 4; // Largest cluster gets bigger marker
                    const highlight = L.circleMarker(cluster.center, {{
                        radius: size,
                        fillColor: '#ffd700',
                        color: '#ffffff',
                        fillOpacity: 0.9,
                        weight: 2
                    }});
                    
                    constellationLayer.addLayer(highlight);
                }});
            }}
            
            // Highlight the filtered goals
            filteredGoals.forEach(goal => {{
                const coord = [goal.geometry.coordinates[1], goal.geometry.coordinates[0]];
                const highlight = L.circleMarker(coord, {{
                    radius: 4,
                    fillColor: '#ffff00',
                    color: '#ffffff',
                    fillOpacity: 0.9,
                    weight: 2
                }});
                
                constellationLayer.addLayer(highlight);
            }});
            
            console.log(`Constellation drawn with ${{filteredGoals.length}} goals across ${{Object.keys(clusterGroups).length}} clusters`);
        }}
        
        // Override search functionality to work with star map mode
        function searchPlayerStarMap(playerName) {{
            selectedPlayer = {{ name: playerName }};
            
            // Enable draw button if filters are active
            updateActiveFilters();
            
            console.log(`Player selected for constellation: ${{playerName}}`);
        }}

        // Initialize the dual-mode system
        initDualModeSystem();
        
        // Show welcome modal on first visit - after map is fully initialized
        if (!localStorage.getItem('nhl-constellation-welcomed')) {{
            // Use longer delay on mobile devices for better performance
            const delay = isMobileDevice() ? 2000 : 500;
            setTimeout(() => {{
                console.log(`Showing welcome modal after full initialization (delay: ${{delay}}ms)`);
                showWelcomeModal();
            }}, delay);
        }}
    </script>
</body>
</html>'''
    
    # Write the HTML file to root directory
    output_path = 'index.html'
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"✅ Created interactive constellation map: {output_path}")
    print(f"📊 Embedded {len(static_geojson_data['features'])} celestial objects")
    print(f"🌌 {len([f for f in static_geojson_data['features'] if f['properties']['type'] == 'galaxy'])} galaxies")
    print(f"⭐ {len([f for f in static_geojson_data['features'] if f['properties']['type'] == 'cluster'])} clusters") 
    print(f"🪐 {len([f for f in static_geojson_data['features'] if f['properties']['type'] == 'solar_system'])} solar systems")
    print(f"🌟 {len([f for f in static_geojson_data['features'] if f['properties']['type'] == 'star'])} stars")
    print(f"🚀 Open {output_path} in Chrome to explore!")

if __name__ == "__main__":
    create_embedded_constellation_html()