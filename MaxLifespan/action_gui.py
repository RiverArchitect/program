try:
    import os, sys
    import Tkinter as tk
    from tkFileDialog import *  # in python3 use tkinter.filedialog instead
    from tkMessageBox import askokcancel, showinfo
    import webbrowser
except:
    print("ExceptionERROR: Missing fundamental packages (required: os, sys, Tkinter, webbrowser).")

try:
    # load function from LifespanDesign
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')) + "\\.site_packages\\riverpy\\")
    import fGlobal as fg
except:
    print("ExceptionERROR: Cannot find package files (/.site_packages/riverpy/fGlobal.py).")


class RunGui:
    def __init__(self, master):
        self.path = r"" + os.path.dirname(os.path.abspath(__file__))

        # Construct the Frame object.
        self.master = tk.Toplevel(master)

        self.master.wm_title("RUNNING ... (console messages)")
        self.master.bell()

        self.msg = ""

        # ARRANGE GEOMETRY
        ww = 400
        wh = 150
        wx = (self.master.winfo_screenwidth() - ww) / 2
        wy = (self.master.winfo_screenheight() - wh) / 2
        self.master.geometry("%dx%d+%d+%d" % (ww, wh, wx, wy))
        self.master.iconbitmap(os.path.dirname(os.path.abspath(__file__)) + "\\.templates\\code_icon.ico")

    def gui_geo_maker(self, condition, feature_type, mapping, units, inpath):
        import action_planner as ap
        ap.geo_file_maker(condition, feature_type, mapping, units, inpath)


    def gui_layout_maker(self, condition, feature_type):
        import action_planner as ap
        ap.layout_maker(condition, feature_type)

    def gui_map_maker(self, condition):
        import action_planner as ap
        ap.map_maker(condition)

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


