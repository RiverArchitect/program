import os, sys
import pandas as pd
import numpy as np
import simpledbf
from scipy.interpolate import interp1d
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon
from matplotlib.collections import PatchCollection
import arcpy
from arcpy import env
from arcpy.sa import *
try:
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')) + "\\.site_packages\\riverpy\\")
    import config
    import fGlobal as fGl
except:
    print("ExceptionERROR: Missing RiverArchitect packages (riverpy).")

# Eco series analysis - SHArea
# This python script (1)
# Before you run this code, please put the excel files in SHArea folder to a new folder called "case_name"

#########################
# User defined variables

case_name = "VanillaC4"

fish_periods = ["chsp"] #fish_periods = ["chju", "raju", "raad"]

timeseries_path = "../00_Flows/" + case_name + "/flow_series_" + case_name + ".xlsx"

figure_path = "../SHArC/SHArea/" + case_name + "/"

interptype = 'linear'
scale_to_one = 0

#########################

ind = 0
colors = ["tab:blue", "tab:orange", "tab:green"]

for fish_period in fish_periods:

    fish_name = fish_period[0:2]
    period = fish_period[2:4]

    if fish_name == 'ch':
        fish_full = 'Chinook Salmon'
    elif fish_name == 'ra':
        fish_full = 'Rainbow / Steelhead Trout'
    if period == 'sp':
        period_full = 'spawning'
    elif period == 'ju':
        period_full = 'juvenile'
    elif period == 'ad':
        period_full = 'adult'


    fish_period_full = fish_full + ' - ' + period_full

    sharea_path = "../SHArC/SHArea/" + case_name + "/" + case_name + "_sharea_" + fish_name + period + ".xlsx"

    ######################
    # Reading SHARrC data

    f1 = pd.read_excel(sharea_path, index_col=None, header=None,usecols="B")[3:].values.tolist()
    f2 = pd.read_excel(sharea_path, index_col=None, header=None,usecols="F")[3:].values.tolist()

    Flow = np.array(f1).transpose()[0]
    CalArea = np.array(f2).transpose()[0]

    Flow = np.append(Flow, [0])
    CalArea = np.append(CalArea, [0])

    ######################
    # Bankfull wetted area
    env.workspace = os.path.abspath("../SHArC/HSI/" + case_name)
    BfQ_hsi = "dsi_" + fish_period + fGl.write_Q_str(Flow[0]) + ".tif"

    # Check out the ArcGIS Spatial Analyst extension license
    arcpy.CheckOutExtension("Spatial")

    # Execute ExtractValuesToPoints
    rasters = arcpy.ListRasters("*", "tif")

    for raster in rasters:
        if raster == BfQ_hsi:
            print(raster)

            outRas = Raster(BfQ_hsi) > -1

            outPolygons = "BfQ_polygon.shp"
            arcpy.RasterToPolygon_conversion(outRas, outPolygons)

            # Set local variables
            inZoneData = outPolygons
            zoneField = "id"
            inClassData = outPolygons
            classField = "id"
            outTable = "BfQ_polygon_table.dbf"
            processingCellSize = 0.01

            # Execute TabulateArea
            TabulateArea(inZoneData, zoneField, inClassData, classField, outTable,
                         processingCellSize, "CLASSES_AS_ROWS")

            BfQ_area_dbf = simpledbf.Dbf5(env.workspace + '\\' + outTable)
            BfQ_partial_area = BfQ_area_dbf.to_dataframe()
            BfQ_area = np.sum(np.array(BfQ_partial_area['Area']))

            del BfQ_area_dbf
            del BfQ_partial_area
            #del BfQ_area

            arcpy.Delete_management(outPolygons)
            arcpy.Delete_management(outTable)

    # Reverse
    #Flow = Flow[::-1]
    #CalArea = CalArea[::-1]

    # Non-dimensionalization
    print(BfQ_area)
    Norm_Flow = Flow / Flow[0]
    Norm_CalArea = CalArea / BfQ_area
    #os.system("pause")

    ######################

    Norm_Flow_new = np.linspace(np.min(Norm_Flow), np.max(Norm_Flow), num=10001, endpoint=True)
    Norm_f = interp1d(Norm_Flow, Norm_CalArea, kind=interptype)
    f = interp1d(Flow, CalArea, kind=interptype)

    plt.figure(1)
    plt.plot(Norm_Flow, Norm_CalArea, marker="o", color=colors[ind], linewidth=0)
    plt.plot(Norm_Flow_new, Norm_f(Norm_Flow_new), color=colors[ind], label= fish_period_full)
    #plt.title(case_name + ', ' + fish_name + ', ' + period)
    plt.title(case_name)
    plt.xlabel('Ratio of discharge to bankfull discharge')
    plt.ylabel('Habitat area / Bankfull area')

    if scale_to_one & (ind == fish_periods.__len__()-1):
        bottom, top = plt.ylim()
        plt.ylim(0, 1.3)
    plt.legend()
    plt.show()
    #plt.savefig(figure_path+case_name+'_'+ fish_name + period +'_Area_Q.svg')
    plt.savefig(figure_path + case_name + '_SHArea_Q.svg')
    plt.savefig(figure_path + case_name + '_SHArea_Q.pdf')

    #########################
    # Reading flow timeseries

    f3 = pd.read_excel(timeseries_path, index_col=None, usecols="A")[3:].values.tolist()
    f4 = pd.read_excel(timeseries_path, indox_col=None, usecols="B")[3:].values.tolist()

    Date = np.array(f3).transpose()[0]
    Flow_series = np.array(f4).transpose()[0]
    Flow_series = np.floor(Flow_series*1000)/1000
    Eco_series = f(Flow_series)
    Norm_Eco_series = Eco_series / BfQ_area
    Norm_Flow_series = Flow_series / Flow[0]

    plt.figure(2)
    plt.plot(Flow_series, 'k')
    #plt.title(case_name + ', ' + fish_name + ', ' + period)
    plt.title(case_name)
    plt.xlabel('Time (days)')
    plt.ylabel('Discharge ($m^3$/s)')
    bottom, top = plt.ylim()
    plt.ylim(0, top)
    plt.show()
    #plt.savefig(figure_path+case_name+'_'+ fish_name + period +'_Q_time.svg')
    plt.savefig(figure_path + case_name + '_Q_time.svg')
    plt.savefig(figure_path + case_name + '_Q_time.pdf')

    plt.figure(3)
    plt.plot(Norm_Eco_series, label= fish_period_full)
    #plt.title(case_name + ', ' + fish_name + ', ' + period)
    plt.title(case_name)
    plt.xlabel('Time (days)')
    plt.ylabel('Habitat area / Bankfull area')
    if scale_to_one &(ind == fish_periods.__len__()-1):
        bottom, top = plt.ylim()
        plt.ylim(0, 1.3)
    plt.legend()
    plt.show()
    #plt.savefig(figure_path+case_name+'_'+ fish_name + period +'_Area_time.svg')
    plt.savefig(figure_path + case_name + '_SHArea_time.svg')
    plt.savefig(figure_path + case_name + '_SHArea_time.pdf')

    #########################
    # Sequence-average plot

    length = Eco_series.__len__()
    windows = range(365, length-1, 365)

    seq_min_series = []
    seq_avg_series = []
    seq_min_10 = []
    seq_min_90 = []
    seq_avg_10 = []
    seq_avg_90 = []

    for window in windows:
        for ii in range(0, length - window + 1):
            seq_min_series.append(np.min(Eco_series[ii:ii+window]))
            seq_avg_series.append(np.average(Eco_series[ii:ii+window]))
    #    seq_min_10.append(np.percentile(seq_min_series, 10))
    #    seq_min_90.append(np.percentile(seq_min_series, 90))
        seq_avg_10.append(np.percentile(seq_avg_series, 10))
        seq_avg_90.append(np.percentile(seq_avg_series, 90))

    # Normalize seq_avg_XX
    seq_avg_10 = seq_avg_10 / BfQ_area
    seq_avg_90 = seq_avg_90 / BfQ_area

    plt.figure(4)
    #plt.plot(seq_min_10)
    #plt.plot(seq_min_90)
    plt.plot(seq_avg_10, colors[ind]) #, label='10 Percentile')
    plt.plot(seq_avg_90, colors[ind], label= fish_period_full)

    # Patches
    m = []
    for i in range(seq_avg_10.__len__()):
        m.append(i)
    x = np.hstack(([m], [m[::-1]]))
    y = np.hstack(([seq_avg_10], [seq_avg_90[::-1]]))
    patches = []
    polygon = Polygon(np.transpose(np.vstack((x,y))), True)
    patches.append(polygon)

    p = PatchCollection(patches, alpha=0.4, facecolors=colors[ind])
    #p.set_array(np.array(colors))
    plt.gca().add_collection(p)

    #plt.title(case_name + ', ' + fish_name + ', ' + period)
    plt.title(case_name)
    plt.xlabel('Length of sequence (year)')
    plt.ylabel('Sequence-averaged Habitat area / Bankfull area')
    # return the current ylim
    if scale_to_one &(ind == fish_periods.__len__()-1):
        bottom, top = plt.ylim()
        plt.ylim(0, 1.3)
    plt.xlim(0, 5)
    plt.legend()
    plt.show()
    plt.savefig(figure_path + case_name + '_SHArea_seq_avg.svg')
    plt.savefig(figure_path + case_name + '_SHArea_seq_avg.pdf')

    ind += 1