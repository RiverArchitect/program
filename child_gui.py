try:
    import os, sys
    import tkinter as tk
    from tkinter import ttk
    from tkinter.messagebox import askokcancel, showinfo
    from tkinter.filedialog import *
    import webbrowser, logging
except:
    print("ERROR: Missing fundamental packages (required: os, sys, tkinter, webbrowser).")
try:
    sys.path.append(os.path.dirname(__file__) + "\\.site_packages\\riverpy\\")
    import config
    import cDefinitions as cDef
    import cReachManager as cRM
    import fGlobal as fGl
except:
    print("ERROR: Could not import riverpy.")


class RaModuleGui(tk.Frame):
    def __init__(self, master=None):
        self.condition_list = fGl.get_subdir_names(config.dir2ra + "01_Conditions\\")
        self.condition = ""
        self.errors = False
        self.features = cDef.FeatureDefinitions()
        self.feature_id_list = []
        self.feature_name_list = []
        self.logger = logging.getLogger("logfile")
        self.reaches = cDef.ReachDefinitions()
        self.reach_ids_applied = []  # self.reaches.id_xlsx ## initial: all reaches (IDs)
        self.reach_lookup_needed = False
        self.reach_names_applied = []  # self.reaches.names_xlsx ## initial: all reaches (full names)
        self.reach_template_dir = config.dir2mt + ".templates\\"
        self.reader = cRM.Read()
        self.unit = "us"
        self.q_unit = "cfs"
        self.h_unit = "ft"
        self.u_unit = "ft/s"
        self.verified = False
        self.ww = int()  # window width
        self.wh = int()  # window height
        self.wx = int()
        self.wy = int()
        self.xd = 5  # distance holder in x-direction (pixel)
        self.yd = 5  # distance holder in y-direction (pixel)

        # Construct the Frame object.
        tk.Frame.__init__(self, master)
        # if imported from master GUI, redefine master as highest level (ttk.Notebook tab container)
        if __name__ != '__main__':
            self.master = self.winfo_toplevel()
        self.pack(expand=True, fill=tk.BOTH)

        # tkinter standard object
        self.l_reaches = tk.Label(self)

        self.make_standard_menus()

    def add_reach(self, reach):
        if str(reach).__len__() < 1:
            self.reach_names_applied = fGl.dict_values2list(self.reaches.name_dict.values())
            self.reach_ids_applied = fGl.dict_values2list(self.reaches.id_dict.values())
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

    def complete_menus(self):
        # dummy ensures consistency
        pass

    def define_reaches(self):
        try:
            webbrowser.open(config.dir2mt + ".templates\\computation_extents.xlsx")
            self.reach_lookup_needed = True  # tells build_reachmenu that lookup of modified spreasheet info is needed
        except:
            showinfo("ERROR", "Cannot open the file\n" + config.dir2mt + ".templates\\computation_extents.xlsx")

    def del_cache(self):
        if askokcancel("Continue?", "This action will close River Architect and delete all .cache folders from the RiverArchitect/ folder tree.\n Continue?"):
            self.master.destroy()
            tk.Frame.quit(self)
            folder_tree = []
            [folder_tree.append(x[0]) for x in os.walk(config.dir2ra)]
            for f in folder_tree:
                if ".cache" in str(f).lower():
                    try:
                        os.rmdir(f)
                        self.logger.info("Deleted %s." % str(f))
                    except:
                        self.logger.info("ERROR: Could not remove %s." % str(f))

    def make_reach_menu(self, reachmenu):
        # reachmenu = tk.Menu object
        # refresh =  BOOL
        if not self.reach_lookup_needed:
            reachmenu.add_command(label="DEFINE REACHES", command=lambda: self.define_reaches())
            reachmenu.add_command(label="RE-BUILD MENU", command=lambda: self.make_reach_menu(reachmenu))
            reachmenu.add_command(label="_____________________________")
            reachmenu.add_command(label="ALL", command=lambda: self.add_reach(""))
            reachmenu.add_command(label="IGNORE (Use Raster extents)", command=lambda: self.add_reach("ignore"))
            reachmenu.add_command(label="CLEAR ALL", command=lambda: self.add_reach("clear"))
            reachmenu.add_command(label="_____________________________")
            reachmenu.add_command(label=self.reaches.name_dict["reach_00"], command=lambda: self.add_reach("reach_00"))
            reachmenu.add_command(label=self.reaches.name_dict["reach_01"], command=lambda: self.add_reach("reach_01"))
            reachmenu.add_command(label=self.reaches.name_dict["reach_02"], command=lambda: self.add_reach("reach_02"))
            reachmenu.add_command(label=self.reaches.name_dict["reach_03"], command=lambda: self.add_reach("reach_03"))
            reachmenu.add_command(label=self.reaches.name_dict["reach_04"], command=lambda: self.add_reach("reach_04"))
            reachmenu.add_command(label=self.reaches.name_dict["reach_05"], command=lambda: self.add_reach("reach_05"))
            reachmenu.add_command(label=self.reaches.name_dict["reach_06"], command=lambda: self.add_reach("reach_06"))
            reachmenu.add_command(label=self.reaches.name_dict["reach_07"], command=lambda: self.add_reach("reach_07"))
            self.reach_lookup_needed = True
        else:
            # re-build reach names if workbook was modified
            self.reaches.names_xlsx = self.reader.get_reach_info("full_name")
            self.reaches.name_dict = dict(zip(self.reaches.internal_id, self.reaches.names_xlsx))
            reachmenu.entryconfig(7, label=self.reaches.name_dict["reach_00"])
            reachmenu.entryconfig(8, label=self.reaches.name_dict["reach_01"])
            reachmenu.entryconfig(9, label=self.reaches.name_dict["reach_02"])
            reachmenu.entryconfig(10, label=self.reaches.name_dict["reach_03"])
            reachmenu.entryconfig(11, label=self.reaches.name_dict["reach_04"])
            reachmenu.entryconfig(12, label=self.reaches.name_dict["reach_05"])
            reachmenu.entryconfig(13, label=self.reaches.name_dict["reach_06"])
            reachmenu.entryconfig(14, label=self.reaches.name_dict["reach_07"])

        return reachmenu

    def make_standard_menus(self):
        # DROP DOWN MENU
        # the menu does not need packing - see page 44ff
        self.mbar = tk.Menu(self)  # create new menubar
        self.master.config(menu=self.mbar)  # attach it to the root window

        # UNIT SYSTEM DROP DOWN
        self.unitmenu = tk.Menu(self.mbar, tearoff=0)  # create new menu
        self.mbar.add_cascade(label="Units", menu=self.unitmenu)  # attach it to the menubar
        self.unitmenu.add_command(label="[current]  U.S. customary", background="pale green")
        self.unitmenu.add_command(label="[             ]  SI (metric)", command=lambda: self.unit_change())

        # TOOLS DROP DOWN
        self.toolsmenu = tk.Menu(self.mbar, tearoff=0)  # create new menu
        self.mbar.add_cascade(label="Tools", menu=self.toolsmenu)  # attach it to the menubar
        self.toolsmenu.add_command(label="Delete .cache folders", command=lambda: self.del_cache())
        # self.toolsmenu.add_command(label="Open rename files script", command=lambda: self.call_idle(config.dir2ra + Tools/rename_files.py))

        # CLOSE DROP DOWN
        self.closemenu = tk.Menu(self.mbar, tearoff=0)  # create new menu
        self.mbar.add_cascade(label="Close", menu=self.closemenu)  # attach it to the menubar
        self.closemenu.add_command(label="Credits", command=lambda: self.show_credits())
        self.closemenu.add_command(label="Quit program", command=lambda: self.quit_tab())

    def quit_tab(self):
        if askokcancel("Close", "Do you really want to quit?"):
            tk.Frame.quit(self)

    def refresh_conditions(self, lb, sb, condition_dir):
        # lb = tk.ListBox of conditions
        # sb = tk.Scrollbar of conditions
        self.condition_list = fGl.get_subdir_names(condition_dir)
        try:
            lb.delete(0, tk.END)
        except:
            pass

        for e in self.condition_list:
            lb.insert(tk.END, e)
        sb.config(command=lb.yview)

    @staticmethod
    def set_bg_color(master_frame, bg_color):
        master_frame.config(bg=bg_color)
        for wid in master_frame.winfo_children():
            try:
                wid.configure(bg=bg_color)
            except:
                # some widget do not accept bg as kwarg
                pass

    def set_geometry(self, ww, wh, tab_title):
        # ww and wh = INT of window width and window height
        # Upper-left corner of the window.
        self.wx = (self.master.winfo_screenwidth() - ww) / 2
        self.wy = (self.master.winfo_screenheight() - wh) / 2
        # Set the height and location.
        self.master.geometry("%dx%d+%d+%d" % (ww, wh, self.wx, self.wy))
        # Give the window a title.
        if __name__ == '__main__':
            self.master.title(tab_title)
            self.master.iconbitmap(config.dir2ra + ".site_packages\\templates\\code_icon.ico")

    def show_credits(self):
        showinfo("Credits", fGl.get_credits())

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
        if self.unit == "si":
            self.q_unit = "cms"
            self.h_unit = "m"
            self.u_unit = "m/s"
        else:
            self.q_unit = "cfs"
            self.h_unit = "ft"
            self.u_unit = "ft/s"
