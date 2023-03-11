# Mar06, 2023, ms
# filter-viewer.py

# ref: TensorFlowとKerasで動かしながら学ぶディープラーニングの仕組み
# chapter 4 のあたり

'''
shows how 6 ax image is 'filtered' by the conv filter(s)

args:
1. tf model (.h5)
2. path to csv dir (put 2 csv files to check in this folder)
'''

import glob
import os
import sys
import numpy as np
import tensorflow as tf
import matplotlib.pyplot as plt
from keras import models
from scipy.interpolate import interp1d


#
# functions
#
def parseTwoCSVs(csv_dir):
    """
    raw csv cols
    0: time stamp
    1-3: acc x, y, z <--- take these and,
    4-6: gyr x, y, z <--- these
    7: A1, touch to read
    8: A3, touch to stop
    """
    reads = []
    labels = []
    count = 0
    for csv in glob.glob(os.path.normpath(os.path.join(csv_dir, '*.csv'))):
        reads.append(np.loadtxt(csv, delimiter=',', usecols=range(1, 7)))
        labels.append(os.path.basename(csv).split('-')[0])
        count += 1
        if count == 2:  # read only 2
            break

    return reads, labels  # list of ndarray and a list


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


def reshapeForCNN(reads_itp_norm):
    datapoints, sensor_axes = reads_itp_norm[0].shape
    # prepare zero bucket
    reads_cnn = np.zeros((len(reads_itp_norm), datapoints, sensor_axes, 1))
    for j in range(len(reads_itp_norm)):
        reads_cnn[j, :, :, 0] = reads_itp_norm[j]

    return reads_cnn


#
# main story
#
def mainStory(model_file, csv_dir):
    #
    # reconstitute saved model and pull the conv_filter
    #
    model = tf.keras.models.load_model(model_file)
    print(model.summary())
    print()

    layer_outputs = [model.get_layer('conv_filter').output]
    model2 = models.Model(inputs=model.input, outputs=layer_outputs)
    filter_vals = model.get_layer('conv_filter').get_weights()[0]
    print(len(filter_vals))

    #
    # read data and make it into a cnn compatible shape
    #
    # read 2 csv
    reads, labels = parseTwoCSVs(csv_dir)
    # interporate data
    reads_itp = interporateData(reads, x_points=30)
    # normalization
    reads_itp_norm = normalizeData(reads_itp)
    # re-shaping for cnn
    reads_cnn = reshapeForCNN(reads_itp_norm)
    print(reads_cnn.shape)
    print()

    # apply the filter to the data
    conv_output = model2.predict(reads_cnn)

    #
    # show images
    #
    num_filters = 4
    fig = plt.figure(figsize=(10, num_filters+1))
    v_max = np.max(conv_output)

    # filters
    for i in range(num_filters):
        subplot = fig.add_subplot(num_filters+1, 6, (i*6)+8)
        subplot.set_xticks([])
        subplot.set_yticks([])
        subplot.imshow(filter_vals[:,:,0,i].T, cmap=plt.cm.gray_r)

    for read_idx in range(len(reads)):
        subplot = fig.add_subplot(num_filters+1, 3, read_idx+2)
        subplot.set_xticks([])
        subplot.set_yticks([])
        subplot.set_title(labels[read_idx])
        subplot.imshow(reads_cnn[read_idx, :, :, 0].T, cmap='gray')
        #subplot.imshow(test_images[i].reshape((28,28)),
        #            vmin=0, vmax=1, cmap=plt.cm.gray_r)

        for f in range(num_filters):
            subplot = fig.add_subplot(num_filters+1, 3, (f*3)+5+read_idx)
            subplot.set_xticks([])
            subplot.set_yticks([])
            subplot.imshow(conv_output[read_idx,:,:,f].T,
                        vmin=0, vmax=v_max, cmap=plt.cm.gray_r)

    out_file = 'filtered-6axes-' + '-'.join(labels) + '.png'
    plt.savefig(out_file)
    plt.show()





if __name__ == '__main__':
    model = sys.argv[1]
    csv_dir = sys.argv[2]
    mainStory(model, csv_dir)
