try:
    import os, sys
    import tkinter as tk
    from tkinter.messagebox import askokcancel, showinfo
    from tkinter.filedialog import *
    import webbrowser
except:
    print("ExceptionERROR: Missing fundamental packages (required: os, sys, tkinter, webbrowser).")

try:
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')) + "\\.site_packages\\riverpy\\")
    import fGlobal as fg
except:
    print("ExceptionERROR: Cannot find package files (RP/fGlobal.py).")


class MainGui(tk.Frame):
    def __init__(self, master=None):

        self.path = r"" + os.path.dirname(os.path.abspath(__file__))
        self.path_lvl_up = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

        # Construct the Frame object
        tk.Frame.__init__(self, master)
        # if imported from master GUI, redefine master as highest level (ttk.Notebook tab container)
        if __name__ != '__main__':
            self.master = self.master.master
        self.pack(expand=True, fill=tk.BOTH)
        self.set_geometry()

        # GUI OBJECT VARIABLES
        self.gui_condition = tk.StringVar()
        self.gui_interpreter = tk.StringVar()
        self.extent_type = tk.StringVar()

        # BUTTONS
        self.b_create_c = tk.Button(self, width=30, bg="white", text="Create New Condition", command=lambda: self.create_c())
        self.b_create_c.grid(sticky=tk.EW, row=0, column=0, columnspan=2, padx=self.xd, pady=self.yd*2)

        self.b_populate_c = tk.Button(self, width=30, bg="white", text="Populate Condition",
                                      command=lambda: self.populate_c())
        self.b_populate_c.grid(sticky=tk.EW, row=1, column=0, columnspan=2, padx=self.xd, pady=self.yd * 2)

        self.b_create_sub_c = tk.Button(self, width=30, bg="white", text="Create a spatial subset of a Condition",
                                        command=lambda: self.create_c_sub())
        self.b_create_sub_c.grid(sticky=tk.EW, row=2, column=0, columnspan=2, padx=self.xd, pady=self.yd*2)

        # self.b_create_Q = tk.Button(self, width=30, bg="white", text="Generate Discharge Tables", command=lambda: self.create_Q())
        # self.b_create_Q.grid(sticky=tk.EW, row=3, column=0, columnspan=2, padx=self.xd, pady=self.yd)

        self.make_menu()

        # MAKE PLACEHOLDER FILL
        logo = tk.PhotoImage(file=os.path.dirname(os.path.abspath(__file__))+"\\.templates\\welcome.gif")
        logo = logo.subsample(6, 6)
        self.l_img = tk.Label(self, image=logo)
        self.l_img.image = logo
        self.l_img.grid(sticky=tk.E, row=3, column=2, rowspan=7, columnspan=2, padx=self.xd*10, pady=self.yd)

        # Add credits
        self.l_credits = tk.Label(self, fg="gray50", text=fg.get_credits(), justify=LEFT)
        self.l_credits.grid(sticky=tk.E, row=8, column=0, rowspan=3, columnspan=2, padx=self.xd, pady=self.yd)

    def set_geometry(self):
        # ARRANGE GEOMETRY
        # width and height of the window.
        self.ww = 700
        self.wh = 490
        self.xd = 5  # distance holder in x-direction (pixel)
        self.yd = 5  # distance holder in y-direction (pixel)
        # height and location
        self.wx = (self.master.winfo_screenwidth() - self.ww) / 2
        self.wy = (self.master.winfo_screenheight() - self.wh) / 2
        self.master.geometry("%dx%d+%d+%d" % (self.ww, self.wh, self.wx, self.wy))
        if __name__ == '__main__':
            self.master.title("Lifespan Design")  # window title
            self.master.iconbitmap(self.path_lvl_up + "\\.site_packages\\templates\\code_icon.ico")

    def make_menu(self):
        # DROP DOWN MENU
        # menu does not need packing - see tkinter manual page 44ff
        self.mbar = tk.Menu(self.master)  # create new menubar
        self.master.config(menu=self.mbar)  # attach it to the root window

        # CLOSE DROP DOWN
        self.closemenu = tk.Menu(self.mbar, tearoff=0)  # create new menu
        self.mbar.add_cascade(label="Close", menu=self.closemenu)  # attach it to the menubar
        self.closemenu.add_command(label="Credits", command=lambda: self.show_credits())
        self.closemenu.add_command(label="Quit program", command=lambda: self.myquit())

    def create_c(self):
        try:
            import popup_create_c as pcc
        except:
            showinfo("Oups ...", "Cannot find condition creation routines -  check RA installation.")
            return -1
        new_window = pcc.CreateCondition(self.master)
        self.b_create_c["state"] = "disabled"
        self.master.wait_window(new_window.top)
        self.b_create_c["state"] = "normal"

    def create_c_sub(self):
        try:
            import popup_create_c_sub as pccs
        except:
            showinfo("Oups ...", "Cannot find sub-condition creation routines -  check RA installation.")
            return -1
        new_window = pccs.CreateSubCondition(self.master)
        self.b_create_sub_c["state"] = "disabled"
        self.master.wait_window(new_window.top)
        self.b_create_sub_c["state"] = "normal"

    def create_Q(self):
        pass

    def populate_c(self):
        try:
            import popup_populate_c as ppc
        except:
            showinfo("Oups ...", "Cannot find condition population routines -  check RA installation.")
            return -1
        new_window = ppc.PopulateCondition(self.master)
        self.b_populate_c["state"] = "disabled"
        self.master.wait_window(new_window.top)
        self.b_populate_c["state"] = "normal"

    def myquit(self):
        if askokcancel("Close", "Do you really wish to quit?"):
            tk.Frame.quit(self)

    def show_credits(self):
        showinfo("Credits", fg.get_credits())

    def __call__(self):
        self.mainloop()


# enable script to run stand-alone
if __name__ == "__main__":
    MainGui().mainloop()
