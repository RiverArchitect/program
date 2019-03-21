try:
    import os, sys
    import Tkinter as tk
    from tkMessageBox import askokcancel, showinfo
    from tkFileDialog import *
    import webbrowser
    from functools import partial
except:
    print("ExceptionERROR: Missing fundamental packages (required: os, sys, Tkinter, webbrowser).")

try:
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')) + "\\.site_packages\\riverpy\\")
    import cDefinitions as cdef
    import fGlobal as fg
    import cTerrainIO as cmio
except:
    print("ExceptionERROR: Cannot find package files (RP/fGlobal.py, RP/cDefinitions.py, RP/cTerrainIO).")


class PopUpWindow(object):
    def __init__(self, master):
        top = self.top = tk.Toplevel(master)
        msg0 = "Manning\'s n is used in the calculation of grain mobility for shear velocity.\n"
        msg1 = "Please refer to the manual (Lifespan mapping section about angular boulders and grain mobility) for more details.\n"
        msg3 = "If you are using US costumary units, River Architect will use an internal conversion factor for the here entered metric value.\n"
        self.l_0 = tk.Label(top, text=msg0)
        self.l_0.pack(padx=5, pady=5)
        self.l_1 = tk.Label(top, text=msg1)
        self.l_1.pack(padx=5, pady=5)
        self.l_2 = tk.Label(top, text="Enter new SI-metric value for Manning\'s n in [s/m^(1/3)]:")
        self.l_2.pack(padx=5, pady=5)
        self.e = tk.Entry(top, width=10)
        self.e.pack(padx=5, pady=5)
        self.b = tk.Button(top, text='OK', command=self.cleanup)
        self.b.pack(padx=5, pady=5)
        self.l_3 = tk.Label(top, text=msg3)
        self.l_3.pack(padx=5, pady=5)
        self.top.iconbitmap(os.path.dirname(os.path.abspath(__file__)) + "\\.templates\\code_icon.ico")

    def cleanup(self):
        self.value = self.e.get()
        self.top.destroy()


class RunGui:
    def __init__(self, master):
        # Construct the Frame object.
        self.master = tk.Toplevel(master)
        self.master.wm_title("CHECK CONSOLE MESSAGES")
        self.master.bell()
        self.msg = ""

        # ARRANGE GEOMETRY
        ww = 400
        wh = 100
        wx = (self.master.winfo_screenwidth() - ww) / 2
        wy = (self.master.winfo_screenheight() - wh) / 2
        self.master.geometry("%dx%d+%d+%d" % (ww, wh, wx, wy))

    def gui_raster_maker(self, condition, reach_ids_applied, feature_list, mapping, habitat, units, wild, n):
        import feature_analysis as fa
        out_dir = fa.raster_maker(condition, reach_ids_applied, feature_list, mapping, habitat, units, wild, n)
        self.master.iconbitmap(os.path.dirname(os.path.abspath(__file__)) + "\\.templates\\code_icon.ico")
        return out_dir

    def gui_layout_maker(self, raster_directories):
        import feature_analysis as fa
        out_lyt_dirs = fa.layout_maker(raster_directories)
        self.master.iconbitmap(os.path.dirname(os.path.abspath(__file__)) + "\\.templates\\code_icon.ico")
        return out_lyt_dirs

    def gui_map_maker(self, layout_directories, reach_ids_applied):
        import feature_analysis as fa
        fa.map_maker(layout_directories, reach_ids_applied)
        self.master.iconbitmap(os.path.dirname(os.path.abspath(__file__)) + "\\.templates\\code_icon.ico")

    def gui_quit(self):
        self.master.destroy()

    def open_log_file(self):
        logfilenames = ["error.log", "rasterlogfile.log", "logfile.log", "map_logfile.log", "mxd_logfile.log"]
        for filename in logfilenames:
            _f = r'' + os.path.dirname(os.path.abspath(__file__)) + "\\" + filename
            if os.path.isfile(_f):
                try:
                    webbrowser.open(_f)
                except:
                    pass


