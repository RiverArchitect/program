try:
    import os, sys
    import tkinter as tk
    from tkinter.messagebox import askokcancel, showinfo
    from tkinter.filedialog import *
    import webbrowser
    import stats
except:
    print("ExceptionERROR: Missing fundamental packages (required: os, sys, tkinter, webbrowser).")

try:
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')) + "\\")
    import child_gui as sg
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')) + "\\.site_packages\\riverpy\\")
    import config
    import cDefinitions as cDef
    import fGlobal as fGl
except:
    print("ExceptionERROR: Cannot find riverpy.")


class RunGui:
    def __init__(self, master):
        # Construct the Frame object.
        self.master = tk.Toplevel(master)
        self.master.wm_title("RUNNING ... (console messages)")
        self.master.bell()
        self.msg = ""

        # ARRANGE GEOMETRY
        self.ww = 400
        self.wh = 150
        self.wx = (self.master.winfo_screenwidth() - self.ww) / 2
        self.wy = (self.master.winfo_screenheight() - self.wh) / 2
        self.master.geometry("%dx%d+%d+%d" % (self.ww, self.wh, self.wx, self.wy))
        self.master.iconbitmap(config.code_icon)


class ActionGui(sg.RaModuleGui):
    def __init__(self, from_master):
        sg.RaModuleGui.__init__(self, from_master)
        self.ww = 810  # window width
        self.wh = 420  # window height
        self.title = "Lifespan Analysis"
        self.set_geometry(self.ww, self.wh, self.title)
        self.input_dir = ""
        self.condition = ""
        self.h_ras_path = ""
        self.dir_input_ras = ""
        self.condition_list = fGl.get_subdir_names(config.dir2output)
        self.condition_selected = False
        self.__ras_name__ = ""
        self.bound_shp = ""
        self.apply_boundary = tk.BooleanVar()
        self.result = ""
        self.flag = ""
        self.length = 0

        self.feature_list = []
        self.features = cDef.FeatureDefinitions(False)
        self.habitat = False
        self.manning_n = 0.0473934
        self.mapping = False
        self.out_lyt_dir = []
        self.out_ras_dir = []
        self.raster_list = ["All Rasters"]
        self.goal = ["2", '5', '10', '20', '70']
        self.listA = []
        self.__goal__ = ""
        self.__poly__ = ""
        self.fail_result = ""
        self.wild = False
        self.result_2 =""

        # GUI OBJECT VARIABLES
        self.gui_condition = tk.StringVar()
        self.gui_interpreter = tk.StringVar()
        self.extent_type = tk.StringVar()

        self.l_condition = tk.Label(self, text="Condition: \n")
        self.l_condition.grid(sticky=tk.W, row=0, column=0, padx=self.xd, pady=self.yd)
        self.b_v_condition = tk.Button(self, fg="red", text="Select",
                                       command=lambda: self.select_condition())
        self.b_v_condition.grid(sticky=tk.W, row=0, column=3, padx=self.xd, pady=self.yd)
        # self.l_n = tk.Label(self, text="Roughness (Manning\'s n): %.3f " % self.manning_n)
        # self.l_n.grid(sticky=tk.W, row=10, column=0, columnspan=3, padx=self.xd, pady=self.yd)

        # DROP DOWN ENTRIES (SCROLL BARS)
        self.sb_condition = tk.Scrollbar(self, orient=tk.VERTICAL)
        self.sb_condition.grid(sticky=tk.W, row=0, column=2, padx=0, pady=self.yd)
        self.lb_condition = tk.Listbox(self, height=3, width=14, yscrollcommand=self.sb_condition.set)
        for e in self.condition_list:
            self.lb_condition.insert(tk.END, e)
        self.lb_condition.grid(sticky=tk.W, row=0, column=1, padx=self.xd, pady=self.yd)
        self.sb_condition.config(command=self.lb_condition.yview)
        self.b_ref_condition = tk.Button(self, text="Refresh list", command=lambda: self.refresh_conditions(self.lb_condition, self.sb_condition, config.dir2output))
        self.b_ref_condition.grid(sticky=tk.W, row=0, column=4, padx=self.xd, pady=self.yd)

        self.l_raster = tk.Label(self, text="Select Raster: \n")
        self.l_raster.grid(sticky=tk.W, row=1, column=0, padx=self.xd, pady=self.yd)
        self.b_v_raster = tk.Button(self, fg="red", text="Select",
                                       command=lambda: self.select_raster())
        self.b_v_raster.grid(sticky=tk.W, row=1, column=3, padx=self.xd, pady=self.yd)

        # DROP DOWN ENTRIES (SCROLL BARS)
        self.sb_raster = tk.Scrollbar(self, orient=tk.VERTICAL)
        self.sb_raster.grid(sticky=tk.W, row=1, column=2, padx=0, pady=self.yd)
        self.lb_raster = tk.Listbox(self, height=4, width=14, yscrollcommand=self.sb_raster.set)
        for e in self.raster_list:
            self.lb_raster.insert(tk.END, e)
        self.lb_raster.grid(sticky=tk.W, row=1, column=1, padx=self.xd, pady=self.yd)
        self.sb_raster.config(command=self.lb_raster.yview)
        self.b_ref_raster = tk.Button(self, text="Refresh list",
                                         command=lambda: self.refresh_rasters(self.lb_raster, self.sb_raster,
                                                                              self.raster_list))
        self.b_ref_raster.grid(sticky=tk.W, row=1, column=4, padx=self.xd, pady=self.yd)

        self.l_goal = tk.Label(self, text="Design Lifespan Goal: \n")
        self.l_goal.grid(sticky=tk.W, row=2, column=0, padx=self.xd, pady=self.yd)
        self.b_v_goal = tk.Button(self, fg="red", text="Select",
                                    command=lambda: self.select_goal())
        self.b_v_goal.grid(sticky=tk.W, row=2, column=3, padx=self.xd, pady=self.yd)
        self.b_v_goal["state"] = "disabled"

        # DROP DOWN ENTRIES (SCROLL BARS)
        self.sb_goal = tk.Scrollbar(self, orient=tk.VERTICAL)
        self.sb_goal.grid(sticky=tk.W, row=2, column=2, padx=0, pady=self.yd)
        self.lb_goal = tk.Listbox(self, height=4, width=14, yscrollcommand=self.sb_goal.set)
        for e in self.goal:
            self.lb_goal.insert(tk.END, e)
        self.lb_goal.grid(sticky=tk.W, row=2, column=1, padx=self.xd, pady=self.yd)
        self.sb_goal.config(command=self.lb_raster.yview)
        # self.b_ref_raster = tk.Button(self, text="Refresh list",
                                      # command=lambda: self.refresh_rasters(self.lb_raster, self.sb_raster,
                                                                         #  self.raster_list))
        # self.b_ref_raster.grid(sticky=tk.W, row=1, column=4, padx=self.xd, pady=self.yd)

        self.l_poly = tk.Label(self, text="Largest X number of polygons: \n")
        self.l_poly.grid(sticky=tk.W, row=3, column=0, padx=self.xd, pady=self.yd)
        self.b_v_poly = tk.Button(self, fg="red", text="Select",
                                  command=lambda: self.select_poly())
        self.b_v_poly.grid(sticky=tk.W, row=3, column=3, padx=self.xd, pady=self.yd)
        self.b_v_poly["state"] = "disabled"

        # DROP DOWN ENTRIES (SCROLL BARS)
        self.sb_poly = tk.Scrollbar(self, orient=tk.VERTICAL)
        self.sb_poly.grid(sticky=tk.W, row=3, column=2, padx=0, pady=self.yd)
        self.lb_poly = tk.Listbox(self, height=4, width=14, yscrollcommand=self.sb_poly.set)
        for e in self.listA:
            self.lb_poly.insert(tk.END, e)
        self.lb_poly.grid(sticky=tk.W, row=3, column=1, padx=self.xd, pady=self.yd)
        self.sb_poly.config(command=self.lb_raster.yview)


        #CHECKBOX
        self.cb_bshp = tk.Checkbutton(self, text="Limit to the zone (shapefile)",
                                      variable=self.apply_boundary, onvalue=True, offvalue=False,
                                      command=lambda: self.activate_shape_selection(self.b_select_bshp))
        self.cb_bshp.grid(sticky=tk.W, row=0, column=4, columnspan=1, padx=self.xd, pady=self.yd)

        #Buttons
        self.b_select_bshp = tk.Button(self, width=8, bg="white", text="Select file",
                                       command=lambda: self.select_boundary_shp())
        self.b_select_bshp.grid(sticky=tk.W, row=0, column=5, padx=self.xd, pady=self.yd)
        self.b_select_bshp["state"] = "disabled"

        self.r_zone_stats = tk.Button(self, width=30, bg="white", text="Run Zone Stats as a Table", command=lambda:
        self.run_stats(self.condition, self.__ras_name__, self.bound_shp, self.__goal__))
        self.r_zone_stats.grid(sticky=tk.EW, row=1, column=4, columnspan=2, padx=self.xd, pady=self.yd)
        self.r_zone_stats["state"] = "disabled"

        self.pdf_r = tk.Button(self, width=10, bg="white", text="PDF Report", command=lambda:
        self.pdf_report(self.condition, self.__ras_name__, self.bound_shp, self.__goal__))
        self.pdf_r.grid(sticky=tk.EW, row=1, column=6, columnspan=1, padx=self.xd, pady=self.yd)
        self.pdf_r["state"] = "disabled"

        self.c_fail = tk.Button(self, width=30, bg="white", text="largest contiguous areas", command=lambda:
        self.c_fail_func(self.condition, self.__ras_name__, self.bound_shp, self.__goal__))
        self.c_fail .grid(sticky=tk.EW, row=2, column=4, columnspan=2, padx=self.xd, pady=self.yd)
        self.c_fail["state"] = "disabled"

        self.c_poly = tk.Button(self, width=30, bg="white", text="Run X largest contiguous areas", command=lambda:
        self.c_poly_func(self.condition, self.__ras_name__, self.bound_shp, self.__goal__, self.flag, self.__poly__))
        self.c_poly.grid(sticky=tk.EW, row=3, column=4, columnspan=2, padx=self.xd, pady=self.yd)
        self.c_poly["state"] = "disabled"

    def select_condition(self):
        try:
            print(" Select : ")
            items = self.lb_condition.curselection()
            self.condition = [self.condition_list[int(item)] for item in items][0]
            print(str(self.condition))
            self.input_dir = config.dir2output + str(self.condition)
            print("input")
            print("input :" + self.input_dir)
            if os.path.exists(self.input_dir) or self.mapping:
                #print("exists")
                self.b_v_condition.config(fg="forest green", text="Selected:\n" + self.condition)
                # self.b_mod_r["state"] = "normal"
                self.condition_selected = True
                #print("in the loop :")
                self.update_rasters()
                self.raster_list = fGl.get_subdir_names(self.input_dir)
                return ""
            else:
                self.b_v_condition.config(fg="red", text="ERROR")
                self.errors = True
                self.verified = False
                return "Invalid file structure (non-existent directory /LifespanDesign/Output/Rasters/)."
        except:
            self.errors = True
            self.verified = False
            return "Invalid entry for \'Condition\'."

    def update_rasters(self):
        # print("entered update_rasters :")
        try:
            self.lb_raster.delete(0, tk.END)  # try to empty listbox if currently filled
        except:
            pass

        # update depth raster file list from condition folder contents (raster has .aux.xml?)
        self.raster_list = ["All Rasters"]
        folder_names = fGl.file_names_in_dir(self.input_dir)
        # print(folder_names)
        if folder_names.__len__() < 1:
            folder_names = [i for i in os.listdir(self.input_dir) if i.endswith('.tif')]
            # print(folder_names)
        for fn in folder_names:
            #if fn[0] == "h":
            # print("fn: " + fn)
            if os.path.isdir(self.input_dir + "\\" + fn) or os.path.isfile(self.input_dir + "\\" + fn):
                if fn.endswith('.tif'):
                    self.raster_list.append(fn)

        for e in self.raster_list:
            # print("update_raster:" + e)
            self.lb_raster.insert(tk.END, e)
        self.sb_raster.config(command=self.lb_raster.yview)

    def update_poly(self):
        # print("entered update_rasters :")
        try:
            self.lb_poly.delete(0, tk.END)  # try to empty listbox if currently filled
        except:
            pass

        # update depth raster file list from condition folder contents (raster has .aux.xml?)
        # self.listA = []
        # folder_names = fGl.file_names_in_dir(self.input_dir)
        # print(folder_names)
        # if folder_names.__len__() < 1:
        #     folder_names = [i for i in os.listdir(self.input_dir) if i.endswith('.tif')]
            # print(folder_names)
        # for fn in folder_names:
        #     #if fn[0] == "h":
        #     # print("fn: " + fn)
        #     if os.path.isdir(self.input_dir + "\\" + fn) or os.path.isfile(self.input_dir + "\\" + fn):
        #         if fn.endswith('.tif'):
        #             self.raster_list.append(fn)

        for e in self.listA:
            # print("update_raster:" + e)
            self.lb_poly.insert(tk.END, e)
        self.sb_poly.config(command=self.lb_poly.yview)

    def select_raster(self):
        self.raster_list = ["All Rasters"]
        folder_names = fGl.file_names_in_dir(self.input_dir)
        # print(folder_names)
        if folder_names.__len__() < 1:
            folder_names = [i for i in os.listdir(self.input_dir) if i.endswith('.tif')]
            # print(folder_names)
        for fn in folder_names:
            # if fn[0] == "h":
            # print("fn: " + fn)
            if os.path.isdir(self.input_dir + "\\" + fn) or os.path.isfile(self.input_dir + "\\" + fn):
                if fn.endswith('.tif'):
                    self.raster_list.append(fn)
        items = self.lb_raster.curselection()
        # print("items:" + self.raster_list[int(items[0])])
        self.__ras_name__ = self.raster_list[int(items[0])]
        if not (self.__ras_name__ == "All Rasters"):
            self.h_ras_path = self.input_dir + "\\" + self.__ras_name__
            if os.path.exists(self.h_ras_path):
                self.b_v_raster.config(fg="forest green", text="Current: " + str(self.__ras_name__))
                self.r_zone_stats["state"] = "normal"
                self.pdf_r["state"] = "normal"
                self.b_v_goal["state"] = "normal"
            else:
                self.b_v_raster.config(fg="red", text="SELECTION ERROR                                 ")
        else:
            self.b_v_raster.config(fg="forest green", text="Current: All Rasters")
            self.h_ras_path = ""
            self.r_zone_stats["state"] = "normal"
            self.b_v_goal["state"] = "normal"

    def select_goal(self):
        items = self.lb_goal.curselection()
        # print("items:" + self.raster_list[int(items[0])])
        self.__goal__ = self.goal[int(items[0])]
        self.b_v_goal.config(fg="forest green", text="Current: " + str(self.__goal__))
        self.c_fail["state"] = "normal"

    def select_poly(self):
        items = self.lb_poly.curselection()
        # print("items:" + self.raster_list[int(items[0])])
        self.__poly__ = self.listA[int(items[0])]
        self.b_v_poly.config(fg="forest green", text="Current: " + str(self.__poly__))
        self.c_poly["state"] = "normal"

    def select_boundary_shp(self):
        self.bound_shp = askopenfilename(initialdir=config.dir2conditions,
                                         title="Select boundary shapefile:",
                                         filetypes=[("Shapefiles", "*.shp")])
        if os.path.isfile(self.bound_shp):
            self.b_select_bshp.config(fg="forest green")
        else:
            self.b_select_bshp.config(text="Invalid file.")
        self.logger.info(" >> Selected boundary shapefile: " + self.bound_shp)

    def activate_shape_selection(self, button):
        if self.apply_boundary.get():
            button["state"] = "normal"
            self.b_select_bshp.config(fg="red")
        else:
            button["state"] = "disabled"

    def run_stats(self, condition, __ras_name__, bound_shp, goal):
        self.flag = 0
        self.result = stats.RunStats(condition, __ras_name__, bound_shp, goal, self.flag, self.__poly__)

    def pdf_report(self, condition, __ras_name__, bound_shp, goal):
        self.flag = 3
        self.result = stats.RunStats(condition, __ras_name__, bound_shp, goal, self.flag, self.__poly__)

    def c_fail_func(self, condition, __ras_name__, bound_shp, goal):
        for a in range(1, 71):
            self.listA.append(a)
        self.update_poly()
        self.flag = 1
        self.b_v_poly["state"] = "normal"
        # self.fail_result = []
        self.fail_result = stats.RunStats(condition, __ras_name__, bound_shp, goal, self.flag, self.__poly__)
        # self.length = len(self.fail_result)
        # if self.length > 0:

    def c_poly_func(self, condition, __ras_name__, bound_shp, __goal__, flag, __poly__):
        self.flag = 2
        self.__poly__ = __poly__
        self.result_2 = stats.RunStats(condition, __ras_name__, bound_shp, __goal__, self.flag, self.__poly__)


    def __call__(self):
        self.mainloop()