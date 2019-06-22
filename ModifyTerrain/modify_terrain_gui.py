try:
    import os, sys
    import tkinter as tk
    from tkinter import ttk
    from tkinter.messagebox import askokcancel, showinfo
    from tkinter.filedialog import *
    import webbrowser
    import cModifyTerrain as cMT
    import cRiverBuilder as cRB
except:
    print("ExceptionERROR: Missing fundamental packages (required: os, sys, tkinter, webbrowser).")

try:
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')) + "\\")
    import slave_gui as sg
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')) + "\\.site_packages\\riverpy\\")
    import config
    import fGlobal as fGl
    import cReachManager as cRM
    import cDefinitions as cDef
except:
    print("ExceptionERROR: Cannot find riverpy.")


class ThresholdFrame(tk.Frame):
    def __init__(self, master=None, **options):
        Frame.__init__(self, master, **options)
        self.config(width=350, height=400)
        self.grid_propagate(False)
        self.px = 5
        self.py = 5
        self.in_topo = config.dir2conditions

        self.l_th = tk.Label(self, fg="dark slate gray", text="THRESHOLD VALUE-BASED TERRAFORMING")
        self.l_th.grid(sticky=tk.EW, row=0, column=0, columnspan=2, padx=self.px, pady=self.py)

        self.b_in_topo = tk.Button(self, width=25, bg="white", text="Modify DEM directory (optional)",
                                   command=lambda: self.change_in_topo())
        self.b_in_topo.grid(sticky=tk.EW, row=1, column=0, columnspan=2, padx=self.px, pady=self.py)

        self.l_inp = tk.Label(self, text="Current DEM Raster:")
        self.l_inp.grid(sticky=tk.W, row=2, column=0, columnspan=2, padx=self.px, pady=self.py)
        self.l_inpath_topo = tk.Label(self, text=str(self.in_topo))
        self.l_inpath_topo.grid(sticky=tk.W, row=3, column=0, columnspan=2, padx=self.px, pady=self.py)
        self.l_inp_feat = tk.Label(self, text="Max. Lifespan Raster directory:")
        self.l_inp_feat.grid(sticky=tk.W, row=4, column=0, padx=self.px, pady=self.py)
        self.l_inpath_feat = tk.Label(self)
        self.l_inpath_feat.grid(sticky=tk.W, row=5, column=0, columnspan=2, padx=self.px, pady=self.py)

        self.b_run_grade = tk.Button(self, text="Grade", width=22)
        self.b_run_grade.grid(sticky=tk.EW, row=7, column=0, padx=self.px, pady=self.py)
        self.b_run_widen = tk.Button(self, text="Widen", width=22)
        self.b_run_widen.grid(sticky=tk.EW, row=7, column=1, padx=self.px, pady=self.py)
        self.set_widget_state("disabled")

    def set_widget_state(self, state):
        # mode = STR (either "normal" or "disabled")
        for wid in self.winfo_children():
            wid["state"] = state

    def change_in_topo(self):
        msg0 = "Make sure there is ONE raster in the directory is named \'dem\'.\n"
        showinfo("SET DIRECTORY", msg0)
        self.in_topo = askdirectory(initialdir=".") + "/"
        if str(self.in_topo).__len__() > 1:
            self.l_inpath_topo.config(fg="dark slate gray", text=str(self.in_topo))
        else:
            self.l_inpath_topo.config(fg="red", text="Invalid directory")


