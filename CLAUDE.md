# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

NHL Cartography is a project that maps NHL goal locations in time and space. The project captures goal data from NHL games and visualizes their spatial and temporal patterns. The data has been parsed already and now we need to work on building the map and visulizaing the data. The overall goal is to make the data appear as if it is on a map or a star chart. There should be clusters of similar goals with perhaps named galaxies/continents and the ability to zoom in and click on each individual goal. When possible, we want to link to the url for the highlight of the goal, or even possible render it in the description of the individual point. Ideally, the visualization will include various filters which could be applied which could create "constellations". The visualization should be able to rendered in browser and will be hosted on github pages.

# Standards
- Comments are welcomed but only if necessary. I do not want to over comment the code. 
- Tests are also welcome, although not required unless stated specifically. 
- There are pieces of this project which will be done in a jupyter notebook, for those instances, we do not need testing code unless required to validate a prompt answer. 
- Correctness of data is extremely important. I do not want to misrepresent data in any way

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

## Next Steps for Development
Now that we have the goals clustered adequately, we have to create a map from these clusters. We can use [maplibre](https://github.com/maplibre/maplibre-gl-js) for generting the map in browser. From there, we convert the data into GeoJSON format, generate tiles with [tippecanoe](https://github.com/mapbox/tippecanoe) and configure the browsing experience.

In order to get to GeoJSON format, we have to assign each goal a point in space. We need to figure out how to do this as I am unsure how to go from clusters to a laid out space.