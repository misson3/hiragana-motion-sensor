# Mar05, 2023, ms
# model-tester-CNN-3.py

# BREAK_TOLERANCE is created as in serialRecorder-touch-robust2.py

import serial
import sys
import numpy as np
from scipy.interpolate import interp1d
import tensorflow as tf
import pickle


#
# functions
#

# interporate data
def interporateAxisData(ax, x_points):
    """
    ax: ndarray, values from single axis
    x_points: points to interporate
    """
    # squeeze original x range into (1 to x_points)
    ori_x_scaled = np.array([(x_points/len(ax)) * i
                                            for i in range(1, len(ax)+1)])
    # linear range 1, 2,,, x_points
    new_x = np.array([i for i in range(1, x_points+1)])
    # interporate function
    myfunc = interp1d(ori_x_scaled, ax, fill_value="extrapolate")
    # return interporated ax values
    return myfunc(new_x)


def interporateData(reads, x_points):
    """
    """
    read_count = len(reads)  # eq. to csv count
    # axis count.  get it from the first read
    ax_count = reads[0].shape[1]

    # prepare a bucket with the same sape of reads and
    # override this with interporated data axis by axis
    reads_bucket = []

    for read_idx in range(read_count):
        temp_read = np.zeros((x_points, ax_count))
        for ax_idx in range(ax_count):
            temp_read[:, ax_idx] = interporateAxisData(
                                        reads[read_idx][:, ax_idx], x_points
                                        )
        reads_bucket.append(temp_read)

    return reads_bucket


# normalize axes values with their max and min (to make value range from 0 to 1)
def normalizeMinMax(array_x):
    """
    min max normalization
    values will be packed into 0 to 1
    """
    return (array_x - array_x.min()) / (array_x.max() - array_x.min())



def normalizeData(reads):
    """
    this is used for interporated reads in which read shape is the same for
    all reads in given reads
    """
    read_count = len(reads)  # eq. to csv count
    # get the read shape from the first read
    x_points, ax_count = reads[0].shape

    # as done in another func, prepare a bucket with the same sape of reads and
    # override this with interporated data axis by axis
    reads_bucket = []

    for read_idx in range(read_count):
        temp_read = np.zeros((x_points, ax_count))
        for ax_idx in range(ax_count):
            temp_read[:, ax_idx] = normalizeMinMax(
                    reads[read_idx][:, ax_idx]
                    )
        reads_bucket.append(temp_read)

    return reads_bucket


#
# main story
#

# load files from training
model = tf.keras.models.load_model(sys.argv[1])
idx2label_pkl = sys.argv[2]
with open(idx2label_pkl, "rb") as PKL:
    idx2label = pickle.load(PKL)

# serial setup. change COM number accordingly
ser = serial.Serial(port='COM4', baudrate=115200)
ser.flushInput()


# main loop
rec = False
axs = []
ays = []
azs = []
gxs = []
gys = []
gzs = []

breaking_count = 0
BREAK_TOLERANCE = 5

while True:
    ser_bytes = ser.readline()
    decoded_bytes = ser_bytes[0:len(ser_bytes)-2].decode("utf-8")
    #print(decoded_bytes)
    ax, ay, az, gx, gy, gz = [float(v) for v in
                                decoded_bytes.split(',')[:-2]]
    # A1: orange, A3: black touch
    A1, A3 = [int(v) for v in decoded_bytes.split(',')[-2:]]

    # record on off
    if (not rec) and (A1 >= 800):  # START RECORDING
        rec = True
        axs = []
        ays = []
        azs = []
        gxs = []
        gys = []
        gzs = []
        continue

    if rec and (A1 < 800):  # STOP RECORDING
        breaking_count += 1
        if breaking_count > BREAK_TOLERANCE:
            rec = False
            # forward collected data to classification
            print('CHECK len() collected:', len(axs))
            print('value check (axs):', axs)
            # make (datapoints, 6) ndarray
            a_read = np.vstack((axs, ays, azs, gxs, gys, gzs)).transpose()
            print('a_read.shape', a_read.shape)

            # interporate
            data_points = 30
            reads_itp = interporateData([a_read], data_points)
            print('a_read_itp.shape', reads_itp[0].shape)

            # normalize with min-max
            # grand min max from training or, max min in this read
            reads_itp_norm = normalizeData(reads_itp)
            print('a_read_itp_norm.shape', reads_itp_norm[0].shape)

            # reshape for cnn
            # it should be (1, 30=datapoints, 6=ax_count, 1)
            # prepare zero bucket
            sensor_axes = 6
            reads_cnn = np.zeros((1, data_points, sensor_axes, 1))
            reads_cnn[0, :, :, 0] = reads_itp_norm[0]

            pred = model.predict(reads_cnn)
            print("max =", pred.max())
            print('it is "' + idx2label[pred.argmax()] + '"')
            print()

            breaking_count = 0
        continue

    # exit program
    if A3 > 800:  # EXIT WHILE LOOP to TERMINATE PROGRAM
        break

    # write to a file
    if rec:
        axs.append(ax)
        ays.append(ay)
        azs.append(az)
        gxs.append(gx)
        gys.append(gy)
        gzs.append(gz)
        #print(x, y, z)

print("program terminated.")
