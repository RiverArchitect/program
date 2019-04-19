try:
    import os, sys
    import Tkinter as tk
    from tkinter import ttk
    from tkFileDialog import *  # in python3 use tkinter.filedialog instead
    from tkMessageBox import askokcancel, showinfo
    import webbrowser
except:
    print("ERROR: Missing fundamental packages (required: os, sys, Tkinter, webbrowser).")
try:
    import ProjectMaker
except:
    print("ERROR: Could not import ProjectMaker.")
try:
    import LifespanDesign
except:
    print("ERROR: Could not import LifespanDesign.")
try:
    import MaxLifespan
except:
    print("ERROR: Could not import MaxLifespan.")
try:
    import ModifyTerrain
except:
    print("ERROR: Could not import ModifyTerrain.")
try:
    import HabitatEvaluation
except:
    print("ERROR: Could not import HabitatEvaluation.")


class RA_GUI(tk.Frame):
    # master GUI for all RiverArchitect modules
    def __init__(self, master=None):
        tk.Frame.__init__(self, master)
        self.pack()

        self.master.title("River Architect")
        self.master.iconbitmap(os.path.dirname(os.path.abspath(__file__)) + "\\MaxLifespan\\.templates\\code_icon.ico")

        self.tab_container = ttk.Notebook(master)

        self.tab_names = ['Lifespan Design',
                          'Max Lifespan',
                          'Modify Terrain',
                          'Habitat Evaluation',
                          'Project Maker']

        # working directory suffixes for each module
        self.tab_dir_names = ['\\LifespanDesign\\',
                              '\\MaxLifespan\\',
                              '\\ModifyTerrain\\',
                              '\\HabitatEvaluation\\',
                              '\\ProjectMaker\\']

        # Frames initialized by module, with parent being tab container
        self.tab_list = [LifespanDesign.lifespan_design_gui.FaGui(self.tab_container),
                         MaxLifespan.action_gui.ActionGui(self.tab_container),
                         ModifyTerrain.modify_terrain_gui.MainGui(self.tab_container),
                         HabitatEvaluation.habitat_gui.MainGui(self.tab_container),
                         ProjectMaker.project_maker_gui.MainGui(self.tab_container)
                         ]

        self.tab_dirs = dict(zip(self.tab_names, self.tab_dir_names))
        self.tabs = dict(zip(self.tab_names, self.tab_list))

        for tab_name in self.tab_names:
            tab = self. tabs[tab_name]
            tab.bind('<Visibility>', self.tab_select)
            self.tab_container.add(tab, text=tab_name)
            self.tab_container.pack(expand=1, fill="both")

    def tab_select(self, event):
        selected_tab_name = self.tab_container.tab(self.tab_container.select(), 'text')
        selected_tab = self.tabs[selected_tab_name]
        os.chdir(os.path.dirname(os.path.abspath(__file__)) + self.tab_dirs[selected_tab_name])
        selected_tab.set_geometry()
        selected_tab.make_menu()

if __name__ == '__main__':
    RA_GUI().mainloop()
