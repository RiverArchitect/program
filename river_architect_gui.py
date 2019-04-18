try:
    import os, sys
    import Tkinter as tk
    from tkFileDialog import * # in python3 use tkinter.filedialog instead
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


class FaGui(tk.Frame):
    def __init__(self, master = None):
        # Construct the Frame object.
        tk.Frame.__init__(self, master)
        self.pack(expand=True, fill=tk.BOTH)
        self.master.iconbitmap(os.path.dirname(os.path.abspath(__file__)) + "\\MaxLifespan\\.templates\\code_icon.ico")

        self.xd = 15  # distance holder in x-direction (pixel)
        self.yd = 15  # distance holder in y-direction (pixel)
        # ARRANGE GEOMETRY
        # Width and height of the window.
        ww = 320
        wh = 400
        # Upper-left corner of the window.
        wx = (self.master.winfo_screenwidth() - ww) / 2
        wy = (self.master.winfo_screenheight() - wh) / 2
        # Set the height and location.
        self.master.geometry("%dx%d+%d+%d" % (ww, wh, wx, wy))
        # Give the window a title.
        self.master.title("River Architect")

        # LABELS
        self.l_welcome = tk.Label(self, fg="forest green", text="Welcome to the River Architect stream design tool kit.\n\nClick to start a module.")
        self.l_welcome.grid(sticky=tk.EW, row=0, column=0, rowspan=2, columnspan=2, padx=self.xd, pady=self.yd)
        self.l_hint = tk.Label(self, fg="gray45", text="The Tools console scripts require individual launches.")
        self.l_hint.grid(sticky=tk.EW, row=7, column=0, rowspan=2, columnspan=2, padx=self.xd, pady=self.yd)

        # BUTTONS
        self.b_lf = tk.Button(self, width=25, bg="white", text="Start Lifespan and Design module",
                              command=lambda: self.start_lf())
        self.b_lf.grid(sticky=tk.EW, row=2, column=0, columnspan=2, padx=self.xd, pady=self.yd)

        self.b_ap = tk.Button(self, width=25, bg="white", text="Start Maximum Lifespan module",
                              command=lambda: self.start_ap())
        self.b_ap.grid(sticky=tk.EW, row=3, column=0, columnspan=2, padx=self.xd, pady=self.yd)

        self.b_mt = tk.Button(self, width=25, bg="white", text="Start Modify Terrain module",
                              command=lambda: self.start_mt())
        self.b_mt.grid(sticky=tk.EW, row=4, column=0, columnspan=2, padx=self.xd, pady=self.yd)

        self.b_he = tk.Button(self, width=25, bg="white", text="Start Habitat Evaluation module",
                              command=lambda: self.start_he())
        self.b_he.grid(sticky=tk.EW, row=5, column=0, columnspan=2, padx=self.xd, pady=self.yd)

        self.b_he = tk.Button(self, width=25, bg="white", text="Start Project Maker module",
                              command=lambda: self.start_pm())
        self.b_he.grid(sticky=tk.EW, row=6, column=0, columnspan=2, padx=self.xd, pady=self.yd)

    def myquit(self):
        tk.Frame.quit(self)

    def start_lf(self):        
        self.master.destroy()
        os.chdir(os.path.dirname(os.path.abspath(__file__)) + "\\LifespanDesign\\")    
        LifespanDesign.lifespan_design_gui.FaGui()

    def start_ap(self):
        self.master.destroy()
        os.chdir(os.path.dirname(os.path.abspath(__file__)) + "\\MaxLifespan\\")   
        MaxLifespan.action_gui.ActionGui()


    def start_mt(self):
        self.master.destroy()
        os.chdir(os.path.dirname(os.path.abspath(__file__)) + "\\ModifyTerrain\\")
        ModifyTerrain.modify_terrain_gui.MainGui()


    def start_he(self):
        self.master.destroy()
        os.chdir(os.path.dirname(os.path.abspath(__file__)) + "\\HabitatEvaluation\\")
        HabitatEvaluation.habitat_gui.MainGui()

    def start_pm(self):
        self.master.destroy()
        os.chdir(os.path.dirname(os.path.abspath(__file__)) + "\\ProjectMaker\\")
        ProjectMaker.project_maker_gui.MainGui()


# enable script to run stand-alone.
if __name__ == "__main__":
    FaGui().mainloop()
