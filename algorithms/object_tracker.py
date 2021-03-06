import cv2
import tensorflow as tf
import time
import numpy as np
import colorsys
import random
import streamlink
import matplotlib.pyplot as plt
from libs.yolo3.utils import transform_images, convert_boxes
from libs.deepsort import preprocessing, nn_matching
from libs.deepsort.detection import Detection
from libs.deepsort.tracker import Tracker
from libs.deepsort.box_encoder import create_box_encoder
from libs.yolo3.layers import yolo_v3
from PIL import Image, ImageFont, ImageDraw
from libs.yolo3.utils import get_anchors


def output(img, tracks, colors):
    img = Image.fromarray(img)
    font = ImageFont.truetype(font='font/Roboto-Regular.ttf',
                              size=np.floor((3e-2 * img.size[1] + 0.5) / 2).astype('int32'))
    thickness = 1
    for track in tracks:
        if not track.is_confirmed() or track.time_since_update > 1:
            continue
        predicted_class = track.get_class()
        bbox = track.to_tlbr()

        label = f'{predicted_class} - №{track.track_id} - {track.score:.2f}'
        draw = ImageDraw.Draw(img)
        label_size = draw.textsize(label, font)

        x1, y1 = bbox[0], bbox[1]
        x2, y2 = bbox[2], bbox[3]

        if y1 - label_size[1] >= 0:
            text_origin = np.array([x1, y1 - label_size[1]])
        else:
            text_origin = np.array([x1, y1 + 5])

        # My kingdom for a good redistributable image drawing library.
        color = colors[int(track.track_id) % len(colors)]
        color = [int(i * 255) for i in color]
        for j in range(thickness):
            draw.rectangle([x1 + j, y1 + j, x2 - j, y2 - j], outline=tuple(color))
        draw.rectangle([tuple(text_origin), tuple(text_origin + label_size)], fill=tuple(color))
        draw.text(text_origin, label, fill=(255, 255, 255), font=font)
        del draw

    return np.asarray(img)


if __name__ == '__main__':
    max_cosine_distance = 0.5
    nn_budget = None
    nms_max_overlap = 1.0

    # initialize deep sort
    model_filename = 'model_data/deepsort.pb'
    encoder = create_box_encoder(model_filename, batch_size=1)
    metric = nn_matching.NearestNeighborDistanceMetric('cosine', max_cosine_distance, nn_budget)
    tracker = Tracker(metric)

    size = 416
    num_classes = 80
    anchors = get_anchors('./model_data/yolo_anchors.txt')

    # yolo = yolo_v4(size=size, classes=num_classes)
    # yolo.load_weights('./model_data/yolov4.tf')

    yolo = yolo_v3(anchors, size, channels=3, classes=num_classes)
    yolo.load_weights('./model_data/yolov3.tf')

    class_names = [c.strip() for c in open('model_data/coco_classes_ru.txt').readlines()]

    # vid = cv2.VideoCapture('other/test.mp4')
    url = f'https://www.youtube.com/watch?v=My_fX46HMH4'

    streams = streamlink.streams(url)
    vid = cv2.VideoCapture(streams["720p"].url)
    vid.set(cv2.CAP_PROP_FPS, 16)

    fps = 0.0
    count = 0
    while True:
        _, img = vid.read()
        img = cv2.resize(img, (1920, 1080))
        img_in = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        img_in = tf.expand_dims(img_in, 0)
        img_in = transform_images(img_in, size)

        t1 = time.time()
        boxes, scores, classes, nums = yolo.predict(img_in)
        classes = classes[0]
        names = []
        for i in range(len(classes)):
            names.append(class_names[int(classes[i])])
        names = np.array(names)
        converted_boxes = convert_boxes(img, boxes[0])
        features = encoder(img, converted_boxes)
        detections = [Detection(bbox, score, class_name, int(class_id), feature)
                      for bbox, score, class_name, class_id, feature
                      in zip(converted_boxes, scores[0], names, classes, features)
                      if class_name == 'человек']

        # run non-maxima suppresion
        boxs = np.array([d.tlwh for d in detections])
        scores = np.array([d.confidence for d in detections])
        classes = np.array([d.class_name for d in detections])
        indices = preprocessing.non_max_suppression(boxs, classes, nms_max_overlap, scores)
        detections = [detections[i] for i in indices]

        cmap = plt.get_cmap('tab20b')
        colors = [cmap(i)[:3] for i in np.linspace(0, 1, 20)]

        # call the tracker
        tracker.predict()
        tracker.update(detections)

        img = output(img, tracker.tracks, colors)

        fps = (fps + (1. / (time.time() - t1))) / 2
        cv2.putText(img, "FPS: {:.2f}".format(fps), (0, 30),
                    cv2.FONT_HERSHEY_COMPLEX_SMALL, 1, (0, 0, 255), 2)
        cv2.namedWindow("output", cv2.WINDOW_NORMAL)
        cv2.imshow('output', img)

        # press q to quit
        if cv2.waitKey(1) == 27:
            break
