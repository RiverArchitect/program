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
    import cConnectivityAnalysis as cCA
    # import slave gui
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')) + "\\")
    import slave_gui as sg
    # load routines from riverpy
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')) + "\\.site_packages\\riverpy\\")
    import cFlows as cFl
    import cFish as cFi
    import fGlobal as fGl
except:
    print("ExceptionERROR: Cannot find riverpy.")


class MainGui(sg.RaModuleGui):
    def __init__(self, from_master):
        sg.RaModuleGui.__init__(self, from_master)
        self.ww = 580  # window width
        self.wh = 650  # window height
        self.title = "Connectivity"
        self.set_geometry(self.ww, self.wh, self.title)

        self.condition = ""
        self.out_dir = ""
        self.fish = cFi.Fish()
        self.fish_applied = {}

        self.l_prompt = tk.Label(self, text="Select Condition and Aquatic Ambiance")
        self.l_prompt.grid(sticky=tk.W, row=2, column=0, columnspan=3, padx=self.xd, pady=self.yd)

        # select condition
        self.l_condition = tk.Label(self, text="Condition: \n")
        self.l_condition.grid(sticky=tk.W, row=3, column=0, columnspan=3, padx=self.xd, pady=self.yd)
        self.b_v_condition = tk.Button(self, text="Select",
                                       command=lambda: self.select_condition())
        self.b_v_condition.grid(sticky=tk.W, row=3, column=5, padx=self.xd, pady=self.yd)
        self.sb_condition = tk.Scrollbar(self, orient=tk.VERTICAL)
        self.sb_condition.grid(sticky=tk.W, row=3, column=4, padx=0, pady=self.yd)
        self.lb_condition = tk.Listbox(self, height=3, width=14, yscrollcommand=self.sb_condition.set)
        for e in self.condition_list:
            self.lb_condition.insert(tk.END, e)
        self.lb_condition.grid(sticky=tk.W, row=3, column=3, padx=self.xd, pady=self.yd)
        self.sb_condition.config(command=self.lb_condition.yview)

        self.l_inpath_curr = tk.Label(self, fg="red", text="No Condition Selected")
        self.l_inpath_curr.grid(sticky=tk.W, row=4, column=0, columnspan=6, padx=0, pady=self.yd)

        self.l_aqua = tk.Label(self, fg="red", text="Select Aquatic Ambiance (at least one)")
        self.l_aqua.grid(row=5, column=0, columnspan=6)

        # run analysis
        self.b_connect = tk.Button(self, text="Run Analysis",
                                   command=lambda: self.run_connectivity())
        self.b_connect.grid(sticky=tk.W, row=6, column=0, columnspan=3, padx=self.xd, pady=self.yd)

        self.complete_menus()

    def run_connectivity(self):
        for species in self.fish_applied.keys():
            for lifestage in self.fish_applied[species]:
                ca = cCA.ConnectivityAnalysis(self.condition, species, lifestage, self.unit) # *** add out dir arg

    def select_condition(self):
        items = self.lb_condition.curselection()
        self.condition = [self.condition_list[int(item)] for item in items][0]
        self.dir_input_ras = self.dir2ra + "01_Conditions\\" + self.condition + "\\"
        self.out_dir = self.dir2co + "Output\\" + self.condition + "\\"
        fGl.chk_dir(self.out_dir)

        if os.path.exists(self.dir_input_ras):
            self.l_inpath_curr.config(fg="forest green", text="Selected: " + str(self.dir_input_ras))
        else:
            self.l_inpath_curr.config(fg="red", text="SELECTION ERROR                                 ")

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


    def complete_menus(self):
        # FISH SPECIES DROP DOWN
        self.fishmenu = tk.Menu(self.mbar, tearoff=0)  # create new menu
        self.mbar.add_cascade(label="Select Aquatic Ambiance", menu=self.fishmenu)  # attach it to the menubar
        self.fishmenu.add_command(label="DEFINE FISH SPECIES", command=lambda: self.fish.edit_xlsx())
        self.fishmenu.add_command(label="RE-BUILD MENU", command=lambda: self.make_fish_menu(rebuild=True))
        self.fishmenu.add_command(label="_____________________________")
        self.fishmenu.add_command(label="ALL", command=lambda: self.set_fish("all"))
        self.fishmenu.add_command(label="CLEAR ALL", command=lambda: self.set_fish("clear"))
        self.fishmenu.add_command(label="_____________________________")
        self.make_fish_menu(rebuild=False)

    def select_boundary_shp(self):
        self.bound_shp = askopenfilename(initialdir=os.path.abspath(os.path.join(os.path.dirname(__file__), '..')) + "\\01_Conditions\\",
                                         title="Select boundary shapefile containing a rectangular polygon",
                                         filetypes=[("Shapefiles", "*.shp")])

    def shout_dict(self, the_dict):
        msg = "Selected:"
        for k in the_dict.keys():
            msg = msg + "\n\n > " + str(k) + " entries:\n   -- " + "\n   -- ".join(the_dict[k])
        showinfo("INFO", msg)

    def __call__(self):
        self.mainloop()


# enable script to run stand-alone
if __name__ == "__main__":
    MainGui().mainloop()