class RiverBuilderFrame(tk.Frame):
    def __init__(self, master=None, unit="si", **options):
        Frame.__init__(self, master, **options)

        self.config(width=350, height=400)
        self.grid_propagate(False)
        self.rb_inp_file = config.dir2mt + "Input.txt"
        self.px = 5
        self.py = 5
        self.unit = unit
        b_width = 45

        self.l_rb = tk.Label(self, fg="dark slate gray", text="RIVER BUILDER")
        self.l_rb.grid(sticky=tk.EW, row=0, column=0, columnspan=2, padx=self.px, pady=self.py)

        self.b_rb_inp = tk.Button(self, bg="white", width=b_width, text="Create RB Input.txt File",
                                  command=lambda: self.start_app("create_rb_input"))
        self.b_rb_inp.grid(sticky=tk.EW, row=1, column=0, columnspan=2, padx=self.px, pady=self.py)
        self.b_rb_inp_s = tk.Button(self, bg="white", text="Select RB Input.txt File",
                                    command=lambda: self.select_input_file())
        self.b_rb_inp_s.grid(sticky=tk.EW, row=2, column=0, columnspan=2, padx=self.px, pady=self.py)
        self.l_inp_rb = tk.Label(self, text="Selected Input.txt file:\n%s" % "None")
        self.l_inp_rb.grid(sticky=tk.W, row=3, rowspan=2, column=0, columnspan=2, padx=self.px, pady=self.py)

        self.b_run_rb = tk.Button(self, text="Run River Builder", command=lambda: self.start_app("rb"))
        self.b_run_rb.grid(sticky=tk.EW, row=5, column=0, columnspan=2, padx=self.px, pady=self.py)

        self.set_widget_state("disabled")

    def select_input_file(self):
        showinfo("INFO", "The file must be located in %s ." % config.dir2rb)
        self.rb_inp_file = askopenfilename(initialdir=config.dir2rb, title="Select RB Input.txt", filetypes=[("TXT", "*.txt")])
        self.l_inp_rb.config(fg="dark slate gray", text="Selected Input.txt file:\n%s" % self.rb_inp_file)

    def start_app(self, app_name):
        # instantiate app
        if app_name == "create_rb_input":
            try:
                import sub_gui_rb as sgr
                sub_gui = sgr.CreateInput(self.master)
                self.b_rb_inp["state"] = "disabled"
                self.master.wait_window(sub_gui.top)
                self.b_rb_inp["state"] = "normal"
            except:
                showinfo("ERROR", "Could not launch River Builder Input File Creator.")

        if app_name == "rb":
            rb = cRB.RiverBuilder(self.unit)
            showinfo("INFO", "Analysis make take some minutes. Press OK to start.")
            try:
                webbrowser.open(rb.run_riverbuilder(self.rb_inp_file))
            except:
                pass

    def set_widget_state(self, state):
        # mode = STR (either "normal" or "disabled")
        for wid in self.winfo_children():
            wid["state"] = state


