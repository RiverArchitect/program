import os
# sys.path.append(os.getcwd() + "\\.openpyxl\\")
import openpyxl as oxl
# wbn = "D:\\Python\\StreamRestoration\\ModifyTerrain\\Output\\Spreadsheets\\volumes_template_save_copy.xlsx"
def myprin(a=str(), b=float()):
    print("a={0}, b={1}".format(a, str(b)))

options = {0: lambda a, b: myprin(a,b),
           2: lambda: myprin(b=3)}

myl = ["3", 4]
myprin(print(myl))