class ActionGui(tk.Frame):
    def __init__(self, master=None):
        self.path = r"" + os.path.dirname(os.path.abspath(__file__))
        self.path2fa_rasters = os.path.abspath(
            os.path.join(os.path.dirname(__file__), '..')) + "\\LifespanDesign\\Products\\Rasters\\"
        self.feature_type = []
        self.condition = "set condition"
        self.condition_list = fg.get_subdir_names(self.path2fa_rasters)
        self.inpath = os.path.abspath(
            os.path.join(os.path.dirname(__file__), '..')) + "\\LifespanDesign\\Products\\Rasters\\" + str(
            self.condition) + "\\"
        self.verified = False
        self.errors = False
        self.mapping = True
        self.mod_dir = False    # if user-defined input directory: True
        self.unit = "us"
        self.wild = False

        # Construct the Frame object.
        tk.Frame.__init__(self, master)
        self.pack(expand=True, fill=tk.BOTH)
        self.master.iconbitmap(os.path.dirname(os.path.abspath(__file__))+"\\.templates\\code_icon.ico")

        # ARRANGE GEOMETRY
        self.xd = 5  # distance holder in x-direction (pixel)
        self.yd = 5  # distance holder in y-direction (pixel)
        # width and height of the window
        ww = 500
        wh = 230
        wx = (self.master.winfo_screenwidth() - ww) / 2
        wy = (self.master.winfo_screenheight() - wh) / 2
        self.master.geometry("%dx%d+%d+%d" % (ww, wh, wx, wy))  # set height and location
        self.master.title("Max Lifespan")  # window title

        # GUI OBJECT VARIABLES
        self.gui_condition = tk.StringVar()
        self.gui_interpreter = tk.StringVar()

        # LABELS
        self.l_s_feat = tk.Label(self, text="Selected feature layer: ")
        self.l_s_feat.grid(sticky=tk.W, row=0, column=0, padx=self.xd, pady=self.yd)
        self.l_features = tk.Label(self, fg="red",
                                   text="Select from \'Feature Layer\' Menu (required for Raster Maker only)")
        self.l_features.grid(sticky=tk.W, row=0, column=1, columnspan=5, padx=self.xd, pady=self.yd)
        self.l_condition = tk.Label(self, text="Condition: \n(select)")
        self.l_condition.grid(sticky=tk.W, row=1, column=0, padx=self.xd, pady=self.yd)

        # DROP DOWN ENTRIES (SCROLL BARS)
        self.sb_condition = tk.Scrollbar(self, orient=tk.VERTICAL)
        self.sb_condition.grid(sticky=tk.W, row=1, column=2, padx=0, pady=self.yd)
        self.lb_condition = tk.Listbox(self, height=3, width=14, yscrollcommand=self.sb_condition.set)
        for e in self.condition_list:
            self.lb_condition.insert(tk.END, e)
        self.lb_condition.grid(sticky=tk.W, row=1, column=1, padx=self.xd, pady=self.yd)
        self.sb_condition.config(command=self.lb_condition.yview)

        # ENTRIES
        self.l_inpath_curr = tk.Label(self, fg="dark slate gray", text="Source: "+str(self.path2fa_rasters))
        self.l_inpath_curr.grid(sticky=tk.W, row=6, column=0, columnspan=5, padx=self.xd, pady=self.yd)

        # BUTTONS
        self.b_c_help = tk.Button(self, width=5, bg="white", text="Info", command=lambda:
                         self.condition_info())
        self.b_c_help.grid(sticky=tk.W, row=1, column=3, padx=self.xd, pady=self.yd)
        self.b_inpath = tk.Button(self, width=25, bg="white", text="Change input directory",
                                  command=lambda: self.change_inpath())
        self.b_inpath.grid(sticky=tk.EW, row=2, column=0, columnspan=2, padx=self.xd, pady=self.yd)
        self.b_mod_m = tk.Button(self, width=25, bg="white", text="Modify map extent", command=lambda:
                        self.open_inp_file("mapping.inp"))
        self.b_mod_m.grid(sticky=tk.EW, row=2, column=2, columnspan=2, padx=self.xd, pady=self.yd)

        # dummy label for arrangement
        self.l_dummy = tk.Label(self, text="                          ")
        self.l_dummy.grid(sticky=tk.W, row=2, column=4, padx=self.xd, pady=self.yd)

        # DROP DOWN MENU
        # menu does not need packing - see slide 44ff
        self.mbar = tk.Menu(self)  # create new menubar
        self.master.config(menu=self.mbar)  # attach it to the root window

        # FEATURE DROP DOWN
        self.featmenu = tk.Menu(self.mbar, tearoff=0)  # create new menu
        self.mbar.add_cascade(label="Feature layer", menu=self.featmenu)  # attach it to the menubar
        # add menu entries
        self.featmenu.add_command(label="Group layer: Terraforming", command=lambda: self.define_feature("Terraforming"))
        self.featmenu.add_command(label="Group layer: Plantings", command=lambda: self.define_feature("Plantings"))
        self.featmenu.add_command(label="Group layer: Bioengineering", command=lambda: self.define_feature("Bioengineering"))
        self.featmenu.add_command(label="Group layer: Maintenance", command=lambda: self.define_feature("Maintenance"))
        self.featmenu.add_command(label="CLEAR", command=lambda: self.define_feature("clear"))

        # RUN DROP DOWN
        self.runmenu = tk.Menu(self.mbar, tearoff=0)  # create new menu
        self.mbar.add_cascade(label="Run", menu=self.runmenu)  # attach it to the menubar
        self.runmenu.add_command(label="Verify settings", command=lambda: self.verify())
        self.runmenu.add_command(label="Run: Geofile Maker", command=lambda: self.run_geo_maker())
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

        # CHECK BOXES (CHECKBUTTONS)
        self.cb_lyt = tk.Checkbutton(self, fg="SteelBlue", text="Create maps and layouts after making geofiles",
                                     command=lambda: self.mod_mapping())
        self.cb_lyt.grid(sticky=tk.W, row=7, column=0, columnspan=4, padx=self.xd, pady=self.yd)
        self.cb_lyt.select()  # select by default

    def condition_info(self):
        msg = "The condition list refers to available rasters in\n" + self.path2fa_rasters + \
              "\n\nThe selected condition will be used for the maximum lifespan map generation."
        showinfo("CONDITION INFO", msg)

    def change_inpath(self):
        self.inpath = askdirectory(initialdir='.')
        self.inpath = self.inpath + "/"
        self.l_inpath_curr.destroy()
        self.l_inpath_curr = tk.Label(self, fg="dark slate gray", text="Current: " + str(self.inpath))
        self.l_inpath_curr.grid(sticky=tk.W, row=6, column=0, columnspan=5, padx=self.xd, pady=self.yd)
        self.mod_dir = True

    def define_feature(self, feature_type):
        if not(feature_type == "clear"):
            self.feature_type.append(feature_type.lower())
            self.l_features.config(fg="SteelBlue", text=", ".join(self.feature_type))
            if self.mapping:
                showinfo("Attention", "Ensure correct layer sources in .mxd files (.templates/layouts/)\n or deactivate \'Create maps ...\' checkbox.")
        else:
            self.feature_type = []
            self.l_features.config(fg="red",
                                   text="Select from \'Feature layer\' Menu (required for Geofile Maker only)")

    def mod_mapping(self):
        if not self.mapping:
            self.mapping = True
        else:
            self.mapping = False

    def myquit(self):
        if askokcancel("Close", "Do you really wish to quit?"):
            tk.Frame.quit(self)

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
            for feat in self.feature_type:
                run.gui_geo_maker(self.condition, feat, self.mapping, self.unit, self.inpath)
                run.gui_quit()
            self.cb_lyt.destroy()
            self.b_inpath.destroy()
            self.lb_condition.destroy()
            self.sb_condition.destroy()
            self.l_c_ok = tk.Label(self, fg="forest green", text=str(self.condition))
            self.l_c_ok.grid(sticky=tk.W, row=1, column=1, padx=self.xd, pady=self.yd)

            if not self.mapping:
                self.master.bell()
            tk.Button(self, width=25, bg="pale green", text="QUIT", command=lambda:
                        tk.Frame.quit(self)).grid(sticky=tk.EW, row=3, column=0, padx=self.xd, pady=self.yd)
            if not self.mapping:
                tk.Button(self, bg="gold", width=25, text="IMPORTANT\n Read logfile(s)", command=lambda:
                        self.open_log_file()).grid(sticky=tk.EW, row=3, column=3, padx=self.xd, pady=self.yd)
            else:
                tk.Button(self, bg="pale green", width=25, text="IMPORTANT\n Read logfile(s) from Layout Maker",
                          command=lambda:
                          self.open_log_file()).grid(sticky=tk.EW, row=3, column=3, padx=self.xd,
                                                     pady=self.yd)
            if self.mapping:
                showinfo("INFORMATION", "Maps (.pdf files) prepared in opened folder.\n" + os.path.dirname(
                    os.path.abspath(__file__)) + "\\Output\\Maps\\" + str(
                    self.condition) + "\n\nLayouts (.mxd) files are stored in:\n" + os.path.dirname(
                    os.path.abspath(__file__)) + "\\Output\\Layouts\\" + str(self.condition))

    def run_layout_maker(self):
        if not self.verified:
            self.verify(False)
        if self.verified:

            run = RunGui(self)
            for feat in self.feature_type:
                run.gui_layout_maker(self.condition, feat)
                run.gui_quit()
            try:
                self.cb_lyt.destroy()
                self.b_inpath.destroy()
                self.lb_condition.destroy()
                self.sb_condition.destroy()
                self.l_c_ok = tk.Label(self, fg="forest green", text=str(self.condition))
                self.l_c_ok.grid(sticky=tk.W, row=1, column=1, padx=self.xd, pady=self.yd)
                if not self.mapping:
                    self.master.bell()
            except:
                pass
            tk.Button(self, width=25, bg="pale green", text="QUIT\n or (re-)Run: Layout / Map Maker",
                      command=lambda:
                      tk.Frame.quit(self)).grid(sticky=tk.EW, row=3, column=0, padx=self.xd,
                                                pady=self.yd)
            tk.Button(self, bg="gold", width=25, text="IMPORTANT\n Read logfile(s) from Layout Maker", command=lambda:
                      self.open_log_file()).grid(sticky=tk.EW, row=3, column=3, padx=self.xd, pady=self.yd)
        showinfo("INFO", "Layout preparation finished.")

    def run_map_maker(self):
        if not self.verified:
            self.verify(False)
        if self.verified:
            showinfo("INFORMATION",
                     "Map creation may take some minutes. \n Python windows seem unresponsive in the meanwhile. \n Check console messages.\n \n PRESS OK TO START")
            run = RunGui(self)

            run.gui_map_maker(self.condition)
            run.gui_quit()
            try:
                self.cb_lyt.destroy()
                self.b_inpath.destroy()
                self.lb_condition.destroy()
                self.sb_condition.destroy()
                self.l_c_ok = tk.Label(self, fg="forest green", text=str(self.condition))
                self.l_c_ok.grid(sticky=tk.W, row=1, column=1, padx=self.xd, pady=self.yd)
            except:
                pass
            self.master.bell()
            tk.Button(self, width=25, bg="pale green", text="QUIT\n or re-Run: Layout / Map Maker",
                      command=lambda:
                      tk.Frame.quit(self)).grid(sticky=tk.EW, row=3, column=0, padx=self.xd, pady=self.yd)
            tk.Button(self, bg="pale green", width=25, text="IMPORTANT\n Read logfile(s) from Map Maker", command=lambda:
                      self.open_log_file()).grid(sticky=tk.EW, row=3, column=3, padx=self.xd, pady=self.yd)

    def show_credits(self):
        msg = "Version info: 0.1 (June 2018)\nAuthor: Sebastian Schwindt\nInstitute: Pasternack Lab, UC Davis \n\nEmail: sschwindt[at]ucdavis.edu"
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
                if not ((sys.version_info.major == 2) and (sys.version_info.minor == 7)):
                    error_msg.append("Wrong Python interpreter (Required: Python v.2.7 or higher but not v.3.x).")
                    self.errors = True
                    self.verified = False
            except:
                pass
        try:
            items = self.lb_condition.curselection()
            self.condition = [self.condition_list[int(item)] for item in items][0]
            if not self.mod_dir:
                self.inpath = r"" + self.path2fa_rasters + str(self.condition) + "\\"

            self.l_inpath_curr.destroy()
            self.l_inpath_curr = tk.Label(self, fg="forest green", text="Apply: " + str(self.inpath))
            self.l_inpath_curr.grid(sticky=tk.W, row=6, column=0, columnspan=5, padx=self.xd, pady=self.yd)

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


# enable script to run stand-alone
if __name__ == "__main__":
    ActionGui().mainloop()