class MainGui(sg.RaModuleGui):
    def __init__(self, from_master):
        sg.RaModuleGui.__init__(self, from_master)
        self.ww = 750  # window width
        self.wh = 650  # window height
        self.title = "Modify Terrain"
        self.set_geometry(self.ww, self.wh, self.title)

        self.in_feat = config.dir2ml + "Output\\Rasters\\"
        self.prevent_popup = False

        # GUI OBJECT VARIABLES
        self.gui_condition = tk.StringVar()
        self.gui_interpreter = tk.StringVar()
        self.mapping = tk.BooleanVar()

        # LABELS
        self.l_reach_label = tk.Label(self, fg="dark slate gray", text="Reaches:")
        self.l_reach_label.grid(sticky=tk.W, row=0, column=0, padx=self.xd, pady=self.yd)
        self.l_reaches.config(fg="red", text="Select from Reaches menu")
        self.l_reaches.grid(sticky=tk.W, row=0, column=1, columnspan=5, padx=self.xd, pady=self.yd)
        self.l_condition = tk.Label(self, text="Select condition:")
        self.l_condition.grid(sticky=tk.W, row=0, column=0, padx=self.xd, pady=self.yd)
        self.l_inpath_curr = tk.Label(self, fg="gray60", text="Source: " + config.dir2conditions)
        self.l_inpath_curr.grid(sticky=tk.W, row=1, column=0, columnspan=3, padx=self.xd, pady=self.yd)
        self.combo_c = ttk.Combobox(self)
        self.combo_c.grid(sticky=tk.W, row=0, column=1, padx=self.xd, pady=self.yd)
        self.combo_c['values'] = tuple(fGl.get_subdir_names(config.dir2conditions))

        # BUTTONS
        self.b_s_condition = tk.Button(self, fg="red", text="Select Condition",
                                       command=lambda: self.select_condition())
        self.b_s_condition.grid(sticky=tk.W, row=0, column=3, columnspan=2, padx=self.xd, pady=self.yd)

        # THRESHOLD-MOD FRAME
        self.th_mod = ThresholdFrame(self, relief=tk.RAISED)
        self.set_bg_color(self.th_mod, "light grey")
        self.th_mod.grid(row=4, column=0, columnspan=2)
        self.th_mod.l_inpath_feat.config(text=str(self.in_feat))
        self.th_mod.b_run_grade.config(command=lambda: self.run_modification("grade"))
        self.th_mod.b_run_widen.config(command=lambda: self.run_modification("widen"))

        # RIVERBUILDER FRAME
        self.rb = RiverBuilderFrame(self, self.unit, relief=tk.RAISED)
        self.set_bg_color(self.rb, "LightBlue1")
        self.rb.grid(row=4, column=3, columnspan=2)

        self.complete_menus()

    def complete_menus(self):
        # add reach menu
        # REACH  DROP DOWN
        self.reach_lookup_needed = False
        self.reachmenu = tk.Menu(self.mbar, tearoff=0)  # create new menu
        self.mbar.add_cascade(label="Reaches", menu=self.reachmenu)  # attach it to the menubar
        self.reachmenu = self.make_reach_menu(self.reachmenu)


    def set_inpath(self):
        self.th_mod.in_topo = config.dir2conditions + str(self.condition) + "\\"
        self.in_feat = config.dir2ml + "Output\\Rasters\\" + str(self.condition) + "\\"
        if not self.condition.lower() == "none":
            if self.th_mod.in_topo.__len__() <= 52:
                show_topo_dir = self.th_mod.in_topo + "dem.tif"
            else:
                show_topo_dir = self.th_mod.in_topo[0:25] + self.th_mod.in_topo[-25:-1] + "dem.tif"
            if self.in_feat.__len__() <= 59:
                show_feat_dir = self.in_feat
            else:
                show_feat_dir = self.in_feat[0:25] + self.in_feat[-32:-1]

            if os.path.exists(self.th_mod.in_topo):
                self.th_mod.l_inpath_topo.config(text=show_topo_dir)
            else:
                if not os.path.isfile(self.th_mod.in_topo + 'dem.tif'):
                    self.th_mod.b_in_topo.config(fg="red", width=25, bg="white",
                                                 text="Change input DEM (condition DEM) directory (REQUIRED)",
                                                 command=lambda: self.change_in_topo())
                    showinfo("WARNING", "Cannot find DEM GeoTIFF:\n" + self.th_mod.in_topo + " (DEM required)")
                self.th_mod.l_inpath_topo.config(fg="red", text="Set DEM input directory")
            if os.path.exists(self.in_feat):
                self.th_mod.l_inpath_feat.config(text=show_feat_dir)
            else:
                self.th_mod.l_inpath_feat.config(text="No alternative feature input directory provided.")
            self.th_mod.set_widget_state("normal")
        self.rb.set_widget_state("normal")

    def run_modification(self, feat):
        showinfo("INFORMATION",
                 " Analysis takes a while.\nPython windows seem unresponsive in the meanwhile.\nCheck console messages.\n\nPRESS OK TO START")
        if not self.verified:
            self.verify()
        if self.verified:
            modification = cMT.ModifyTerrain(condition=self.condition, unit_system=self.unit,
                                             feature_ids=self.feature_id_list, topo_in_dir=self.th_mod.in_topo,
                                             feat_in_dir=feat, reach_ids=self.reach_ids_applied)
            modification()
            self.prevent_popup = True

            self.master.bell()
            tk.Button(self, width=25, bg="forest green", text="Terrain modification finished. Click to quit.",
                      command=lambda: self.quit_tab()).grid(sticky=tk.EW, row=8, column=0, columnspan=2,
                                                            padx=self.xd, pady=self.yd)

    def select_condition(self):
        try:
            self.condition = self.combo_c.get()
            input_dir = config.dir2conditions + str(self.condition)
            if os.path.exists(input_dir) or self.mapping:
                self.b_s_condition.config(fg="forest green", text="Selected: " + self.condition)
                self.condition_selected = True
                self.set_inpath()
                return ""
            else:
                self.b_s_condition.config(fg="red", text="ERROR")
                self.errors = True
                self.verified = False
                return "Invalid file structure (non-existent directory /01_Conditions/CONDITION/)."
        except:
            self.errors = True
            self.verified = False
            return "Invalid entry for \'Condition\'."

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
                import cRiverBuilder
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
