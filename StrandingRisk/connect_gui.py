try:
    import os, sys
    import tkinter as tk
    from tkinter import ttk
    from tkinter.messagebox import askokcancel, showinfo
    from tkinter.filedialog import *
    import webbrowser
    import logging
except:
    print("ExceptionERROR: Missing fundamental packages (required: os, sys, logging tkinter, webbrowser).")

try:
    # import own routines
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    import cConnectivityAnalysis as cCA
    # import slave gui
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')) + "\\")
    import slave_gui as sg
    # load routines from riverpy
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')) + "\\.site_packages\\riverpy\\")
    import config
    import cFlows as cFl
    import cFish as cFi
    import fGlobal as fGl
    import cMakeTable as cMkT
except:
    print("ExceptionERROR: Cannot find riverpy.")


class MainGui(sg.RaModuleGui):
    def __init__(self, from_master):
        sg.RaModuleGui.__init__(self, from_master)
        self.ww = 580  # window width
        self.wh = 650  # window height
        self.title = "Stranding Risk"
        self.set_geometry(self.ww, self.wh, self.title)

        self.condition = ""
        self.out_dir = ""
        self.fish = cFi.Fish()
        self.fish_applied = {}

        row = 0

        self.l_prompt = tk.Label(self, text="Select Condition and Physical Habitat")
        self.l_prompt.grid(sticky=tk.W, row=row, column=0, columnspan=3, padx=self.xd, pady=self.yd)
        row += 1

        # select condition
        self.l_condition = tk.Label(self, text="Select condition:")
        self.l_condition.grid(sticky=tk.W, row=row, column=0, padx=self.xd, pady=self.yd)
        self.combo_c = ttk.Combobox(self)
        self.combo_c.grid(sticky=tk.W, row=row, column=1, padx=self.xd, pady=self.yd)
        self.combo_c['values'] = tuple(fGl.get_subdir_names(config.dir2conditions))
        self.combo_c['state'] = 'readonly'
        self.b_s_condition = tk.Button(self, fg="red", text="Select",
                                       command=lambda: self.select_condition())
        self.b_s_condition.grid(sticky=tk.W, row=row, column=2, columnspan=2, padx=self.xd, pady=self.yd)
        row += 1

        self.l_inpath_curr = tk.Label(self, fg="gray60", text="Source: " + config.dir2conditions)
        self.l_inpath_curr.grid(sticky=tk.W, row=row, column=0, columnspan=3, padx=self.xd, pady=self.yd)
        row += 1

        # select Physical Habitat
        self.b_show_fish = tk.Button(self, width=10, fg="RoyalBlue3", bg="white",
                                     text="Show selected Physical Habitat(s)",
                                     command=lambda: self.shout_dict(self.fish_applied))
        self.b_show_fish.grid(sticky=tk.EW, row=row, column=0, columnspan=2, padx=self.xd, pady=self.yd)
        self.b_show_fish["state"] = "disabled"
        self.l_aqua = tk.Label(self, fg="red", text="Select Physical Habitat (at least one)")
        self.l_aqua.grid(sticky=tk.W, row=row, column=2, columnspan=2, padx=0, pady=self.yd)
        row += 1

        # Apply flow reduction
        tk.Label(self, text=" ").grid(row=row, column=0, columnspan=4)  # dummy
        row += 1

        tk.Label(self, text="", bg="LightBlue1", height=10).grid(sticky=tk.EW, row=row, rowspan=4, column=0,
                                                                 columnspan=4)  # dummy
        self.l_flow_red = tk.Label(self, text="Apply flow reduction", bg="LightBlue1")
        self.l_flow_red.grid(sticky=tk.W, row=row, column=0, columnspan=4, padx=self.xd, pady=self.yd)
        row += 1

        self.l_q_high = tk.Label(self, text="Q_high:", bg="LightBlue1")
        self.l_q_high.grid(sticky=tk.W, row=row, column=0, padx=self.xd, pady=self.yd)
        self.c_q_high = ttk.Combobox(self)
        self.c_q_high.grid(sticky=tk.W, row=row, column=1, padx=self.xd, pady=self.yd)
        self.c_q_high['state'] = 'disabled'

        self.l_q_low = tk.Label(self, text="Q_low:", bg="LightBlue1")
        self.l_q_low.grid(sticky=tk.W, row=row, column=2, padx=self.xd, pady=self.yd)
        self.c_q_low = ttk.Combobox(self)
        self.c_q_low.grid(sticky=tk.W, row=row, column=3, padx=self.xd, pady=self.yd)
        self.c_q_low['state'] = 'disabled'
        row += 1

        self.l_dt = tk.Label(self, text="Time period (mins):", bg="LightBlue1")
        self.l_dt.grid(sticky=tk.W, row=row, column=0, padx=self.xd, pady=self.yd)
        self.e_dt = tk.Entry(self)
        self.e_dt.grid(sticky=tk.W, row=row, column=1, padx=self.xd, pady=self.yd)

        self.l_interp = tk.Label(self, text="Interpolation method:", bg="LightBlue1")
        self.l_interp.grid(sticky=tk.W, row=row, column=2, padx=self.xd, pady=self.yd)
        self.c_interp = ttk.Combobox(self)
        self.c_interp.grid(sticky=tk.W, row=row, column=3, padx=self.xd, pady=self.yd)
        self.c_interp['state'] = 'readonly'
        self.c_interp['values'] = ["IDW", "EBK", "Kriging", "Nearest Neighbor"]
        self.c_interp.set("IDW")

        row += 1

        self.b_apply_flow_red = tk.Button(self, text="Apply Flow Reduction", bg="LightBlue1", width=50,
                                          command=lambda: self.apply_flow_red())
        self.b_apply_flow_red.grid(sticky=tk.W, row=row, column=0, columnspan=4, padx=self.xd, pady=self.yd)
        self.b_apply_flow_red['state'] = 'disabled'

        self.complete_menus()

    def run_connectivity(self):
        for species in self.fish_applied.keys():
            for lifestage in self.fish_applied[species]:
                ca = cCA.ConnectivityAnalysis(self.condition, species, lifestage, self.unit) # *** add out dir arg
                ca.connectivity_analysis()

    def apply_flow_red(self):
        if self.c_q_high.get() == '' or self.c_q_low.get() == '':
            self.logger.info("ERROR: Select Q_high and Q_low.")
            return
        q_high = float(self.c_q_high.get().split(" ")[0])
        q_low = float(self.c_q_low.get().split(" ")[0])
        dt = float(self.e_dt.get())
        for species in self.fish_applied.keys():
            for lifestage in self.fish_applied[species]:
                ca = cCA.ConnectivityAnalysis(self.condition,
                                              species, lifestage,
                                              self.unit,
                                              q_high=q_high, q_low=q_low,
                                              dt=dt,
                                              method=self.c_interp.get())
                ca.apply_flow_reduction()

    def select_condition(self):
        try:
            self.condition = self.combo_c.get()
            input_dir = config.dir2conditions + str(self.condition)
            if os.path.exists(input_dir):
                self.b_s_condition.config(fg="forest green", text="Selected: " + self.condition)

                # update flow reduction comboboxes
                mkt = cMkT.MakeFlowTable(self.condition, "", unit=self.unit)
                discharges = sorted(mkt.discharges)
                discharges = ["%i %s" %(q, self.q_unit) for q in discharges]
                self.c_q_high['state'] = 'readonly'
                self.c_q_high['values'] = discharges
                self.c_q_high.set('')
                self.c_q_low['state'] = 'readonly'
                self.c_q_low['values'] = discharges
                self.c_q_low.set('')
                if self.fish_applied != {}:
                    self.b_apply_flow_red["state"] = "normal"
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
            self.logger.info(" >> Rebuilding Physical Habitat menu ...")
            entry_count = 6
            for f_spec in self.fish.species_dict.keys():
                lf_stages = self.fish.species_dict[f_spec]
                for lf_stage in lf_stages:
                    entry = str(f_spec) + " - " + str(lf_stage)
                    self.fishmenu.entryconfig(entry_count, label=entry,
                                              command=lambda arg1=f_spec, arg2=lf_stage: self.set_fish(arg1, arg2))
                    entry_count += 1

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
                self.logger.info(" >> Added Physical Habitat: " + str(species) + " - " + str(lifestage))
                self.b_show_fish["state"] = "normal"
                if self.condition not in ["", "none"]:
                    self.activate_buttons()
                self.l_aqua.config(text="")
            else:
                self.activate_buttons(revert=True)
                self.fish_applied = {}
                self.logger.info(" >> All species cleared.")
                self.l_aqua.config(text="Select Physical Habitat (at least one)")
        else:
            self.fish_applied = self.fish.species_dict
            self.logger.info(" >> All available Physical Habitats added.")
            self.activate_buttons()
            self.l_aqua.config(text="")

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
        self.b_apply_flow_red["state"] = target_state

    def complete_menus(self):
        # FISH SPECIES DROP DOWN
        self.fishmenu = tk.Menu(self.mbar, tearoff=0)  # create new menu
        self.mbar.add_cascade(label="Select Physical Habitat", menu=self.fishmenu)  # attach it to the menubar
        self.fishmenu.add_command(label="DEFINE FISH SPECIES", command=lambda: self.fish.edit_xlsx())
        self.fishmenu.add_command(label="RE-BUILD MENU", command=lambda: self.make_fish_menu(rebuild=True))
        self.fishmenu.add_command(label="_____________________________")
        self.fishmenu.add_command(label="ALL", command=lambda: self.set_fish("all"))
        self.fishmenu.add_command(label="CLEAR ALL", command=lambda: self.set_fish("clear"))
        self.fishmenu.add_command(label="_____________________________")
        self.make_fish_menu(rebuild=False)

    def select_boundary_shp(self):
        self.bound_shp = askopenfilename(initialdir=config.dir2conditions,
                                         title="Select boundary shapefile containing a rectangular polygon",
                                         filetypes=[("Shapefiles", "*.shp")])

    def shout_dict(self, the_dict):
        msg = "Selected:"
        for k in the_dict.keys():
            msg = msg + "\n\n > " + str(k) + " entries:\n   -- " + "\n   -- ".join(the_dict[k])
        showinfo("INFO", msg)

    def __call__(self):
        self.mainloop()

