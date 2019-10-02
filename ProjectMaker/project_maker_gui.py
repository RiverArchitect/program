try:
    import os, sys
    import tkinter as tk
    from tkinter.messagebox import askokcancel, showinfo, askyesno
    from tkinter.filedialog import *
    import webbrowser, shutil, random
except:
    print("ERROR: Missing fundamental packages (required: os, sys, tkinter, webbrowser).")

try:
    import s20_plantings_delineation as s20
    import s21_plantings_stabilization as s21
    import s30_terrain_stabilization as s30
    import s40_compare_sharea as s40

    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')) + "\\")
    import slave_gui as sg

    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')) + "\\.site_packages\\riverpy\\")
    import config
    import fGlobal as fGl
except:
    print("ERROR: Missing sub routines (cannot access python files in subfolder).")


class PopUpStab(object):
    def __init__(self, master, n_curr, txcr_curr):
        top = self.top = tk.Toplevel(master)
        msg0 = "Manning\'s n and the critical dimensionless bed shear (Shields) Tau_x,cr stress determine grain stability.\n"
        msg1 = "Please refer to the Wiki for more details:\n"
        msg2 = "     https://github.com/RiverArchitect/RA_wiki/LifespanDesign#inpras"
        msg3 = "River Architect uses an internal conversion factor to convert between US customary and metric units.\n"
        self.n_usr = tk.DoubleVar()
        self.txcr_usr = tk.DoubleVar()

        self.l_0 = tk.Label(top, text=msg0+msg1+msg2)
        self.l_0.grid(sticky=tk.W, row=0, rowspan=4, column=0, columnspan=3, padx=5, pady=5)

        self.l_n = tk.Label(top, text="Enter new SI-metric value for Manning\'s n in [s/m^(1/3)]:")
        self.l_n.grid(sticky=tk.W, row=4, column=0, padx=5, pady=5)
        self.e_n = tk.Entry(top, width=10, textvariable=self.n_usr)
        self.e_n.grid(sticky=tk.W, row=4, column=1, padx=5, pady=5)
        self.l_n_c = tk.Label(top, text="current: %s" % str(n_curr))
        self.l_n_c.grid(sticky=tk.W, row=4, column=2, padx=5, pady=5)
        tk.Label(top, text=msg3).grid(row=5, column=0, columnspan=3, padx=5, pady=5)
        tk.Label(top, text="  ").grid(row=6, column=0, columnspan=3, padx=5, pady=5)

        self.l_t = tk.Label(top, text="Enter new value for Tau_x,cr [dimensionless]:")
        self.l_t.grid(sticky=tk.W, row=7, column=0, padx=5, pady=5)
        self.e_t = tk.Entry(top, width=10, textvariable=self.txcr_usr)
        self.e_t.grid(sticky=tk.W, row=7, column=1, padx=5, pady=5)
        self.l_t_c = tk.Label(top, text="current: %s" % str(txcr_curr))
        self.l_t_c.grid(sticky=tk.W, row=7, column=2, padx=5, pady=5)
        tk.Label(top, text="  ").grid(row=8, column=0, columnspan=3, padx=5, pady=5)

        self.b = tk.Button(top, text='OK', command=self.cleanup)
        self.b.grid(row=9, column=2, padx=5, pady=5)

        self.top.iconbitmap(config.code_icon)

    def cleanup(self):
        self.n_def = self.n_usr.get()
        self.t_def = self.txcr_usr.get()
        self.top.destroy()


