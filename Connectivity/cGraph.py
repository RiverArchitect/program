"""Helper class for graph theory applications"""
try:
    import sys, os, logging
except:
    print("ExceptionERROR: Missing fundamental packages (required: os, sys, logging).")
try:
    from collections import deque
except:
    print("ExceptionERROR: Missing fundamental package 'collections'.")
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
    def __init__(self, path2_h_ras, path2_u_ras, path2_u_dir_ras):

        self.logger = logging.getLogger("logfile")
        self.cache = config.dir2co + ".cache\\"
        fG.chk_dir(self.cache)

        self.path2_h_ras = path2_h_ras
        self.path2_u_ras = path2_u_ras
        self.path2_u_dir_ras = path2_u_dir_ras

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
        graph = {}
        for row, i in enumerate(mat):
            for col, j in enumerate(row):
                key = str(i) + ',' + str(j)

                neighbors = get_neighbors(i, j)


    def get_neighbors(self, i, j):
        # static method for now

        # list of indices
        l = [(i + 1, j),
             (i - 1, j),
             (i, j + 1),
             (i, j - 1),
             (i + 1, j + 1),
             (i - 1, j - 1),
             (i - 1, j + 1),
             (i + 1, j - 1)]

        # corresponding unit vectors for step direction

        # 45 deg rotation matrix
        rot = [[np.cos(), np.sin()], [-np.sin(), np.cos()]]
        
        vs = []

        return l, vs

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
