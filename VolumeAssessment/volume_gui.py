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
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')) + "\\")
    import child_gui as sg
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')) + "\\.site_packages\\riverpy\\")
    import config
    import fGlobal as fGl
    import cReachManager as cRM
    import cDefinitions as cDef
    import cMapper as cMp
except:
    print("ExceptionERROR: Cannot find package files (/.site_packages/riverpy/*.py).")


class MainGui(sg.RaModuleGui):
    def __init__(self, from_master):
        sg.RaModuleGui.__init__(self, from_master)
        self.ww = 580  # window width
        self.wh = 650  # window height
        self.title = "Volume Assessment"
        self.set_geometry(self.ww, self.wh, self.title)

        self.dir_ras_vol = ""

        self.org_dem_dir = config.dir2conditions
        self.mod_dem_dir = config.dir2conditions
        self.raster4mapping = []
        self.template_dir = config.dir2va + ".templates\\"
        self.vol_name = ""

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

        self.complete_menus()

        # CHECK BOXES
        self.cb_mapping = tk.Checkbutton(self, fg="dark slate gray",
                                         text="Automatically run mapping after DEM / volume calculation.",
                                         variable=self.mapping, onvalue=True, offvalue=False)
        self.cb_mapping.grid(sticky=tk.W, row=15, column=0, columnspan=5, padx=self.xd, pady=self.yd*2)
        self.cb_mapping.deselect()  # select by default

    def complete_menus(self):
        # REACH  DROP DOWN
        self.reach_lookup_needed = False
        self.reachmenu = tk.Menu(self.mbar, tearoff=0)  # create new menu
        self.mbar.add_cascade(label="Reaches", menu=self.reachmenu)  # attach it to the menubar
        self.reachmenu = self.make_reach_menu(self.reachmenu)

        # RUN DROP DOWN
        self.runmenu = tk.Menu(self.mbar, tearoff=0)  # create new menu
        self.mbar.add_cascade(label="Run", menu=self.runmenu)  # attach it to the menubar
        self.runmenu.add_command(label="Run: Volume Calculator", command=lambda: self.run_volume_calculator())
        self.runmenu.add_command(label="Run: Map Maker", command=lambda: showinfo("INFO", "Run volume calculator first."))

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

    def run_map_maker(self):
        mapper = cMp.Mapper(self.vol_name, "mt", self.dir_ras_vol)
        for ras in self.raster4mapping:
            mapper.prepare_layout(True, map_items=[ras])

        self.master.bell()
        tk.Button(self, width=25, bg="pale green", text="Mapping finished. Click to quit.",
                  command=lambda: self.quit_tab()).grid(sticky=tk.EW, row=12, column=0, columnspan=5,
                                                        padx=self.xd, pady=self.yd)
        try:
            if not mapper.error:
                fGl.open_folder(mapper.output_dir)
        except:
            pass

    def run_volume_calculator(self):
        showinfo("INFORMATION",
                 " Analysis may take a while.\nPython windows seem unresponsive in the meanwhile.\nCheck console messages.\n \n PRESS OK TO START")
        vola = cMT.VolumeAssessment(unit_system=self.unit, org_ras_dir=self.org_dem_dir,
                                    mod_ras_dir=self.mod_dem_dir, reach_ids=self.reach_ids_applied)
        self.vol_name, self.dir_ras_vol = vola.get_volumes()
        self.raster4mapping = vola.rasters
        try:
            fGl.rm_dir(vola.cache)
        except:
            showinfo("WARNING", "Could not remove %s.\nManual deletion required")

        self.runmenu.entryconfig(1, command=lambda: self.run_map_maker())
        if self.mapping.get():
            self.run_map_maker()
        self.master.bell()

    def __call__(self):
        self.mainloop()
