"""Helper class for graph theory applications"""
try:
    import sys, os, logging, random
except:
    print("ExceptionERROR: Missing fundamental packages (required: os, sys, logging, random).")
try:
    from collections import deque
    import numpy as np
except:
    print("ExceptionERROR: Missing fundamental packages (required: collections, numpy).")
try:
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')) + "\\.site_packages\\riverpy\\")
    import config
    import cFish as cFi
    import fGlobal as fG
    import cMakeTable as cMkT
except:
    print("ExceptionERROR: Missing RiverArchitect packages (required: riverpy).")
try:
    import arcpy
except:
    print("ExceptionERROR: arcpy is not available (check license connection?)")
try:
    from arcpy.sa import *
except:
    print("ExceptionERROR: Spatial Analyst (arcpy.sa) is not available (check license?)")


class Graphy:
    """
    Class for constructing and navigating directed graphs
    """

    def __init__(self, path2_h_ras, path2_u_ras, path2_va_ras, h_thresh, u_thresh, path2_target):

        self.logger = logging.getLogger("logfile")
        self.cache = config.dir2co + ".cache\\%s" % str(random.randint(1000000, 9999999))
        fG.chk_dir(self.cache)

        self.path2_h_ras = path2_h_ras
        self.path2_u_ras = path2_u_ras
        self.path2_va_ras = path2_va_ras
        self.path2_target_ras = path2_target
        self.h_thresh = h_thresh
        self.u_thresh = u_thresh

        self.h_ras = None
        self.u_ras = None
        self.va_ras = None
        self.h_mat = np.ndarray((0, 0))
        self.u_mat = np.ndarray((0, 0))
        self.va_mat = np.ndarray((0, 0))
        self.graph = {}

        self.path2_target = path2_target
        self.target_ras = None
        self.target_mat = np.ndarray((0, 0))


        self.read_hydraulic_rasters()
        self.construct_graph()

    def read_hydraulic_rasters(self):
        self.logger.info("Retrieving hydraulic rasters...")
        try:
            self.logger.info("Reading depth raster %s" % self.path2_h_ras)
            self.h_ras = Raster(self.path2_h_ras)
            self.logger.info("Reading velocity raster %s" % self.path2_u_ras)
            self.u_ras = Raster(self.path2_u_ras)
            self.logger.info("Reading velocity angle raster %s" % self.path2_va_ras)
            self.va_ras = Raster(self.path2_va_ras)
            self.logger.info("Reading target area raster %s" % self.path2_target)
            self.target_ras = Raster(self.path2_target)
            self.logger.info("OK")
        except:
            self.logger.info("ERROR: Could not retrieve hydraulic rasters.")
        self.ras_2_mats()

    def ras_2_mats(self):
        self.logger.info("Converting rasters to arrays...")
        try:
            self.h_mat = arcpy.RasterToNumPyArray(self.h_ras)
            self.u_mat = arcpy.RasterToNumPyArray(self.u_ras)
            self.va_mat = arcpy.RasterToNumPyArray(self.va_ras)
            self.target_mat = arcpy.RasterToNumPyArray(self.target_ras)
            self.logger.info("OK")
        except:
            self.logger.info("ERROR: Could not convert rasters to arrays.")

    def construct_graph(self):
        """Convert matrices to directed graph"""
        self.logger.info("Constructing graph...")
        graph = {}
        for i, row in enumerate(self.h_mat):
            for j, val in enumerate(row):
                key = str(i) + ',' + str(j)
                neighbors, pvecs, pvecs_perp = self.get_neighbors(i, j)

                for n_i, neighbor in enumerate(neighbors):
                    # check if neighbor index is within array
                    if (0 <= neighbor[0] < self.h_mat.shape[0]) and (0 <= neighbor[1] < self.h_mat.shape[1]):
                        # check if depth > threshold
                        if self.h_mat[i, j] > self.h_thresh:
                            # check velocity condition
                            mag_u_a = self.u_mat[i, j]  # magnitude of water velocity
                            dir_u_a = self.va_mat[i, j] * np.pi / 180  # angle from north (degrees -> radians)
                            if self.check_velocity_condition(mag_u_a, dir_u_a, pvecs[n_i], pvecs_perp[n_i]):
                                graph[key] = str(neighbor[0]) + ',' + str(neighbor[1])
        self.logger.info("OK")

    @staticmethod
    def get_neighbors(i, j):
        # neighboring indices, going ccw from east
        neighbors = [(i + 1, j),
                     (i + 1, j + 1),
                     (i, j + 1),
                     (i - 1, j + 1),
                     (i - 1, j),
                     (i - 1, j - 1),
                     (i, j - 1),
                     (i + 1, j - 1)]

        # unit vectors pointing from current node to neighbors
        pvecs = [(1, 0),
                 (1 / np.sqrt(2), 1 / np.sqrt(2)),
                 (0, 1),
                 (-1 / np.sqrt(2), 1 / np.sqrt(2)),
                 (-1, 0),
                 (-1 / np.sqrt(2), -1 / np.sqrt(2)),
                 (0, -1),
                 (1 / np.sqrt(2), -1 / np.sqrt(2))]

        # perpendicular complements to pvecs
        q = deque(pvecs)
        q.rotate(-2)
        pvecs_perp = list(q)

        return neighbors, pvecs, pvecs_perp

    def check_velocity_condition(self, mag_u_a, dir_u_a, pvec, pvec_perp):
        """Checks if velocity vector u_a allows travel in direction pvec"""
        # if magnitude of water velocity is less than max swimming speed, can always pass
        if mag_u_a < self.u_thresh:
            return True
        else:
            # u_a vector (dir is angle from north!)
            u_a = (mag_u_a * np.sin(dir_u_a), mag_u_a * np.cos(dir_u_a))
            # split into components parallel and perpendicular to travel direction
            u_a_perp = np.dot(u_a, pvec_perp)
            # if we can't cancel perpendicular component, not passable
            if abs(u_a_perp) > self.u_thresh:
                return False
            else:
                u_a_par = np.dot(u_a, pvec)
                u_f_par = np.sqrt(self.u_thresh ** 2 - u_a_perp ** 2)
                if u_f_par + u_a_par > 0:
                    return True
                else:
                    return False

    def target_to_keys(self):
        """Converts self.escape_target polygon to a list of target node keys (end) used for graph traversal"""
        # for each active target cell, add corresponding key to list
        l = []
        for i, row in enumerate(self.target_mat):
            for j, val in enumerate(row):
                # if cell value is not null or zero
                if self.target_mat[i, j] > 0:
                    key = str(i) + ',' + str(j)
                    l.append(key)
        return l

    """Dynamic program"""
    def find_shortest_path(self, start, end):
        """Finds shortest path from start node to set of end nodes (i,.e. target)"""
        # if we start in target area, path length is zero
        if start in end:
            return 0
        # key = node, value = shortest path to that node
        dist = {start: [start]}
        q = deque(start)
        while len(q):
            # at = node we know the shortest path to already
            # goes from left so we always get to that node in least steps possible
            at = q.popleft()
            # for all possible next nodes
            for next_node in self.graph[at]:
                # if we don't already have a path to the next node
                if next_node not in dist:
                    # add path = path to at node, then from at to next node
                    dist[next_node] = [dist[at], next_node]
                    # add next node to end of q
                    q.append(next_node)
                # if we made it to target, get length of path
                if next_node in end:
                    shortest_path = self.flatten_path(dist[next_node])
                    return shortest_path
        # if no path found after traversing graph from start
        return -999

    def flatten_path(self, path_obj):
        p = []
        for obj in path_obj:
            if type(obj) == list:
                for item in self.flatten_path(obj):
                    p.append(item)
            else:
                p.append(obj)
        return p

    def make_shortest_paths_raster(self):
        """Makes a raster where each cell indicates the shortest path to end"""
        # for each cell, find shortest path to target
        # get length of shortest path (len(shortest_path) - 1), save at corresponding array index
        # convert output array to raster
        # save output raster
        pass
