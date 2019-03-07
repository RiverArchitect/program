from __future__ import division
# Filename: fGlobal.py
try:
    import os, logging, sys, glob, webbrowser, time
except:
    print("ExceptionERROR: Missing fundamental packages (required: os, sys, glob, logging, time, webbrowser).")


try:
    import cDefinitions as cdef
except:
    print("ExceptionERROR: Cannot find package files (cDefinitions.py).")


def chk_is_empty(variable):
    try:
        value = float(variable)
    except ValueError:
        value = variable
        pass
    try:
        value = str(variable)
    except ValueError:
        pass
    return bool(value)


def chk_dir(directory):
    if not(os.path.exists(directory)):
            os.makedirs(directory)


def clean_dir(directory):
    # Delete everything reachable IN the directory named in 'directory',
    # assuming there are no symbolic links.
    # CAUTION:  This is dangerous!  For example, if directory == '/', it
    # could delete all your disk files.
    for root, dirs, files in os.walk(directory, topdown=False):
        for name in files:
            os.remove(os.path.join(root, name))
        for name in dirs:
            os.rmdir(os.path.join(root, name))


def cool_down(seconds):
    # Pauses script execution for the input argument number of seconds
    # seconds = INT
    sys.stdout.write('Cooling down (waiting for processes to end) ... ')
    for i in xrange(seconds, 0, -1):
        sys.stdout.write(str(i) + ' ')
        sys.stdout.flush()
        time.sleep(1)
    sys.stdout.write('\n')


def get_newest_output_folder(directory):
    # return that the newest folder in a directory
    lof = glob.glob(directory + "*\\")
    latest_dir = max(lof, key=os.path.getctime)
    return str(latest_dir)


def get_subdir_names(directory):
    subdir_list = [name for name in os.listdir(directory) if os.path.isdir(os.path.join(directory, name))]
    return subdir_list


def initialize_logger(output_dir, app_name):
    logfilenames = ["error.log", "lifespan_design.log", "logfile.log", "mapper.log"]
    for fn in logfilenames:
        fn_full = os.path.join(os.getcwd(), fn)
        if os.path.isfile(fn_full):
            try:
                os.remove(fn_full)
                print("Overwriting old logfiles (" + fn + ").")
            except:
                print("WARNING: Old logfiles are locked.")

    logger = logging.getLogger(app_name)
    logger.setLevel(logging.INFO)

    # create console handler and set level to info
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter("%(asctime)s - %(message)s")
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    # create error file handler and set level to error
    err_handler = logging.FileHandler(os.path.join(output_dir, "error.log"), "w", encoding=None, delay="true")
    err_handler.setLevel(logging.ERROR)
    err_formatter = logging.Formatter("%(asctime)s - %(message)s")
    err_handler.setFormatter(err_formatter)
    logger.addHandler(err_handler)

    # create debug file handler and set level to debug
    debug_handler = logging.FileHandler(os.path.join(output_dir, "logfile.log"), "w")
    debug_handler.setLevel(logging.DEBUG)
    debug_formatter = logging.Formatter("%(asctime)s - %(message)s")
    debug_handler.setFormatter(debug_formatter)
    logger.addHandler(debug_handler)

    return logger


def interpolate_linear(x1, x2, y1, y2, xi):
    # returns linear interpolation yi of xi between two points 1 and 2
    yi = y1 + ((xi - x1) / (x2 - x1) * (y2 - y1))
    return yi


def make_output_dir(condition, reach_ids, habitat_analysis, relevant_feat_names):
    # sets / creates a raster/shp/mxd/pdf output dir as a function of provided condition + feature layer type
    # condition = STR or number (will be converted to str)
    # reach_id = LIST from MT/.templates/computation_extents.xlsx
    # habitat_analysis = BOOL
    # relevant_feat_names = LIST with entries from LD/.templates/threshold_values.xlsx
    features = cdef.Features()
    feat_id_list = []
    [feat_id_list.append(features.name_dict[item]) for item in relevant_feat_names]
    feat_col_list = []
    [feat_col_list.append(features.col_name_dict[item]) for item in relevant_feat_names]
    dir2LD = os.path.abspath(os.path.join(os.path.dirname(__file__), '..\..')) + "\\LifespanDesign\\"

    if reach_ids.__len__() == 1:
        reach_name = "_" + str(reach_ids[0])
    else:
        reach_name = "_all"

    type_int_list = []
    for tt in feat_col_list:
        if tt in features.threshold_cols_framework:
            type_int_list.append(1)
        if tt in features.threshold_cols_plants:
            type_int_list.append(2)
        if tt in features.threshold_cols_toolbox:
            type_int_list.append(2)
        if tt in features.threshold_cols_complement:
            type_int_list.append(3)
    try:
        feat_lyr_type = int(sum(type_int_list)/type_int_list.__len__())
    except:
        feat_lyr_type = 0

    if not habitat_analysis:
        # define output directory as a function of layer type
        if feat_lyr_type > 0:
            for i in range(0, 9):
                test_folder = str(condition)[0:4] + reach_name + "_lyr" + str(feat_lyr_type) + str(i)
                test_dir = dir2LD + "Output\\Rasters\\" + test_folder + "\\"
                if not (os.path.exists(test_dir)):
                    os.makedirs(test_dir)
                    output_dir = test_dir
                    break
                else:
                    files_exist = True  # basic assumption: a raster for the analyzed feature already exists
                    file_count = len(
                        [name for name in os.listdir(test_dir) if os.path.isfile(os.path.join(test_dir, name))])
                    if file_count < 9:
                        output_dir = test_dir
                        break
                    else:
                        file_names = []
                        [file_names.append(fn) for fn in os.listdir(test_dir) if os.path.isfile(os.path.join(test_dir, fn))]
                        for f_id in feat_id_list:
                            for f_n in file_names:
                                if not(f_id in f_n):
                                    files_exist = False  # if any analyzed feature is not yet present, this folder is OK
                                    output_dir = test_dir
                                    break

                        if not files_exist:
                            break
                        if not (i < 9):
                            print("Maximum folder size for this layer reached -- restarting at lyrX0.")
                            print("Consider better file structure; this time, old files are deleted.")
                            test_folder = str(condition)[0:4] + "_lyr" + str(feat_lyr_type) + str(0)
                            output_dir = dir2LD + "Output\\Rasters\\" + test_folder + "\\"
                            break
        else:
            output_dir = dir2LD + "Output\\Rasters\\" + str(condition)[0:4] + reach_name + "lyr00\\"
    else:
        output_dir = dir2LD + "Output\\Rasters\\" + str(condition)[0:4] + reach_name + "_hab\\"

    if not("output_dir" in locals()):
        print("No reach or feature layer or habitat_analysis information.")
        print("--> Output folder name corresponds to input condition.")
        output_dir =dir2LD + "Output\\Rasters\\" + str(condition) + "\\"

    chk_dir(output_dir)

    return output_dir


