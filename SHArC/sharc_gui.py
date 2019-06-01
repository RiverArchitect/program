try:
    import os, sys
    import tkinter as tk
    from tkinter.messagebox import askokcancel, showinfo
    from tkinter.filedialog import *
    import webbrowser
    import logging
except:
    print("ExceptionERROR: Missing fundamental packages (required: os, sys, logging tkinter, webbrowser).")

try:
    # import own routines
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    import cHSI as chsi
    # load routines from LifespanDesign
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')) + "\\.site_packages\\riverpy\\")
    import cFish as cFi
    import fGlobal as fG
    import cInputOutput as cIO
except:
    print("ExceptionERROR: Cannot find package files (riverpy).")


class PopUpWindow(object):
    def __init__(self, master):
        self.dir2ra = os.path.abspath(os.path.join(os.path.dirname(__file__), '..')) + "\\"
        top = self.top = tk.Toplevel(master)
        self.l = tk.Label(top, text="Enter value:")
        self.l.pack()
        self.e = tk.Entry(top, width=10)
        self.e.pack()
        self.b = tk.Button(top, text='OK', command=self.cleanup)
        self.b.pack()
        self.top.iconbitmap(self.dir2ra + ".site_packages\\templates\\code_icon.ico")

    def cleanup(self):
        self.value = self.e.get()
        self.top.destroy()


