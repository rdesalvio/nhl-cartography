# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

NHL Cartography is a project that maps NHL goal locations in time and space. The project captures goal data from NHL games and visualizes their spatial and temporal patterns. The data has been parsed already and now we need to work on building the map and visulizaing the data. The overall goal is to make the data appear as if it is on a map or a star chart. There should be clusters of similar goals with perhaps named galaxies/continents and the ability to zoom in and click on each individual goal. When possible, we want to link to the url for the highlight of the goal, or even possible render it in the description of the individual point. Ideally, the visualization will include various filters which could be applied which could create "constellations". The visualization should be able to rendered in browser and will be hosted on github pages.

# Standards
- Comments are welcomed but only if necessary. I do not want to over comment the code. 
- Tests are also welcome, although not required unless stated specifically. 
- There are pieces of this project which will be done in a jupyter notebook, for those instances, we do not need testing code unless required to validate a prompt answer. 
- Correctness of data is extremely important. I do not want to misrepresent data in any way
- The project uses uv as the package manager. 

## Data Structure

The dataset is built from parsing NHL play by play data. The data is stored in data/nhl_goals.csv and includes the following fields:
 - team_id: int
 - player_id: int
 - period: int
 - time: str
 - situation_code: str
 - x: int
    - Not populated for every goal. More of a recent offering.
 - y: int
    - Not populated for every goal. More of a recent offering.
 - url: str
    - Seems to only have the option to be populated from the 20232024 season onwards
 - shot_type: str
 - goalie: str
 - home_team_defending_side: str
 - team_score: int
 - opponent_score: int
 - game_date: str


## Data Clustering
To cluster the data, a series of cluster steps were done. Many approaches were tried including clustering with a single vector, clustering with weighted values, and clustering numerical and categorical data separately. In addition, there were multiple types of clustering algorithms attempted such as KMeans, Jaccard similarity, Heirarchial, Cosine, and using LLM embedding models.

Ultimately, what I found to be the most pleasing results was using KMeans clustering on different subsets of the data in a specific sequence and using the Damerau-Levenshtein on names to judge similarity of categorical data.

The clustering process went like this:
1. Cluster goals by their x & y coordinates, shot type, and team
2. Cluster those clusters by period, the time in minutes of the goal, the time in seconds of the goal, the score of the players team, and the score of the opponent's team
3. Cluster those groups by finding the Damerau-Levenshtein distance of the player's name who scored

This process gives us a series of clusters contained in one another, resembling what a "galaxy" may look like.

## UI
A UI is built with the create_embedded_html.py script. It generates an HTML file for running a UI and stores all of the data from the GeoJSON output into that file as well. The UI allows for a user to:
- View all of the galaxies, clusters, stolar systems, and stars
- Get high level information about what each grouping represents
- Zoom in and out to get dynamically rendered stars
- View video and information about individual goals
- Search by Player Name and see all of the connections the player is in within the viewport


## Next Steps for Development
Next steps would be refine the UI, clean up any bugs, and look for new ideas. Improving performance and simplifying code is always a priority. 

Eventually, I wil rename the clusters and potentially revisit some of the clustering but I am pretty happy with that for now.

I am on the lookout for any easy to implement new ideas for the UI to make it better and make it more fun to interact with the data. Some off the cuff ideas
- How the galaxies are rendered at the most zoomed out view are pretty boring as they are just red rectangles. It might be cooler if there was a better way to show them
- Add subtle pulsing/breathing animation to active clusters
- Implement constellation lines connecting related goals within clusters
- Timeline scrubber to watch goals appear chronologically across the map
- Replace red rectangles with actual galaxy-like spirals or nebula shapes using
  CSS animations or SVG