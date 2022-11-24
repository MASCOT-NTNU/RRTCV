"""
Config has the most important parameter setting in the long horizon operation in MASCOT Nidelva mission 2022.
- polygon_operational_area: the polygon used to define the safe operational area.
- polygon_operational_area_shapely: shapely object to detect collision or border.
- polygon_obstalce: polygons used for identifying collisions.
- polygon_obstalce_shapely: shapely object to detect collision with obstacles.

- starting location: (lat, lon) used to define the starting location for the long horizon operation.
- home location: (lat, lon) used to define the end location for the home in the long horizon operation.
"""
from WGS import WGS
import numpy as np
import pandas as pd
from shapely.geometry import Polygon


class Config:
    """ Config contains essential setup for the simulation or experiment study. """
    def __init__(self) -> None:
        """ Initializes the crucial parameters used later in the simulation/experiment. """

        """ Set up WGS polygons and starting and end locations. """
        self.__wgs_polygon_border = pd.read_csv("csv/polygon_border.csv").to_numpy()
        self.__wgs_polygon_obstacle = pd.read_csv("csv/polygon_obstacle.csv").to_numpy()
        self.__wgs_loc_start = np.array([63.45582, 10.43287])
        self.__wgs_loc_end = np.array([63.440323, 10.355410])

        """ Convert them to cartesian polygons and starting and end locations. """
        self.__polygon_border = self.wgs2xy(self.__wgs_polygon_border)
        self.__polygon_border_shapely = Polygon(self.__polygon_border)
        self.__polygon_obstacle = self.wgs2xy(self.__wgs_polygon_obstacle)
        self.__polygon_obstacle_shapely = Polygon(self.__polygon_obstacle)
        x, y = WGS.latlon2xy(self.__wgs_loc_start[0], self.__wgs_loc_start[1])
        self.__loc_start = np.array([x, y])
        x, y = WGS.latlon2xy(self.__wgs_loc_end[0], self.__wgs_loc_end[1])
        self.__loc_end = np.array([x, y])

    @staticmethod
    def wgs2xy(value: np.ndarray) -> np.ndarray:
        """ Convert polygon containing wgs coordinates to polygon containing xy coordinates. """
        x, y = WGS.latlon2xy(value[:, 0], value[:, 1])
        return np.stack((x, y), axis=1)

    def set_polygon_border(self, value: np.ndarray) -> None:
        """ Set operational area using polygon defined by lat lon coordinates.
        Example:
             value: np.ndarray([[lat1, lon1],
                                [lat2, lon2],
                                ...
                                [latn, lonn]])
        """
        self.__wgs_polygon_border = value
        self.__polygon_border = self.wgs2xy(self.__wgs_polygon_border)
        self.__polygon_border_shapely = Polygon(self.__polygon_border)

    def set_polygon_obstacle(self, value: np.ndarray) -> None:
        """ Set polygon obstacle using polygon defined by lat lon coordinates.
        Example:
             value: np.ndarray([[lat1, lon1],
                                [lat2, lon2],
                                ...
                                [latn, lonn]])
        """
        self.__wgs_polygon_obstacle = value
        self.__polygon_obstacle = self.wgs2xy(self.__wgs_polygon_obstacle)
        self.__polygon_obstacle_shapely = Polygon(self.__polygon_obstacle)

    def set_loc_start(self, loc: np.ndarray) -> None:
        """ Set the starting location with (lat,lon). """
        self.__wgs_loc_start = loc
        x, y = WGS.latlon2xy(self.__wgs_loc_start[0], self.__wgs_loc_start[1])
        self.__loc_start = np.array([x, y])

    def set_loc_end(self, loc: np.ndarray) -> None:
        """ Set the home location with (lat, lon). """
        self.__wgs_loc_end = loc
        x, y = WGS.latlon2xy(self.__wgs_loc_end[0], self.__wgs_loc_end[1])
        self.__loc_end = np.array([x, y])

    def get_polygon_border(self) -> np.ndarray:
        """ Return polygon for opa in x y coordinates. """
        return self.__polygon_border

    def get_polygon_border_shapely(self) -> 'Polygon':
        """ Return shapelized polygon for opa in xy coordinates. """
        return self.__polygon_border_shapely

    def get_polygon_obstacle(self) -> np.ndarray:
        """ Return polygon for the obstacle. """
        return self.__polygon_obstacle

    def get_polygon_obstacle_shapely(self) -> 'Polygon':
        """ Return shapelized polygon for the obstacle. """
        return self.__polygon_obstacle_shapely

    def get_loc_start(self) -> np.ndarray:
        """ Return starting location in (x, y). """
        return self.__loc_start

    def get_loc_end(self) -> np.ndarray:
        """ Return home location in (x, y). """
        return self.__loc_end

    def get_wgs_polygon_border(self) -> np.ndarray:
        """ Return polygon for the oprational area in wgs coordinates. """
        return self.__wgs_polygon_border

    def get_wgs_polygon_obstacle(self) -> np.ndarray:
        """ Return polygon for the oprational area in wgs coordinates. """
        return self.__wgs_polygon_obstacle

    def get_wgs_loc_start(self) -> np.ndarray:
        """ Return starting location in (lat, lon). """
        return self.__wgs_loc_start

    def get_wgs_loc_end(self) -> np.ndarray:
        """ Return end location in (lat, lon). """
        return self.__wgs_loc_end


if __name__ == "__main__":
    s = Config()






