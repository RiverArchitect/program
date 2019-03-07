# !/usr/bin/python
import sys, os
try:
    import cTerrainIO as cio

    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')) + "\\openpyxl\\")
    import openpyxl as oxl
except:
    print("ExceptionERROR: Cannot find package files (cTerrainIO.py / openpyxl/openpyxl).")


class FeatureReader:
    # Reads threshold values from file as a function of feature name
    def __init__(self):

        self.row_feat_names = 4
        self.row_feat_ids = 5

        self.path2lf = os.path.abspath(os.path.join(os.path.dirname(__file__), '..\\..')) + "\\LifespanDesign\\"
        self.thresh_xlsx = self.path2lf + ".templates\\threshold_values.xlsx"
        try:
            self.wb = oxl.load_workbook(filename=self.thresh_xlsx, read_only=True, data_only=True)
            wb_open = True
        except:
            wb_open = False
            print("FeatureReader: Could not find " + str(self.thresh_xlsx))
        try:
            if wb_open:
                self.ws = self.wb['thresholds']
            else:
                self.ws = ""
        except:
            print("FeatureReader: Could not find sheet \'thresholds\' in threshold_values.xlsx.")

    def close_wb(self):
        self.wb.close()

    def get_feat_id(self, column_list):
        feature_id_list = []
        for col in column_list:
            try:
                cell_value = str(self.ws[str(col) + str(self.row_feat_ids)].value)
            except:
                cell_value = ""
                print("FeatureReader: Failed to read values from threshold_values.xlsx (return empty).")
            feature_id_list.append(cell_value)
        return feature_id_list

    def get_feat_name(self, column_list):
        feature_list = []
        for col in column_list:
            try:
                cell_value = str(self.ws[str(col) + str(self.row_feat_names)].value)
            except:
                cell_value = ""
                print("FeatureReader: Failed to read values from threshold_values.xlsx (return empty).")
            feature_list.append(cell_value)
        return feature_list

    def __call__(self):
        print("Class Info: <type> = FeatureReader")


class Features:
    def __init__(self, *args):
        # args[0]: BOOL - False if called from application that cannot use "Custom DEM" option
        try:
            use_cust = args[0]
        except:
            use_cust = True  # Default value

        # Modify feature/plantings IDs, names and columns with thresholds types in the next lines
        self.threshold_cols_framework = ["E", "F", "G", "H", "I"]
        self.threshold_cols_plants = ["J", "K", "L", "M"]
        self.threshold_cols_toolbox = ["N", "O", "P"]
        self.threshold_cols_complement = ["Q", "R", "S"]
        self.fill_cols = ["E", "H", "I", "S", "O", "Q", "R"]  # columns with terrain filling feature IDs
        self.excavate_cols = ["E", "F", "G", "H", "I"]  # columns with terrain lowering feature IDs

        # DO NOT MODIFY ANYTHING DOWN HERE
        self.read_user_input = FeatureReader()
        self.id_list_framework = self.read_user_input.get_feat_id(self.threshold_cols_framework)
        self.id_list_plants = self.read_user_input.get_feat_id(self.threshold_cols_plants)
        self.id_list_toolbox = self.read_user_input.get_feat_id(self.threshold_cols_toolbox)
        self.id_list_complement = self.read_user_input.get_feat_id(self.threshold_cols_complement)
        self.name_list_framework = self.read_user_input.get_feat_name(self.threshold_cols_framework)
        self.name_list_plants = self.read_user_input.get_feat_name(self.threshold_cols_plants)
        self.name_list_toolbox = self.read_user_input.get_feat_name(self.threshold_cols_toolbox)
        self.name_list_complement = self.read_user_input.get_feat_name(self.threshold_cols_complement)
        self.fill_ids = self.read_user_input.get_feat_id(self.fill_cols)
        self.excavate_ids = self.read_user_input.get_feat_id(self.excavate_cols)
        self.read_user_input.close_wb()

        # merge lists
        self.id_list = []
        self.name_list = []
        self.threshold_cols = []

        [self.id_list.append(item) for item in self.id_list_framework]
        [self.name_list.append(item) for item in self.name_list_framework]
        [self.threshold_cols.append(item) for item in self.threshold_cols_framework]

        [self.id_list.append(item) for item in self.id_list_plants]
        [self.name_list.append(item) for item in self.name_list_plants]
        [self.threshold_cols.append(item) for item in self.threshold_cols_plants]

        [self.id_list.append(item) for item in self.id_list_toolbox]
        [self.name_list.append(item) for item in self.name_list_toolbox]
        [self.threshold_cols.append(item) for item in self.threshold_cols_toolbox]

        [self.id_list.append(item) for item in self.id_list_complement]
        [self.name_list.append(item) for item in self.name_list_complement]
        [self.threshold_cols.append(item) for item in self.threshold_cols_complement]

        if use_cust:
            self.id_list.append("cust")
            self.name_list.append("Custom DEM")
            self.threshold_cols.append("T")

        # create dictionaries
        self.feat_name_dict = dict(zip(self.id_list, self.name_list))
        self.feat_num_dict = dict(zip(self.id_list, range(0, self.id_list.__len__())))
        self.thresh_col_dict = dict(zip(self.id_list, self.threshold_cols))
        self.col_name_dict = dict(zip(self.name_list, self.threshold_cols))
        self.name_dict = dict(zip(self.name_list, self.id_list))

        if use_cust:
            # finalize excavation / terrain fill features
            self.fill_ids.append("cust")
            self.excavate_ids.append("cust")


class Reaches:
    def __init__(self):
        self.internal_id = ["reach_00", "reach_01", "reach_02", "reach_03", "reach_04", "reach_05", "reach_06",
                            "reach_07"]
        self.reach_no = range(0, self.internal_id.__len__())
        self.reader = cio.Read()
        self.id_xlsx = self.reader.get_reach_info("id")
        self.id_dict = dict(zip(self.internal_id, self.id_xlsx))
        self.id_no_dict = dict(zip(self.id_xlsx, self.reach_no))

        self.names_xlsx = self.reader.get_reach_info("full_name")
        self.name_dict = dict(zip(self.internal_id, self.names_xlsx))

        # make dictionaries containing reach id information
        self.dict_id_names = {}
        self.dict_id_int_id = {}
        i = 0
        for id in self.id_xlsx:
            self.dict_id_names.update({id: self.names_xlsx[i]})
            self.dict_id_int_id.update({id: self.internal_id[i]})
            i += 1
        del i

