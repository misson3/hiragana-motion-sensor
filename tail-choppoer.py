# Mar05, 2023, ms
# tail-chopper.py

# saved files from serialRecorder-touch-robust2.py contains
# 3-5 lines after the pen is detached from the pad.
# this is because a short break is neglected (up to 5 in current setting,
# see BREAK_TOLERANCE var)

# This is a code to chop off those last lines after the pen is released.

# to do
# - create a file name based on the input file name

import sys
import csv
import os
import glob


def createOutFileName(file_path, post_fix):
    stem = os.path.splitext(os.path.basename(file_path))[0]
    return stem + post_fix + '.csv'


def main_story(input_dir):
    for csvf in glob.glob(os.path.normpath(os.path.join(input_dir, '*.csv'))):
        with open(csvf, mode='r') as CSV:
            rows = csv.reader(CSV, delimiter=',')
            keeps = []
            temp = []
            for row in rows:
                # A1 read is in column 8. >= 800 is considered touching
                # in serialRecorder-touch-robust2.py
                if int(row[7]) >= 800:
                    if len(temp) == 0:  # temp is empty
                        keeps.append(row)
                    else:
                        # temp is not empty.  Add this row to temp and
                        # dump the temp to keeps.
                        # do not forget to empty temp.
                        temp.append(row)
                        keeps.extend(temp)
                        temp = []
                else:
                    temp.append(row)
            # write rows in keeps to an out file
            out_file = createOutFileName(csvf, "-no-tail")
            with open(out_file, "w", newline='') as OUT:
                writer = csv.writer(
                    OUT, delimiter=",", quoting=csv.QUOTE_NONE
                )
                for row in keeps:
                    writer.writerow(row)


if __name__ == '__main__':
    input_dir = sys.argv[1]
    main_story(input_dir)