class MainGui(tk.Frame):
    def __init__(self, master=None):
        self.logger = logging.getLogger("logfile")
        self.dir2ra = os.path.abspath(os.path.join(os.path.dirname(__file__), '..')) + "\\"

        self.bound_shp = ""  # full path of a boundary shapefile
        self.combine_method = "geometric_mean"
        self.dir = os.path.dirname(os.path.abspath(__file__))
        self.dir_conditions = self.dir + "\\HSI\\"
        self.dir_inp_hsi_hy = ""
        self.dir_inp_hsi_cov = ""
        self.chsi_condition_hy = ""
        self.chsi_condition_cov = ""
        self.condition_list = fG.get_subdir_names(self.dir_conditions)
        self.cover_applies = False
        self.fish = cFi.Fish()
        self.fish_applied = {}
        self.max_columnspan = 5
        self.unit = "us"
        self.sharea_threshold = 0.5

        # Construct the Frame object.
        tk.Frame.__init__(self, master)
        # if imported from master GUI, redefine master as highest level (ttk.Notebook tab container)
        if __name__ != '__main__':
            self.master = self.master.master

        self.apply_boundary = tk.BooleanVar()
        self.cover_applies_sharea = tk.BooleanVar()
        self.pack(expand=True, fill=tk.BOTH)

        self.set_geometry()

        # LABELS
        self.l_aqua = tk.Label(self, fg="firebrick3", text="Select Aquatic Ambiance (at least one)")
        self.l_aqua.grid(sticky=tk.W, row=0, column=0, columnspan=2, padx=self.xd, pady=self.yd)
        self.l_combine = tk.Label(self, text="Select HSI combination method: ")
        self.l_combine.grid(sticky=tk.W, row=2, column=0, columnspan=1, padx=self.xd, pady=self.yd)
        tk.Label(self, text="").grid(sticky=tk.W, row=3, column=0)  # dummy

        imsg = "\n(Use \'Make HSI Rasters\' menu to create habitat conditions)"
        self.l_condition_hy = tk.Label(self, justify=tk.LEFT, fg="cyan4", text="Hydraulic habitat conditions (no cover):" + imsg)
        self.l_condition_hy.grid(sticky=tk.W, row=4, rowspan=3, column=0, columnspan=2, padx=self.xd, pady=self.yd)
        self.l_inpath_hy = tk.Label(self, justify=tk.LEFT, fg="cyan4", text="Source: " + str(self.dir_conditions))
        self.l_inpath_hy.grid(sticky=tk.W, row=7, column=0, columnspan=self.max_columnspan + 1, padx=self.xd, pady=self.yd)
        tk.Label(self, text="").grid(sticky=tk.W, row=9, column=0)  # dummy
        self.l_condition_hy["state"] = "disabled"
        self.l_inpath_hy["state"] = "disabled"

        self.l_condition_cov = tk.Label(self, justify=tk.LEFT, fg="gold4", text="Cover habitat conditions:" + imsg)
        self.l_condition_cov.grid(sticky=tk.W, row=10, rowspan=3, column=0, columnspan=2, padx=self.xd, pady=self.yd)
        self.l_inpath_cov = tk.Label(self, justify=tk.LEFT, fg="gold4", text="Source: " + str(self.dir_conditions))
        self.l_inpath_cov.grid(sticky=tk.W, row=13, column=0, columnspan=self.max_columnspan + 1, padx=self.xd,
                               pady=self.yd)
        tk.Label(self, text="").grid(sticky=tk.W, row=15, column=0)  # dummy
        self.l_condition_cov["state"] = "disabled"
        self.l_inpath_cov["state"] = "disabled"

        # DROP DOWN ENTRIES (SCROLL BARS)
        self.sb_condition_hy = tk.Scrollbar(self, orient=tk.VERTICAL)
        self.sb_condition_hy.grid(sticky=tk.W, row=4, column=3, padx=0, pady=self.yd)
        self.lb_condition_hy = tk.Listbox(self, height=3, width=15, yscrollcommand=self.sb_condition_hy.set)
        self.sb_condition_cov = tk.Scrollbar(self, orient=tk.VERTICAL)
        self.sb_condition_cov.grid(sticky=tk.W, row=10, column=3, padx=0, pady=self.yd)
        self.lb_condition_cov = tk.Listbox(self, height=3, width=15, yscrollcommand=self.sb_condition_cov.set)
        self.list_habitat_conditions()

        # CHECK BUTTONS -- determine if geometric mean or product is used
        self.cb_combine_method_gm = tk.Checkbutton(self, text="Geometric mean", variable=self.combine_method,
                                                   onvalue="geometric_mean", offvalue="product")
        self.cb_combine_method_gm.grid(sticky=tk.W, row=2, column=2, padx=self.xd, pady=self.yd)
        self.cb_combine_method_gm.select()
        self.cb_combine_method_pd = tk.Checkbutton(self, text="Product", variable=self.combine_method,
                                                   onvalue="product", offvalue="geometric_mean")
        self.cb_combine_method_pd.grid(sticky=tk.W, row=2, column=3, columnspan=2, padx=self.xd, pady=self.yd)
        self.cb_bshp = tk.Checkbutton(self, text="Use calculation boundary (rectangular polygon) shapefile",
                                      variable=self.apply_boundary, onvalue=True, offvalue=False,
                                      command=lambda: self.activate_shape_selection(self.b_select_bshp))
        self.cb_bshp.grid(sticky=tk.W, row=1, column=0, columnspan=self.max_columnspan - 1, padx=self.xd, pady=self.yd)
        self.cb_use_cov = tk.Checkbutton(self, fg="gold4", text="Use cover CHSI (requires COVER HSI conditions)",
                                         variable=self.cover_applies_sharea,
                                         onvalue=True, offvalue=False)
        self.cb_use_cov.grid(sticky=tk.W, row=16, column=0, columnspan=self.max_columnspan, padx=self.xd,
                             pady=self.yd)
        self.cb_use_cov["state"] = "disabled"

        # BUTTONS
        self.b_show_fish = tk.Button(self, width=15, fg="RoyalBlue3", bg="white", text="Show selected\nAquatic Ambiance(s)",
                                     command=lambda: self.shout_dict(self.fish_applied))
        self.b_show_fish.grid(sticky=tk.W, row=0, rowspan=3, column=self.max_columnspan, padx=self.xd, pady=self.yd)
        self.b_show_fish["state"] = "disabled"

        self.b_select_bshp = tk.Button(self, width=8, bg="white", text="Select file", command=lambda: self.select_boundary_shp())
        self.b_select_bshp.grid(sticky=tk.W, row=1, column=self.max_columnspan - 1, padx=self.xd, pady=self.yd)
        self.b_select_bshp["state"] = "disabled"

        self.b_csi_nc = tk.Button(self, fg="cyan4", width=30, bg="white", text="Combine HSI rasters (pure hydraulic)",
                                  command=lambda: self.start_app("chsi", cover=False))
        self.b_csi_nc.grid(sticky=tk.EW, row=8, column=0, columnspan=self.max_columnspan, padx=self.xd, pady=self.yd)
        self.b_csi_nc["state"] = "disabled"

        self.b_csi_c = tk.Button(self, fg="gold4", width=30, bg="white",
                                 text="Combine HSI rasters (hydraulic and cover)",
                                 command=lambda: self.start_app("chsi", cover=True))
        self.b_csi_c.grid(sticky=tk.EW, row=14, column=0, columnspan=self.max_columnspan, padx=self.xd, pady=self.yd)
        self.b_csi_c["state"] = "disabled"

        self.b_sharc = tk.Button(self, width=30, bg="white",
                                 text="Run Seasonal Habitat Area Calculator (SHArC)",
                                 command=lambda: self.start_app("sharea", cover=False))
        self.b_sharc.grid(sticky=tk.EW, row=17, column=0, columnspan=self.max_columnspan, rowspan=2,
                          padx=self.xd, pady=self.yd)
        self.b_sharc["state"] = "disabled"

        self.b_sha_th = tk.Button(self, width=15, fg="RoyalBlue3", bg="white",
                                  text="Set SHArea\nthreshold\nCurrent: CHSI = " + str(self.sharea_threshold),
                                  command=lambda: self.set_sharea())
        self.b_sha_th.grid(sticky=tk.EW, row=16, rowspan=3, column=self.max_columnspan, padx=self.xd, pady=self.yd)
        self.b_sha_th["state"] = "disabled"

        self.make_menu()

    def set_geometry(self):
        # ARRANGE GEOMETRY
        self.xd = 5  # distance holder in x-direction (pixel)
        self.yd = 5  # distance holder in y-direction (pixel)
        # width and height of the window
        self.ww = 690
        self.wh = 550
        self.wx = (self.master.winfo_screenwidth() - self.ww) / 2
        self.wy = (self.master.winfo_screenheight() - self.wh) / 2
        self.master.geometry("%dx%d+%d+%d" % (self.ww, self.wh, self.wx, self.wy))  # set height and location
        if __name__ == '__main__':
            self.master.title("Seasonal Habitat Area Calculator (SHArC)")  # window title
            self.master.iconbitmap(self.dir2ra + ".site_packages\\templates\\code_icon.ico")

    def make_menu(self):
        # DROP DOWN MENU
        self.mbar = tk.Menu(self)  # create new menubar
        self.master.config(menu=self.mbar)  # attach it to the root window

        # MAKE FISH SPECIES DROP DOWN
        self.fishmenu = tk.Menu(self.mbar, tearoff=0)  # create new menu
        self.mbar.add_cascade(label="Select Aquatic Ambiance", menu=self.fishmenu)  # attach it to the menubar
        self.fishmenu.add_command(label="DEFINE FISH SPECIES", command=lambda: self.fish.edit_xlsx())
        self.fishmenu.add_command(label="RE-BUILD MENU", command=lambda: self.make_fish_menu(rebuild=True))
        self.fishmenu.add_command(label="_____________________________")
        self.fishmenu.add_command(label="ALL", command=lambda: self.set_fish("all"))
        self.fishmenu.add_command(label="CLEAR ALL", command=lambda: self.set_fish("clear"))
        self.fishmenu.add_command(label="_____________________________")
        self.make_fish_menu(rebuild=False)

        # MAKE HSI DROP DOWN
        self.hsimenu = tk.Menu(self.mbar, tearoff=0)  # create new menu
        self.mbar.add_cascade(label="Make HSI Rasters (habitat conditions)",
                              menu=self.hsimenu)  # attach it to the menubar
        self.hsimenu.add_command(label="HYDRAULIC", foreground="gray60")  # POTENTIAL ERROR SOURCE: "foreground"
        self.hsimenu.add_command(label="> Flow depth - flow velocity HSIs", foreground="cyan4",
                                 command=lambda: self.start_app("hhsi_gui"))
        self.hsimenu.add_command(label="OTHER (COVER)", foreground="gray60")  # POTENTIAL ERROR SOURCE: "foreground"
        label_text = "> Substrate - Boulder - Cobble - Streamwood - Vegetation HSIs"
        self.hsimenu.add_command(label=label_text, foreground="gold4", command=lambda: self.start_app("mhsi_gui"))

        # UNIT SYSTEM DROP DOWN
        self.unitmenu = tk.Menu(self.mbar, tearoff=0)  # create new menu
        self.mbar.add_cascade(label="Units", menu=self.unitmenu)  # attach it to the menubar
        self.unitmenu.add_command(label="[current]  U.S. customary", background="pale green")
        self.unitmenu.add_command(label="[             ]  SI (metric)", command=lambda: self.unit_change())

        # CLOSE DROP DOWN
        self.closemenu = tk.Menu(self.mbar, tearoff=0)  # create new menu
        self.mbar.add_cascade(label="Close", menu=self.closemenu)  # attach it to the menubar
        self.closemenu.add_command(label="Credits", command=lambda: self.show_credits())
        self.closemenu.add_command(label="Open logfile", command=lambda: self.open_log_file())
        self.closemenu.add_command(label="Quit program", command=lambda: self.myquit())

    def activate_shape_selection(self, button):
        if self.apply_boundary.get():
            button["state"] = "normal"
            self.b_select_bshp.config(fg="red")
        else:
            button["state"] = "disabled"

    def activate_buttons(self, **kwargs):
        target_state = "normal"
        # parse optional arguments
        try:
            for k in kwargs.items():
                if "revert" in k[0]:
                    if k[1]:
                        # disable buttons if revert = True
                        target_state = "disabled"
        except:
            pass
        self.b_show_fish["state"] = target_state
        self.b_c_select_cov["state"] = target_state
        self.b_c_select_hy["state"] = target_state
        self.l_condition_hy["state"] = target_state
        self.l_inpath_hy["state"] = target_state
        self.l_condition_cov["state"] = target_state
        self.l_inpath_cov["state"] = target_state

    def list_habitat_conditions(self):
        # update habitat conditions listbox
        self.condition_list = fG.get_subdir_names(self.dir_conditions)
        try:
            self.lb_condition_hy.delete(0, tk.END)
            self.lb_condition_cov.delete(0, tk.END)
        except:
            pass

        for e in self.condition_list:
            self.lb_condition_hy.insert(tk.END, e)
            self.lb_condition_cov.insert(tk.END, e)
        self.lb_condition_hy.grid(sticky=tk.E, row=4, column=2, padx=0, pady=self.yd)
        self.sb_condition_hy.config(command=self.lb_condition_hy.yview)
        self.lb_condition_cov.grid(sticky=tk.E, row=10, column=2, padx=0, pady=self.yd)
        self.sb_condition_cov.config(command=self.lb_condition_cov.yview)

        # update selection button
        try:
            self.b_c_select_hy.config(text="Confirm\nselection", command=lambda: self.select_HSIcondition("hy"))
            self.b_c_select_cov.config(text="Confirm\nselection", command=lambda: self.select_HSIcondition("cov"))
        except:
            self.b_c_select_hy = tk.Button(self, fg="cyan4", width=8, bg="white", text="Confirm\nselection",
                                           command=lambda: self.select_HSIcondition("hy"))
            self.b_c_select_cov = tk.Button(self, fg="gold4", width=8, bg="white", text="Confirm\nselection",
                                            command=lambda: self.select_HSIcondition("cov"))
            self.b_c_select_hy.grid(sticky=tk.W, row=4, rowspan=2, column=self.max_columnspan - 1, padx=self.xd,
                                    pady=self.yd)
            self.b_c_select_cov.grid(sticky=tk.W, row=10, rowspan=2, column=self.max_columnspan - 1, padx=self.xd,
                                     pady=self.yd)
            self.b_c_select_hy["state"] = "disabled"
            self.b_c_select_cov["state"] = "disabled"

    def make_fish_menu(self, rebuild):
        # rebuild = True -> rebuilt menu mode
        if not rebuild:
            for f_spec in self.fish.species_dict.keys():
                lf_stages = self.fish.species_dict[f_spec]
                for lf_stage in lf_stages:
                    entry = str(f_spec) + " - " + str(lf_stage)
                    self.fishmenu.add_command(label=entry,
                                              command=lambda arg1=f_spec, arg2=lf_stage: self.set_fish(arg1, arg2))
        else:
            self.fish.assign_fish_names()
            self.logger.info(" >> Rebuilding Aquatic Ambiance menu ...")
            entry_count = 6
            for f_spec in self.fish.species_dict.keys():
                lf_stages = self.fish.species_dict[f_spec]
                for lf_stage in lf_stages:
                    entry = str(f_spec) + " - " + str(lf_stage)
                    self.fishmenu.entryconfig(entry_count, label=entry,
                                              command=lambda arg1=f_spec, arg2=lf_stage: self.set_fish(arg1, arg2))
                    entry_count += 1

    def myquit(self):
        self.open_log_file()
        tk.Frame.quit(self)

    def open_log_file(self):
        logfilenames = ["error.log", "habitat_evaluation.log", "logfile.log", "map_logfile.log", "mxd_logfile.log"]
        for filename in logfilenames:
            _f = r'' + os.path.dirname(os.path.abspath(__file__)) + "\\" + filename
            if os.path.isfile(_f):
                try:
                    webbrowser.open(_f)
                except:
                    pass

    def select_boundary_shp(self):
        self.bound_shp = askopenfilename(initialdir=os.path.abspath(os.path.join(os.path.dirname(__file__), '..')) + "\\01_Conditions\\",
                                         title="Select boundary shapefile containing a rectangular polygon",
                                         filetypes=[("Shapefiles", "*.shp")])
        if os.path.isfile(self.bound_shp):
            self.b_select_bshp.config(fg="forest green")
        else:
            self.b_select_bshp.config(text="Invalid file.")
        self.logger.info(" >> Selected boundary shapefile: " + self.bound_shp)

    def select_HSIcondition(self, *args):
        if args[0] == "hy":
            items = self.lb_condition_hy.curselection()
            self.chsi_condition_hy = [self.condition_list[int(item)] for item in items][0]
            self.dir_inp_hsi_hy = self.dir + "\\HSI\\" + str(self.chsi_condition_hy) + "\\"

            if os.path.exists(self.dir_inp_hsi_hy):
                self.l_inpath_hy.config(fg="cyan4", text="Selected: " + str(self.dir_inp_hsi_hy))
            else:
                self.l_inpath_hy.config(fg="red", text="SELECTION ERROR                                       ")

            self.b_csi_nc["state"] = "normal"
            # update SHArea buttons
            if os.path.isdir(self.dir + "\\CHSI\\" + self.chsi_condition_hy + "\\"):
                self.b_sha_th["state"] = "normal"
                if os.path.isdir(self.dir + "\\CHSI\\" + self.chsi_condition_hy + "\\no_cover\\"):
                    self.b_sharc["state"] = "normal"

        if args[0] == "cov":
            items = self.lb_condition_cov.curselection()
            self.chsi_condition_cov = [self.condition_list[int(item)] for item in items][0]
            self.dir_inp_hsi_cov = self.dir + "\\HSI\\" + str(self.chsi_condition_cov) + "\\"

            if os.path.exists(self.dir_inp_hsi_cov):
                self.l_inpath_cov.config(fg="gold4", text="Selected: " + str(self.dir_inp_hsi_cov))
            else:
                self.l_inpath_cov.config(fg="red", text="SELECTION ERROR                                       ")
            self.b_csi_c["state"] = "normal"
            # update SHArea buttons
            if os.path.isdir(self.dir + "\\CHSI\\" + self.chsi_condition_cov + "\\"):
                self.b_sha_th["state"] = "normal"
                if os.path.isdir(self.dir + "\\CHSI\\" + self.chsi_condition_cov + "\\cover\\"):
                    self.b_sharc["state"] = "normal"
                    self.cb_use_cov["state"] = "normal"

    def set_fish(self, species, *lifestage):
        try:
            lifestage = lifestage[0]
        except:
            lifestage = ""
        if not species == "all":
            if not species == "clear":
                if not (species in self.fish_applied.keys()):
                    self.fish_applied.update({species: []})
                self.fish_applied[species].append(lifestage)
                self.logger.info(" >> Added ambiance: " + str(species) + " - " + str(lifestage))
                self.activate_buttons()
                self.l_aqua.config(text="")
            else:
                self.activate_buttons(revert=True)
                self.fish_applied = {}
                self.logger.info(" >> All species cleared.")
                self.l_aqua.config(text="Select Aquatic Ambiance (at least one)")
        else:
            self.fish_applied = self.fish.species_dict
            self.logger.info(" >> All available ambiances added.")
            self.activate_buttons()
            self.l_aqua.config(text="")

    def set_sharea(self):
        sub_frame = PopUpWindow(self.master)
        self.b_sha_th["state"] = "disabled"
        self.master.wait_window(sub_frame.top)
        self.b_sha_th["state"] = "normal"
        self.sharea_threshold = float(sub_frame.value)
        self.b_sha_th.config(text="Set SHArea\nthreshold\nCurrent: CHSI = " + str(self.sharea_threshold))

        if float(self.sharea_threshold) > 1.0:
            showinfo("WARNING", "The CHSI threshold value for SHArea calcula-\ntion needs to be smaller than 1.0.")

    def shout_dict(self, the_dict):
        msg = "Selected Ambiance(s):"
        for k in the_dict.keys():
            msg = msg + "\n\n > " + str(k) + " - \n   - " + "\n   - ".join(the_dict[k])
        showinfo("Aquatic Ambiance Info", msg)

    def start_app(self, app_name, *args, **kwargs):
        # parse optional arguments
        try:
            for k in kwargs.items():
                if "cover" in k[0]:
                    self.cover_applies = k[1]
        except:
            pass

        # shout if no fish was selected
        if self.fish_applied.__len__() == 0:
            showinfo("ATTENTION", "Select fish species!")
            return -1

        # instantiate app
        if app_name == "hhsi_gui":
            try:
                import sub_gui_hhsi as sgh
                if not self.apply_boundary.get():
                    sub_gui = sgh.HHSIgui(self.master, self.unit, self.fish_applied)
                else:
                    sub_gui = sgh.HHSIgui(self.master, self.unit, self.fish_applied, self.bound_shp)
                self.b_c_select_hy["state"] = "disabled"
                self.master.wait_window(sub_gui.top)
                self.b_c_select_hy["state"] = "normal"
                self.list_habitat_conditions()
            except:
                msg = "ERROR: Failed importing HHSI GUI."

        if app_name == "mhsi_gui":
            try:
                import sub_gui_covhsi as cgh
                sub_gui = cgh.CovHSIgui(self.master, self.unit, self.fish_applied)
                self.b_c_select_cov["state"] = "disabled"
                self.master.wait_window(sub_gui.top)
                self.b_c_select_cov["state"] = "normal"
                self.list_habitat_conditions()
                self.cover_applies = True
            except:
                msg = "Failed importing (cover) HSI GUI."

        if app_name == "chsi":
            try:
                if self.cover_applies:
                    combine_hsi = chsi.CHSI(self.chsi_condition_cov, self.cover_applies, self.unit)
                    self.cb_use_cov["state"] = "normal"
                    self.cb_use_cov.select()
                else:
                    combine_hsi = chsi.CHSI(self.chsi_condition_hy, self.cover_applies, self.unit)
                if not self.apply_boundary.get():
                    ans = combine_hsi.launch_chsi_maker(self.fish_applied, self.combine_method, "")
                else:
                    ans = combine_hsi.launch_chsi_maker(self.fish_applied, self.combine_method, self.bound_shp)
                combine_hsi.clear_cache()
                self.master.bell()
                if not (ans == "OK"):
                    showinfo("WARNING", "No HSI rasters were available for the selected fish species - lifestage.")
                else:
                    # update SHArea buttons
                    self.b_sharc["state"] = "normal"
                    self.b_sha_th["state"] = "normal"
                    webbrowser.open(combine_hsi.path_csi)
            except:
                showinfo("ERROR", "Problem in CHSI object.")

        if app_name == "sharea":
            try:
                if self.cover_applies_sharea.get():
                    sharea = chsi.CHSI(self.chsi_condition_cov, True, self.unit)
                else:
                    try:
                        if not self.cover_applies:
                            sharea = chsi.CHSI(self.chsi_condition_hy, False, self.unit)
                        else:
                            sharea = chsi.CHSI(self.chsi_condition_cov, True, self.unit)
                    except:
                        showinfo("INFO", "Using \'WITH COVER\' option (hydraulic only condition is empty).")
                        sharea = chsi.CHSI(self.chsi_condition_cov, self.cover_applies, self.unit)
                ans = sharea.calculate_sha(self.sharea_threshold, self.fish_applied)
                sharea.clear_cache()

                if ans == "OK":
                    webbrowser.open(sharea.xlsx_out)
                else:
                    showinfo("WARNING", "No CHSI rasters were available for the selected fish species - lifestage.")
            except:
                showinfo("ERROR", "Could not instantiate CHSI object for SHArea calculation.")

        if app_name == "no_condition":
            msg = "CONFIRM HABITAT CONDITION !"
            showinfo("ERROR", msg)

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
    MainGui().mainloop()
