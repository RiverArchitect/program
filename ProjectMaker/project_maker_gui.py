try:
    import os, sys
    import tkinter as tk
    from tkinter.messagebox import askokcancel, showinfo
    from tkinter.filedialog import *
    import webbrowser, shutil, random
except:
    print("ERROR: Missing fundamental packages (required: os, sys, tkinter, webbrowser).")

try:
    import s20_plantings_delineation as s20
    import s21_plantings_stabilization as s21
    import s40_compare_sharea as s40

    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')) + "\\")
    import slave_gui as sg

    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')) + "\\.site_packages\\riverpy\\")
    import config
    import fGlobal as fGl
except:
    print("ERROR: Missing sub routines (cannot access python files in subfolder).")


class MainGui(sg.RaModuleGui):
    def __init__(self, from_master):
        sg.RaModuleGui.__init__(self, from_master)
        self.ww = 740  # window width
        self.wh = 990  # window height
        self.title = "Project Maker"
        self.set_geometry(self.ww, self.wh, self.title)

        self.condition_i_list = []
        self.condition_p_list = []
        self.condition_pl_list = []
        self.condition_bio_list = []
        self.condition_init = ""
        self.condition_proj = ""

        self.dir2prj = ""  #os.path.dirname(os.path.abspath(__file__)) + "\\Geodata\\"
        self.dir2AP = config.dir2ml + "Output\\Rasters\\"
        self.fish = {}
        self.fish_applied = {}
        self.reach = ""
        self.site_name = ""
        self.stn = ""
        self.vege_cr = float(0.0)
        self.version = ""
        self.w_e = 14  # width of entries
        self.w_lb = 20  # width of listboxes
        self.xlsx_file_name = ""

        self.get_condition_lists()

        self.cover_app_pre = tk.BooleanVar()
        self.cover_app_post = tk.BooleanVar()

        self.complete_menus()

        # Create LABELS, ENTRIES and BUTTONS from LEFT to RIGHT and TOP-DOWN
        msg0 = "Welcome to the project maker GUI."
        msg1 = "Info - buttons help identifying requirements for running individual modules.\n\n"
        msg2 = "START: DEFINE AND VALIDATE VARIABLES\n"

        self.l_welcome = tk.Label(self, fg="white", background="gray45", text=msg0 + msg1 + msg2)
        self.l_welcome.grid(sticky=tk.EW, row=0, column=0, rowspan=3, columnspan=3, padx=self.xd, pady=self.yd)

        self.l_version = tk.Label(self, text="Project version: ")
        self.l_version.grid(sticky=tk.W, row=3, column=0, padx=self.xd, pady=self.yd)
        self.e_version = tk.Entry(self, width=self.w_e, textvariable=self.version)
        self.e_version.grid(sticky=tk.EW, row=3, column=1, padx=self.xd, pady=self.yd)
        self.l_version_help = tk.Label(self, fg="gray26", text="(3-digits: v+INT+INT, example: v10)")
        self.l_version_help.grid(sticky=tk.W, row=3, column=2, padx=self.xd, pady=self.yd)

        self.l_reach = tk.Label(self, text="Reach: ")
        self.l_reach.grid(sticky=tk.W, row=4, column=0, padx=self.xd, pady=self.yd)
        self.e_reach = tk.Entry(self, width=self.w_e, textvariable=self.version)
        self.e_reach.grid(sticky=tk.EW, row=4, column=1, padx=self.xd, pady=self.yd)
        self.l_reach_help = tk.Label(self, fg="gray26", text="(3-characters: RRR, example: TBR)")
        self.l_reach_help.grid(sticky=tk.W, row=4, column=2, padx=self.xd, pady=self.yd)

        self.l_site_name = tk.Label(self, text="Site name: ")
        self.l_site_name.grid(sticky=tk.W, row=5, column=0, padx=self.xd, pady=self.yd)
        self.e_site_name = tk.Entry(self, width=self.w_e, textvariable=self.version)
        self.e_site_name.grid(sticky=tk.EW, row=5, column=1, padx=self.xd, pady=self.yd)
        self.l_site_name_help = tk.Label(self, fg="gray26", text="(CamelCase string, no spaces, example: MySite)")
        self.l_site_name_help.grid(sticky=tk.W, row=5, column=2, padx=self.xd, pady=self.yd)

        self.l_stn = tk.Label(self, text="Site short name: ")
        self.l_stn.grid(sticky=tk.W, row=6, column=0, padx=self.xd, pady=self.yd)
        self.e_stn = tk.Entry(self, width=self.w_e, textvariable=self.version)
        self.e_stn.grid(sticky=tk.EW, row=6, column=1, padx=self.xd, pady=self.yd)
        self.l_stn_help = tk.Label(self, fg="gray26", text="(3-characters: stn, example: sit)")
        self.l_stn_help.grid(sticky=tk.W, row=6, column=2, padx=self.xd, pady=self.yd)

        self.l_vege_cr = tk.Label(self, text="Critical plantings lifespan:\n(for plant stabilization)")
        self.l_vege_cr.grid(sticky=tk.W, row=7, column=0, padx=self.xd, pady=self.yd)
        self.e_vege_cr = tk.Entry(self, width=self.w_e, textvariable=self.version)
        self.e_vege_cr.grid(sticky=tk.EW, row=7, column=1, padx=self.xd, pady=self.yd)
        self.l_vege_cr_help = tk.Label(self, fg="gray26", text=" years (float number, example: 2.5)")
        self.l_vege_cr_help.grid(sticky=tk.W, row=7, column=2, padx=self.xd, pady=self.yd)

        self.b_dir2SR = tk.Button(self, text="Change path to RiverArchitect package (skip this if current is ok)",
                                  command=lambda: self.set_dir2SR())
        self.b_dir2SR.grid(sticky=tk.EW, row=8, column=0, columnspan=3, padx=self.xd, pady=self.yd)
        self.l_dir2SR = tk.Label(self, fg="gray26", text="Current: " + str(config.dir2ra))
        self.l_dir2SR.grid(sticky=tk.W, row=9, column=0, columnspan=3, padx=self.xd, pady=self.yd - 3)

        self.b_val_var = tk.Button(self, text="VALIDATE VARIABLES", command=lambda: self.verify_variables())
        self.b_val_var.grid(sticky=tk.EW, row=10, column=0, columnspan=3, padx=self.xd, pady=self.yd * 2)

        self.l_placeholder1 = tk.Label(self, fg="white", background="gray45", text="ASSESS AND DELINEATE PLANTINGS")
        self.l_placeholder1.grid(sticky=tk.EW, row=11, column=0, columnspan=3, padx=self.xd, pady=self.yd * 2)
        self.l_condition_pl = tk.Label(self, text="Select plant MaxLifespan map folder: ")
        self.l_condition_pl.grid(sticky=tk.W, row=13, column=0, padx=self.xd, pady=self.yd)
        self.sb_condition_pl = tk.Scrollbar(self, orient=tk.VERTICAL)
        self.sb_condition_pl.grid(sticky=tk.W, row=13, column=2, padx=0, pady=self.yd)
        self.lb_condition_pl = tk.Listbox(self, height=3, width=self.w_lb, yscrollcommand=self.sb_condition_pl.set)
        self.lb_condition_pl.grid(sticky=tk.EW, row=13, column=1, padx=self.xd, pady=self.yd)
        self.lb_condition_pl.insert(tk.END, "Validate Variables")
        self.sb_condition_pl.config(command=self.lb_condition_pl.yview)
        self.l_sel_pl = tk.Label(self, fg="gray27",
                                 text="No validation required for selection.")
        self.l_sel_pl.grid(sticky=tk.E, row=13, column=2, padx=self.xd, pady=self.yd)

        self.b_s20 = tk.Button(self, text="Delineate plantings", command=lambda: self.start_app("s20"))
        self.b_s20.grid(sticky=tk.EW, row=15, column=0, columnspan=2, padx=self.xd, pady=self.yd)
        self.b_s20["state"] = "disabled"
        self.b_s20_help = tk.Button(self, width=14, bg="white", text="Info (help)", command=lambda: self.help_info("s20"))
        self.b_s20_help.grid(sticky=tk.E, row=15, column=2, padx=self.xd, pady=self.yd * 2)

        self.l_placeholder2 = tk.Label(self, fg="white", background="gray45", text="VEGETATION PLANTINGS STABILIZATION")
        self.l_placeholder2.grid(sticky=tk.EW, row=16, column=0, columnspan=3, padx=self.xd, pady=self.yd * 2)
        self.l_condition_tbx = tk.Label(self, text="Select bioeng. MaxLifespan Raster folder: ")
        self.l_condition_tbx.grid(sticky=tk.W, row=18, column=0, padx=self.xd, pady=self.yd)
        self.sb_condition_tbx = tk.Scrollbar(self, orient=tk.VERTICAL)
        self.sb_condition_tbx.grid(sticky=tk.W, row=18, column=2, padx=0, pady=self.yd)
        self.lb_condition_tbx = tk.Listbox(self, height=3, width=self.w_lb, yscrollcommand=self.sb_condition_tbx.set)
        self.lb_condition_tbx.grid(sticky=tk.EW, row=18, column=1, padx=self.xd, pady=self.yd)
        self.lb_condition_tbx.insert(tk.END, "Validate Variables")
        self.sb_condition_tbx.config(command=self.lb_condition_tbx.yview)
        self.l_sel_tbx = tk.Label(self, fg="gray27", text="No validation required for selection.")
        self.l_sel_tbx.grid(sticky=tk.E, row=18, column=2, padx=self.xd, pady=self.yd)

        self.b_s21 = tk.Button(self, text="Stabilize plantings", command=lambda: self.start_app("s21"))
        self.b_s21.grid(sticky=tk.EW, row=20, column=0, columnspan=2, padx=self.xd, pady=self.yd)
        self.b_s21["state"] = "disabled"
        self.b_s21_help = tk.Button(self, width=14, bg="white", text="Info (help)", command=lambda: self.help_info("s21"))
        self.b_s21_help.grid(sticky=tk.E, row=20, column=2, padx=self.xd, pady=self.yd * 2)

        self.l_placeholder3 = tk.Label(self, fg="white", background="gray45", text=" NET GAIN IN SEASONAL USABLE HABITAT AREA ")
        self.l_placeholder3.grid(sticky=tk.EW, row=21, column=0, columnspan=3, padx=self.xd, pady=self.yd * 2)
        self.l_choose_fish = tk.Label(self, text="1) Select at least one fish species-lifestage (Aquatic Ambiance).")
        self.l_choose_fish.grid(sticky=tk.W, row=22, column=0, columnspan=2, padx=self.xd, pady=self.yd)
        self.b_show_fish = tk.Button(self, width=14, background="white", text="Show selected fish", command=lambda: self.help_info("fish_selected"))
        self.b_show_fish.grid(sticky=tk.E, row=22, column=2, padx=self.xd, pady=self.yd)
        self.cb_cover_pre = tk.Checkbutton(self, text="Optional: Apply cover to pre-project", variable=self.cover_app_pre, onvalue=True, offvalue=False)
        self.cb_cover_pre.grid(sticky=tk.W, row=23, column=0, columnspan=2, padx=self.xd, pady=self.yd)
        self.cb_cover_pre.deselect()
        self.cb_cover_post = tk.Checkbutton(self, text="Optional: Apply cover to post-project",
                                            variable=self.cover_app_post, onvalue=True, offvalue=False)
        self.cb_cover_post.grid(sticky=tk.W, row=23, column=2, columnspan=2, padx=self.xd, pady=self.yd)
        self.cb_cover_post.deselect()
        self.l_condition_i = tk.Label(self, text="2) Select pre-project condition: ")
        self.l_condition_i.grid(sticky=tk.W, row=25, column=0, padx=self.xd, pady=self.yd)
        self.sb_condition_i = tk.Scrollbar(self, orient=tk.VERTICAL)
        self.sb_condition_i.grid(sticky=tk.W, row=25, column=2, padx=0, pady=self.yd)
        self.lb_condition_i = tk.Listbox(self, height=3, width=self.w_lb, yscrollcommand=self.sb_condition_i.set)
        self.lb_condition_i.grid(sticky=tk.EW, row=25, column=1, padx=self.xd, pady=self.yd)
        self.lb_condition_i.insert(tk.END, "Validate Variables")
        self.sb_condition_i.config(command=self.lb_condition_i.yview)
        self.b_select_c_i = tk.Button(self, width=14, background="white", text="Confirm Selection",
                                      command=lambda: self.select_condition("chsi_initial"))
        self.b_select_c_i.grid(sticky=tk.E, row=25, column=2, padx=self.xd, pady=self.yd)
        self.l_condition_p = tk.Label(self, text="3) Select post-project condition: ")
        self.l_condition_p.grid(sticky=tk.W, row=28, column=0, padx=self.xd, pady=self.yd)
        self.sb_condition_p = tk.Scrollbar(self, orient=tk.VERTICAL)
        self.sb_condition_p.grid(sticky=tk.W, row=28, column=2, padx=0, pady=self.yd)
        self.lb_condition_p = tk.Listbox(self, height=3, width=self.w_lb, yscrollcommand=self.sb_condition_p.set)
        self.lb_condition_p.grid(sticky=tk.EW, row=28, column=1, padx=self.xd, pady=self.yd)
        self.lb_condition_p.insert(tk.END, "Validate Variables")
        self.sb_condition_p.config(command=self.lb_condition_i.yview)
        self.b_select_c_p = tk.Button(self, width=14, background="white", text="Confirm Selection",
                                      command=lambda: self.select_condition("chsi_project"))
        self.b_select_c_p.grid(sticky=tk.E, row=28, column=2, padx=self.xd, pady=self.yd)
        self.b_s40 = tk.Button(self, text="Calculate Net gain in Seasonal Habitat Area (SHArea)", command=lambda: self.start_app("s40"))
        self.b_s40.grid(sticky=tk.EW, row=30, column=0, columnspan=2, padx=self.xd, pady=self.yd)
        self.b_s40["state"] = "disabled"
        self.b_s40_help = tk.Button(self, width=14, bg="white", text="Info (help)", command=lambda: self.help_info("s40"))
        self.b_s40_help.grid(sticky=tk.E, row=30, column=2, padx=self.xd, pady=self.yd)

    def complete_menus(self):
        # FISH SPECIES-LIFESTAGE DROP DOWN
        self.fishmenu = tk.Menu(self.mbar, tearoff=0)  # create new menu
        self.mbar.add_cascade(label="Aquatic Ambiance",
                              menu=self.fishmenu)  # attach it to the menubar
        self.fishmenu.add_command(label="VARIABLES REQUIRED", foreground="gray50",
                                  command=lambda: self.help_info("fish"))
        self.rebuild_fish_menu = False

    def get_condition_lists(self):
        self.condition_i_list = []  # reset pre-project condition list
        self.condition_p_list = []  # reset post-project condition list
        self.condition_pl_list = []  # reset plant condition list
        self.condition_bio_list = []  # reset tbx condition list

        dir2HE = config.dir2sh + "CHSI\\"
        full_list = [d for d in os.listdir(dir2HE) if os.path.isdir(os.path.join(dir2HE, d))]
        for f in full_list:
            self.condition_i_list.append(str(f))  # pre-project propositions
            self.condition_p_list.append(str(f))  # post-project propositions

        dir2lf_ras = config.dir2lf + "Output\\Rasters\\"
        ap_list = [d for d in os.listdir(dir2lf_ras) if os.path.isdir(os.path.join(dir2lf_ras, d))]
        for f in ap_list:
            if ("plant" in str(f).lower()) or ("lyr20" in str(f).lower()):
                if not("bio" in str(f).lower()):
                    self.condition_pl_list.append(f)
            if "bio" in str(f).lower() or ("lyr20" in str(f).lower()):
                if not("plant" in str(f).lower()):
                    self.condition_bio_list.append(f)

    def get_variables(self):
        self.version = str(self.e_version.get())
        self.reach = str(self.e_reach.get()).upper()
        self.site_name = str(self.e_site_name.get())
        self.stn = str(self.e_stn.get()).lower()
        try:
            self.vege_cr = float(self.e_vege_cr.get())
        except:
            self.vege_cr = 0.01

    def help_info(self, app_name):
        # app_name = STR
        msges = []
        if app_name == "fish":
            msges.append("Fishmenu:\n")
            msges.append("Set and validate parameters to complete the fish dropdown menu.")

        if app_name == "fish_selected":
            msges.append("Selected fish:\n")
            for k in self.fish_applied.keys():
                msges.append("> " + str(k) + " lifestage(s):\n   - " + "\n   - ".join(self.fish_applied[k]))

        if app_name == "s20":
            msges.append("Plant delineation module requirements:\n")
            msges.append("- ProjectArea.shp (Polygon)")
            msges.append("- PlantDelineation.shp (Polygon)")
            msges.append("- Maximum Lifespan Maps for plants (lyr20) are stored in /MaxLifespan/Output/Rasters/condition_RRR_lyr20.../\n")

        if app_name == "s21":
            msges.append("Plant stabilization module requirements:\n")
            msges.append("- ProjectArea.shp (Polygon)")
            msges.append("- Critical plantings lifespan determines plantings that require stabilization with bioengineering features")
            msges.append("- Maximum Lifespan Maps for bioengineering (lyr20) features are stored in /MaxLifespan/Output/Rasters/condition_RRR_lyr20.../\n")

        if app_name == "s40":
            msges.append("Weighted Usable habitat Area module requirements:\n")
            msges.append("- ProjectArea.shp (Polygon)")
            msges.append("- The fish menu is situated in the upper left corner of the GUI window.")
            msges.append("- The fish menu contents originate from definitions in /RiverArchitect/.site_packages/templates/Fish.xlsx.")
            msges.append("- CHSI conditions refer to available folders in /SHArC/CHSI\n")

        showinfo("Module Info", "\n".join(msges))

    def make_fish_menu(self):
        # rebuild = True -> rebuilt menu mode
        if not self.rebuild_fish_menu:
            # initial menu construction
            sys.path.append(config.dir2ripy)
            try:
                import cFish as cFi
                self.fish = cFi.Fish()
            except:
                showinfo("ERROR", "Invalid directory to RiverArchitect/.site_packages/riverpy/.")
                return -1
            self.fishmenu.entryconfig(0, label="EDIT FISH", command=lambda: self.fish.edit_xlsx())
            self.fishmenu.add_command(label="RE-BUILD FISH MENU", command=lambda: self.make_fish_menu())
            self.fishmenu.add_command(label="_____________________________")
            self.fishmenu.add_command(label="ALL", command=lambda: self.set_fish("all"))
            self.fishmenu.add_command(label="CLEAR ALL", command=lambda: self.set_fish("clear"))
            self.fishmenu.add_command(label="_____________________________")
            for f_spec in self.fish.species_dict.keys():
                lf_stages = self.fish.species_dict[f_spec]
                for lf_stage in lf_stages:
                    entry = str(f_spec) + " - " + str(lf_stage)
                    self.fishmenu.add_command(label=entry,
                                              command=lambda arg1=f_spec, arg2=lf_stage: self.set_fish(arg1, arg2))
            self.rebuild_fish_menu = True
        else:
            self.fish.assign_fish_names()
            entry_count = 6
            for f_spec in self.fish.species_dict.keys():
                lf_stages = self.fish.species_dict[f_spec]
                for lf_stage in lf_stages:
                    entry = str(f_spec) + " - " + str(lf_stage)
                    self.fishmenu.entryconfig(entry_count, label=entry,
                                              command=lambda arg1=f_spec, arg2=lf_stage: self.set_fish(arg1, arg2))
                    entry_count += 1

    def prepare_project(self):
        # requires that self.dir2prj was updated before
        self.xlsx_file_name = self.reach + "_" + self.stn + "_assessment_" + self.version + ".xlsx"
        if not(os.path.exists(self.dir2prj)):
            shutil.copytree(config.dir2pm + ".templates\\REACH_stn_vii_TEMPLATE\\", self.dir2prj)
            os.rename(self.dir2prj + "REACH_stn_assessment_vii.xlsx", self.dir2prj + self.xlsx_file_name)
            return "New project assessment folder created."
        else:
            if os.path.isfile(self.dir2prj + self.xlsx_file_name):
                rnd_ext = str(random.randint(1000000, 9999999))
                alt_xlsx_file_name = self.reach + "_" + self.stn + "_assessment_" + self.version + "_old" + rnd_ext + ".xlsx"
                shutil.copyfile(self.dir2prj + self.xlsx_file_name, self.dir2prj + alt_xlsx_file_name)
                return "Old project assessment workbook renamed."
            else:
                try:
                    os.rename(self.dir2prj + "REACH_stn_assessment_vii.xlsx", self.dir2prj + self.xlsx_file_name)
                    return "Project assessment workbook created."
                except:
                    return "A PROBLEM OCCURRED: Ensure that " + self.dir2prj + self.xlsx_file_name + " exists."

    def select_condition(self, condition_type):
        if condition_type == "chsi_initial":
            items = self.lb_condition_i.curselection()
            self.condition_init = [self.condition_i_list[int(item)] for item in items][0]
            self.b_select_c_i.config(fg="forest green", text="Selection OK")
        if condition_type == "chsi_project":
            items = self.lb_condition_p.curselection()
            self.condition_proj = [self.condition_p_list[int(item)] for item in items][0]
            self.b_select_c_p.config(fg="forest green", text="Selection OK")

    def set_dir2SR(self):
        config.dir2ra = askdirectory(initialdir=".") + "/"
        self.l_dir2SR.config(text="Current: " + str(config.dir2ra))

    def set_fish(self, species, *lifestage):
        try:
            lifestage = lifestage[0]
        except:
            lifestage = ""
        if not species == "all":
            if not species == "clear":
                if not (species in self.fish_applied.keys()):
                    self.fish_applied.update({species: []})
                try:
                    self.fish_applied[species].append(lifestage)
                except:
                    pass
                self.b_show_fish.config(fg="forest green")
                showinfo("Fish added", "Added: " + species + " - " + lifestage)
            else:
                self.fish_applied = {}
        else:
            self.fish_applied = self.fish.species_dict
            self.b_show_fish.config(fg="forest green")
            showinfo("Fish added", "All available species added.")

    def start_app(self, app_name):
        # app_name = STR
        c_msg1 = "Background calcluation (check console window).\n\n"
        c_msg2 = "Python windows seem unresponsive in the meanwhile.\n\n"
        c_msg3 = "Logfile and cost master file automatically open once the process successfully terminated.\n\n"
        c_msg4 = "\n    >> PRESS OK TO START << "
        if app_name == "s20":
            try:
                items = self.lb_condition_pl.curselection()
                condition_pl = [self.condition_pl_list[int(item)] for item in items][0]
                if (condition_pl.__len__() < 1) or (str(condition_pl) == "Validate Variables"):
                    showinfo("ERROR", "Select condition.")
                    return -1
                dir2AP_pl = config.dir2ml + "Output\\Rasters\\" + condition_pl + "\\"
                showinfo("INFO", c_msg1 + c_msg2 + c_msg3 + c_msg4)
                s20.main(dir2AP_pl, self.reach, self.stn, self.unit, self.version)
                self.b_s20.config(text="Delineate plantings OK", fg="forest green")
            except:
                showinfo("ERROR", "Close all relevant geofiles and the cost master workbook (xlsx).")

        if app_name == "s21":
            try:
                items = self.lb_condition_tbx.curselection()
                condition_tbx = [self.condition_bio_list[int(item)] for item in items][0]
                if (condition_tbx.__len__() < 1) or (str(condition_tbx) == "Validate Variables"):
                    showinfo("ERROR", "Select condition.")
                    return -1
                dir2AP_tbx = config.dir2ml + "Output\\Rasters\\" + condition_tbx + "\\"
                showinfo("INFO", c_msg1 + c_msg2 + c_msg3 + c_msg4)
                s21.main(dir2AP_tbx, self.vege_cr, self.reach, self.stn, self.unit, self.version)
                self.b_s21.config(text="Stabilize plantings OK", fg="forest green")
            except:
                showinfo("ERROR", "Close all relevant geofiles and the cost master workbook (xlsx).")

        if app_name == "s40":
            try:
                if self.fish_applied.__len__() == 0:
                    showinfo("ATTENTION", "Select at least one fish species - lifestage!")
                    return -1
                if self.cover_app_pre.get() or self.cover_app_post.get():
                    msg1 = "Make sure that cover cHSI rasters are available in SHArC/cHSI/"
                    msg2 = str(self.condition_init) + " AND / OR " + str(self.condition_proj) + "/cover/.\n\n"
                    msg3 = "Press OK to launch SHArea calculation with cover."
                    showinfo("Info", msg1 + msg2 + msg3)
                if (self.condition_init.__len__() < 1) or (str(self.condition_init) == "Validate Variables"):
                    showinfo("ERROR", "Select initial condition.")
                    return -1
                if (self.condition_proj.__len__() < 1) or (str(self.condition_proj) == "Validate Variables"):
                    showinfo("ERROR", "Select condition after terraforming.")
                    return -1
                showinfo("INFO", c_msg1 + c_msg2 + c_msg3 + c_msg4)
                s40.main(self.condition_init, self.condition_proj, self.cover_app_pre.get(), self.cover_app_post.get(), config.dir2ra, self.fish_applied, self.reach, self.stn, self.unit, self.version)
                self.b_s40.config(text="Net gain in SHArea calculation OK", fg="forest green")
            except:
                showinfo("ERROR", "Close all relevant geofiles and the cost master workbook (xlsx).")

    def verify_variables(self):
        self.get_variables()
        error_msges = []
        if not (self.version[0] == "v"):
            error_msges.append("Project version must start with small letter \'v\'.")
        if not (self.version.__len__() == 3):
            error_msges.append("Project version string must have three digits (v + number + number).")
        if not (self.reach.__len__() == 3):
            error_msges.append("Reach string must consist of three character (Letter1 + Letter2 + Letter3).")
        if self.site_name.split(" ").__len__() > 1:
            error_msges.append("SiteName may not contain spaces. Use CamelCases instead.")
        if not (self.stn.__len__() == 3):
            error_msges.append("Site short name must consist of three small letters (letter1 + letter2 + letter3).")
        if self.vege_cr == 0.01:
            error_msges.append("Minimum survival threshold for plants must be a float number in years.")
        if not os.path.isdir(config.dir2ml + "Output\\"):
            error_msges.append("Check path to RiverArchitect package and its subdirectory MaxLifespan/Output.")

        if error_msges.__len__() > 0:
            self.master.bell()
            showinfo("VERIFICATION ERROR(S)", "Variable definition errors occurred:\n - ".join(error_msges))
        else:
            self.get_condition_lists()
            self.update_condition_lb("plant")
            self.update_condition_lb("toolbox")
            self.update_condition_lb("init")
            self.update_condition_lb("proj")

            self.dir2prj = os.path.dirname(os.path.abspath(__file__)) + "\\" + self.reach + "_" + self.stn + "_" + self.version + "\\"
            msg = self.prepare_project()
            self.make_fish_menu()
            self.b_s20["state"] = "normal"
            self.b_s21["state"] = "normal"
            self.b_s40["state"] = "normal"
            msg_next0 = "\n\n A workbook and a layout file will automatically open after clicking on OK."
            msg_next1 = "\n\n >> Create relevant shapefiles and safe the layout as \n" + self.dir2prj + "ProjectMaps.aprx\n \n"
            msg_next2 = "\n\n >> Verify the assessment workbook, transfer terraforming volumes (tab: terraforming volumes), and safe-close the workbook."
            showinfo("INFO", msg + msg_next0 + msg_next1 + msg_next2)

            try:
                webbrowser.open(self.dir2prj + self.xlsx_file_name)
                try:
                    webbrowser.open(self.dir2prj + "ProjectMaps.aprx")
                except:
                    pass
            except:
                sol1 = "\n\n >> Verify that the workbook exists in " + self.dir2prj
                sol2 = "\n\n >> Ensure that a standard application is defined for opening workbooks."
                showinfo("ERROR", "Could not open " + self.xlsx_file_name + "." + sol1 + sol2)

    def update_condition_lb(self, condition_type):
        if condition_type == "init":
            try:
                self.lb_condition_i.delete(0, tk.END)
            except:
                pass
            for e in self.condition_i_list:
                self.lb_condition_i.insert(tk.END, e)
            self.lb_condition_i.grid(sticky=tk.EW, row=25, column=1, padx=self.xd, pady=self.yd)
            self.sb_condition_i.config(command=self.lb_condition_i.yview)

        if condition_type == "plant":
            try:
                self.lb_condition_pl.delete(0, tk.END)
            except:
                pass
            for e in self.condition_pl_list:
                self.lb_condition_pl.insert(tk.END, e)
            self.lb_condition_pl.grid(sticky=tk.EW, row=13, column=1, padx=self.xd, pady=self.yd)
            self.sb_condition_pl.config(command=self.lb_condition_pl.yview)

        if condition_type == "proj":
            try:
                self.lb_condition_p.delete(0, tk.END)
            except:
                pass
            for e in self.condition_p_list:
                self.lb_condition_p.insert(tk.END, e)
            self.lb_condition_p.grid(sticky=tk.EW, row=28, column=1, padx=self.xd, pady=self.yd)
            self.sb_condition_p.config(command=self.lb_condition_p.yview)

        if condition_type == "toolbox":
            try:
                self.lb_condition_tbx.delete(0, tk.END)
            except:
                pass
            for e in self.condition_bio_list:
                self.lb_condition_tbx.insert(tk.END, e)
            self.lb_condition_tbx.grid(sticky=tk.EW, row=18, column=1, padx=self.xd, pady=self.yd)
            self.sb_condition_tbx.config(command=self.lb_condition_tbx.yview)

    def __call__(self):
        self.mainloop()
