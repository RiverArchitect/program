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
    import fGlobal as fGl
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
        self.inv_graph = {}

        self.path2_target = path2_target
        self.target_ras = None
        self.target_mat = np.ndarray((0, 0))
        self.end = []

        self.cell_size = 1
        self.ref_pt = arcpy.Point(0, 0)

        # populates rasters and matrices, gets cell size and lower left corner reference point from depth raster
        self.read_hydraulic_rasters()
        # makes target into "end" graph nodes list
        self.target_to_keys()
        # construct directed graph
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
            self.cell_size = float(arcpy.GetRasterProperties_management(self.h_ras, 'CELLSIZEX').getOutput(0))
            self.ref_pt = arcpy.Point(self.h_ras.extent.XMin, self.h_ras.extent.YMin)
        except:
            self.logger.info("ERROR: Could not retrieve hydraulic rasters.")
        self.ras_2_mats()

    def ras_2_mats(self):
        self.logger.info("Converting rasters to arrays...")
        try:
            self.h_mat = arcpy.RasterToNumPyArray(self.h_ras, lower_left_corner=self.ref_pt, nodata_to_value=np.nan)
            self.u_mat = arcpy.RasterToNumPyArray(self.u_ras, lower_left_corner=self.ref_pt, nodata_to_value=np.nan)
            self.va_mat = arcpy.RasterToNumPyArray(self.va_ras, lower_left_corner=self.ref_pt, nodata_to_value=np.nan)
            self.target_mat = arcpy.RasterToNumPyArray(self.target_ras, lower_left_corner=self.ref_pt)  # integer type
            self.logger.info("OK")
        except:
            self.logger.info("ERROR: Could not convert rasters to arrays.")

    @fGl.err_info
    def construct_graph(self):
        """Convert matrices to directed graph"""
        self.logger.info("Constructing graph...")
        for i, row in enumerate(self.h_mat):
            for j, val in enumerate(row):
                # check if val is nan
                if not np.isnan(val):
                    key = str(i) + ',' + str(j)
                    neighbors, pvecs, pvecs_perp = self.get_neighbors(i, j)

                    for n_i, neighbor in enumerate(neighbors):
                        # check if neighbor index is within array
                        if (0 <= neighbor[0] < self.h_mat.shape[0]) and (0 <= neighbor[1] < self.h_mat.shape[1]):
                            # check if neighbor is nan
                            if not np.isnan(self.h_mat[neighbor]):
                                # check if depth > threshold (at current location and neighbor location)
                                if (self.h_mat[i, j] > self.h_thresh) and (self.h_mat[neighbor] > self.h_thresh):
                                    # check velocity condition
                                    mag_u_a = self.u_mat[i, j]  # magnitude of water velocity
                                    dir_u_a = self.va_mat[i, j] * np.pi / 180  # angle from north (degrees -> radians)
                                    if self.check_velocity_condition(mag_u_a, dir_u_a, pvecs[n_i], pvecs_perp[n_i]):
                                        neighbor_key = str(neighbor[0]) + ',' + str(neighbor[1])
                                        try:
                                            self.graph[key] = self.graph[key] + [neighbor_key]
                                        except KeyError:
                                            self.graph[key] = [neighbor_key]
                                        try:
                                            self.inv_graph[neighbor_key] = self.inv_graph[neighbor_key] + [key]
                                        except KeyError:
                                            self.inv_graph[neighbor_key] = [key]
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

    @fGl.err_info
    def target_to_keys(self):
        """Converts escape target matrix to a list of target node keys (self.end) used for graph traversal"""
        # for each active target cell, add corresponding key to list
        for i, row in enumerate(self.target_mat):
            for j, val in enumerate(row):
                # active if cell value = 1
                if self.target_mat[i, j] == 1:
                    key = str(i) + ',' + str(j)
                    self.end.append(key)

    def dynamic_shortest_paths(self):
        """A dynamic program for finding shortest escape routes; much faster than previous method!"""
        self.logger.info("Finding escape routes...")
        # set of nodes for which we already know the shortest path length. key=node key, value=number of steps
        known_nodes = {end_node: 0 for end_node in self.end}
        # number of steps to target area
        steps = 1
        valid_neighbors = True
        while valid_neighbors:
            self.logger.info("path step: %i" % steps)
            valid_neighbors = False  # gets reset to True if any neighbors are added
            # only nodes added from the previous iteration (used as stepping stones)
            prev_nodes = [known_node for known_node in known_nodes.keys() if known_nodes[known_node] == steps - 1]
            for prev_node in prev_nodes:
                # get all nodes that can reach prev_node
                if prev_node in self.inv_graph.keys():
                    neighbors = self.inv_graph[prev_node]
                    for neighbor in neighbors:
                        # if neighbor is not already in known_nodes
                        if neighbor not in known_nodes.keys():
                            # save node and steps to known_nodes
                            known_nodes[neighbor] = steps
                            valid_neighbors = True
            steps += 1
        self.logger.info("OK")

        self.logger.info("Converting node dict to array...")
        # initialize output array as nans
        shortest_path_mat = np.zeros(self.h_mat.shape)
        shortest_path_mat[:] = np.nan
        for known_node in known_nodes.keys():
            i, j = list(map(int, known_node.split(',')))
            shortest_path_mat[i, j] = known_nodes[known_node]
        self.logger.info("OK")

        self.logger.info("Converting escape route lengths array to raster...")
        shortest_path_ras = arcpy.NumPyArrayToRaster(shortest_path_mat,
                                                     lower_left_corner=self.ref_pt,
                                                     x_cell_size=self.cell_size,
                                                     value_to_nodata=np.nan)
        # *** set disconnectd areas to -999
        # Con(~IsNull(h_interp) & IsNull(shortest_path_ras), -999, shortest_path_ras)
        # *** revise disconnected areas calculation; there could be more disconnected areas due to velocity condition
        self.logger.info("OK")
        return shortest_path_ras