def open_file(full_file_path):
    _f = full_file_path
    if os.path.isfile(_f):
        try:
            webbrowser.open(_f)
            msg = ""
        except:
            msg = "Cannot open " + str(_f) + ". Ensure that your OS has a defined standard application for relevant file types (e.g., .inp or .xlsx)."
    else:
        msg = "The file \'\n" + str(_f) + "\'\n does not exist. Check action planner directory."
    return msg


def open_folder(directory):
    try:
        import subprocess
        # other python versions than 2.7: import subprocess32
        my_platform = sys.platform
        if my_platform[0:3].lower() == "win":
            # print("Hello Windows!")
            call_target = "explorer " + directory
            subprocess.call(call_target, shell=True)
            print("Found subprocess --> opening target folder.")
        if my_platform[0:3].lower() == "lin":
            # print("Hello Linux!")
            subprocess.check_call(['xdg-open', '--', directory])
            print("Found subprocess --> opening target folder.")
        if my_platform[0:3].lower() == "dar":
            # print("Hello Mac OS!")
            subprocess.check_call(['open', '--', directory])
            print("Found subprocess --> opening target folder.")
            try:
                os.system("start \"\" https://en.wikipedia.org/wiki/Criticism_of_Apple_Inc.")
            except:
                pass

        # Alternative:
        # subprocess.Popen(r'explorer /select,"C:\path\of\folder\file"')
    except:
        pass


def rm_dir(directory):
    # Deletes everything reachable from the directory named in 'directory', and the directory itself
    # assuming there are no symbolic links.
    # CAUTION:  This is dangerous!  For example, if directory == '/' deletes all disk files
    for root, dirs, files in os.walk(directory, topdown=False):
        for name in files:
            os.remove(os.path.join(root, name))
        for name in dirs:
            os.rmdir(os.path.join(root, name))
    os.rmdir(directory)


def rm_file(full_name):
    # fullname = str of directory + file name
    try:
        os.remove(full_name)
    except:
        pass


def rm_raster(full_path):
    # Deletes everything reachable from the rasters full_path
    # full_path = "D:\\example_folder\\example_raster_name"
    locked = False
    try:
        os.remove(full_path + ".aux.xml")
    except:
        locked = True

    try:
        os.remove(full_path + ".ovr")
    except:
        locked = True

    try:
        rm_dir(full_path + "\\")
    except:
        locked = True

    return locked


def str2frac(arg):
    arg = arg.split('/')
    return int(arg[0]) / int(arg[1])


def str2num(arg, sep):
    # function converts string of type 'X[sep]Y' to number
    # sep is either ',' or '.'
    # e.g. '2,30' is converted with SEP = ',' to 2.3
    _num = arg.split(sep)
    _a = int(_num[0])
    _b = int(_num[1])
    _num = _a + _b * 10 ** (-1 * len(str(_b)))
    return _num


def str2tuple(arg):
    try:
        arg = arg.split(',')
    except ValueError:
        print('ERROR: Bad assignment of separator.\nSeparator must be [,].')
    tup = (int(arg[0]), int(arg[1]))
    return tup


def tuple2num(arg):
    # function converts float number with ',' separator for digits to '.' separator
    # type(arg) = tuple with two entries, e.g. (2,40)
    # call: tuple2num((2,3))
    new = arg[0] + arg[1] * 10 ** (-1 * len(str(arg[1])))
    return new


def write_data(folder_dir, file_name, data):
    if not os.path.exists(folder_dir):
            os.mkdir(folder_dir)
    os.chdir(folder_dir)

    f = open(file_name+'.txt', 'w')
    for i in data:
        line = str(i)+'\n'
        f.write(line)
    print('Data written to: \n' + folder_dir + '\\' + str(file_name) + '.csv')

