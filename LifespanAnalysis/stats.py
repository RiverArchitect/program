try:
    import sys, os, logging, random
    import pandas as pd
    import tkinter as tk
    from tkinter.messagebox import askokcancel, showinfo
    from tkinter.filedialog import *
except:
    print("ExceptionERROR: Missing fundamental packages (required: os, sys, logging, random).")

try:
    import arcpy
    from arcpy.sa import *
except:
    print("ExceptionERROR: No valid arcpy found.")

try:
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')) + "\\.site_packages\\riverpy\\")
    import config
    import fGlobal as fGl
except:
    print("ExceptionERROR: Missing RiverArchitect packages (required: riverpy).")


class RunStats:
    def __init__(self, condition, __ras_name__, bound_shp, goal, flag, poly):
        self.condition = condition
        _name__ = __ras_name__.replace(".tif", "")
        self.ras_name = __ras_name__
        self.bound_shp = bound_shp
        self.goal = goal
        self.areas = []
        self.msg = ""
        self.output1 = config.dir2output + self.condition + "\\"
        self.output = config.dir2output + self.condition + "\\" + 'Stat' + _name__ + '.dbf'
        self.raster = config.dir2output + self.condition + "\\" + self.ras_name
        self.polygon = config.dir2output + self.condition + "\\" + 'Poly' + _name__ + '.shp'
        self.polygon1 = config.dir2output + self.condition + "\\" + 'Final_P_' + _name__ + '.shp'
        self.poly = poly
        self.dict = {}
        self.dict_percent = {}
        self.excel = config.dir2output + self.condition + "\\" + "PDF_" + _name__ + ".xlsx"

        self.total = 0
        self.target = ""
        self.cache = config.dir2lf + ".cache%s\\" % str(random.randint(1000000, 9999999))
        self.polygon2 = self.cache + "inter.shp"
        fGl.chk_dir(self.cache)
        self.new_one = self.cache + self.ras_name
        self.units = "us"
        self.given = 3
        self.flag = flag
        # self.new_raster = config.dir2output + self.condition + "\\" + 'new_raster'
        # self.output_poly =
        print(self.condition)
        print(self.raster)
        print(self.bound_shp)
        print(self.output)
        if goal == "":
            self.goal = 1
        raster1 = Raster(self.raster)
        # arcpy.SetRasterProperties_management(self.raster)
        # arcpy.management.BuildRasterAttributeTable(Int(raster1), True)
        # self.column = arcpy.GetRasterProperties_management(self.raster, 'COLUMNCOUNT')
        # self.row = arcpy.GetRasterProperties_management(self.raster, 'ROWCOUNT')

        # fields = arcpy.ListFields(self.raster)

        # for field in fields:
        #     print("{0} is a type of {1} with a length of {2}"
        #           .format(field.name, field.type, field.length))

        # indexes = arcpy.ListIndexes(self.bound_shp)
        # for index in indexes:
        #     print("Name        : {0}".format(index.name))
        #     print("IsAscending : {0}".format(index.isAscending))
        #     print("IsUnique    : {0}".format(index.isUnique))

        # for i in range(int(self.row[0])+1):
        #     for j in range(int(self.column[0])+1):
        #         self.location = str(i) + " " + str(j)
        #         self.result = arcpy.management.GetCellValue(self.raster, self.location)
        #         if self.result.getOutput(0) != 'NoData':
        #             self.cell_value = int(self.result.getOutput(0))
        #             print(self.cell_value)

        self.raster_new1 = Raster(self.raster)
        self.raster1 = Int(self.raster_new1)
        self.raster_use = Raster(raster1)
        self.ras_new = Raster(self.raster)
        self.r = self.sec_func()
        # return self.r
        # arcpy.management.CreateRasterDataset(self.output1, "test.tif")
        # arcpy.conversion.RasterToPolygon(self.raster, self.output, 'NO_SIMPLIFY')
        # self.raster_to_use = Raster(self.output1 + "test.tif")

    def sec_func(self):
        if self.flag == 0:
            ZonalStatisticsAsTable(self.raster1, 'Value', self.raster1, self.output)
        elif self.flag == 1:
            print("goal:")
            self.ras_new = Con(self.raster_use >= int(self.goal), 1)
            # isFile = os.path.isfile(self.polygon)
            # print(isFile)
            arcpy.conversion.RasterToPolygon(Int(self.ras_new), self.polygon, 'NO_SIMPLIFY')
            # arcpy.conversion.RasterToPolygon(Int(self.ras_new), self.polygon, 'NO_SIMPLIFY', 'Value')
            arcpy.AddField_management(self.polygon, "Area", "DOUBLE")
            if self.units == "us":
                exp = "!SHAPE.AREA@SQUAREFEET!"
            elif self.units == "si":
                exp = "!SHAPE.AREA@SQUAREMETERS!"
            arcpy.CalculateField_management(self.polygon, "Area", exp)
            # arcpy.management.CalculateGeometryAttributes(self.polygon,  [["DOUBLE", "AREA"], ["DOUBLE", "AREA"]],
                                                         # 'FEET_US')
            # def run_stats(self, sha_threshold, fish, apply_weighing=False):
            all_areas = self.polygon
            disconnected_areas = os.path.join(self.cache, "disc_area%06d.shp")
            arcpy.CopyFeatures_management(all_areas, disconnected_areas)
            for a in [value for (key, value) in arcpy.da.SearchCursor(all_areas, ['Id', 'Area'])]:
                self.areas.append(a)

            number = len(self.areas)
            self.msg = 'Total number of failing polygons : %d' % number
            self.popupmsg(self.msg)
            self.areas = []

        elif self.flag == 2:
            # print("goal:")
            self.ras_new = Con(self.raster_use >= int(self.goal), 1)
            # isFile = os.path.isfile(self.polygon)
            # print(isFile)
            # if isFile:
            #     os.remove(self.polygon)
            #     print("deleted")
            # arcpy.conversion.RasterToPolygon(Int(self.ras_new), self.polygon, 'NO_SIMPLIFY')
            # arcpy.conversion.RasterToPolygon(Int(self.ras_new), self.polygon, 'NO_SIMPLIFY', 'Value')
            # arcpy.AddField_management(self.polygon, "Area", "DOUBLE")
            if self.units == "us":
                exp = "!SHAPE.AREA@SQUAREFEET!"
            elif self.units == "si":
                exp = "!SHAPE.AREA@SQUAREMETERS!"
            arcpy.CalculateField_management(self.polygon, "Area", exp)
            # arcpy.management.CalculateGeometryAttributes(self.polygon,  [["DOUBLE", "AREA"], ["DOUBLE", "AREA"]],
            # 'FEET_US')
            # def run_stats(self, sha_threshold, fish, apply_weighing=False):

            all_areas = self.polygon
            disconnected_areas = os.path.join(self.cache, "disc_area%06d.shp")
            arcpy.CopyFeatures_management(all_areas, disconnected_areas)
            for a in [value for (key, value) in arcpy.da.SearchCursor(all_areas, ['Id', 'Area'])]:
                self.areas.append(a)
                print(a)
            self.areas.sort(reverse=True)
            for i in range(0, self.poly):
                if i == 0:
                    exp = "Area = %f" % self.areas[i]
                else:
                    exp = exp + " or Area = %f" % self.areas[i]

            disconnected_layer = os.path.join(self.cache, "disc_area%06d")
            # convert shp to feature layer
            arcpy.MakeFeatureLayer_management(disconnected_areas, disconnected_layer)
            # select largest area (mainstem)
            arcpy.SelectLayerByAttribute_management(disconnected_layer, "NEW_SELECTION", exp)
            arcpy.env.extent = Raster(self.raster)  # target needs matching extent so matrices align
            target_lyr = os.path.join(self.cache, "target")
            self.target = os.path.join(self.output1, "final.tif")
            arcpy.MakeFeatureLayer_management(disconnected_layer, target_lyr, exp)
            # convert target feature layer to raster
            cell_size = arcpy.GetRasterProperties_management(self.raster, 'CELLSIZEX').getOutput(0)
            arcpy.FeatureToRaster_conversion(target_lyr, 'gridcode', self.target, cell_size)
            # delete intermediate products (no longer needed, also removes schema lock issue)
            arcpy.Delete_management(disconnected_layer)
            arcpy.Delete_management(disconnected_areas)
            raster2 = Raster(self.target)
            arcpy.conversion.RasterToPolygon(Int(raster2), self.polygon1, 'NO_SIMPLIFY')
            number = len(self.areas)
            self.msg = 'Polygon Shapefile has been Created.'
            self.popupmsg(self.msg)
            return len(self.areas)

        elif self.flag == 3:
            arcpy.conversion.RasterToPolygon(Int(self.raster_use), self.polygon2, 'NO_SIMPLIFY')
            all_deatils = self.polygon2
            for a in [value for (key, value) in arcpy.da.SearchCursor(all_deatils, ['Id', 'gridcode'])]:
                self.total = self.total + 1
                if a in self.dict:
                    self.dict[a] += 1
                else:
                    self.dict[a] = 1
            print(self.total)
            print(self.dict)

            for key in self.dict:
                self.dict_percent[key] = (self.dict[key]/self.total)*100
            # self.logger.info("OK.")
            print(self.dict_percent)
            df = pd.DataFrame(data=self.dict_percent, index=[0])
            df = (df.T)
            print(df)
            df.to_excel(self.excel)


    def popupmsg(self,msg):
        LARGE_FONT = ("Verdana", 12)
        NORM_FONT = ("Verdana", 10)
        SMALL_FONT = ("Verdana", 8)
        popup = tk.Tk()
        popup.wm_title("!")
        label = tk.Label(popup, text=msg, font=NORM_FONT)
        label.pack(side="top", fill="x", pady=10)
        B1 = tk.Button(popup, text="Okay", command=popup.destroy)
        B1.pack()
        popup.mainloop()