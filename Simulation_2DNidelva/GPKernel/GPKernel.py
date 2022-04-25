"""
This script builds the kernel for simulation
Author: Yaolin Ge
Contact: yaolin.ge@ntnu.no
Date: 2022-03-16
"""
import numpy as np

from usr_func import *
from GOOGLE.Simulation_2DNidelva.Tree.Location import *
from GOOGLE.Simulation_2DNidelva.Config.Config import *


class GPKernel:

    def __init__(self, knowledge=None):
        self.knowledge = knowledge
        self.coordinates_xyz = self.knowledge.coordinates_xy
        self.get_Sigma_prior()
        self.get_ground_truth()
        self.knowledge.mu_cond = self.knowledge.mu_prior
        self.knowledge.Sigma_cond = self.knowledge.Sigma_prior
        self.get_obstacle_field()
        self.cost_direction = None
        self.cost_vr = None
        self.cost_eibv = None
        self.cost_budget = None
        self.cost_valley = None
        self.budget_middle_location = None
        self.budget_ellipse_angle = None
        self.budget_ellipse_a = None
        self.budget_ellipse_b = None
        self.budget_ellipse_c = None

    def get_Sigma_prior(self):
        self.set_coef()
        DistanceMatrix = cdist(self.coordinates_xyz, self.coordinates_xyz)
        self.knowledge.Sigma_prior = self.sigma ** 2 * (1 + self.eta * DistanceMatrix) * np.exp(-self.eta * DistanceMatrix)

    def set_coef(self):
        self.sigma = SIGMA
        self.eta = 4.5 / LATERAL_RANGE
        self.tau = np.sqrt(NUGGET)
        self.R = np.diagflat(self.tau ** 2)
        print("Coef is set successfully!")

    def get_ground_truth(self):
        self.knowledge.mu_truth = (self.knowledge.mu_prior.reshape(-1, 1) +
                                   np.linalg.cholesky(self.knowledge.Sigma_prior) @
                                   np.random.randn(len(self.knowledge.mu_prior)).reshape(-1, 1))

    def get_obstacle_field(self):
        t1 = time.time()
        self.cost_obstacle = np.zeros(self.knowledge.coordinates_xy.shape[0])
        ind_collided = [self.is_within_obstacles(LocationXY(location[0], location[1]))
                        for location in self.knowledge.coordinates_xy]
        self.cost_obstacle[ind_collided] = np.inf
        t2 = time.time()
        print("Obstacle field time consumed: ", t2 - t1)

    def get_cost_valley(self, current_location=None, previous_location=None, goal_location=None, budget=None):
        t1 = time.time()
        self.get_eibv_field()
        self.get_variance_reduction_field()
        self.get_direction_field(current_location, previous_location)
        self.get_budget_field(current_location, goal_location, budget)
        self.cost_valley = (self.cost_eibv +
                          self.cost_budget +
                          self.cost_vr +
                          self.cost_obstacle +
                          self.cost_direction)
        self.save_information_to_knowledge()
        t2 = time.time()
        print("Cost valley computed successfully!, time consumed: ", t2 - t1)

    def save_information_to_knowledge(self):
        self.knowledge.cost_eibv = self.cost_eibv
        self.knowledge.cost_vr = self.cost_vr
        self.knowledge.cost_budget = self.cost_budget
        self.knowledge.cost_direction = self.cost_direction
        self.knowledge.cost_obstacle = self.cost_obstacle
        self.knowledge.cost_valley = self.cost_valley
        self.knowledge.budget_middle_location = self.budget_middle_location
        self.knowledge.budget_ellipse_angle = self.budget_ellipse_angle
        self.knowledge.budget_ellipse_a = self.budget_ellipse_a
        self.knowledge.budget_ellipse_b = self.budget_ellipse_b
        self.knowledge.budget_ellipse_c = self.budget_ellipse_c

    def get_eibv_field(self):
        t1 = time.time()
        self.cost_eibv = []
        for i in range(self.coordinates_xyz.shape[0]):
            F = getFVector(i, self.coordinates_xyz.shape[0])
            self.cost_eibv.append(get_eibv_1d(self.knowledge.threshold, self.knowledge.mu_cond,
                                              self.knowledge.Sigma_cond, F, self.R))
        self.cost_eibv = normalise(np.array(self.cost_eibv))
        t2 = time.time()
        print("EIBV field takes: ", t2 - t1)

    # TODO: check multiprocessing
    # def get_eibv_field_mp(self):
    #     t1 = time.time()
    #     ind = np.arange(self.grid_vector.shape[0])
    #     pool = Pool(cpu_count())
    #     pool.map(self.get_eibv_mp, ind)
    #     t2 = time.time()
    #     print("MP EIBV field takes: ", t2 - t1)
    #
    # def get_eibv_mp(self, ind):
    #     F = np.zeros([1, self.grid_vector.shape[0]])
    #     F[0, ind] = True
    #     Sigma_updated = self.Sigma_cond - self.Sigma_cond @ F.T @ np.linalg.solve(F @ self.Sigma_cond @ F.T + self.R,
    #                                                                               F @ self.Sigma_cond)
    #     Variance = np.diag(Sigma_updated).reshape(-1, 1)
    #     EIBV = 0
    #     for i in range(self.mu_cond.shape[0]):
    #         EIBV += (mvn.mvnun(-np.inf, THRESHOLD, self.mu_cond[i], Variance[i])[0] -
    #                  mvn.mvnun(-np.inf, THRESHOLD, self.mu_cond[i], Variance[i])[0] ** 2)

    def get_budget_field(self, current_location, goal_location, budget):
        t1 = time.time()
        if budget >= BUDGET_MARGIN:
            self.budget_middle_location = self.get_middle_location(current_location, goal_location)
            self.budget_ellipse_angle = self.get_angle_between_locations(current_location, goal_location)
            self.budget_ellipse_a = budget / 2
            self.budget_ellipse_c = get_distance_between_xy_locations(current_location, goal_location) / 2
            self.budget_ellipse_b = np.sqrt(self.budget_ellipse_a ** 2 - self.budget_ellipse_c ** 2)
            print("a: ", self.budget_ellipse_a, "b: ", self.budget_ellipse_b, "c: ", self.budget_ellipse_c)
            if self.budget_ellipse_b > BUDGET_ELLIPSE_B_MARGIN:
                x_wgs = self.coordinates_xyz[:, 0] - self.budget_middle_location.x
                y_wgs = self.coordinates_xyz[:, 1] - self.budget_middle_location.y
                self.cost_budget = []
                for i in range(self.coordinates_xyz.shape[0]):
                    x_usr = (x_wgs[i] * np.cos(self.budget_ellipse_angle) -
                             y_wgs[i] * np.sin(self.budget_ellipse_angle))
                    y_usr = (x_wgs[i] * np.sin(self.budget_ellipse_angle) +
                             y_wgs[i] * np.cos(self.budget_ellipse_angle))
                    if (x_usr / self.budget_ellipse_b) ** 2 + (y_usr / self.budget_ellipse_a) ** 2 <= 1:
                        self.cost_budget.append(0)
                    else:
                        self.cost_budget.append(np.inf)
                self.cost_budget = np.array(self.cost_budget)
            else:
                self.knowledge.gohome = True
        else:
            self.knowledge.gohome = True
        t2 = time.time()
        print("budget field consumed: ", t2 - t1)

    @staticmethod
    def get_middle_location(location1, location2):
        x_middle = (location1.X_START + location2.X_START) / 2
        y_middle = (location1.Y_START + location2.Y_START) / 2
        return LocationXY(x_middle, y_middle)

    @staticmethod
    def get_angle_between_locations(location1, location2):
        delta_y = location2.Y_START - location1.Y_START
        delta_x = location2.X_START - location1.X_START
        angle = np.math.atan2(delta_x, delta_y)
        return angle

    def get_variance_reduction_field(self):
        t1 = time.time()
        self.cost_vr = []
        for i in range(len(self.knowledge.coordinates_xy)):
            ind_F = get_ind_at_location2d_xy(self.knowledge.coordinates_xy,
                                             LocationXY(self.knowledge.coordinates_xy[i, 0],
                                                        self.knowledge.coordinates_xy[i, 1]))
            F = np.zeros([1, self.coordinates_xyz.shape[0]])
            F[0, ind_F] = True
            self.cost_vr.append(self.get_variance_reduction(self.knowledge.Sigma_cond, F, self.R))
        self.cost_vr = 1 - normalise(np.array(self.cost_vr))
        t2 = time.time()
        print("Variance Reduction field takes: ", t2 - t1)

    @staticmethod
    def get_variance_reduction(Sigma, F, R):
        Reduction = Sigma @ F.T @ np.linalg.solve(F @ Sigma @ F.T + R, F @ Sigma)
        vr = np.sum(np.diag(Reduction))
        return vr

    def is_within_obstacles(self, location):
        point = Point(location.X_START, location.Y_START)
        within = False
        if self.knowledge.polygon_obstacles_shapely.contains(point):
            within = True
        return within

    def get_direction_field(self, current_location, previous_location):
        t1 = time.time()
        dx = current_location.X_START - previous_location.X_START
        dy = current_location.Y_START - previous_location.Y_START
        vec1 = np.array([[dx, dy]])
        self.cost_direction = []
        for i in range(self.coordinates_xyz.shape[0]):
            dx = self.coordinates_xyz[i, 0] - current_location.X_START
            dy = self.coordinates_xyz[i, 1] - current_location.Y_START
            vec2 = np.array([[dx, dy]])
            if np.dot(vec1, vec2.T) >= 0:
                self.cost_direction.append(0)
            else:
                self.cost_direction.append(PENALTY)
        self.cost_direction = np.array(self.cost_direction)
        t2 = time.time()
        print("Direction field takes: ", t2 - t1)







