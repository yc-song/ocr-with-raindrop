"""
Copyright (c) 2019-present NAVER Corp.
MIT License
"""

# -*- coding: utf-8 -*-
import sys
import os
import time
import argparse
import imgproc

import torch
import torch.backends.cudnn as cudnn
from torch.autograd import Variable
from tqdm import tqdm
import cv2
import numpy as np
import sys
sys.path.append('.')
from craft import CRAFT
from data.load_icdar import load_icdar2015_gt, load_icdar2013_gt
from utils.inference_boxes import test_net
from data import imgproc
from collections import OrderedDict
from metrics.eval_det_iou import DetectionIoUEvaluator
import file_utils


def copyStateDict(state_dict):
    if list(state_dict.keys())[0].startswith("module"):
        start_idx = 1
    else:
        start_idx = 0
    new_state_dict = OrderedDict()
    for k, v in state_dict.items():
        name = ".".join(k.split(".")[start_idx:])
        new_state_dict[name] = v
    return new_state_dict

def str2bool(v):
    return v.lower() in ("yes", "y", "true", "t", "1")

parser = argparse.ArgumentParser(description='CRAFT Text Detection')
parser.add_argument('--trained_model', default='/home/yanhai/OCR/OCRRepo/craft/githubcraft/CRAFT-Reimplementation/weights_52000.pth', type=str, help='pretrained model')
parser.add_argument('--text_threshold', default=0.7, type=float, help='text confidence threshold')
parser.add_argument('--low_text', default=0.4, type=float, help='text low-bound score')
parser.add_argument('--link_threshold', default=0.4, type=float, help='link confidence threshold')
parser.add_argument('--cuda', default=True, type=str2bool, help='Use cuda for inference')
parser.add_argument('--canvas_size', default=1280, type=int, help='image size for inference')
parser.add_argument('--mag_ratio', default=1.5, type=float, help='image magnification ratio')
parser.add_argument('--poly', default=False, action='store_true', help='enable polygon type')
parser.add_argument('--isTraingDataset', default=False, type=str2bool, help='test for traing or test data')
parser.add_argument('--test_folder', default='/media/yanhai/disk1/ICDAR/icdar2013', type=str, help='folder path to input images')
parser.add_argument('--derain', action='store_true', help='derain or not')
parser.add_argument('--result_folder', default='./result/', type=str, help='path to result')


def main(model, args, evaluator):
    if not os.path.isdir(args.result_folder):
        os.mkdir(args.result_folder)
    
    if args.derain:
        result_folder = os.path.join(args.result_folder , 'derain/')
    else:
        result_folder = os.path.join(args.result_folder , 'no_derain/')
    if not os.path.isdir(result_folder):
        os.mkdir(result_folder)
    test_folder = args.test_folder
    total_imgs_bboxes_gt, total_img_path = load_icdar2015_gt(dataFolder=test_folder, isTraing=args.isTraingDataset)
    total_img_bboxes_pre = []
    for img_path in tqdm(total_img_path):
        image = imgproc.loadImage(img_path)
        single_img_bbox = []
        filename, file_ext = os.path.splitext(os.path.basename(img_path))
        bboxes, polys, score_text, image_derained = test_net(model,
                                             image,
                                             args.text_threshold,
                                             args.link_threshold,
                                             args.low_text,
                                             args.cuda,
                                             args.poly,
                                             args.canvas_size,
                                             args.mag_ratio,
                                             args.derain)
        for box in bboxes:
            box_info = {"points": None, "text": None, "ignore": None}
            box_info["points"] = box
            box_info["text"] = "###"
            box_info["ignore"] = False
            single_img_bbox.append(box_info)
        total_img_bboxes_pre.append(single_img_bbox)
        mask_file = result_folder + "/res_" + filename + '_mask.jpg'
        cv2.imwrite(mask_file, score_text)
        if image_derained is not None:
            derained_file = result_folder + "/res_" + filename + '_derained.jpg'
            cv2.imwrite(derained_file, image_derained)
        file_utils.saveResult(img_path, image[:,:,::-1], polys, dirname=result_folder)
        
    results = []
    for gt, pred in zip(total_imgs_bboxes_gt, total_img_bboxes_pre):
        results.append(evaluator.evaluate_image(gt, pred))
    metrics = evaluator.combine_results(results)
    print(metrics)

if __name__ == '__main__':

    args = parser.parse_args()
    # load net
    net = CRAFT()     # initialize

    print('Loading weights from checkpoint (' + args.trained_model + ')')
    if args.cuda:
        net.load_state_dict(copyStateDict(torch.load(args.trained_model)))
    else:
        net.load_state_dict(copyStateDict(torch.load(args.trained_model, map_location='cpu')))

    if args.cuda:
        net = net.cuda()
        net = torch.nn.DataParallel(net)
        cudnn.benchmark = False
    net.eval()
    evaluator = DetectionIoUEvaluator()

    main(net, args, evaluator)
