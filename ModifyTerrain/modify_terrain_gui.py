try:
    import os, sys
    import tkinter as tk
    from tkinter.messagebox import askokcancel, showinfo
    from tkinter.filedialog import *
    import webbrowser
    import cModifyTerrain as cMT
except:
    print("ExceptionERROR: Missing fundamental packages (required: os, sys, Tkinter, webbrowser).")

try:
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')) + "\\.site_packages\\riverpy\\")
    import fGlobal as fG
    import cReachManager as cRM
    import cDefinitions as cDef
except:
    print("ExceptionERROR: Cannot find package files (/.site_packages/riverpy/*.py).")


class MainGui(tk.Frame):
    def __init__(self, master=None):
        self.dir2ra = os.path.abspath(os.path.join(os.path.dirname(__file__), '..')) + "\\"
        self.condition = ""
        self.errors = False
        self.features = cDef.FeatureDefinitions()
        self.feature_id_list = []
        self.feature_name_list = []
        self.in_feat = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..")) + "\\MaxLifespan\\Output\\Rasters\\"
        self.in_topo = os.path.abspath(os.path.join(os.path.dirname(__file__), "..")) + "\\01_Conditions\\"
        self.prevent_popup = False
        self.reader = cRM.Read()
        self.reaches = cDef.ReachDefinitions()
        self.reach_ids_applied = []  # self.reaches.id_xlsx ## initial: all reaches (IDs)
        self.reach_names_applied = []  # self.reaches.names_xlsx ## initial: all reaches (full names)
        self.reach_lookup_needed = False
        self.template_dir = os.path.dirname(os.path.abspath(__file__)) + "\\.templates\\"
        self.unit = "us"
        self.verified = False

        # Construct the Frame object.
        tk.Frame.__init__(self, master)
        # if imported from master GUI, redefine master as highest level (ttk.Notebook tab container)
        if __name__ != '__main__':
            self.master = self.winfo_toplevel()
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
                                   text="Choose from \"Features\" Menu\n(requires maximum lifespan rasters)")
        self.l_features.grid(sticky=tk.W, row=1, column=1, columnspan=7, padx=self.xd, pady=self.yd)
        self.l_inp = tk.Label(self, fg="dark slate gray", text="Current input Raster directory:")
        self.l_inp.grid(sticky=tk.W, row=4, column=0, columnspan=2, padx=self.xd, pady=self.yd)
        self.l_inpath_topo = tk.Label(self, fg="dark slate gray", text=str(self.in_topo))
        self.l_inpath_topo.grid(sticky=tk.W, row=5, column=0, columnspan=5, padx=self.xd, pady=self.yd)
        self.l_inp_feat = tk.Label(self, text="Current MaxLifespan Raster directory (threshold-based modification):")
        tk.Label(self, text="").grid(row=7, column=0, padx=self.xd, pady=self.yd)
        self.l_inp_feat.grid(sticky=tk.W, row=9, column=0, columnspan=5, padx=self.xd, pady=self.yd)
        self.l_inpath_feat = tk.Label(self, text=str(self.in_feat))
        self.l_inpath_feat.grid(sticky=tk.W, row=10, column=0, columnspan=5, padx=self.xd, pady=self.yd)

        # ENTRIES
        self.e_condition = tk.Entry(self, bg="salmon", width=10, textvariable=self.gui_condition)
        self.e_condition.grid(sticky=tk.EW, row=2, column=1, padx=self.xd, pady=self.yd)

        # BUTTONS
        self.b_condition = tk.Button(self, width=5, bg="white", text="Verify",
                                     command=lambda: self.generate_inpath())
        self.b_condition.grid(sticky=tk.W, row=2, column=2, padx=self.xd, pady=self.yd*5)
        self.b_in_topo = tk.Button(self, width=25, bg="white", text="Change input DEM directory (optional)",
                                   command=lambda: self.change_in_topo())
        self.b_in_topo.grid(sticky=tk.EW, row=3, column=0, columnspan=5, padx=self.xd, pady=self.yd)
        self.b_in_feat = tk.Button(self, width=25, text="Change max. lifespan Raster directory (optional)",
                                   command=lambda: showinfo("INFO", "Check max. lifespan raster box first."))
        self.b_in_feat.grid(sticky=tk.EW, row=8, column=0, columnspan=5, padx=self.xd, pady=self.yd)
        self.make_menu()

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
        self.featmenu.add_command(label="Terraform: Grading (threshold-based)", command=lambda: self.define_feature("grade"))
        self.featmenu.add_command(label="Terraform: Widen (threshold-based)", command=lambda: self.define_feature("widen"))
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
        self.runmenu.add_command(label="Threshold-based DEM Modification")

        # CLOSE DROP DOWN
        self.closemenu = tk.Menu(self.mbar, tearoff=0)  # create new menu
        self.mbar.add_cascade(label="Close", menu=self.closemenu)  # attach it to the menubar
        self.closemenu.add_command(label="Credits", command=lambda: self.show_credits())
        self.closemenu.add_command(label="Quit program", command=lambda: self.myquit())

    def add_reach(self, reach):
        if str(reach).__len__() < 1:
            self.reach_names_applied = fG.dict_values2list(self.reaches.name_dict.values())
            self.reach_ids_applied = fG.dict_values2list(self.reaches.id_dict.values())
            self.reach_names_applied.remove("Raster extents")
            self.reach_ids_applied.remove("none")
            if self.reach_names_applied.__len__() > 5:
                label_text = "Many / All"
            else:
                label_text = ", ".join(self.reach_names_applied)
            self.l_reaches.config(fg="dark slate gray", text=label_text)
        else:
            if not(reach == "clear"):
                if not (reach == "ignore"):
                    if not(reach in self.reach_names_applied):
                        self.reach_names_applied.append(self.reaches.name_dict[reach])
                        self.reach_ids_applied.append(self.reaches.id_dict[reach])
                else:
                    # ignore reaches
                    self.reach_names_applied = ["Raster extents"]
                    self.reach_ids_applied = ["none"]
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
            self.reachmenu.add_command(label="IGNORE (Use Raster extents)", command=lambda: self.add_reach("ignore"))
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
            self.reachmenu.entryconfig(7, label=self.reaches.name_dict["reach_00"])
            self.reachmenu.entryconfig(8, label=self.reaches.name_dict["reach_01"])
            self.reachmenu.entryconfig(9, label=self.reaches.name_dict["reach_02"])
            self.reachmenu.entryconfig(10, label=self.reaches.name_dict["reach_03"])
            self.reachmenu.entryconfig(11, label=self.reaches.name_dict["reach_04"])
            self.reachmenu.entryconfig(12, label=self.reaches.name_dict["reach_05"])
            self.reachmenu.entryconfig(13, label=self.reaches.name_dict["reach_06"])
            self.reachmenu.entryconfig(14, label=self.reaches.name_dict["reach_07"])

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

    def change_in_topo(self):
        msg0 = "Make sure there is ONE raster in the directory is named \'dem\'.\n"
        showinfo("SET DIRECTORY", msg0)
        self.in_topo = askdirectory(initialdir=".") + "/"
        if str(self.in_topo).__len__() > 1:
            self.l_inpath_topo.config(fg="dark slate gray", text=str(self.in_topo))
        else:
            self.l_inpath_topo.config(fg="red", text="Invalid directory")

    def define_feature(self, feature_id):
        if feature_id.__len__() < 1:
            # append ALL available features
            self.feature_id_list = self.features.id_list
            self.feature_name_list = self.features.name_list
            self.l_features.config(fg="SteelBlue", text=", ".join(self.feature_name_list))
        else:
            if not(feature_id == "clear"):
                if not(feature_id in self.feature_id_list):
                    # append single features
                    self.feature_id_list.append(feature_id)
                    self.feature_name_list.append(self.features.feat_name_dict[feature_id])
                self.l_features.config(fg="SteelBlue", text=", ".join(self.feature_name_list))
            else:
                # clear all features
                self.feature_id_list = []
                self.feature_name_list = []
                self.l_features.config(fg="red", text="Select from \'Features\' Menu")

        if ("grade" in self.feature_id_list) or ("widen" in self.feature_id_list):
            self.runmenu.entryconfig(1, label="Threshold-based DEM Modification",
                                     command=lambda: self.run_modification())

    def define_reaches(self):
        try:
            webbrowser.open(self.template_dir + "computation_extents.xlsx")
            self.reach_lookup_needed = True  # tells build_reachmenu that lookup of modified spreasheet info is needed
        except:
            showinfo("ERROR", "Cannot open the file\n" + self.template_dir + "computation_extents.xlsx")

    def enable_mterrain(self):
        self.b_in_feat.config(command=lambda: self.change_in_feat())
        self.l_inpath_feat.config(text=str(self.in_feat))
        self.runmenu.entryconfig(1, label="Threshold-based DEM Modification",
                                 command=lambda: self.run_modification())

    def generate_inpath(self):
        self.condition = self.e_condition.get()
        self.in_topo = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..")) + "\\01_Conditions\\" + str(self.condition) + "\\"
        self.in_feat = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..")) + "\\MaxLifespan\\Output\\Rasters\\" + str(
            self.condition) + "\\"

        self.e_condition.config(bg="pale green", width=10, textvariable=self.gui_condition)

        if os.path.exists(self.in_topo):
            self.l_inpath_topo.config(fg="forest green", text=str(self.in_topo))
        else:
            if not os.path.isfile(self.in_topo + 'dem.tif'):
                self.b_in_topo.config(fg="red", width=25, bg="white",
                                      text="Change input topo (condition DEM) directory (REQUIRED)",
                                      command=lambda: self.change_in_topo())
                showinfo("WARNING", "Cannot find DEM grid:\n" + self.in_topo + "dem\nTopo (DEM) input directory required")
            self.l_inpath_topo.config(fg="red", text="Set topo input directory")
        if os.path.exists(self.in_feat):
            self.l_inpath_feat.config(fg="forest green", text=str(self.in_feat))
        else:
            self.l_inpath_feat.config(text="No alternative feature input directory provided.")
        self.enable_mterrain()

    def myquit(self):
        if askokcancel("Close", "Do you really wish to quit?"):
            tk.Frame.quit(self)

    def run_modification(self):
        showinfo("INFORMATION",
                 " Analysis takes a while.\nPython windows seem unresponsive in the meanwhile.\nCheck console messages.\n\nPRESS OK TO START")
        if not self.verified:
            self.verify()
        if self.verified:
            modification = cMT.ModifyTerrain(condition=self.condition, unit_system=self.unit,
                                             feature_ids=self.feature_id_list, topo_in_dir=self.in_topo,
                                             feat_in_dir=self.in_feat, reach_ids=self.reach_ids_applied)
            modification()
            self.prevent_popup = True

            self.master.bell()
            tk.Button(self, width=25, bg="pale green", text="Terrain modification finished. Click to quit.",
                      command=lambda: self.myquit()).grid(sticky=tk.EW, row=8, column=0, columnspan=5,
                                                          padx=self.xd, pady=self.yd)

    def show_credits(self):
        showinfo("Credits", fG.get_credits())

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
