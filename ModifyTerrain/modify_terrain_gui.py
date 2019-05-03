try:
    import os, sys
    import tkinter as tk
    from tkinter.messagebox import askokcancel, showinfo
    from tkinter.filedialog import *
    import webbrowser
    import cModifyTerrain as cmt
except:
    print("ExceptionERROR: Missing fundamental packages (required: os, sys, Tkinter, webbrowser).")

try:
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')) + "\\.site_packages\\riverpy\\")
    import fGlobal as fg
    import cReachManager as cio
    import cDefinitions as cdef
    import cMapper as cmp
except:
    print("ExceptionERROR: Cannot find package files (/.site_packages/riverpy/*.py).")


class MainGui(tk.Frame):
    def __init__(self, master=None):
        self.dir2ra = os.path.abspath(os.path.join(os.path.dirname(__file__), '..')) + "\\"
        self.dir_ras_vol = ""
        self.path = r"" + os.path.dirname(os.path.abspath(__file__))
        self.condition = ""
        self.errors = False
        self.features = cdef.Features()
        self.feature_id_list = []
        self.feature_name_list = []
        self.in_feat = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..")) + "\\MaxLifespan\\Output\\Rasters\\"
        self.in_topo = os.path.abspath(os.path.join(os.path.dirname(__file__), "..")) + "\\01_Conditions\\"
        self.in_vol = os.path.dirname(os.path.abspath(__file__)) + "\\Input\\DEM\\"
        self.logfile_name = "logfile.log"
        self.mapping = False
        self.mod_dir = None
        self.prevent_popup = False
        self.reader = cio.Read()
        self.reaches = cdef.Reaches()
        self.reach_ids_applied = []  # self.reaches.id_xlsx ## initial: all reaches (IDs)
        self.reach_names_applied = []  # self.reaches.names_xlsx ## initial: all reaches (full names)
        self.reach_lookup_needed = False
        self.template_dir = os.path.dirname(os.path.abspath(__file__)) + "\\.templates\\"
        self.unit = "us"
        self.verified = False
        self.vol_only = True
        self.volume_types = []  # automatically append for -1=excavation and +1=fill features

        # Construct the Frame object.
        tk.Frame.__init__(self, master)
        # if imported from master GUI, redefine master as highest level (ttk.Notebook tab container)
        if __name__ != '__main__':
            self.master = self.master.master
        self.pack(expand=True, fill=tk.BOTH)

        self.set_geometry()

        # GUI OBJECT VARIABLES
        self.gui_condition = tk.StringVar()
        self.gui_interpreter = tk.StringVar()
        self.mapping = tk.BooleanVar()

        # LABELS
        self.l_reach_label = tk.Label(self, fg="dark slate gray", text="Reaches:")
        self.l_reach_label.grid(sticky=tk.W, row=0, column=0, columnspan=1, padx=self.xd, pady=self.yd * 2)
        self.l_reaches = tk.Label(self, fg="red", text="Select from Reaches menu")
        self.l_reaches.grid(sticky=tk.W, row=0, column=1, columnspan=5, padx=self.xd, pady=self.yd * 2)
        self.l_condition = tk.Label(self, fg="dark slate gray", text="Condition: ")
        self.l_condition.grid(sticky=tk.W, row=2, column=0, padx=self.xd, pady=self.yd * 2)
        self.l_s_feat = tk.Label(self, fg="dark slate gray", text="Selected features: ")
        self.l_s_feat.grid(sticky=tk.W, row=1, column=0, padx=self.xd, pady=self.yd * 2)
        self.l_features = tk.Label(self, fg="red",
                                   text="Choose from \"Features\" Menu\n(requires maximum lifespan rasters or CAD-modified rasters)")
        self.l_features.grid(sticky=tk.W, row=1, column=1, columnspan=7, padx=self.xd, pady=self.yd)
        self.l_inp = tk.Label(self, fg="dark slate gray", text="Current topo raster input directory:")
        self.l_inp.grid(sticky=tk.W, row=4, column=0, columnspan=2, padx=self.xd, pady=self.yd)
        self.l_inpath_topo = tk.Label(self, fg="dark slate gray", text=str(self.in_topo))
        self.l_inpath_topo.grid(sticky=tk.W, row=5, column=0, columnspan=5, padx=self.xd, pady=self.yd)
        self.l_inp_feat = tk.Label(self, fg="snow3", text="Current MaxLifespan raster directory:")
        self.l_inp_feat.grid(sticky=tk.W, row=9, column=0, columnspan=2, padx=self.xd, pady=self.yd)
        self.l_inpath_feat = tk.Label(self, fg="snow3", text=str(self.in_feat))
        self.l_inpath_feat.grid(sticky=tk.W, row=10, column=0, columnspan=5, padx=self.xd, pady=self.yd)
        self.l_inp_vol = tk.Label(self, fg="snow3", text="Input directory of CAD-modified DEMs for volume computation:")
        self.l_inp_vol.grid(sticky=tk.W, row=13, column=0, columnspan=5, padx=self.xd, pady=self.yd)
        self.l_inpath_vol = tk.Label(self, fg="snow3", text="None")
        self.l_inpath_vol.grid(sticky=tk.W, row=14, column=0, columnspan=5, padx=self.xd, pady=self.yd)

        # ENTRIES
        self.e_condition = tk.Entry(self, bg="salmon", width=10, textvariable=self.gui_condition)
        self.e_condition.grid(sticky=tk.EW, row=2, column=1, padx=self.xd, pady=self.yd)

        # BUTTONS
        self.b_condition = tk.Button(self, width=5, bg="white", text="Verify",
                                     command=lambda: self.generate_inpath())
        self.b_condition.grid(sticky=tk.W, row=2, column=2, padx=self.xd, pady=self.yd*5)
        self.b_in_topo = tk.Button(self, width=25, bg="white", text="Change input topo (condition DEM) directory (optional)",
                                   command=lambda: self.change_in_topo())
        self.b_in_topo.grid(sticky=tk.EW, row=3, column=0, columnspan=5, padx=self.xd, pady=self.yd)
        self.b_in_feat = tk.Button(self, width=25, fg="snow3", bg="gray90", text="Change feature max. lifespan raster directory (widen / grading)",
                                   command=lambda: showinfo("INFO", "Check max. lifespan raster box first."))
        self.b_in_feat.grid(sticky=tk.EW, row=8, column=0, columnspan=5, padx=self.xd, pady=self.yd)
        self.b_set_vol_ras = tk.Button(self, fg="snow3", width=25, bg="gray90", text="Set directory of CAD-modified DEM rasters",
                                       command=lambda: showinfo("INFO", "Check volume calculation box first."))
        self.b_set_vol_ras.grid(sticky=tk.EW, row=12, column=0, columnspan=5, padx=self.xd, pady=self.yd)

        self.make_menu()

        # CHECK BOXES
        self.cb_mterrain = tk.Checkbutton(self, fg="dark slate gray",
                                          text="Enable max. lifespan-based terrain modification (Graden and Widen only)",
                                          command=lambda: self.enable_mterrain())
        self.cb_mterrain.grid(sticky=tk.W, row=7, column=0, columnspan=5, padx=self.xd, pady=self.yd)
        self.cb_volumes = tk.Checkbutton(self, fg="dark slate gray",
                                         text="Enable volume difference calculator",
                                         command=lambda: self.enable_volumes())
        self.cb_volumes.grid(sticky=tk.W, row=11, column=0, columnspan=5, padx=self.xd, pady=self.yd)
        self.cb_mapping = tk.Checkbutton(self, fg="dark slate gray",
                                         text="Automatically run mapping after DEM / volume calculation.",
                                         variable=self.mapping, onvalue=True, offvalue=False)
        self.cb_mapping.grid(sticky=tk.W, row=15, column=0, columnspan=5, padx=self.xd, pady=self.yd*2)
        self.cb_mapping.deselect()  # select by default

    def set_geometry(self):
        # ARRANGE GEOMETRY
        self.ww = 580  # window width
        self.wh = 650  # window height
        self.xd = 5  # distance holder in x-direction (pixel)
        self.yd = 5  # distance holder in y-direction (pixel)
        # Upper-left corner of the window.
        self.wx = (self.master.winfo_screenwidth() - self.ww) / 2
        self.wy = (self.master.winfo_screenheight() - self.wh) / 2
        # Set the height and location.
        self.master.geometry("%dx%d+%d+%d" % (self.ww, self.wh, self.wx, self.wy))
        # Give the window a title.
        if __name__ == '__main__':
            self.master.title("Modify Terrain")
            self.master.iconbitmap(self.dir2ra + ".site_packages\\templates\\code_icon.ico")

    def make_menu(self):
        # DROP DOWN MENU
        # the menu does not need packing - see page 44ff
        self.mbar = tk.Menu(self)  # create new menubar
        self.master.config(menu=self.mbar)  # attach it to the root window

        # FEATURES DROP DOWN
        self.featmenu = tk.Menu(self.mbar, tearoff=0)  # create new menu
        self.mbar.add_cascade(label="Features", menu=self.featmenu)  # attach it to the menubar
        self.featmenu.add_command(label="ALL", command=lambda: self.define_feature(""))
        self.featmenu.add_command(label="Terraform: Custom (CAD-modified DEM)", command=lambda: self.define_feature("cust"))
        self.featmenu.add_command(label="Terraform: Grading", command=lambda: self.define_feature("grade"))
        self.featmenu.add_command(label="Terraform: Widen", command=lambda: self.define_feature("widen"))
        self.featmenu.add_command(label="CLEAR ALL", command=lambda: self.define_feature("clear"))

        # REACH  DROP DOWN
        self.reach_lookup_needed = False
        self.reachmenu = tk.Menu(self.mbar, tearoff=0)  # create new menu
        self.mbar.add_cascade(label="Reaches", menu=self.reachmenu)  # attach it to the menubar
        self.build_reach_menu()

        # UNIT SYSTEM DROP DOWN
        self.unitmenu = tk.Menu(self.mbar, tearoff=0)  # create new menu
        self.mbar.add_cascade(label="Units", menu=self.unitmenu)  # attach it to the menubar
        self.unitmenu.add_command(label="[current]  U.S. customary", background="pale green")
        self.unitmenu.add_command(label="[             ]  SI (metric)", command=lambda: self.unit_change())

        # RUN DROP DOWN
        self.runmenu = tk.Menu(self.mbar, tearoff=0)  # create new menu
        self.mbar.add_cascade(label="Run", menu=self.runmenu)  # attach it to the menubar
        self.runmenu.add_command(label="Verify settings", command=lambda: self.verify())
        self.runmenu.add_command(label="Run: DEM Modification", foreground="snow3")
        self.runmenu.add_command(label="Run: Volume Calculator", foreground="snow3")
        self.runmenu.add_command(label="Run: Map Maker", foreground="snow3")

        # CLOSE DROP DOWN
        self.closemenu = tk.Menu(self.mbar, tearoff=0)  # create new menu
        self.mbar.add_cascade(label="Close", menu=self.closemenu)  # attach it to the menubar
        self.closemenu.add_command(label="Credits", command=lambda: self.show_credits())
        self.closemenu.add_command(label="Quit program", command=lambda: self.myquit())

    def add_reach(self, reach):
        if str(reach).__len__() < 1:
            self.reach_names_applied = fg.dict_values2list(self.reaches.name_dict.values())
            self.reach_ids_applied = fg.dict_values2list(self.reaches.id_dict.values())
            if self.reach_names_applied.__len__() > 5:
                label_text = "Many / All"
            else:
                label_text = ", ".join(self.reach_names_applied)
            self.l_reaches.config(fg="dark slate gray", text=label_text)
        else:
            if not(reach == "clear"):
                if not(reach in self.reach_names_applied):
                    self.reach_names_applied.append(self.reaches.name_dict[reach])
                    self.reach_ids_applied.append(self.reaches.id_dict[reach])
                if self.reach_names_applied.__len__() > 5:
                    label_text = "Many / All"
                else:
                    label_text = ", ".join(self.reach_names_applied)
                self.l_reaches.config(fg="dark slate gray", text=label_text)
            else:
                self.reach_names_applied = []
                self.reach_ids_applied = []
                self.l_reaches.config(fg="red", text="Select from \'Reaches\' Menu")

    def build_reach_menu(self):
        if not self.reach_lookup_needed:
            self.reachmenu.add_command(label="DEFINE REACHES", command=lambda: self.define_reaches())
            self.reachmenu.add_command(label="RE-BUILD MENU", command=lambda: self.build_reach_menu())
            self.reachmenu.add_command(label="_____________________________")
            self.reachmenu.add_command(label="ALL", command=lambda: self.add_reach(""))
            self.reachmenu.add_command(label="CLEAR ALL", command=lambda: self.add_reach("clear"))
            self.reachmenu.add_command(label="_____________________________")
            self.reachmenu.add_command(label=self.reaches.name_dict["reach_00"], command=lambda: self.add_reach("reach_00"))
            self.reachmenu.add_command(label=self.reaches.name_dict["reach_01"], command=lambda: self.add_reach("reach_01"))
            self.reachmenu.add_command(label=self.reaches.name_dict["reach_02"], command=lambda: self.add_reach("reach_02"))
            self.reachmenu.add_command(label=self.reaches.name_dict["reach_03"], command=lambda: self.add_reach("reach_03"))
            self.reachmenu.add_command(label=self.reaches.name_dict["reach_04"], command=lambda: self.add_reach("reach_04"))
            self.reachmenu.add_command(label=self.reaches.name_dict["reach_05"], command=lambda: self.add_reach("reach_05"))
            self.reachmenu.add_command(label=self.reaches.name_dict["reach_06"], command=lambda: self.add_reach("reach_06"))
            self.reachmenu.add_command(label=self.reaches.name_dict["reach_07"], command=lambda: self.add_reach("reach_07"))
            self.reach_lookup_needed = True
        else:
            # re-build reach names if workbook was modified
            self.reaches.names_xlsx = self.reader.get_reach_info("full_name")
            self.reaches.name_dict = dict(zip(self.reaches.internal_id, self.reaches.names_xlsx))
            self.reachmenu.entryconfig(6, label=self.reaches.name_dict["reach_00"])
            self.reachmenu.entryconfig(7, label=self.reaches.name_dict["reach_01"])
            self.reachmenu.entryconfig(8, label=self.reaches.name_dict["reach_02"])
            self.reachmenu.entryconfig(9, label=self.reaches.name_dict["reach_03"])
            self.reachmenu.entryconfig(10, label=self.reaches.name_dict["reach_04"])
            self.reachmenu.entryconfig(11, label=self.reaches.name_dict["reach_05"])
            self.reachmenu.entryconfig(12, label=self.reaches.name_dict["reach_06"])
            self.reachmenu.entryconfig(13, label=self.reaches.name_dict["reach_07"])

    def change_in_feat(self):
        msg0 = "Make sure there is ONE raster in the directory that contains the string of a feature ID. "
        msg1 = "Valid feature IDs are:\n"
        msglist = []
        try:
            feat_dict = dict(zip(self.features.name_list, self.features.id_list))
            for feat in feat_dict.items():
                msglist.append(": ".join(feat))
            showinfo("SET DIRECTORY", msg0 + msg1 + ", ".join(msglist))
        except:
            pass
        self.in_feat = askdirectory(initialdir=".") + "/"
        if str(self.in_feat).__len__() > 1:
            self.l_inpath_feat.config(fg="dark slate gray", text=str(self.in_feat))
        else:
            self.l_inpath_feat.config(fg="red", text="Invalid directory")
        self.mod_dir = True

    def change_in_topo(self):
        msg0 = "Make sure there is ONE raster in the directory is named \'dem\'.\n"
        showinfo("SET DIRECTORY", msg0)
        self.in_topo = askdirectory(initialdir=".") + "/"
        if str(self.in_topo).__len__() > 1:
            self.l_inpath_topo.config(fg="dark slate gray", text=str(self.in_topo))
        else:
            self.l_inpath_topo.config(fg="red", text="Invalid directory")
        self.mod_dir = True

    def define_feature(self, feature_id):
        if feature_id.__len__() < 1:
            # append ALL available features
            self.feature_id_list = self.features.id_list
            self.feature_name_list = self.features.name_list
            self.l_features.config(fg="SteelBlue", text=", ".join(self.feature_name_list))
        else:
            if not(feature_id == "clear"):
                if not(feature_id == "cust"):
                    if not(feature_id in self.feature_id_list):
                        # append single features
                        self.feature_id_list.append(feature_id)
                        self.feature_name_list.append(self.features.feat_name_dict[feature_id])
                    self.l_features.config(fg="SteelBlue", text=", ".join(self.feature_name_list))
                else:
                    # custom feature from CAD (contour modification)
                    self.feature_id_list.append(feature_id)
                    self.l_features.config(fg="SteelBlue", text="Custom: Define CAD-modified DEM directory.")
                    self.enable_volumes()
                    self.cb_volumes.select()
            else:
                # clear all features
                self.feature_id_list = []
                self.feature_name_list = []
                self.l_features.config(fg="red", text="Select from \'Features\' Menu")

        if ("grade" in self.feature_id_list) or ("widen" in self.feature_id_list):
            self.vol_only = False
            self.runmenu.entryconfig(1, label="Run: DEM Modification", foreground="dark slate gray",
                                     command=lambda: self.run_modification())

    def define_reaches(self):
        try:
            webbrowser.open(self.template_dir + "computation_extents.xlsx")
            self.reach_lookup_needed = True  # tells build_reachmenu that lookup of modified spreasheet info is needed
        except:
            showinfo("ERROR", "Cannot open the file\n" + self.template_dir + "computation_extents.xlsx")

    def enable_mterrain(self):
        self.b_in_feat.config(fg="dark slate gray", width=25, bg="white",
                              text="Change feature max. lifespan raster directory (optional for widen / grading)",
                              command=lambda: self.change_in_feat())
        self.cb_volumes.select()
        self.l_inp_feat.config(fg="dark slate gray", text="Current max. lifespan raster directory:")
        self.l_inpath_feat.config(fg="dark slate gray", text=str(self.in_feat))
        self.runmenu.entryconfig(1, label="Run: DEM Modification", foreground="dark slate gray",
                                 command=lambda: self.run_modification())
        self.vol_only = False

    def enable_volumes(self):
        self.runmenu.entryconfig(2, label="Run: Volume calculator", foreground="dark slate gray",
                                 command=lambda: self.run_volume_calculator())
        self.l_inp_vol.config(fg="dark slate gray", text="Input directory of modified DEMs for volume computation:")
        self.l_inpath_vol.config(fg="dark slate gray", text=str(self.in_vol))
        self.b_set_vol_ras.config(fg="dark slate gray", width=25, bg="white",
                                  text="Set directory of modified DEM rasters", command=lambda: self.set_dir2vol_ras())
        self.vol_only = True

    def generate_inpath(self):
        self.condition = self.e_condition.get()
        self.in_topo = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..")) + "\\01_Conditions\\" + str(self.condition) + "\\"
        self.in_feat = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..")) + "\\MaxLifespan\\Output\\Rasters\\" + str(
            self.condition) + "\\"
        self.in_vol = os.path.dirname(os.path.abspath(__file__)) + "\\Input\\DEM\\" + str(
            self.condition) + "\\"

        self.e_condition.config(bg="pale green", width=10, textvariable=self.gui_condition)

        if os.path.exists(self.in_topo):
            self.l_inpath_topo.config(fg="forest green", text=str(self.in_topo))

        else:
            if not os.path.isfile(self.in_topo + 'dem.aux.xml'):
                self.b_in_topo.config(fg="red", width=25, bg="white",
                                      text="Change input topo (condition DEM) directory (REQUIRED)",
                                      command=lambda: self.change_in_topo())
                showinfo("WARNING", "Cannot find DEM grid:\n" + self.in_topo + "dem\nTopo (DEM) input directory required")
            self.l_inpath_topo.config(fg="red", text="Set topo input directory")
        if os.path.exists(self.in_feat) and not self.vol_only:
            self.l_inpath_feat.config(fg="forest green", text=str(self.in_feat))
        else:
            if not self.vol_only:
                self.l_inpath_feat.config(fg="red", text="Set CAD raster input directory")
            else:
                self.l_inpath_feat.config(fg="snow3", text="No alternative feature input directory provided.")

        if os.path.exists(self.in_vol) and self.vol_only:
            self.l_inpath_vol.config(fg="forest green", text=str(self.in_vol))
        else:
            if self.vol_only:
                showinfo("INFO", "Define an input directory for the modified DEM raster.")
                self.l_inpath_vol.config(fg="red", text="Set feature input directory")
            else:
                self.l_inpath_vol.config(fg="snow3", text="No modified DEM directory provided.")

        self.runmenu.entryconfig(3, label="Run: Map Maker", foreground="dark slate gray",
                                 command=lambda: self.run_map_maker())

    def logfile_quit(self):
        try:
            self.open_log_file()
        except:
            showinfo("WARNING", "Cannot open logfile.")
        tk.Frame.quit(self)

    def myquit(self):
        if askokcancel("Close", "Do you really wish to quit?"):
            tk.Frame.quit(self)

    def open_log_file(self):
        _f = self.logfile
        if os.path.isfile(_f):
            try:
                webbrowser.open(_f)
            except:
                pass

    def run_map_maker(self):
        if not self.prevent_popup:
            showinfo("INFORMATION",
                     " Analysis takes a while. \n Python windows seem unresponsive in the meanwhile. \n Check console messages.\n \n PRESS OK TO START")
        if not self.verified:
            self.verify()
        if self.verified:
            mapper = cmp.Mapper(self.condition, "mt", self.dir_ras_vol)
            map_list = []
            for fid in self.feature_id_list:
                add_str = ""
                if "grad" in fid:
                    add_str = "grade"
                if "wide" in fid:
                    add_str = "widen"
                if "cus" in fid:
                    add_str = "cust"
                    map_list.append("volume_%s_pos" % add_str)  # pos not meaningful for widen or grade
                map_list.append("volume_%s_neg" % add_str)

            for map_name in map_list:
                mapper.prepare_layout(True, map_items=[map_name])

            self.master.bell()
            tk.Button(self, width=25, bg="pale green", text="Mapping finished. Click to quit.",
                      command=lambda: self.logfile_quit()).grid(sticky=tk.EW, row=12, column=0, columnspan=5,
                                                                padx=self.xd, pady=self.yd)
            try:
                if not mapper.error:
                    fg.open_folder(mapper.output_dir)
            except:
                pass

    def run_modification(self):
        showinfo("INFORMATION",
                 " Analysis takes a while. \n Python windows seem unresponsive in the meanwhile. \n Check console messages.\n \n PRESS OK TO START")
        if not self.verified:
            self.verify()
        if self.verified:
            modification = cmt.ModifyTerrain(condition=self.condition, unit_system=self.unit,
                                             feature_ids=self.feature_id_list, topo_in_dir=self.in_topo,
                                             feat_in_dir=self.in_feat, reach_ids=self.reach_ids_applied)
            self.logfile = modification()
            self.dir_ras_vol = modification.output_ras_dir
            self.prevent_popup = True

            if self.mapping.get():
                self.run_map_maker()
            self.master.bell()
            tk.Button(self, width=25, bg="pale green", text="Terrain modification finished. Click to quit.",
                      command=lambda: self.logfile_quit()).grid(sticky=tk.EW, row=8, column=0, columnspan=5,
                                                                padx=self.xd, pady=self.yd)

    def run_volume_calculator(self):
        showinfo("INFORMATION",
                 " Analysis takes a while. \n Python windows seem unresponsive in the meanwhile. \n Check console messages.\n \n PRESS OK TO START")
        if not self.verified:
            self.verify()
        if self.verified:
            modification = cmt.ModifyTerrain(condition=self.condition, unit_system=self.unit,
                                             feature_ids=self.feature_id_list, topo_in_dir=self.in_topo,
                                             feat_in_dir=self.in_feat, reach_ids=self.reach_ids_applied)

            self.logfile = modification(self.vol_only, self.in_vol)
            self.dir_ras_vol = modification.output_ras_dir
            self.prevent_popup = True
            del modification
            fg.rm_dir(self.path + "\\.cache\\")

            if self.mapping.get():
                self.run_map_maker()
            self.master.bell()
            tk.Button(self, width=25, bg="pale green", text="Volume calculator finished. Click to quit.",
                      command=lambda: self.logfile_quit()).grid(sticky=tk.EW, row=4, column=0, columnspan=5,
                                                                padx=self.xd, pady=self.yd)

    def set_dir2vol_ras(self):
        msg0 = "Make sure there is ONE raster in the directory that contains the string \'dem\' OR \'mod\' OR a feature ID.\n"
        msg1 = "Valid feature IDs are:\n"
        msglist = []
        feat_dict = dict(zip(self.features.name_list, self.features.id_list))
        for feat in feat_dict.items():
            msglist.append(": ".join(feat))
        showinfo("SET DIRECTORY", msg0 + msg1 + ", ".join(msglist))
        self.in_vol = askdirectory(initialdir=".")
        self.in_vol = self.in_vol + "/"
        if str(self.in_vol).__len__() > 1:
            self.l_inpath_vol.config(fg="dark slate gray", text=str(self.in_vol))
        else:
            self.l_inpath_vol.config(fg="red", text="Invalid directory")

    def show_credits(self):
        msg = "Version info: 0.3 (May 2019)\nAuthor: Sebastian Schwindt\n     Kenny Larrieu\nInstitute: Pasternack Lab, UC Davis \n\nEmail: sschwindt[at]ucdavis.edu"
        showinfo("Credits", msg)

    def unit_change(self):
        if self.unit == "si":
            new_unit = "us"
            self.unitmenu.delete(0, 1)
            self.unitmenu.add_command(label="[current]  U.S. customary", background="pale green")
            self.unitmenu.add_command(label="[             ]  SI (metric)", command=lambda: self.unit_change())
            self.master.bell()
            showinfo("UNIT CHANGE", "Unit system changed to U.S. customary.")
        else:
            new_unit = "si"
            self.unitmenu.delete(0, 1)
            self.unitmenu.add_command(label="[             ]  U.S. customary", command=lambda: self.unit_change())
            self.unitmenu.add_command(label="[current]  SI (metric)", background="pale green")
            self.master.bell()
            showinfo("UNIT CHANGE", "Unit system changed to SI (metric).")
        self.unit = new_unit

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
                import cModifyTerrain
            except:
                error_msg.append("Check installation of modify_terrain package.")
                self.verified = False
                self.errors = True
            try:
                import arcpy
                if not (sys.version_info.major == 3):
                    error_msg.append("Wrong Python interpreter (Required: Python3 and arcpy).")
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


# enable script to run stand-alone
if __name__ == "__main__":
    print("Loading GUI (ModifyTerrain) ...")
    MainGui().mainloop()
