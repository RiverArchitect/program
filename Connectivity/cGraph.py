"""Helper class for graph theory applications"""
try:
    import sys, os, logging
except:
    print("ExceptionERROR: Missing fundamental packages (required: os, sys, logging).")
try:
    from collections import deque
    import numpy as np
except:
    print("ExceptionERROR: Missing fundamental packages (required: collections, numpy).")
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
    def __init__(self, path2_h_ras, path2_u_ras, path2_u_dir_ras, h_thresh, u_thresh):

        self.logger = logging.getLogger("logfile")
        self.cache = config.dir2co + ".cache\\"
        fG.chk_dir(self.cache)

        self.path2_h_ras = path2_h_ras
        self.path2_u_ras = path2_u_ras
        self.path2_u_dir_ras = path2_u_dir_ras
        self.h_thresh = h_thresh
        self.u_thresh = u_thresh

        self.read_hydraulic_rasters()
        self.construct_graph()

    def read_hydraulic_rasters(self):
        self.logger.info("Retrieving hydraulic rasters...")
        try:
            self.h_ras = Raster(self.path2_h_ras)
            self.u_ras = Raster(self.path2_u_ras)
            self.u_dir_ras = Raster(self.path2_u_dir_ras)
            self.logger.info("OK")
        except:
            self.logger.info("ERROR: Could not retrieve hydraulic rasters.")
        self.ras_2_mats()

    def ras_2_mats(self):
        self.logger.info("Converting rasters to arrays...")
        try:
            self.h_mat = arcpy.RasterToNumPyArray(self.h_ras)
            self.u_mat = arcpy.RasterToNumPyArray(self.u_ras)
            self.u_dir_mat = arcpy.RasterToNumPyArray(self.u_dir_ras)
        except:
            self.logger.info("ERROR: Could not convert rasters to arrays.")

    def construct_graph(self):
        """Convert matrices to directed graph"""
        self.logger.info("Constructing graph...")
        graph = {}
        for i, row in enumerate(mat):
            for j, col in enumerate(row):
                key = str(i) + ',' + str(j)
                neighbors, pvecs, pvecs_perp = self.get_neighbors(i, j)

                for n_i, neighbor in enumerate(neighbors):
                    # check if neighbor index is within array
                    if 0 <= neighbor[0] < len(row) and 0 <= neighbor[1] <= len(col):
                        # check if depth > threshold
                        if self.h_mat[i, j] > self.h_thresh:
                            # check velocity condition
                            mag_u_a = self.u_mat[i, j]  # magnitude of water velocity
                            dir_u_a = self.u_dir_mat[i, j] * np.pi/180  # angle from north (degrees -> radians)
                            if self.check_velocity_condition(mag_u_a, dir_u_a, pvecs[n_i], pvecs_perp[n_i]):
                                graph[key] = str(neighbor[0]) + ',' + str(neighbor[1])
        self.logger.info("OK")

    def get_neighbors(self, i, j):
        # static method for now

        # neighboring indices, going ccw from east
        l = [(i + 1, j),
             (i + 1, j + 1),
             (i, j + 1),
             (i - 1, j + 1),
             (i - 1, j),
             (i - 1, j - 1),
             (i, j - 1),
             (i + 1, j - 1)]

        # unit vectors pointing from current node to neighbors
        pvecs = [(1, 0),
                 (1/np.sqrt(2), 1/np.sqrt(2)),
                 (0, 1),
                 (-1/np.sqrt(2), 1/np.sqrt(2)),
                 (-1, 0),
                 (-1/np.sqrt(2), -1/np.sqrt(2)),
                 (0, -1),
                 (1/np.sqrt(2), -1/np.sqrt(2))]

        # perpendicular complements to pvecs
        q = deque(pvecs)
        q.rotate(-2)
        pvecs_perp = list(q)

        return l, pvecs, pvecs_perp

    def check_velocity_condition(self, mag_u_a, dir_u_a, pvec, pvec_perp):
        """Checks if velocity vector u_a allows travel in direction pvec"""
        # check if magnitude is too high
        if mag_u_a < self.u_thresh:
            # u_a vector (dir is angle from north!)
            u_a = (mag_u_a * np.sin(dir_u_a), mag_u_a * np.cos(dir_u_a))
            # split into components parallel and perpendicular to travel direction
            u_a_perp = np.dot(u_a, pvec_perp)
            u_a_par = np.dot(u_a, pvec)
            u_f_par = np.sqrt(self.u_thresh**2 - u_a_perp**2)
            if u_f_par + u_a_par > 0:
                return True
            else:
                return False
        else:
            return False

    """Dynamic program"""
    def find_shortest_path(self, start, end):
        # key = node, value = shortest path to that node
        dist = {start: [start]}
        q = deque(start)
        while len(q):
            # at = node we know the shortest path to already
            # goes from left so we always get to that node in least steps possible
            at = q.popleft()
            # for all possible next nodes
            for next in self.graph[at]:
                # if we don't already have a path to the next node
                if next not in dist:
                    # add path = path to at node, then from at to next
                    dist[next] = [dist[at], next]
                    # add next node to end of q
                    q.append(next)
        return dist[end]
