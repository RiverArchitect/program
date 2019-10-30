import os, sys
try:
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')) + "\\.site_packages\\riverpy\\")
    import config
    import fGlobal as fGl
except:
    print("ExceptionERROR: Cannot find riverpy.")
import logging

def main():
    # VARIABLES - MAKE CHANGES HERE
    prefix_org = "d"
    prefix_new = "h"
    suffix_org = "_suffx"
    suffix_new = ""
    file_type = ".tif"
    condition_name = "2017"
    

    # CALCULUS - DO NOT CHANGE ANYTHING HERE (unless your know what you are doing)
    dir2c = os.path.abspath(os.path.join(os.path.dirname(__file__), '..')) + "\\01_Conditions\\" + condition_name + "\\"
    all_files = fGl.file_names_in_dir(dir2c)
    for _f in all_files:
        if str(_f).endswith(suffix_org + file_type) and str(_f).startswith(prefix_org):
            new_f_name = prefix_new + str(_f).split(prefix_org)[-1].split(suffix_org)[0] + suffix_new + file_type
            try:
                print("Renaming {0} to {1}".format(str(_f), new_f_name))
                os.rename(dir2c + _f, dir2c + new_f_name)
            except:
                print("ERROR: Renaming failed.")
    

if __name__ == "__main__":
    main()
