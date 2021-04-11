import shutil
import os
import tensorflow_datasets as tfds


def _prepare_annotation(filename, path, dataset, classes):
    value = 0
    class_names = dict()
    with open('./model_data/coco_classes_en.txt') as f:
        clazzs = f.readlines()

    for clazz in clazzs:
        class_names[clazz.replace("\n", "")] = value
        value += 1

    processing_classes = set()
    if 'all' in classes:
        for key in class_names.keys():
            processing_classes.add(class_names[key])
    else:
        for key in classes:
            processing_classes.add(class_names[key])

    with open(filename, 'w') as file:
        for example in dataset:
            string = os.path.join(path, example['image/filename'].numpy().decode())
            height, width, _ = example['image'].shape
            label = example['objects']['label'].numpy()
            bbox = example['objects']['bbox'].numpy()
            bboxs = ''
            for i in range(len(label)):
                if label[i] in processing_classes:
                    bbox_string = f'{int(bbox[i][1] * width)},{int(bbox[i][0] * height)},' \
                                  f'{int(bbox[i][3] * width)},{int(bbox[i][2] * height)},{label[i]}'
                    bboxs += ' ' + bbox_string
            string += bboxs
            print(string)
            file.write(string + '\n')


def coco_dataset_annotations(classes, root_path='./', is_prepare_annotation=True):
    train_path = f'{root_path}coco/COCO_train/'
    test_path = f'{root_path}coco/COCO_test/'
    val_path = f'{root_path}coco/COCO_val/'
    train_ds = tfds.load('coco', split='train', data_dir=root_path)
    val_ds = tfds.load('coco', split='validation', data_dir=root_path)
    test_ds = tfds.load('coco', split='test', data_dir=root_path)

    list_d = os.listdir(os.path.join(root_path, 'downloads'))
    if len(list_d) != 0 and list_d[0] == 'extracted':
        list_d = os.listdir(os.path.join(root_path, 'downloads', 'extracted'))
        for d in list_d:
            list_dir = os.listdir(os.path.join(root_path, 'downloads', 'extracted', d))
            if len(list_dir) != 0:
                if list_dir[0] == 'train2014':
                    shutil.move(os.path.join(root_path, 'downloads', 'extracted', d, 'train2014'),
                                os.path.join(root_path, 'coco', 'COCO_train'))
                elif list_dir[0] == 'test2014':
                    shutil.move(os.path.join(root_path, 'downloads', 'extracted', d, 'test2014'),
                                os.path.join(root_path, 'coco', 'COCO_test'))
                elif list_dir[0] == 'val2014':
                    shutil.move(os.path.join(root_path, 'downloads', 'extracted', d, 'val2014'),
                                os.path.join(root_path, 'coco', 'COCO_val'))
    else:
        for d in list_d:
            list_dir = os.listdir(os.path.join(root_path, 'downloads', d))
            if len(list_dir) != 0:
                if list_dir[0] == 'train2014':
                    shutil.move(os.path.join(root_path, 'downloads', d, 'train2014'),
                                os.path.join(root_path, 'coco', 'COCO_train'))
                elif list_dir[0] == 'test2014':
                    shutil.move(os.path.join(root_path, 'downloads', d, 'test2014'),
                                os.path.join(root_path, 'coco', 'COCO_test'))
                elif list_dir[0] == 'val2014':
                    shutil.move(os.path.join(root_path, 'downloads', d, 'val2014'),
                                os.path.join(root_path, 'coco', 'COCO_val'))

    ann_train_path = './model_data/coco_train_annotation.txt'
    ann_test_path = './model_data/coco_test_annotation.txt'
    ann_val_path = './model_data/coco_val_annotation.txt'

    if is_prepare_annotation:
        _prepare_annotation(ann_train_path, train_path, train_ds, classes)
        _prepare_annotation(ann_test_path, test_path, test_ds, classes)
        _prepare_annotation(ann_val_path, val_path, val_ds, classes)

    return ann_train_path, ann_test_path, ann_val_path