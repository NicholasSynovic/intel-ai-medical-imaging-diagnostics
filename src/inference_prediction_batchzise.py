# Copyright (C) 2022 Intel Corporation
# SPDX-License-Identifier: BSD-3-Clause

"""
Inference script
"""

import argparse
import logging
import os
# pylint: disable=C0301 E0401 C0103 W0612 I1101 E1129 W0311 C0411
import time
import warnings

import numpy as np
import tensorflow as tf
from cv2 import cv2

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
warnings.filterwarnings("ignore")


# Define the command line arguments to input
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--codebatchsize",
        type=int,
        default=1,
        help="enter the required batch size parameter?",
    )
    parser.add_argument(
        "--modeldir", type=str, default="./model/updated_model.pb", help="Specify path"
    )

    paramters = parser.parse_args()

    code_batch_size = paramters.codebatchsize
    model_dir = paramters.modeldir


# tf.disable_v2_behavior()
INPUT_IMAGE_SIZE = (300, 300)
padding = "SAME"  # @param ['SAME', 'VALID' ]
NUM_OUTPUT_CLASSES = 2  # @param {type: "number"}
# code_batch_size = 20  # @param {type: "number"}
# val_batch_size = 2
# learning_rate = 0.001  # @param {type: "number"}
ABS_TEST_PATH = "./data/chest_xray/test"


def create_path_list(abspath="None"):
    """defining function"""
    pathlist = []
    for root, dirs, files in os.walk(abspath):
        for subdir in dirs:
            for imgpath in os.listdir(os.path.join(abspath, subdir)):
                if imgpath.endswith(".jpeg"):
                    img_app = os.path.join(abspath, subdir, imgpath)
                    pathlist.append(img_app)
                    # print(img_app)
        break
    return pathlist


def read_Image(batch_size=4, Last_index=2, pathlist=None):
    """Define a read_image function"""
    x_batch, y_batch = [], []
    for imagepath in pathlist[Last_index : Last_index + batch_size]:
        image = cv2.imread(imagepath)
        image = cv2.resize(image, dsize=INPUT_IMAGE_SIZE)
        image = image / 255.0
        if imagepath.split("/")[-2] == "NORMAL":
            y = np.array([0, 1])
        else:
            y = np.array(([1, 0]))
        x_batch.append(image)
        y_batch.append(y)
    x_batch_train = np.stack(x_batch, axis=0)
    y_batch_train = np.stack(y_batch, axis=0)
    return x_batch_train, y_batch_train


path_val_list = create_path_list(ABS_TEST_PATH)
test_images, test_labels = read_Image(code_batch_size, 0, path_val_list)
# Load frozen graph using TensorFlow 1.x functions using FP32 Model
logger.info(
    "Load frozen graph using TensorFlow 1.x functions using fpmodel32============================>"
)

with tf.Graph().as_default() as graph:
    with tf.compat.v1.Session() as sess:
        # Load the graph in graph_def
        print("load graph")
        with tf.io.gfile.GFile(model_dir, "rb") as f:
            graph_def = tf.compat.v1.GraphDef()
            loaded = graph_def.ParseFromString(f.read())
            sess.graph.as_default()
            tf.import_graph_def(
                graph_def,
                input_map=None,
                return_elements=None,
                name="",
                op_dict=None,
                producer_op_list=None,
            )
            for op in graph.get_operations():
                logger.info("Operation Name :%s", op.name)  # Operation name
                logger.info("Tensor Stats :%s", str(op.values()))  # Tensor name
            l_input = graph.get_tensor_by_name("Placeholder:0")  # Input Tensor
            l_output = graph.get_tensor_by_name("Softmax:0")  # Output Tensor
            tf.compat.v1.global_variables_initializer()  # initialize_all_variables
            start_time = time.time()
            Session_out = sess.run(l_output, feed_dict={l_input: test_images})
            logger.info(
                "Time Taken for model inference in seconds ---> %f",
                time.time() - start_time,
            )
            LAST_INDEX = 175
            CORRECT_PREDICTION_COUNTER = 0
            WRONG_PREDICTION_COUNTER = 0
            # Calculating prediction
            for step in range(175, 375, code_batch_size):
                x_batch, y_batch = read_Image(
                    code_batch_size, LAST_INDEX, path_val_list
                )
                LAST_INDEX += code_batch_size
                start_time = time.time()
                correct_prediction_temp = sess.run(
                    l_output, feed_dict={l_input: x_batch, l_output: y_batch}
                )
                logger.info(
                    "Time Taken for model inference in seconds ---> %f",
                    time.time() - start_time,
                )
                for i, j in zip(correct_prediction_temp, y_batch):
                    if i[0] == j[0]:
                        CORRECT_PREDICTION_COUNTER = CORRECT_PREDICTION_COUNTER + 1
                    else:
                        WRONG_PREDICTION_COUNTER = WRONG_PREDICTION_COUNTER + 1
            print(
                "the number of correct predcitions (TP + TN) is:",
                CORRECT_PREDICTION_COUNTER,
            )
            print(
                "The number of wrong predictions (FP + FN) is", WRONG_PREDICTION_COUNTER
            )
