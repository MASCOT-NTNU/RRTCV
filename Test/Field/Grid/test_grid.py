import pandas as pd

from GOOGLE.Field.Grid.gridWithinPolygonGenerator import GridGenerator
from usr_func import *

PATH_OPERATION_AREA = "/Users/yaoling/OneDrive - NTNU/MASCOT_PhD/Projects/GOOGLE/Config/OpArea.csv"
PATH_MUNKHOLMEN = "/Users/yaoling/OneDrive - NTNU/MASCOT_PhD/Projects/GOOGLE/Config/Munkholmen.csv"
DISTANCE_LATERAL = 150

polygon = pd.read_csv(PATH_OPERATION_AREA).to_numpy()
munkholmen = pd.read_csv(PATH_MUNKHOLMEN).to_numpy()
gridGenerator = GridGenerator(polygon=polygon, depth=[0], distance_neighbour=DISTANCE_LATERAL, no_children=6, points_allowed=5000)
# grid = gridGenerator.grid
coordinates = gridGenerator.coordinates

plt.plot(coordinates[:, 1], coordinates[:, 0], 'k.')
plt.plot(polygon[:, 1], polygon[:, 0], 'r-.')
plt.plot(munkholmen[:, 1], munkholmen[:, 0], 'r-.')
plt.show()

