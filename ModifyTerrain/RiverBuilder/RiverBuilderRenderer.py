# Produces coordinates, boundary, TIN, raster, and hillshade files

import arcpy
import csv

# Stores ordered FID values which map to outer vertices of boundary
boundaryIDs = []
# Hash data buffer to store boundary points
searchPoints = {}
# Stores boundary points based on in-order FID values
boundaryPoints = []

# Paths to input and output folders/files
name = arcpy.GetParameterAsText(0)
outfolderpath = arcpy.GetParameterAsText(1)
coordinates = arcpy.GetParameterAsText(2)
boundaryData = arcpy.GetParameterAsText(3)
# Raster and hillshade properties
cellsize = arcpy.GetParameterAsText(4)
azimuth = arcpy.GetParameter(5)
altitude = arcpy.GetParameter(6)

# Create folder to store all output files
if arcpy.Exists(outfolderpath + r'\\' + name) == False:
    arcpy.CreateFolder_management(outfolderpath, name)

# Establish workspace in which output files are generated
arcpy.env.workspace = outfolderpath + r'\\' + name
# Overwrite duplicate files per program execution
arcpy.env.overwriteOutput = True

# Retrieve 3D Analyst license for ArcGIS to generate files
arcpy.CheckOutExtension('3D')

# Create the shape file based off of a river's Cartesian coordinates
arcpy.MakeXYEventLayer_management(coordinates, 'X', 'Y', name + '_Layer')
arcpy.FeatureClassToFeatureClass_conversion(name + '_Layer', arcpy.env.workspace, name + '_Points')
arcpy.AddMessage(name + '_Layer.shp generated.')

# Read in ordered FID values
with open(boundaryData, 'r') as file:
    reader = csv.reader(file)
    for num in reader:
        boundaryIDs.append(int(num[0]))

# Look through coordinates to extract boundary points
with arcpy.da.SearchCursor(arcpy.env.workspace + r'\\' + name + '_Points.shp', ['FID', 'X', 'Y']) as pointsCursor:                                                                        
    for row in pointsCursor:
        if int(row[0]) in boundaryIDs:
            searchPoints[int(row[0])] = arcpy.Point(row[1], row[2])

# Store individual points in a particular order to form the boundary
for vertex in boundaryIDs:
    boundaryPoints.append(searchPoints[vertex])

# Boundary creation
polygon = arcpy.Polygon(arcpy.Array(boundaryPoints))
arcpy.CreateFeatureclass_management(arcpy.env.workspace, name + '_Boundary.shp', 'POLYGON', polygon)
arcpy.CopyFeatures_management(polygon, name + '_Boundary.shp')
arcpy.AddMessage(name + '_Boundary.shp generated.')

# Create TIN based on topo data and boundary
arcpy.CreateTin_3d(name + '_TIN')
arcpy.EditTin_3d(name + '_TIN', [[name + '_Points.shp', 'Z', '<None>', 'Mass_Points', False], [name + '_Boundary.shp', '<None>', '<None>', 'Soft_Clip', False]])
arcpy.AddMessage(name + '_TIN generated.')

# Create raster out of TIN
arcpy.TinRaster_3d(name + '_TIN', name + '_Raster.tif', 'FLOAT', 'LINEAR', sample_distance='CELLSIZE {}'.format(cellsize), z_factor=1)
arcpy.AddMessage(name + '_Raster.tif generated.')

# Create hillshade out of raster
arcpy.HillShade_3d(name + '_Raster.tif', name + '_Hillshade.tif', azimuth, altitude, z_factor=1)
arcpy.AddMessage(name + '_Hillshade.tif generated.')
