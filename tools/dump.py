#
# Edirol/Roland PCR-800 control map sysex research
# Dump a comparative analysis of sysex messages
#
#


import os


# Directory containing files to be compared to base
SYSEX_DIR_2 = "/Volumes/Z77ExtremeDataSSD/dhocker/Documents/PCR800/map4"
# Initial set of sysex files
SYSEX_DIR_1 = "/Volumes/Z77ExtremeDataSSD/dhocker/Documents/PCR800/map4-base"


def check_sum(sx_data):
    """
    Compute checksum over bytes 7-138 of the sysex
    :param sx_data: control map sysex data (141 bytes)
    :return:
    """
    s = 0
    for i in range(7, 139):
        s += sx_data[i]
        s = s % 128
    return 128 - s


def diff_sysex(sysex_base, sx_data):
    new_line = False
    match = True
    for i in range(1, 138):
        if sysex_base[i] != sx_data[i]:
            print(i, "{0}:{1}".format(sysex_base[i], sx_data[i]), " ", end="")
            match = False
            new_line = True

    if new_line:
        print()
    return match


def find_value(sx_data, value):
    found = False
    for i in range(1, 138):
        if sx_data[i] == value:
            print(i, "value {0}".format(value), " ", end="")
            found = True
    if found:
        print()
    return found


def main_1():
    """
    Look for differences between files
    :return:
    """
    files = os.scandir(SYSEX_DIR_1)
    nfiles = 0
    sysex_base = None
    found = False
    print("ID[9], 22, csumb[139], csum_calc")
    for f in files:
        print(f.name)
        fn = SYSEX_DIR_1 + "/" + f.name
        fh = open(fn, "rb")
        sx_data = fh.read()
        b = sx_data[9] # controller ID?
        c = sx_data[22]
        csumb = sx_data[139]
        csum_calc = check_sum(sx_data)

        if sysex_base is None:
            sysex_base = sx_data
        else:
            diff_sysex(sysex_base, sx_data)
            found |= find_value(sx_data, 55)

        # print(b, c, csumb, csum_calc)
        nfiles += 1
    print("{0} files found".format(nfiles))

    if not found:
        print("Value was not found")


def main_2():
    """
    Determine ID scheme (C1 and C2 changed)
    :return:
    """
    files_1 = os.scandir(SYSEX_DIR_1)
    files_2 = os.scandir(SYSEX_DIR_2)
    sysex_base = None
    found = False

    # Build list of files to be compared
    flist_1 = []
    flist_2 = []
    for f in files_1:
        if f.name.endswith(".syx"):
            flist_1.append(SYSEX_DIR_1 + "/" + f.name)
    files_1.close()
    for f in files_2:
        if f.name.endswith(".syx"):
            flist_2.append(SYSEX_DIR_2 + "/" + f.name)
    files_2.close()

    if len(flist_1) != len(flist_2):
        print("Wrong number of files:", len(flist_1), len(flist_2))
        return

    print("ID[9], csumb[139]")
    for i in range(len(flist_1)):
        fh_1 = open(flist_1[i], "rb")
        fh_2 = open(flist_2[i], "rb")
        sx_data_1 = fh_1.read()
        sx_data_2 = fh_2.read()

        if sx_data_1[139] != sx_data_2[139]:
            print("Mismatch checksum")
            print(flist_1[i])
            print(flist_2[i])
            print("ID", sx_data_1[9], sx_data_2[9]) # controller ID?

        if not diff_sysex(sx_data_1, sx_data_2):
            print("Diff file", i + 1)
            print(flist_1[i])
            print(flist_2[i])
            print("ID", sx_data_1[9], sx_data_2[9]) # controller ID?
            print()

        fh_1.close()
        fh_2.close()


if __name__ == "__main__":
    # main_1()
    main_2()
