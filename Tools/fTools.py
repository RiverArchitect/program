#!/usr/bin/python
try:
    import os, logging, sys
    import datetime as dt
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))  # add this folder to the system path
except:
    print("ExceptionERROR: Missing fundamental packages (required: os, sys, logging).")


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


def chk_folder_structure(foldername):
    ScriptDir = os.path.dirname(os.path.abspath(__file__))  # get base working directory of script
    if not (os.path.exists(ScriptDir+'\\'+foldername)):
            os.mkdir(ScriptDir+'\\'+foldername)


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


def initialize_logger(output_dir, app_name):
    logger = logging.getLogger(app_name)
    logger.setLevel(logging.DEBUG)

    # create console handler and set level to info
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter("%(asctime)s - %(levelname)s: %(message)s")
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    # create error file handler and set level to error
    err_handler = logging.FileHandler(os.path.join(output_dir, "error.log"), "w", encoding=None, delay="true")
    err_handler.setLevel(logging.ERROR)
    err_formatter = logging.Formatter("%(asctime)s - %(levelname)s: %(message)s")
    err_handler.setFormatter(err_formatter)
    logger.addHandler(err_handler)

    # create debug file handler and set level to debug
    debug_handler = logging.FileHandler(os.path.join(output_dir, "logfile.log"), "w")
    debug_handler.setLevel(logging.DEBUG)
    debug_formatter = logging.Formatter("%(asctime)s - %(message)s")
    debug_handler.setFormatter(debug_formatter)
    logger.addHandler(debug_handler)

    logger.info("Logger initiated")
    return logger


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
        # subprocess.open(r'explorer /select,"C:\path\of\folder\file"')
    except:
        pass


def get_subdir_names(directory):
    subdir_list = [name for name in os.listdir(directory) if os.path.isdir(os.path.join(directory, name))]
    return subdir_list


def read_csv(file_name, header, column, *is_str):
    # returns numeric data of a comma delimited text file
    # INPUT:  file = full path of text (or csv) file
    #         header = BOOL (True or False) causes first line skipp
    #         column = column number
    #         is_str = BOOL, if True -> cells are read as string
    # OUTPUT: data = LIST: [[col0_row0, col1_row0, ...], [col0_row1, col1_row1, ...], ...]

    try:
        is_str = is_str[0]
    except:
        is_str = False

    print(" >> Reading " + str(file_name))
    data = []
    if os.path.isfile(file_name):
        file_name = open(file_name)
        lines = file_name.readlines()

        if header:
            lines = lines[1:]  # remove header if True
        for line in lines:
            try:
                line = str(line).split(",")
                e = line[column]
                try:
                    if not is_str:
                        data.append(float(e))
                    else:
                        data.append(str(e))
                except:
                    try:
                        data.append(dt.datetime.strptime(e, '%m/%d/%Y'))
                    except ValueError:
                        data.append(e)
            except:
                print("    !! could not read line " + str(line) + ".")
        file_name.close()
        print("     --> File read finished.")
    else:
        print("ERROR: File not found.")
    return data


def rindex(iterable, value):
    try:
        return len(iterable) - next(i for i, val in enumerate(reversed(iterable)) if val == value) - 1
    except StopIteration:
        raise ValueError


def rm_dir(directory):
    # Delete everything reachable from the directory named in 'directory', and the directory itself
    # assuming there are no symbolic links.
    # CAUTION:  This is dangerous!  For example, if directory == '/', it
    # could delete all your disk files.
    for root, dirs, files in os.walk(directory, topdown=False):
        for name in files:
            os.remove(os.path.join(root, name))
        for name in dirs:
            os.rmdir(os.path.join(root, name))
    os.rmdir(directory)


def rm_file(directory):
    # Delete everything reachable from the directory named in 'directory', and the directory itself
    # assuming there are no symbolic links.
    # CAUTION:  This is dangerous!  For example, if directory == '/', it
    # could delete all your disk files.
    for root, dirs, files in os.walk(directory, topdown=False):
        for name in files:
            os.remove(os.path.join(root, name))
        for name in dirs:
            os.rmdir(os.path.join(root, name))
    os.rmdir(directory)


def stop_logging(logger):
    # stop logging and release logfile
    for handler in logger.handlers:
        handler.close()
        logger.removeHandler(handler)


def str2frac(arg):
    arg = arg.split('/')
    return(int(arg[0])/int(arg[1]))


def str2num(arg,SEP):
    # function converts string of type 'X[SEP]Y' to number
    # SEP is either ',' or '.'
    # e.g. '2,30' is converted with SEP = ',' to 2.3
    _num = arg.split(SEP)
    _a = int(_num[0])
    _b = int(_num[1])
    _num = _a+_b*10**(-1*len(str(_b)))
    return(_num)


def str2tuple(arg):
    try:
        arg = arg.split(',')
    except ValueError:
        print('ERROR: Bad assignment of separator.\nSeparator must be [,].')
    tup = (int(arg[0]),int(arg[1]))
    return(tup)


def tuple2num(arg):
    # function converts float number with ',' separator for digits to '.' separator
    # type(arg) = tuple with two entries, e.g. (2,40)
    # call: tuple2num((2,3))
    new =  arg[0]+arg[1]*10**(-1*len(str(arg[1])))
    return(new)


def write_data(folderDir, fileName, data):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    if not os.path.exists(folderDir):
            os.mkdir(folderDir)
    os.chdir(folderDir)

    f = open(fileName+'.csv', 'w')
    for i in data:
         line = str(i)+'\n'
         f.write(line)
    os.chdir(script_dir)
    print('Data written to: \n'+folderDir+'\\'+str(fileName)+'.csv')

