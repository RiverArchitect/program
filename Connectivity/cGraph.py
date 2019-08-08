"""Helper class for graph theory applications"""
try:
    import sys, os, logging, random
except:
    print("ExceptionERROR: Missing fundamental packages (required: os, sys, logging, random).")
try:
    from heapq import heappush, heappop
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
        self.cost_func = "distance"

        self.path2_target = path2_target
        self.target_ras = None
        self.target_mat = np.ndarray((0, 0))
        self.end = set()  # sets are quickest for checking membership of elements

        self.cell_size = 1
        self.ref_pt = arcpy.Point(0, 0)

        # populates rasters and matrices, gets cell size and lower left corner reference point from depth raster
        self.read_hydraulic_rasters()
        # makes target into "end" graph vertices list
        self.target_to_keys()
        # construct weighted digraph
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

    def construct_graph(self):
        """
        Convert matrices to weighted inverse digraph
        key = to_vertex
        values = list of tuples [(from_vertex, cost),...] with cost of getting from from_vertex to to_vertex
        """
        self.logger.info("Constructing graph...")
        for i, row in enumerate(self.h_mat):
            for j, val in enumerate(row):
                # check if val is nan
                if not np.isnan(val):
                    key = str(i) + ',' + str(j)
                    neighbors, octants = self.get_neighbors(i, j)

                    for neighbor_i, octant in zip(neighbors, octants):
                        neighbor_key = str(neighbor_i[0]) + ',' + str(neighbor_i[1])
                        # check if neighbor index is within array
                        if (0 <= neighbor_i[0] < self.h_mat.shape[0]) and (0 <= neighbor_i[1] < self.h_mat.shape[1]):
                            # check if neighbor is nan
                            if not np.isnan(self.h_mat[neighbor_i]):
                                # check if depth > threshold (at current location and neighbor location)
                                if (self.h_mat[i, j] > self.h_thresh) and (self.h_mat[neighbor_i] > self.h_thresh):
                                    # check velocity condition
                                    mag_u_w = self.u_mat[i, j]  # magnitude of water velocity
                                    dir_u_w = self.va_mat[i, j] * np.pi / 180  # angle from north (degrees -> radians)
                                    if self.check_velocity_condition(mag_u_w, dir_u_w, octant):
                                        cost = self.get_cost(key, neighbor_key)
                                        try:
                                            self.inv_graph[neighbor_key] = self.inv_graph[neighbor_key] + [(key, cost)]
                                        except KeyError:
                                            self.inv_graph[neighbor_key] = [(key, cost)]
        self.logger.info("Merging target vertices...")
        # make copy so we can delete keys of original graph during iteration (not containing "end" key)
        graph_copy = {k: v for k, v in self.inv_graph.items()}
        self.inv_graph["end"] = []
        for v, neighbors in graph_copy.items():
            # update values
            self.inv_graph[v] = list(map(lambda x: ("end", x[1]) if x[0] in self.end else x, neighbors))
            # merge vertices
            if v in self.end:
                self.inv_graph["end"] += neighbors
                del self.inv_graph[v]
        del graph_copy
        # remove duplicate values
        for v, neighbors in self.inv_graph.items():
            num_vs = [neighbor[0] for neighbor in neighbors].count("end")
            if num_vs > 1:
                # keep one with least cost, remove other duplicates
                least_cost = min([x[1] for x in neighbors if x[0] == "end"])
                self.inv_graph[v] = [x for x in self.inv_graph[v] if x[0] != "end"] + [("end", least_cost)]

    @staticmethod
    def get_neighbors(i, j):
        # neighboring indices, going cw from north
        neighbors = [(i - 1, j),  # up (decreasing row)
                     (i - 1, j + 1),  # up-right
                     (i, j + 1),  # right
                     (i + 1, j + 1),  # down-right
                     (i + 1, j),  # down
                     (i + 1, j - 1),  # down-left
                     (i, j - 1),  # left
                     (i - 1, j - 1)]  # up-left

        # angle ranges corresponding to travel in direction to neighbor
        octants = [[(-22.5, 22.5)],  # up
                   [(22.5, 67.5)],  # up-right
                   [(67.5, 112.5)],  # right
                   [(112.5, 157.5)],  # down-right
                   [(157.5, 180), (-180, -157.5)],  # down
                   [(-157.5, -112.5)],  # down-left
                   [(-112.5, -67.5)],  # left
                   [(-67.5, -22.5)]]  # up-left

        return neighbors, octants

    def check_velocity_condition(self, mag_u_w, dir_u_w, octant):
        """Checks if velocity vector u_w allows travel in direction within octant"""
        # if magnitude of water velocity is less than max swimming speed, can always pass
        if mag_u_w <= self.u_thresh:
            return True
        else:
            # max angle resultant vector can differ from u_w
            theta_max = np.rad2deg(np.arctan(
                np.sin(np.arccos(-self.u_thresh / mag_u_w)) / (mag_u_w / self.u_thresh - self.u_thresh / mag_u_w)))
            # get ranges of possible angles
            dir_u_ws = dir_u_w + 180  # scaled to 0-360 range
            lower, upper = dir_u_ws - theta_max, dir_u_ws + theta_max  # range of possible angles
            lower, upper = lower % 360, upper % 360  # keep in 0-360 range
            # convert back to original range
            lower -= 180
            upper -= 180
            # handle wrap-around ranges
            if lower < upper:
                ranges = [[lower, upper]]
            else:
                ranges = [[lower, 360], [0, upper]]
            # check if travel direction octant overlaps with angle range
            for a, b in ranges:
                for c, d in octant:
                    if a <= c <= b or a <= d <= b:
                        return True
            return False

    def get_cost(self, key, neighbor_key):
        i1, j1 = list(map(int, key.split(",")))
        i2, j2 = list(map(int, neighbor_key.split(",")))

        if self.cost_func == 'distance':
            return self.cell_size * np.sqrt((i2 - i1) ** 2 + (j2 - j1) ** 2)

        elif self.cost_func == 'steps':
            return 1

        elif self.cost == 'other':
            """Could add other cost functions using these values"""
            # distance between points
            dist = self.cell_size * np.sqrt((i2 - i1) ** 2 + (j2 - j1) ** 2)
            # depths
            h1 = self.h_mat[i1, j1]
            h2 = self.h_mat[i2, j2]
            # velocities
            u1 = self.u_mat[i1, j1]
            u2 = self.u_mat[i2, j2]
            # velocity angles
            va1 = self.va_mat[i1, j1]
            va2 = self.va_mat[i2, j2]

    def dijkstra(self):
        """
        Dijkstra's algorithm finding the least cost path along the inverse weighted digraph from target to all other vertices
        """
        known_vertices = {key: None for key in self.inv_graph.keys()}
        queue = [(0, "end")]  # path length, vertex
        while queue:
            path_len, v = heappop(queue)  # return the item with the smallest path length
            if known_vertices[v] is None:  # vertex is unvisited
                known_vertices[v] = path_len
                for neighbor, edge_len in self.inv_graph[v]:
                    if neighbor in known_vertices.keys():  # *** avoid KeyError
                        if known_vertices[neighbor] is None:
                            heappush(queue, (path_len + edge_len, neighbor))

        del known_vertices["end"]
        known_vertices = {**known_vertices, **{end_vertex: 0 for end_vertex in self.end}}

        return known_vertices

    @fGl.err_info
    def target_to_keys(self):
        """Converts escape target matrix to a list of target vertex keys (self.end) used for graph traversal"""
        # for each active target cell, add corresponding key to list
        for i, row in enumerate(self.target_mat):
            for j, val in enumerate(row):
                # active if cell value = 1
                if self.target_mat[i, j] == 1:
                    key = str(i) + ',' + str(j)
                    self.end.add(key)

    def find_shortest_paths(self):
        self.logger.info("Finding escape routes...")

        known_vertices = self.dijkstra()

        self.logger.info("Converting vertex dict to array...")
        # initialize output array as nans
        shortest_path_mat = np.zeros(self.h_mat.shape)
        shortest_path_mat[:] = np.nan
        for known_vertex in known_vertices.keys():
            i, j = list(map(int, known_vertex.split(',')))
            shortest_path_mat[i, j] = known_vertices[known_vertex]
        self.logger.info("OK")

        self.logger.info("Converting escape route lengths array to raster...")
        shortest_path_ras = arcpy.NumPyArrayToRaster(shortest_path_mat,
                                                     lower_left_corner=self.ref_pt,
                                                     x_cell_size=self.cell_size,
                                                     value_to_nodata=np.nan)
        self.logger.info("OK")
        return shortest_path_ras
