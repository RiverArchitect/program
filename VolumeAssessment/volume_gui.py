try:
    import os, sys
    import tkinter as tk
    from tkinter.messagebox import askokcancel, showinfo
    from tkinter.filedialog import *
    import webbrowser
    import cVolumeAssessment as cMT
except:
    print("ExceptionERROR: Missing fundamental packages (required: os, sys, tkinter, webbrowser).")

try:
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')) + "\\.site_packages\\riverpy\\")
    import fGlobal as fG
    import cReachManager as cRM
    import cDefinitions as cDef
    import cMapper as cMp
except:
    print("ExceptionERROR: Cannot find package files (/.site_packages/riverpy/*.py).")


class MainGui(tk.Frame):
    def __init__(self, master=None):
        self.dir2ra = os.path.abspath(os.path.join(os.path.dirname(__file__), '..')) + "\\"
        self.dir_ras_vol = ""
        self.path = r"" + os.path.dirname(os.path.abspath(__file__))
        self.errors = False
        self.org_dem_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..")) + "\\01_Conditions\\"
        self.mod_dem_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..")) + "\\01_Conditions\\"
        self.mapping = False
        self.raster4mapping = []
        self.reader = cRM.Read()
        self.reaches = cDef.Reaches()
        self.reach_ids_applied = []  # self.reaches.id_xlsx ## initial: all reaches (IDs)
        self.reach_names_applied = []  # self.reaches.names_xlsx ## initial: all reaches (full names)
        self.reach_lookup_needed = False
        self.template_dir = os.path.dirname(os.path.abspath(__file__)) + "\\.templates\\"
        self.unit = "us"
        self.vol_name = ""

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

        self.l_org_dem = tk.Label(self, text="Original DEM Raster:")
        self.l_org_dem.grid(sticky=tk.W, row=4, column=0, columnspan=2, padx=self.xd, pady=self.yd)
        self.l_dir2orgdem = tk.Label(self, fg="dark slate gray", text="None")
        self.l_dir2orgdem.grid(sticky=tk.W, row=5, column=0, columnspan=5, padx=self.xd, pady=self.yd)
        self.l_mod_dem = tk.Label(self, text="Modified DEM Raster:")
        self.l_mod_dem.grid(sticky=tk.W, row=13, column=0, columnspan=5, padx=self.xd, pady=self.yd)
        self.l_dir2modem = tk.Label(self, fg="dark slate gray", text="None")
        self.l_dir2modem.grid(sticky=tk.W, row=14, column=0, columnspan=5, padx=self.xd, pady=self.yd)

        # BUTTONS
        self.b_chg_org_dem = tk.Button(self, width=25, bg="white", text="Select original DEM Raster",
                                       command=lambda: self.select_org_dem())
        self.b_chg_org_dem.grid(sticky=tk.EW, row=3, column=0, columnspan=5, padx=self.xd, pady=self.yd)
        self.b_chg_mod_dem = tk.Button(self, width=25, text="Select modified DEM Raster",
                                       command=lambda: self.select_mod_dem())
        self.b_chg_mod_dem.grid(sticky=tk.EW, row=12, column=0, columnspan=5, padx=self.xd, pady=self.yd)

        self.make_menu()

        # CHECK BOXES
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
            self.master.title("Volume Assessment")
            self.master.iconbitmap(self.dir2ra + ".site_packages\\templates\\code_icon.ico")

    def make_menu(self):
        # DROP DOWN MENU
        # the menu does not need packing - see page 44ff
        self.mbar = tk.Menu(self)  # create new menubar
        self.master.config(menu=self.mbar)  # attach it to the root window

        # FEATURES DROP DOWN
        self.featmenu = tk.Menu(self.mbar, tearoff=0)  # create new menu

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
        self.runmenu.add_command(label="Run: Volume Calculator", command=lambda: self.run_volume_calculator())
        self.runmenu.add_command(label="Run: Map Maker", command=lambda: showinfo("INFO", "Run volume calculator first."))

        # CLOSE DROP DOWN
        self.closemenu = tk.Menu(self.mbar, tearoff=0)  # create new menu
        self.mbar.add_cascade(label="Close", menu=self.closemenu)  # attach it to the menubar
        self.closemenu.add_command(label="Credits", command=lambda: self.show_credits())
        self.closemenu.add_command(label="Quit program", command=lambda: self.myquit())

    def add_reach(self, reach):
        if str(reach).__len__() < 1:
            self.reach_names_applied = fG.dict_values2list(self.reaches.name_dict.values())
            self.reach_ids_applied = fG.dict_values2list(self.reaches.id_dict.values())
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

    def select_mod_dem(self):
        self.mod_dem_dir = askopenfilename(initialdir=self.mod_dem_dir.split(".")[0],
                                           title="Select modified DEM tif",
                                           filetypes=[("GeoTIFF", "*.tif")])
        if str(self.l_dir2modem).__len__() > 1:
            self.l_dir2modem.config(fg="forest green", text=str(self.mod_dem_dir))
        else:
            self.l_dir2modem.config(fg="red", text="Invalid directory")

    def select_org_dem(self):
        self.org_dem_dir = askopenfilename(initialdir=self.org_dem_dir.split(".")[0],
                                           title="Select original DEM tif",
                                           filetypes=[("GeoTIFF", "*.tif")])
        if str(self.org_dem_dir).__len__() > 1:
            self.l_dir2orgdem.config(fg="forest green", text=str(self.org_dem_dir))
        else:
            self.l_dir2orgdem.config(fg="red", text="Invalid directory")

    def define_reaches(self):
        try:
            webbrowser.open(self.template_dir + "computation_extents.xlsx")
            self.reach_lookup_needed = True  # tells build_reachmenu that lookup of modified spreasheet info is needed
        except:
            showinfo("ERROR", "Cannot open the file\n" + self.template_dir + "computation_extents.xlsx")

    def myquit(self):
        if askokcancel("Close", "Do you really wish to quit?"):
            tk.Frame.quit(self)

    def run_map_maker(self):
        mapper = cMp.Mapper(self.vol_name, "mt", self.dir_ras_vol)
        for ras in self.raster4mapping:
            mapper.prepare_layout(True, map_items=[ras])

        self.master.bell()
        tk.Button(self, width=25, bg="pale green", text="Mapping finished. Click to quit.",
                  command=lambda: self.myquit()).grid(sticky=tk.EW, row=12, column=0, columnspan=5,
                                                      padx=self.xd, pady=self.yd)
        try:
            if not mapper.error:
                fG.open_folder(mapper.output_dir)
        except:
            pass

    def run_volume_calculator(self):
        showinfo("INFORMATION",
                 " Analysis may take a while.\nPython windows seem unresponsive in the meanwhile.\nCheck console messages.\n \n PRESS OK TO START")
        vola = cMT.VolumeAssessment(unit_system=self.unit, org_ras_dir=self.org_dem_dir,
                                    mod_ras_dir=self.mod_dem_dir, reach_ids=self.reach_ids_applied)
        self.vol_name, self.dir_ras_vol = vola.get_volumes()
        self.raster4mapping = vola.rasters
        fG.rm_dir(self.path + "\\.cache\\")

        self.runmenu.entryconfig(1, command=lambda: self.run_map_maker())
        if self.mapping.get():
            self.run_map_maker()
        self.master.bell()

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

    def __call__(self):
        self.mainloop()


# enable script to run stand-alone
if __name__ == "__main__":
    print("Loading GUI (VolumeAssessment) ...")
    MainGui().mainloop()
