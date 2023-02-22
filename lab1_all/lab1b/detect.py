# Copyright 2021 The TensorFlow Authors. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Main script to run the object detection routine."""
import argparse
import sys
import time

import cv2
from tflite_support.task import core
from tflite_support.task import processor
from tflite_support.task import vision
import utils


def run(model: str, camera_id: int, width: int, height: int, num_threads: int,
        enable_edgetpu: bool, fc) -> None:
  """Continuously run inference on images acquired from the camera.

  Args:
    model: Name of the TFLite object detection model.
    camera_id: The camera id to be passed to OpenCV.
    width: The width of the frame captured from the camera.
    height: The height of the frame captured from the camera.
    num_threads: The number of CPU threads to run the model.
    enable_edgetpu: True/False whether the model is a EdgeTPU model.
  """

  # Variables to calculate FPS
  counter, fps = 0, 0
  start_time = time.time()
  directional = False
  # Start capturing video input from the camera
  cap = cv2.VideoCapture(camera_id)
  # default also 480
  cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
  cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
  # go to 480p
  # cap.set(3, 640)
  # cap.set(4, 480)
  # go to 240p
  # cap.set(3, 320)
  # cap.set(4, 240)

  # Visualization parameters
  row_size = 20  # pixels
  left_margin = 24  # pixels
  text_color = (0, 0, 255)  # red
  font_size = 1
  font_thickness = 1
  fps_avg_frame_count = 10

  # Initialize the object detection model
  base_options = core.BaseOptions(
      file_name=model, use_coral=enable_edgetpu, num_threads=num_threads)
  detection_options = processor.DetectionOptions(
      max_results=2, score_threshold=0.3)
  options = vision.ObjectDetectorOptions(
      base_options=base_options, detection_options=detection_options)
  detector = vision.ObjectDetector.create_from_options(options)

  # Continuously capture images from the camera and run inference
  # while cap.isOpened():
  if cap.isOpened():
    success, image = cap.read()
    if not success:
      sys.exit(
          'ERROR: Unable to read from webcam. Please verify your webcam settings.'
      )

    counter += 1
    image = cv2.flip(image, 1)

    # Convert the image from BGR to RGB as required by the TFLite model.
    rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

    # Create a TensorImage object from the RGB image.
    input_tensor = vision.TensorImage.create_from_array(rgb_image)

    # Run object detection estimation using the model.
    detection_result = detector.detect(input_tensor)
    
    for det in detection_result.detections:
      if det.categories:
        for cat in det.categories:
          if cat.score >= 0.5:
            if cat.category_name == 'stopsign' :
              directional = 'stopsign'
              # fc.logger.info('stopsign detected')
            elif cat.category_name == 'redlight':
              directional = 'redlight'
              # fc.logger.info('redlight detected')
            elif cat.category_name == 'yellowlight':
              directional = 'yellowlight'
              # fc.logger.info('yellowlight detected')
            elif cat.category_name == 'cone':
              # fc.logger.info('cone detected')
              directional = 'cone'
            elif cat.category_name == 'greenlight':
              # fc.logger.info('greenlight detected')
              directional = 'greenlight'
              pass
            

    # Draw keypoints and edges on input image
    img = utils.visualize(image, detection_result)

    image = cv2.flip(img, 0)
    filename = './photos/'+  str(int(time.time())) +'.jpg'
    cv2.imwrite(filename, image)
    
    cv2.imshow('object_detector', image)
  cap.release()
  return directional


def start(fc):
  model = './model2.tflite'
  cameraId = 0
  frameWidth = 320
  frameHeight = 240
  numThreads = 4
  enableEdgeTPU = False

  run(model, int(cameraId), frameWidth, frameHeight,
      int(numThreads), bool(enableEdgeTPU), fc)