class MainGui(sg.RaModuleGui):
    def __init__(self, from_master):
        sg.RaModuleGui.__init__(self, from_master)
        self.ww = 740  # window width
        self.wh = 900  # window height
        self.title = "Project Maker"
        self.set_geometry(self.ww, self.wh, self.title)

        self.condition_i_list = []
        self.condition_p_list = []
        self.condition_pl_list = []
        self.condition_ter_list = []
        self.condition_init = ""
        self.condition_proj = ""

        self.dir2prj = ""  # os.path.dirname(os.path.abspath(__file__)) + "\\Geodata\\"
        self.dir2ap = config.dir2ml + "Output\\Rasters\\"
        self.fish = {}
        self.fish_applied = {}
        self.n = 0.04
        self.txcr = 0.047
        self.version = ""
        self.w_e = 14  # width of entries
        self.w_lb = 20  # width of listboxes
        self.xlsx_file_name = ""

        self.get_condition_lists()

        self.apply_wua = tk.BooleanVar()
        self.cover_app_pre = tk.BooleanVar()
        self.cover_app_post = tk.BooleanVar()
        self.prj_name = tk.StringVar()
        self.ter_cr = tk.DoubleVar()
        self.vege_cr = tk.DoubleVar()
        self.vege_stab_cr = tk.DoubleVar()

        self.complete_menus()

        # Create LABELS, ENTRIES and BUTTONS from LEFT to RIGHT and TOP-DOWN
        msg0 = "Welcome to the project maker GUI."
        msg1 = "Info - buttons help identifying requirements for running individual modules.\n\n"
        msg2 = "START: DEFINE AND VALIDATE VARIABLES\n"

        self.l_welcome = tk.Label(self, fg="white", background="gray45", text=msg0 + msg1 + msg2)
        self.l_welcome.grid(sticky=tk.EW, row=0, column=0, rowspan=2, columnspan=3, padx=self.xd, pady=self.yd)

        self.l_version = tk.Label(self, text="Project version: ")
        self.l_version.grid(sticky=tk.W, row=3, column=0, padx=self.xd, pady=self.yd)
        self.e_version = tk.Entry(self, width=self.w_e, textvariable=self.version)
        self.e_version.grid(sticky=tk.EW, row=3, column=1, padx=self.xd, pady=self.yd)
        self.l_version_help = tk.Label(self, fg="gray26", text="(3-digits: v+INT+INT, example: v10)")
        self.l_version_help.grid(sticky=tk.W, row=3, column=2, padx=self.xd, pady=self.yd)

        self.l_site_name = tk.Label(self, text="Project name: ")
        self.l_site_name.grid(sticky=tk.W, row=4, column=0, padx=self.xd, pady=self.yd)
        self.e_site_name = tk.Entry(self, width=self.w_e, textvariable=self.prj_name)
        self.e_site_name.grid(sticky=tk.EW, row=4, column=1, padx=self.xd, pady=self.yd)
        self.l_site_name_help = tk.Label(self, fg="gray26", text="(CamelCase string, no spaces, example: MySite)")
        self.l_site_name_help.grid(sticky=tk.W, row=4, column=2, padx=self.xd, pady=self.yd)

        self.b_val_var = tk.Button(self, text="VALIDATE VARIABLES", command=lambda: self.verify_variables())
        self.b_val_var.grid(sticky=tk.EW, row=8, column=0, columnspan=3, padx=self.xd, pady=self.yd * 2)

        self.l_placeholder1 = tk.Label(self, fg="white", background="gray45", text="ASSESS, DELINEATE AND STABILIZE PLANTINGS")
        self.l_placeholder1.grid(sticky=tk.EW, row=9, column=0, columnspan=3, padx=self.xd, pady=self.yd * 2)
        self.l_vege_cr = tk.Label(self, text="Do not plant where expected lifespans are less than:")
        self.l_vege_cr.grid(sticky=tk.W, row=10, column=0, padx=self.xd, pady=self.yd)
        self.e_vege_cr = tk.Entry(self, width=self.w_e, textvariable=self.vege_cr)
        self.e_vege_cr.grid(sticky=tk.EW, row=10, column=1, padx=self.xd, pady=self.yd)
        self.l_vege_cr_help = tk.Label(self, fg="gray26", text=" years (float number, example: 2.5)")
        self.l_vege_cr_help.grid(sticky=tk.W, row=10, column=2, padx=self.xd, pady=self.yd)
        self.l_vege_stab_cr = tk.Label(self, text="Stabilize plants where expected lifespans are less than:")
        self.l_vege_stab_cr.grid(sticky=tk.W, row=11, column=0, padx=self.xd, pady=self.yd)
        self.e_vege_stab_cr = tk.Entry(self, width=self.w_e, textvariable=self.vege_stab_cr)
        self.e_vege_stab_cr.grid(sticky=tk.EW, row=11, column=1, padx=self.xd, pady=self.yd)
        self.l_vege_stab_cr_help = tk.Label(self, fg="gray26", text=" years (should be higher than above value)")
        self.l_vege_stab_cr_help.grid(sticky=tk.W, row=11, column=2, padx=self.xd, pady=self.yd)
        self.l_condition_pl = tk.Label(self, text="Select plant Max Lifespan Condition: ")
        self.l_condition_pl.grid(sticky=tk.W, row=12, column=0, padx=self.xd, pady=self.yd)
        self.sb_condition_pl = tk.Scrollbar(self, orient=tk.VERTICAL)
        self.sb_condition_pl.grid(sticky=tk.W, row=12, column=2, padx=0, pady=self.yd)
        self.lb_condition_pl = tk.Listbox(self, height=3, width=self.w_lb, yscrollcommand=self.sb_condition_pl.set)
        self.lb_condition_pl.grid(sticky=tk.EW, row=12, column=1, padx=self.xd, pady=self.yd)
        self.lb_condition_pl.insert(tk.END, "Validate Variables")
        self.sb_condition_pl.config(command=self.lb_condition_pl.yview)
        self.b_s20 = tk.Button(self, text="Place best vegetation plantings", command=lambda: self.start_app("s2X"))
        self.b_s20.grid(sticky=tk.EW, row=13, column=0, columnspan=2, padx=self.xd, pady=self.yd)
        self.b_s20["state"] = "disabled"
        self.b_s20_help = tk.Button(self, width=14, bg="white", text="Info (help)", command=lambda: self.help_info("s2X"))
        self.b_s20_help.grid(sticky=tk.E, row=13, column=2, padx=self.xd, pady=self.yd * 2)

        self.l_placeholder2 = tk.Label(self, fg="white", background="gray45", text="TERRAIN STABILIZATION")
        self.l_placeholder2.grid(sticky=tk.EW, row=14, column=0, columnspan=3, padx=self.xd, pady=self.yd * 2)
        self.l_ter_cr = tk.Label(self, text="Critical lifespan:")
        self.l_ter_cr.grid(sticky=tk.W, row=15, column=0, padx=self.xd, pady=self.yd)
        self.e_ter_cr = tk.Entry(self, width=self.w_e, textvariable=self.ter_cr)
        self.e_ter_cr.grid(sticky=tk.EW, row=15, column=1, padx=self.xd, pady=self.yd)
        self.l_ter_cr_help = tk.Label(self, fg="gray26", text=" years (float number, example: 2.5)")
        self.l_ter_cr_help.grid(sticky=tk.W, row=15, column=2, padx=self.xd, pady=self.yd)
        self.l_condition_ter = tk.Label(self, text="Select bioeng. MaxLifespan Condition: ")
        self.l_condition_ter.grid(sticky=tk.W, row=18, column=0, padx=self.xd, pady=self.yd)
        self.sb_condition_ter = tk.Scrollbar(self, orient=tk.VERTICAL)
        self.sb_condition_ter.grid(sticky=tk.W, row=18, column=2, padx=0, pady=self.yd)
        self.lb_condition_ter = tk.Listbox(self, height=3, width=self.w_lb, yscrollcommand=self.sb_condition_ter.set)
        self.lb_condition_ter.grid(sticky=tk.EW, row=18, column=1, padx=self.xd, pady=self.yd)
        self.lb_condition_ter.insert(tk.END, "Validate Variables")
        self.sb_condition_ter.config(command=self.lb_condition_ter.yview)
        self.b_s30_def = tk.Button(self, width=14, bg="white", text="Set stability drivers",
                                   command=lambda: self.set_stab_vars())
        self.b_s30_def.grid(sticky=tk.E, row=18, column=2, padx=self.xd, pady=self.yd * 2)
        self.b_s30 = tk.Button(self, text="Stabilize terrain", command=lambda: self.start_app("s30"))
        self.b_s30.grid(sticky=tk.EW, row=20, column=0, columnspan=2, padx=self.xd, pady=self.yd)
        self.b_s30["state"] = "disabled"
        self.b_s30_help = tk.Button(self, width=14, bg="white", text="Info (help)", command=lambda: self.help_info("s30"))
        self.b_s30_help.grid(sticky=tk.E, row=20, column=2, padx=self.xd, pady=self.yd * 2)

        self.l_placeholder3 = tk.Label(self, fg="white", background="gray45", text=" NET GAIN IN SEASONAL USABLE HABITAT AREA ")
        self.l_placeholder3.grid(sticky=tk.EW, row=21, column=0, columnspan=3, padx=self.xd, pady=self.yd * 2)
        self.l_choose_fish = tk.Label(self, text="1) Select at least one fish species-lifestage (Aquatic Ambiance).")
        self.l_choose_fish.grid(sticky=tk.W, row=22, column=0, columnspan=2, padx=self.xd, pady=self.yd)
        self.b_show_fish = tk.Button(self, width=14, background="white", text="Show selected fish", command=lambda: self.help_info("fish_selected"))
        self.b_show_fish.grid(sticky=tk.E, row=22, column=2, padx=self.xd, pady=self.yd)
        self.cb_cover_pre = tk.Checkbutton(self, text="Optional: Apply cover to pre-project", variable=self.cover_app_pre, onvalue=True, offvalue=False)
        self.cb_cover_pre.grid(sticky=tk.W, row=23, column=0, padx=self.xd, pady=self.yd)
        self.cb_cover_pre.deselect()
        self.cb_cover_post = tk.Checkbutton(self, text="Optional: Apply cover to post-project",
                                            variable=self.cover_app_post, onvalue=True, offvalue=False)
        self.cb_cover_post.grid(sticky=tk.W, row=23, column=1, columnspan=2, padx=self.xd, pady=self.yd)
        self.cb_cover_post.deselect()
        # self.cb_apply_wua = tk.Checkbutton(self, text="Use WUA", variable=self.apply_wua, onvalue=True, offvalue=False)
        # self.cb_apply_wua.grid(sticky=tk.E, row=23, column=2, padx=self.xd, pady=self.yd)
        # self.cb_apply_wua.deselect()
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
        self.condition_ter_list = []  # reset terrain stab. condition list

        dir2HE = config.dir2sh + "CHSI\\"
        full_list = [d for d in os.listdir(dir2HE) if os.path.isdir(os.path.join(dir2HE, d))]
        for f in full_list:
            self.condition_i_list.append(str(f))  # pre-project propositions
            self.condition_p_list.append(str(f))  # post-project propositions

        dir2mlf_ras = config.dir2ml + "Output\\Rasters\\"
        ap_list = [d for d in os.listdir(dir2mlf_ras) if os.path.isdir(os.path.join(dir2mlf_ras, d))]
        for f in ap_list:
            if ("plant" in str(f).lower()) or ("lyr20" in str(f).lower()):
                if not("bio" in str(f).lower()):
                    self.condition_pl_list.append(f)
        dir2lf_ras = config.dir2lf + "Output\\Rasters\\"
        lf_list = [d for d in os.listdir(dir2lf_ras) if os.path.isdir(os.path.join(dir2lf_ras, d))]
        for f in lf_list:
            if ("bio" in str(f).lower()) or ("lyr20" in str(f).lower()) or ("lf_wood" in str(f).lower()) or ("lf_grains" in str(f).lower()):
                if not("plant" in str(f).lower()):
                    self.condition_ter_list.append(f)

    def get_variables(self):
        self.version = str(self.e_version.get())

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

        if app_name == "s2X":
            msges.append("Plant delineation requirements:\n")
            msges.append("- Critical lifespan determines what plantings require stabilization with bioengineering features")
            msges.append("- ProjectArea.shp (Polygon)")
            msges.append("- PlantDelineation.shp (Polygon)")
            msges.append("- Max. Lifespan Maps for plants (lyr20) exist in /MaxLifespan/Output/Rasters/CONDITION/")
            msges.append("    (max_lf_plants.tif)")
            msges.append("- Max. Lifespan Maps for bioengineering (lyr20) exist in /MaxLifespan/Output/Rasters/CONDITION/")
            msges.append("    (lf_wood.tif, lf_bio.tif)\n")

        if app_name == "s30":
            msges.append("Stabilization requirements:\n")
            msges.append("- Critical lifespan determines what plantings require stabilization with bioengineering features")
            msges.append("- ProjectArea.shp (Polygon)")
            msges.append("- Max. Lifespan Maps for bioengineering (lyr20) exist in /MaxLifespan/Output/Rasters/CONDITION/")
            msges.append("    (lf_grains.tif)\n")

        if app_name == "s40":
            msges.append("Seasonal Habitat Area (SHArea) calculation requires:\n")
            msges.append("- ProjectArea.shp (Polygon)")
            msges.append("- Aquatic ambiance for target fish-lifestage (upper left corner of the window - source: RiverArchitect/.site_packages/templates/Fish.xlsx).")
            msges.append("- CHSI conditions defined by folder in /SHArC/CHSI/\n")

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
        self.xlsx_file_name = self.prj_name.get() + "_assessment_" + self.version + ".xlsx"
        if not(os.path.exists(self.dir2prj)):
            shutil.copytree(config.dir2pm + ".templates\\Project_vii_TEMPLATE\\", self.dir2prj)
            os.rename(self.dir2prj + "Project_assessment_vii.xlsx", self.dir2prj + self.xlsx_file_name)
            return "New project assessment folder created."
        else:
            if os.path.isfile(self.dir2prj + self.xlsx_file_name):
                rnd_ext = str(random.randint(1000000, 9999999))
                alt_xlsx_file_name = self.xlsx_file_name.split(".xlsx")[0] + "_old" + rnd_ext + ".xlsx"
                shutil.copyfile(self.dir2prj + self.xlsx_file_name, self.dir2prj + alt_xlsx_file_name)
                return "Old project assessment workbook renamed."
            else:
                try:
                    shutil.copyfile(config.dir2pm + ".templates\\Project_vii_TEMPLATE\\Project_assessment_vii.xlsx", self.dir2prj + self.xlsx_file_name)
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

    def set_stab_vars(self):
        sub_frame = PopUpStab(self.master, self.n, self.txcr)
        self.b_s30_def["state"] = "disabled"
        self.master.wait_window(sub_frame.top)
        self.b_s30_def["state"] = "normal"
        if sub_frame.n_def > 0.0:
            self.n = float(sub_frame.n_def)
        if sub_frame.t_def > 0.0:
            self.txcr = float(sub_frame.t_def)
        showinfo("INFO", "Applying\n Manning\'s n = {0} s/m^(1/3) and\n Tau_x,cr = {1}.".format(str(self.n), str(self.txcr)))

    def start_app(self, app_name):
        # app_name = STR
        c_msg1 = "Background calcluation (check console window).\n\n"
        c_msg2 = "Python windows seem unresponsive in the meanwhile.\n\n"
        c_msg3 = "Logfile and cost master file automatically open once the process successfully terminated.\n\n"
        c_msg4 = "\n    >> PRESS OK TO START << "
        if app_name == "s2X":
            try:
                items = self.lb_condition_pl.curselection()
                condition_pl = [self.condition_pl_list[int(item)] for item in items][0]
                if (condition_pl.__len__() < 1) or (str(condition_pl) == "Validate Variables"):
                    showinfo("ERROR", "Select condition.")
                    return -1
                dir2ml_pl = config.dir2ml + "Output\\Rasters\\" + condition_pl + "\\"
                showinfo("INFO", c_msg1 + c_msg2 + c_msg3 + c_msg4)
                best_plant_dir = s20.main(dir2ml_pl, self.vege_cr.get(), self.prj_name.get(), self.unit, self.version)
                try:
                    lf_req = float(self.vege_stab_cr.get())
                except:
                    showinfo("ERROR", "Wrong format of critical lifespan (must be numeric).")
                    return -1
                s21.main(best_plant_dir,  config.dir2lf + "Output\\Rasters\\" + condition_pl + "\\", lf_req,
                         self.prj_name.get(), self.unit, self.version)
                self.b_s20.config(text="Plantings OK", fg="forest green")
            except:
                showinfo("ERROR", "Close all relevant geofiles and the cost master workbook (xlsx).")

        if app_name == "s30":
            try:
                items = self.lb_condition_ter.curselection()
                condition_ter = [self.condition_ter_list[int(item)] for item in items][0]
                if (condition_ter.__len__() < 1) or (str(condition_ter) == "Validate Variables"):
                    showinfo("ERROR", "Validate Variables first.")
                    return -1
            except:
                showinfo("ERROR", "Select condition.")
                return -1
            try:
                dir2lf_ter = config.dir2lf + "Output\\Rasters\\" + condition_ter + "\\"
                showinfo("INFO", c_msg1 + c_msg2 + c_msg3 + c_msg4)
                try:
                    lf_req = float(self.ter_cr.get())
                except:
                    showinfo("ERROR", "Wrong format of critical lifespan (must be numeric).")
                    return -1
                s30.main(dir2lf_ter, lf_req, self.prj_name.get(), self.unit, self.version, self.n, self.txcr)

                self.b_s30.config(text="Stabilize terrain OK", fg="forest green")
            except:
                showinfo("ERROR", "Close all relevant geofiles and the cost master workbook (xlsx).")

        if app_name == "s40":
            try:
                if self.fish_applied.__len__() == 0:
                    showinfo("ATTENTION", "Select at least one fish species - lifestage!")
                    return -1
                if self.cover_app_pre.get() or self.cover_app_post.get():
                    msg1 = "Make sure that cover cHSI rasters are available in SHArC/CHSI/"
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
                s40.main(self.condition_init, self.condition_proj, self.cover_app_pre.get(), self.cover_app_post.get(), self.fish_applied, self.prj_name.get(), self.unit, self.version, self.apply_wua.get())
                self.b_s40.config(text="Net gain in SHArea calculation OK", fg="forest green")
            except:
                showinfo("ERROR", "Close all relevant geofiles and the cost master workbook (xlsx).")

    def verify_variables(self):
        self.get_variables()
        error_msges = []

        if not (self.version.__len__() == 3):
            error_msges.append("Project version string must have three digits (v + number + number).")
        if self.prj_name.get().split(" ").__len__() > 1:
            error_msges.append("SiteName may not contain spaces. Use CamelCases instead.")
        if not os.path.isdir(config.dir2ml + "Output\\"):
            error_msges.append("Cannot find " + config.dir2ml + "Output\\")

        if error_msges.__len__() > 0:
            self.master.bell()
            showinfo("VERIFICATION ERROR(S)", "Variable definition errors occurred:\n - ".join(error_msges))
            return -1
        else:
            self.get_condition_lists()
            self.update_condition_lb("plant")
            self.update_condition_lb("terrain")
            self.update_condition_lb("init")
            self.update_condition_lb("proj")

            self.dir2prj = config.dir2pm + self.prj_name.get() + "_" + self.version + "\\"
            msg = self.prepare_project()
            self.make_fish_menu()
            self.b_s20["state"] = "normal"
            self.b_s30["state"] = "normal"
            self.b_s40["state"] = "normal"
            msg_next0 = "\n\n A workbook and a layout file will automatically open after clicking on OK."
            msg_next1 = "\n\n >> Create relevant shapefiles and safe the layout as \n" + self.dir2prj + "ProjectMaps.aprx\n \n"
            msg_next2 = "\n\n >> Verify the assessment workbook, transfer terraforming volumes (tab: terraforming volumes), and safe-close the workbook."
            qes = "\n\n Open workbook and Project (aprx) to make the required adaptations?"

            answer = askyesno("INFO", msg + msg_next0 + msg_next1 + msg_next2 + qes)
            if answer:
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
            # self.lb_condition_i.grid(sticky=tk.EW, row=25, column=1, padx=self.xd, pady=self.yd)
            self.sb_condition_i.config(command=self.lb_condition_i.yview)

        if condition_type == "plant":
            try:
                self.lb_condition_pl.delete(0, tk.END)
            except:
                pass
            for e in self.condition_pl_list:
                self.lb_condition_pl.insert(tk.END, e)
            # self.lb_condition_pl.grid(sticky=tk.EW, row=13, column=1, padx=self.xd, pady=self.yd)
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

        if condition_type == "terrain":
            try:
                self.lb_condition_ter.delete(0, tk.END)
            except:
                pass
            for e in self.condition_ter_list:
                self.lb_condition_ter.insert(tk.END, e)
            # self.lb_condition_ter.grid(sticky=tk.EW, row=18, column=1, padx=self.xd, pady=self.yd)
            self.sb_condition_ter.config(command=self.lb_condition_ter.yview)

    def __call__(self):
        self.mainloop()
