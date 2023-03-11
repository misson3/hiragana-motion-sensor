# Feb25, 27, 2023, ms
# serialRecorder-touch-robust2.py

# feature added
# print line count in the file when
# ... created is printed

"""
1. Connect QtPy---LSM6DSOX (Arduino) to USB
              └--cap touch A1:recording, A3:exit
2. run this code giving a prefix string in the second arg

start recording when A1 cap touch value is >= 800
exit program when A3 cap touch value is >= 800

                   < acc >  < gyr >
values in serial = x, y, z, x, y, z, A1,A3

touch and hold A1 to record
touch A3 to exit while loop (terminate program)

robust version
allow short break on A1 value
arduino side is sending values in every 30 ms
give rec = False after 5 consecutive value < 800
"""

import serial
import time
import csv
import sys

prefix = sys.argv[1]

# change COM number accordingly
ser = serial.Serial(port='COM4', baudrate=115200)
ser.flushInput()

rec = False
file_num = 0
breaking_count = 0
line_count = 0
BREAK_TOLERANCE = 5
while True:
    ser_bytes = ser.readline()
    decoded_bytes = ser_bytes[0:len(ser_bytes)-2].decode("utf-8")
    # print(decoded_bytes)
    acc_gyr = [float(v) for v in decoded_bytes.split(',')[:-2]]
    A1, A3 = [int(v) for v in decoded_bytes.split(',')[-2:]]
    #print(acc_gyr, A1, A3)

    # record on off
    if (not rec) and (A1 >= 800):
        rec = True
        # prepare output file name
        file_num += 1
        out_file = prefix + '-' + str(file_num).zfill(3) + '.csv'
        #print(out_file)
    if rec and (A1 < 800):
        breaking_count += 1
        if breaking_count > BREAK_TOLERANCE:
            rec = False
            breaking_count = 0
            print()
            print(acc_gyr)
            print('Lines saved:', line_count)
            print(out_file, "created.")
            # reset line_count
            line_count = 0
    # exit program
    if A3 > 800:
        break

    # write to a file
    if rec:
        with open(out_file, "a", newline='') as OUT:
            writer = csv.writer(
                OUT, delimiter=",", quoting=csv.QUOTE_NONNUMERIC
                )
            writer.writerow([time.time()] + acc_gyr + [A1, A3])
            # line count
            line_count += 1

print("program terminated.")
print(file_num, "files were created.")