class FaGui(tk.Frame):
    def __init__(self, master=None):
        self.path = r"" + os.path.dirname(os.path.abspath(__file__))
        self.path_lvl_up = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

        self.condition = ""
        self.condition_list = fg.get_subdir_names(self.path_lvl_up + "\\01_Conditions\\")
        self.errors = False
        self.feature_list = []
        self.features = cdef.Features(False)
        self.habitat = False
        self.manning_n = 0.0473934
        self.mapping = False
        self.mt_template_dir = os.path.abspath(
            os.path.join(os.path.dirname(__file__), '..')) + "\\ModifyTerrain\\.templates\\"
        self.out_lyt_dir = []
        self.out_ras_dir = []
        self.reaches = cdef.Reaches()
        self.reach_ids_applied = []  # self.reaches.id_xlsx ## initial: all reaches (IDs)
        self.reach_names_applied = []  # self.reaches.names_xlsx ## initial: all reaches (full names)
        self.reach_lookup_needed = False
        self.reach_reader = cmio.Read()
        self.unit = "us"
        self.verified = False
        self.wild = False

        # Construct the Frame object.
        tk.Frame.__init__(self, master)
        self.pack(expand=True, fill=tk.BOTH)
        self.master.iconbitmap(os.path.dirname(os.path.abspath(__file__))+"\\.templates\\code_icon.ico")

        # ARRANGE GEOMETRY
        # width and height of the window.
        ww = 700
        wh = 440
        self.xd = 5  # distance holder in x-direction (pixel)
        self.yd = 5  # distance holder in y-direction (pixel)
        # height and location
        wx = (self.master.winfo_screenwidth() - ww) / 2
        wy = (self.master.winfo_screenheight() - wh) / 2
        self.master.geometry("%dx%d+%d+%d" % (ww, wh, wx, wy))
        self.master.title("Lifespan Design")  # window title

        # GUI OBJECT VARIABLES
        self.gui_condition = tk.StringVar()
        self.gui_interpreter = tk.StringVar()

        # LABELS
        self.l_s_feat = tk.Label(self, text="Selected features: ")
        self.l_s_feat.grid(sticky=tk.W, row=0, column=0, padx=self.xd, pady=self.yd)
        self.l_features = tk.Label(self, fg="red",
                                   text="Choose from \'Add Features\' Menu (required for Raster Maker only)")
        self.l_features.grid(sticky=tk.W, row=0, column=1, columnspan=6, padx=self.xd, pady=self.yd)
        self.l_reach_label = tk.Label(self, text="Reaches:")
        self.l_reach_label.grid(sticky=tk.W, row=1, column=0, columnspan=1, padx=self.xd, pady=self.yd * 2)
        self.l_reaches = tk.Label(self, fg="red", text="Select from Reaches menu")
        self.l_reaches.grid(sticky=tk.W, row=1, column=1, columnspan=6, padx=self.xd, pady=self.yd * 2)
        self.l_condition = tk.Label(self, text="Condition: \n (select)")
        self.l_condition.grid(sticky=tk.W, row=3, column=0, columnspan=3, padx=self.xd, pady=self.yd)
        self.l_v_condition = tk.Label(self, fg="red", text="Verify (Run menu)")
        self.l_v_condition.grid(sticky=tk.W, row=3, column=3, padx=self.xd, pady=self.yd)
        self.l_n = tk.Label(self, text="Roughness (Manning\'s n): %.3f " % self.manning_n)
        self.l_n.grid(sticky=tk.W, row=10, column=0, columnspan=3, padx=self.xd, pady=self.yd)

        # DROP DOWN ENTRIES (SCROLL BARS)
        self.sb_condition = tk.Scrollbar(self, orient=tk.VERTICAL)
        self.sb_condition.grid(sticky=tk.W, row=3, column=2, padx=0, pady=self.yd)
        self.lb_condition = tk.Listbox(self, height=3, width=14, yscrollcommand=self.sb_condition.set)
        for e in self.condition_list:
            self.lb_condition.insert(tk.END, e)
        self.lb_condition.grid(sticky=tk.W, row=3, column=1, padx=self.xd, pady=self.yd)
        self.sb_condition.config(command=self.lb_condition.yview)

        # BUTTONS
        self.b_mod_r = tk.Button(self, width=25, bg="white", text="Modify raster input", command=lambda:
                                 self.open_inp_file("input_definitions.inp"))
        self.b_mod_r.grid(sticky=tk.EW, row=5, column=0, columnspan=2, padx=self.xd, pady=self.yd)
        self.b_mod_m = tk.Button(self, width=25, bg="white", text="Modify global map parameters", command=lambda:
                                 self.open_inp_file("mapping.inp"))
        self.b_mod_m.grid(sticky=tk.EW,row=5, column=2, columnspan=2, padx=self.xd, pady=self.yd)
        self.b_mod_th = tk.Button(self, width=25, bg="white", text="Modify survival threshold values", command=lambda:
                                  self.open_inp_file("threshold_values.xlsx"))
        self.b_mod_th.grid(sticky=tk.EW, row=6, column=0, columnspan=2, padx=self.xd, pady=self.yd)
        self.b_mod_rea = tk.Button(self, width=25, bg="white", text="Modify river/reach extents", command=lambda:
                                   self.open_inp_file("computation_extents.xlsx", "MT"))
        self.b_mod_rea.grid(sticky=tk.EW, row=6, column=2, columnspan=2, padx=self.xd, pady=self.yd)
        self.b_n = tk.Button(self, width=25, bg="white", text="Change / Info", command=lambda: self.set_n())
        self.b_n.grid(sticky=tk.W, row=10, column=2, columnspan=5, padx=self.xd, pady=self.yd)

        # DROP DOWN MENU
        # menu does not need packing - see tkinter manual page 44ff
        self.mbar = tk.Menu(self)  # create new menubar
        self.master.config(menu=self.mbar)  # attach it to the root window

        # FEATURE DROP DOWN
        self.featmenu = tk.Menu(self.mbar, tearoff=0)  # create new menu
        self.mbar.add_cascade(label="Add Features", menu=self.featmenu)  # attach it to the menubar
        # add menu entries
        self.build_feat_menu()

        # REACH  DROP DOWN
        self.reachmenu_list = []
        self.reachmenu = tk.Menu(self.mbar, tearoff=0)  # create new menu
        self.mbar.add_cascade(label="Reaches", menu=self.reachmenu)  # attach it to the menubar
        self.build_reach_menu()

        # RUN DROP DOWN
        self.runmenu = tk.Menu(self.mbar, tearoff=0)  # create new menu
        self.mbar.add_cascade(label="Run", menu=self.runmenu)  # attach it to the menubar
        self.runmenu.add_command(label="Verify settings", command=lambda: self.verify())
        self.runmenu.add_command(label="Run: Raster Maker", command=lambda: self.run_raster_maker())
        self.runmenu.add_command(label="Run: Layout Maker", command=lambda: self.run_layout_maker())
        self.runmenu.add_command(label="Run: Map Maker", command=lambda: self.run_map_maker())

        # UNIT SYSTEM DROP DOWN
        self.unitmenu = tk.Menu(self.mbar, tearoff=0)  # create new menu
        self.mbar.add_cascade(label="Units", menu=self.unitmenu)  # attach it to the menubar
        self.unitmenu.add_command(label="[current]  U.S. customary", background="pale green")
        self.unitmenu.add_command(label="[             ]  SI (metric)", command=lambda: self.unit_change())

        # CLOSE DROP DOWN
        self.closemenu = tk.Menu(self.mbar, tearoff=0)  # create new menu
        self.mbar.add_cascade(label="Close", menu=self.closemenu)  # attach it to the menubar
        self.closemenu.add_command(label="Credits", command=lambda: self.show_credits())
        self.closemenu.add_command(label="Quit programm", command=lambda: self.myquit())

        # CHECK BOXES(CHECKBUTTONS)
        self.cb_lyt = tk.Checkbutton(self, text="Create layouts after running raster maker", command=lambda:
                                     self.mod_mapping())
        self.cb_lyt.grid(sticky=tk.W, row=7, column=0, columnspan=4, padx=self.xd, pady=self.yd)
        self.cb_wild = tk.Checkbutton(self, text="Apply wildcard raster to spatially confine analysis", command=lambda:
                                      self.mod_wild())
        self.cb_wild.grid(sticky=tk.W, row=8, column=0, columnspan=5, padx=self.xd, pady=self.yd)

        self.cb_habitat = tk.Checkbutton(self, text="Apply habitat matching",
                                         command=lambda: self.mod_habitat())
        self.cb_habitat.grid(sticky=tk.W, row=9, column=0, columnspan=5, padx=self.xd, pady=self.yd)

        # MAKE PLACEHOLDER FILL
        logo = tk.PhotoImage(file=os.path.dirname(os.path.abspath(__file__))+"\\.templates\\title_042.GIF")
        logo = logo.subsample(7, 6)
        self.l_img = tk.Label(self, image=logo)
        self.l_img.image = logo
        self.l_img.grid(sticky=tk.E, row=3, column=6, rowspan=7, columnspan=2)

    def add_reach(self, reach):
        self.l_reaches.destroy()
        if str(reach).__len__() < 1:
            # appends all available reaches
            self.reach_names_applied = self.reaches.name_dict.values()
            self.reach_ids_applied = self.reaches.id_dict.values()
            label_text = "All"
            self.l_reaches = tk.Label(self, fg="dark slate gray", text=label_text)
        else:
            if not(reach == "clear"):
                if not(reach in self.reach_names_applied):
                    self.reach_names_applied.append(self.reaches.name_dict[reach])
                    self.reach_ids_applied.append(self.reaches.id_dict[reach])
                if self.reach_names_applied.__len__() > 6:
                    if self.reach_names_applied.__len__() == 8:
                        label_text = "All"
                    else:
                        label_text = "Multiple (> 6)"
                else:
                    label_text = ", ".join(self.reach_names_applied)
                self.l_reaches = tk.Label(self, fg="dark slate gray", text=label_text)
            else:
                self.reach_names_applied = []
                self.reach_ids_applied = []
                self.l_reaches = tk.Label(self, fg="red", text="Select from \'Reaches\' Menu")

        self.l_reaches.grid(sticky=tk.W, row=1, column=1, columnspan=6, padx=self.xd, pady=self.yd*2)

    def build_feat_menu(self):
        self.featmenu.add_command(label="Add: ALL", command=lambda: self.define_feature(""))

        for feat in self.features.name_list:
            menu_name = "Add: " + str(feat)
            self.featmenu.add_command(label=menu_name, command=partial(self.define_feature, feat))
        self.featmenu.add_command(label="_____________________________")
        self.featmenu.add_command(label="Group layer: Terraforming", command=lambda: self.define_feature("framework"))
        self.featmenu.add_command(label="Group layer: Plantings", command=lambda: self.define_feature("plants"))
        self.featmenu.add_command(label="Group layer: Bioengineering", command=lambda: self.define_feature("toolbox"))
        self.featmenu.add_command(label="Group layer: Maintenance", command=lambda: self.define_feature("complementary"))
        self.featmenu.add_command(label="CLEAR ALL", command=lambda: self.define_feature("clear"))

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
            # re-build reach names if spreadsheet was modified
            self.reaches.names_xlsx = self.reach_reader.get_reach_info("full_name")
            self.reaches.name_dict = dict(zip(self.reaches.internal_id, self.reaches.names_xlsx))
            self.reachmenu.entryconfig(6, label=self.reaches.name_dict["reach_00"])
            self.reachmenu.entryconfig(7, label=self.reaches.name_dict["reach_01"])
            self.reachmenu.entryconfig(8, label=self.reaches.name_dict["reach_02"])
            self.reachmenu.entryconfig(9, label=self.reaches.name_dict["reach_03"])
            self.reachmenu.entryconfig(10, label=self.reaches.name_dict["reach_04"])
            self.reachmenu.entryconfig(11, label=self.reaches.name_dict["reach_05"])
            self.reachmenu.entryconfig(12, label=self.reaches.name_dict["reach_06"])
            self.reachmenu.entryconfig(13, label=self.reaches.name_dict["reach_07"])

    def define_feature(self, feature_name):
        if feature_name.__len__() < 1:
            # append all available
            self.feature_list = self.features.name_list
            self.l_features.config(fg="SteelBlue", text="All")
        else:
            if not(feature_name == "clear"):
                if not(feature_name == "framework"):
                    if not(feature_name == "toolbox"):
                        if not(feature_name == "complementary"):
                            if not (feature_name == "plants"):
                                if not(feature_name in self.feature_list):
                                    # append single feature to analysis list
                                    self.feature_list.append(str(feature_name))
                            else:
                                # append plant features
                                self.feature_list = self.features.name_list_plants
                        else:
                            # append complementary features
                            self.feature_list = self.features.name_list_complement
                    else:
                        # append toolbox features
                        self.feature_list = self.features.name_list_toolbox
                else:
                    # append framework features
                    self.feature_list = self.features.name_list_framework
                self.l_features.config(fg="SteelBlue", text=", ".join(self.feature_list))
            else:
                # clear
                self.feature_list = []
                self.l_features.config(fg="red",
                                       text="Choose from \'Add Features\' Menu (required for Raster Maker only)")

    def define_reaches(self):
        try:
            webbrowser.open(self.mt_template_dir + "computation_extents.xlsx")
            self.reach_lookup_needed = True  # tells build_reachmenu that lookup of modified spreasheet info is needed
        except:
            showinfo("ERROR", "Cannot open the file\n" + self.mt_template_dir + "computation_extents.xlsx")

    def mod_habitat(self):
        if not self.habitat:
            self.habitat = True
        else:
            self.habitat = False

    def mod_mapping(self):
        if not self.mapping:
            self.mapping = True
        else:
            self.mapping = False

    def mod_wild(self):
        if not self.wild:
            self.wild = True
        else:
            self.wild = False

    def myquit(self):
        if askokcancel("Close", "Do you really wish to quit?"):
            tk.Frame.quit(self)

    def open_inp_file(self, filename, *args):
        # args[0] = STR indicating other modules
        try:
            if str(args[0]) == "MT":
                _f = r'' + os.path.abspath(
                    os.path.join(os.path.dirname(__file__), '..')) + "\\ModifyTerrain\\.templates\\" + filename
            else:
                _f = r'' + os.path.dirname(os.path.abspath(__file__)) + "\\.templates\\" + filename
        except:
            _f = r'' + os.path.dirname(os.path.abspath(__file__)) + "\\.templates\\" + filename

        if os.path.isfile(_f):
            try:
                webbrowser.open(_f)
            except:
                showinfo("ERROR ", "Cannot open " + str(filename) +
                         ". Make sure that your operating system has a standard application defined for *.inp-files.")
        else:
            showinfo("ERROR ", "The file " + str(filename) +" does not exist. Check feature_analysis directory.")

    def open_log_file(self):
        logfilenames = ["error.log", "rasterlogfile.log", "logfile.log", "map_logfile.log", "mxd_logfile.log"]
        for filename in logfilenames:
            _f = r'' + os.path.dirname(os.path.abspath(__file__)) + "\\" + filename
            if os.path.isfile(_f):
                try:
                    webbrowser.open(_f)
                except:
                    pass

    def run_raster_maker(self):
        showinfo("INFORMATION",
                 " Analysis takes a while. \n Python windows seem unresponsive in the meanwhile. \n Check console messages.\n \n PRESS OK TO START")
        if not self.verified:
            self.verify()
        if self.verified:
            run = RunGui(self)
            out_dir = run.gui_raster_maker(self.condition, self.reach_ids_applied, self.feature_list,
                                           self.mapping, self.habitat, self.unit, self.wild, self.manning_n)
            if self.mapping:
                self.out_lyt_dir = out_dir
            else:
                self.out_ras_dir = out_dir
            run.gui_quit()
            self.cb_lyt.destroy()
            self.cb_habitat.destroy()
            self.cb_wild.destroy()
            self.master.bell()
            tk.Button(self, width=25, bg="pale green", text="QUIT\n", command=lambda:
                      tk.Frame.quit(self)).grid(sticky=tk.EW, row=9, column=0, columnspan=2, padx=self.xd,
                                                pady=self.yd)
            if not self.mapping:
                tk.Button(self, bg="salmon", width=25, text="IMPORTANT\n Read logfile(s)", command=lambda:
                          self.open_log_file()).grid(sticky=tk.EW, row=9, column=2, columnspan=2, padx=self.xd,
                                                     pady=self.yd)
            else:
                tk.Button(self, bg="gold", width=25, text="IMPORTANT\n Read logfile(s) from Layout Maker",
                          command=lambda:
                          self.open_log_file()).grid(sticky=tk.EW, row=9, column=2, columnspan=2, padx=self.xd,
                                                     pady=self.yd)
            if self.habitat:
                tk.Label(self, fg="forest green", text=
                            "Applied habitat matching").grid(
                            sticky=tk.W, row=8, column=0, columnspan=6, padx=self.xd, pady=self.yd)
            if self.mapping:
                showinfo("INFORMATION",
                             "Layouts (.mxd files) prepared in opened folder.\n\n>> For obtaining PDF maps do the following:\n   1) Open layouts (mxd) in ArcMap Desktop and adapt symbology of sym layer.\n   2) Save layouts (overwrite existing) without committing any other change.\n   3) Back in Python console: Run feature_analysis.map_making(condition). \n \n Then, run Map Maker to obtain PDF maps.")

    def run_layout_maker(self):
        if not self.verified:
            self.verify(False)
        if self.verified:
            run = RunGui(self)
            if self.out_ras_dir.__len__() < 1:
                showinfo("INFORMATION", "Choose folder that contains lifespan and design rasters.")
                self.out_ras_dir = [askdirectory(initialdir=".") + "/"]
            self.out_lyt_dir = run.gui_layout_maker(self.out_ras_dir)
            run.gui_quit()
            self.cb_lyt.destroy()
            self.cb_habitat.destroy()
            self.cb_wild.destroy()
            self.master.bell()
            tk.Button(self, width=25, bg="pale green", text="QUIT\n",
                      command=lambda:
                      tk.Frame.quit(self)).grid(sticky=tk.EW, row=9, column=0, columnspan=2, padx=self.xd,
                                                pady=self.yd)
            tk.Button(self, bg="gold", width=25, text="IMPORTANT\n Read logfile(s) from Layout Maker", command=lambda:
                      self.open_log_file()).grid(sticky=tk.EW, row=9, column=2, columnspan=2, padx=self.xd, pady=self.yd)
            showinfo("INFORMATION",
                     "Layouts (.mxd files) prepared in opened folder.\n \n >> For obtaining PDF maps do the following:\n   1) Open layouts (mxd) in ArcMap Desktop and adapt symbology of sym layer.\n   2) Save layouts (overwrite existing) without committing any other change.\n   3) Back in Python console: Run feature_analysis.map_making(condition). \n \n Then, run Map Maker to obtain PDF maps.")

    def run_map_maker(self):
        if not self.verified:
            self.verify(False)
        if self.verified:
            run = RunGui(self)
            if self.out_lyt_dir.__len__() < 1:
                msg0 = "Choose folder that contains layouts.\n"
                msg1 = "Try .../LifespanDesign/Output/Mapping/CONDITION/ > Layouts"
                showinfo("INFORMATION", msg0 + msg1)
                self.out_lyt_dir = [askdirectory(initialdir=".") + "/"]
            run.gui_map_maker(self.out_lyt_dir, self.reach_ids_applied)
            run.gui_quit()
            self.cb_lyt.destroy()
            self.cb_habitat.destroy()
            self.cb_wild.destroy()
            self.master.bell()
            tk.Button(self, width=25, bg="pale green", text="QUIT\n",
                      command=lambda:
                      tk.Frame.quit(self)).grid(sticky=tk.EW, row=9, column=0, columnspan=2, padx=self.xd,
                                                pady=self.yd)
            tk.Button(self, bg="pale green", width=25, text="IMPORTANT\n Read logfile(s) from Map Maker", command=lambda:
                      self.open_log_file()).grid(sticky=tk.EW, row=9, column=2, columnspan=2, padx=self.xd, pady=self.yd)

    def set_n(self):
        sub_frame = PopUpWindow(self.master)
        self.b_n["state"] = "disabled"
        self.master.wait_window(sub_frame.top)
        self.b_n["state"] = "normal"
        self.manning_n = float(sub_frame.value)
        self.l_n.config(text="Roughness (Manning\'s n): %.3f " % self.manning_n)
        if float(self.manning_n) > 0.2:
            showinfo("WARNING", "That seems to be an incredibly rough channel. Consider revising the new value for Manning\'s n")

    def show_credits(self):
        msg = "Version info: 0.1 (July 2018)\nAuthor: Sebastian Schwindt\nInstitute: Pasternack Lab, UC Davis \n\nEmail: sschwindt[at]ucdavis.edu"
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
            showinfo("UNIT CHANGE", "Unit system changed to SI (metric).\n\nThreshold values need separate definition in threshold_values.xlsx (click button \'Modify survival threshold values\').")
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
                import feature_analysis
            except:
                error_msg.append("Check installation of feature_analysis package.")
                self.verified = False
                self.errors = True
            if not (self.feature_list.__len__() > 0):
                error_msg.append("For RasterMaker: Choose at least one feature.")
                self.verified = False
                self.errors = True
            else:
                if self.feature_list.__len__() < 6:
                    self.l_features.config(fg="forest green", text=", ".join(self.feature_list))
                else:
                    self.l_features.config(fg="forest green", text="Many / All")
            try:
                if not ((sys.version_info.major == 2) and (sys.version_info.minor == 7)):
                    error_msg.append("Wrong Python interpreter (Required: Python v.2.7 or higher--do not use v.3.x).")
                    self.errors = True
                    self.verified = False
            except:
                pass
        try:
            items = self.lb_condition.curselection()
            self.condition = [self.condition_list[int(item)] for item in items][0]
            input_dir = self.path_lvl_up + "\\01_Conditions\\" + str(self.condition)
            if os.path.exists(input_dir):
                self.l_v_condition.config(fg="forest green", text="Selected: " + self.condition)
            else:
                error_msg.append("Invalid file structure (non-existent directory /01_Conditions/condition ).")
                self.l_v_condition.config(fg="red", text="ERROR                                 ")
                self.errors = True
                self.verified = False
        except:
            error_msg.append("Invalid entry for \'Condition\'.")
            self.errors = True
            self.verified = False
        if self.errors:
            self.master.bell()
            showinfo("VERIFICATION ERROR(S)", "\n ".join(error_msg))
            self.errors = False

    def __call__(self):
        self.mainloop()


# enable script to run stand-alone
if __name__ == "__main__":
    FaGui().mainloop()
