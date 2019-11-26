try:
    import os, sys
    import tkinter as tk
    from tkinter.messagebox import askokcancel, showinfo
    from tkinter.filedialog import *
    import webbrowser
except:
    print("ExceptionERROR: Missing fundamental packages (required: os, sys, tkinter, webbrowser).")

try:
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')) + "\\")
    import slave_gui as sg
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')) + "\\.site_packages\\riverpy\\")
    import config
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

    def gui_geo_maker(self, condition, feature_type, units, inpath, dir_base_ras):
        import action_planner as ap
        ap.geo_file_maker(condition, feature_type, dir_base_ras, unit_system=units, alternate_inpath=inpath)

    def gui_map_maker(self, condition, feature_type):
        import action_planner as ap
        ap.map_maker(condition, feature_type)

    def gui_quit(self):
        self.master.destroy()


class ActionGui(sg.RaModuleGui):
    def __init__(self, from_master):
        sg.RaModuleGui.__init__(self, from_master)
        self.ww = 570  # window width
        self.wh = 400  # window height
        self.title = "Max Lifespan"
        self.set_geometry(self.ww, self.wh, self.title)
        
        self.dir_base_ras = "None (Geofile Maker only)"
        self.dir2lf_rasters = config.dir2lf + "Output\\Rasters\\"
        self.feature_text = []
        self.feature_type = []
        self.condition = "set condition"
        self.condition_list = fGl.get_subdir_names(self.dir2lf_rasters)
        self.inpath = config.dir2lf + "Output\\Rasters\\" + str(self.condition) + "\\"
        self.mod_dir = False    # if user-defined input directory: True

        # GUI OBJECT VARIABLES
        self.gui_condition = tk.StringVar()
        self.gui_interpreter = tk.StringVar()
        self.lf_extents = tk.BooleanVar()
        self.mapping = tk.BooleanVar()

        # LABELS
        self.l_s_feat = tk.Label(self, text="Selected feature layer: ")
        self.l_s_feat.grid(sticky=tk.W, row=0, column=0, padx=self.xd, pady=self.yd)
        self.l_features = tk.Label(self, width=40, fg="red",
                                   text="Select from \'Feature Layer\' Menu (Geofile Maker only)")
        self.l_features.grid(sticky=tk.W, row=0, column=1, columnspan=5, padx=self.xd, pady=self.yd)
        self.l_condition = tk.Label(self, text="Condition: \n(select)")
        self.l_condition.grid(sticky=tk.W, row=1, column=0, padx=self.xd, pady=self.yd)
        self.l_base_ras = tk.Label(self, text="Base raster: " + self.dir_base_ras)
        self.l_base_ras.grid(sticky=tk.W, row=6, column=0, columnspan=5, padx=self.xd, pady=self.yd)

        # DROP DOWN ENTRIES (SCROLL BARS)
        self.sb_condition = tk.Scrollbar(self, orient=tk.VERTICAL)
        self.sb_condition.grid(sticky=tk.W, row=1, column=2, padx=0, pady=self.yd)
        self.lb_condition = tk.Listbox(self, height=3, width=20, yscrollcommand=self.sb_condition.set)
        for e in self.condition_list:
            self.lb_condition.insert(tk.END, e)
        self.lb_condition.grid(sticky=tk.W, row=1, column=1, padx=self.xd, pady=self.yd)
        self.sb_condition.config(command=self.lb_condition.yview)
        self.b_ref_condition = tk.Button(self, text="Refresh list",
                                         command=lambda: self.refresh_conditions(self.lb_condition, self.sb_condition, config.dir2lf + "Output\\Rasters\\"))
        self.b_ref_condition.grid(sticky=tk.W, row=1, column=4, padx=self.xd, pady=self.yd)

        # ENTRIES
        self.l_inpath_curr = tk.Label(self, fg="dark slate gray", text="Source: "+str(self.dir2lf_rasters))
        self.l_inpath_curr.grid(sticky=tk.W, row=3, column=0, columnspan=5, padx=self.xd, pady=self.yd)

        # BUTTONS
        self.b_c_help = tk.Button(self, width=5, bg="white", text="Info", command=lambda: self.condition_info())
        self.b_c_help.grid(sticky=tk.W, row=1, column=3, padx=self.xd, pady=self.yd)
        self.b_inpath = tk.Button(self, width=50, bg="white", text="Change input directory",
                                  command=lambda: self.change_inpath())
        self.b_inpath.grid(sticky=tk.W, row=2, column=0, columnspan=5, padx=self.xd, pady=self.yd)
        self.b_mod_m = tk.Button(self, width=50, bg="white", text="Modify map extent", command=lambda:
                                 self.open_inp_file("mapping.inp"))
        self.b_mod_m.grid(sticky=tk.W, row=7, column=0, columnspan=5, padx=self.xd, pady=self.yd)
        self.b_set_base = tk.Button(self, width=50, bg="white", text="Define extent Raster (FLOAT tif-raster)",
                                    command=lambda: self.set_base_ras())
        self.b_set_base.grid(sticky=tk.W, row=5, column=0, columnspan=5, padx=self.xd, pady=self.yd)

        self.complete_menus()

        # CHECK BOXES (CHECKBUTTONS)
        self.cb_base = tk.Checkbutton(self, fg="SteelBlue", text="Use lifespan Raster extents OR",
                                      variable=self.lf_extents, onvalue=True, offvalue=False)
        self.cb_base.grid(sticky=tk.W, row=4, column=0, columnspan=5, padx=self.xd, pady=self.yd)
        self.cb_base.select()
        self.cb_lyt = tk.Checkbutton(self, fg="SteelBlue", text="Create maps and layouts after making geofiles",
                                     variable=self.mapping, onvalue=True, offvalue=False)
        self.cb_lyt.grid(sticky=tk.W, row=8, column=0, columnspan=5, padx=self.xd, pady=self.yd)

    def set_base_ras(self):
        self.dir_base_ras = askopenfilename(defaultextension=".tif", initialdir=config.dir2conditions,
                                            filetypes=[("GeoTIFF files", "*.tif")])
        self.l_base_ras.config(fg="green4", text="Base raster: " + self.dir_base_ras)
        self.b_set_base.config(fg="green4")

    def complete_menus(self):
        # FEATURE DROP DOWN
        self.featmenu = tk.Menu(self.mbar, tearoff=0)  # create new menu
        self.mbar.add_cascade(label="Feature layer", menu=self.featmenu)  # attach it to the menubar
        # add menu entries
        self.featmenu.add_command(label="Group layer: Terraforming", command=lambda: self.define_feature("Terraforming"))
        self.featmenu.add_command(label="Group layer: Plantings", command=lambda: self.define_feature("Plantings"))
        self.featmenu.add_command(label="Group layer: Nature-based (other)", command=lambda: self.define_feature("Bioengineering"))
        self.featmenu.add_command(label="Group layer: Connectivity", command=lambda: self.define_feature("Connectivity"))
        self.featmenu.add_command(label="CLEAR", command=lambda: self.define_feature("clear"))

        # RUN DROP DOWN
        self.runmenu = tk.Menu(self.mbar, tearoff=0)  # create new menu
        self.mbar.add_cascade(label="Run", menu=self.runmenu)  # attach it to the menubar
        self.runmenu.add_command(label="Verify settings", command=lambda: self.verify())
        self.runmenu.add_command(label="Run: Geofile Maker", command=lambda: self.run_geo_maker())
        self.runmenu.add_command(label="Run: Map Maker", command=lambda: self.run_map_maker())

    def condition_info(self):
        msg = "The condition list refers to available rasters in\n" + self.dir2lf_rasters + \
              "\n\nThe selected condition will be used for the maximum lifespan map generation."
        showinfo("CONDITION INFO", msg)

    def change_inpath(self):
        self.inpath = askdirectory(initialdir='.')
        self.inpath = self.inpath + "/"
        self.l_inpath_curr.config(fg="dark slate gray", text="Current: " + str(self.inpath))
        self.mod_dir = True

    def define_feature(self, feature_type):
        if not(feature_type == "clear"):
            self.feature_text.append(feature_type)
            self.feature_type.append(feature_type.lower() + "_mlf")
            self.l_features.config(fg="SteelBlue", text=", ".join(self.feature_text))
        else:
            self.feature_text = []
            self.feature_type = []
            self.l_features.config(fg="red",
                                   text="Select from \'Feature layer\' Menu (Geofile Maker only)")

    def open_inp_file(self, filename):
        _f = r'' + os.path.dirname(os.path.abspath(__file__)) + "\\.templates\\" + filename
        if os.path.isfile(_f):
            try:
                webbrowser.open(_f)
            except:
                showinfo("ERROR ", "Cannot open " + str(filename) +
                         ". Make sure that your operating system has a standard application defined for *.inp-files.")
        else:
            showinfo("ERROR ", "The file " + str(filename) + " does not exist. Check MaxLifespan directory.")

    def open_log_file(self):
        logfilenames = ["error.log", "max_lifespan.log", "logfile.log", "map_logfile.log", "mxd_logfile.log"]
        for filename in logfilenames:
            _f = r'' + os.path.dirname(os.path.abspath(__file__)) + "\\" + filename
            if os.path.isfile(_f):
                try:
                    webbrowser.open(_f)
                except:
                    pass

    def run_geo_maker(self):
        showinfo("INFORMATION", "Analysis takes a while. \nPython windows seem unresponsive in the meanwhile. \nCheck console messages.\n \nPRESS OK TO START")
        if not self.verified:
            self.verify()
        if self.verified:
            run = RunGui(self)
            if self.lf_extents.get():
                self.dir_base_ras = "blank"

            for feat in self.feature_type:
                run.gui_geo_maker(self.condition, feat.split("_mlf")[0], self.unit, self.inpath, self.dir_base_ras)
                run.gui_quit()
            self.l_inpath_curr.config(fg="forest green", text="Finished.")

            if not self.mapping.get():
                self.master.bell()
                tk.Button(self, bg="gold", width=50, text="IMPORTANT\n Read logfile(s)", command=lambda:
                          self.open_log_file()).grid(sticky=tk.W, row=3, column=0, columnspan=3, padx=self.xd, pady=self.yd)
            else:
                tk.Button(self, bg="pale green", width=50, text="IMPORTANT\n Read logfile(s) from Map Maker",
                          command=lambda:
                          self.open_log_file()).grid(sticky=tk.W, row=3, column=0, columnspan=3, padx=self.xd, pady=self.yd)
            if self.mapping.get():
                self.run_map_maker()
        self.verified = False

    def run_map_maker(self):
        if not self.verified:
            self.verify(False)
        if self.verified:
            if not self.mapping.get():
                showinfo("INFORMATION",
                         "Map creation may take some minutes. \n Python windows seem unresponsive in the meanwhile. \n Check console messages.\n \n PRESS OK TO START")
            run = RunGui(self)
            run.gui_map_maker(self.condition, self.feature_type)
            run.gui_quit()

            self.master.bell()

            tk.Button(self, bg="pale green", width=50, text="IMPORTANT\n Read logfile(s)", command=lambda:
                      self.open_log_file()).grid(sticky=tk.W, row=3, column=0, columnspan=3, padx=self.xd, pady=self.yd)

    def verify(self, *args):
        # args[0] = True limits verification to condition only
        try:
            full_check = args[0]
        except:
            full_check = True

        error_msg = []
        self.verified = True
        if full_check:
            try:
                import action_planner
            except:
                error_msg.append("Check installation of the MaxLifespan module.")
                self.verified = False
                self.errors = True
            for feat in self.feature_type:
                if not (feat.__len__() > 0):
                    error_msg.append("Select feature layer.")
                    self.verified = False
                    self.errors = True
                else:
                    self.l_features.destroy()
                    self.l_features = tk.Label(self, fg="forest green", text=", ".join(self.feature_type))
                    self.l_features.grid(sticky=tk.W, row=0, column=1, columnspan=3, padx=self.xd, pady=self.yd)
            try:
                if not (sys.version_info.major == 3):
                    import arcpy
                    error_msg.append("Wrong Python interpreter (Required: Python3 with arcpy).")
                    self.errors = True
                    self.verified = False
            except:
                pass
        try:
            items = self.lb_condition.curselection()
            self.condition = [self.condition_list[int(item)] for item in items][0]
            if not self.mod_dir:
                self.inpath = r"" + self.dir2lf_rasters + str(self.condition) + "\\"

            self.l_inpath_curr.config(fg="forest green", text="Apply: " + str(self.inpath))

            if str(self.condition).__len__() < 2:
                error_msg.append("Invalid condition.")
                self.errors = True
                self.verified = False
        except:
            pass

        if self.errors:
            self.master.bell()
            showinfo("VERIFICATION ERROR(S)", "\n ".join(error_msg))
            self.errors = False

    def __call__(self):
        self.mainloop()
