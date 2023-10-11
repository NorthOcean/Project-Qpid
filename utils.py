"""
@Author: Conghao Wong
@Date: 2022-06-20 20:10:58
@LastEditors: Conghao Wong
@LastEditTime: 2023-10-11 12:46:41
@Description: file content
@Github: https://github.com/cocoon2wong
@Copyright 2022 Conghao Wong, All Rights Reserved.
"""

import logging
import os
import plistlib
import time

import numpy as np
import torch

"""
Configs
"""
# Basic parameters
TIME = time.strftime('%Y%m%d-%H%M%S', time.localtime(time.time()))

# Paths settings
ROOT_TEMP_DIR = './temp_files'
DATASET_CONFIG_DIR = './dataset_configs'

# Dataset configs
INIT_POSITION = 100000000

# Context map configs
SEG_IMG = 'segmentation_image'
RGB_IMG = 'rgb_image'

# WINDOW_EXPAND_PIXEL = 0.3
# WINDOW_SIZE_PIXEL = 200.0
WINDOW_EXPAND_PIXEL = 10.0
WINDOW_SIZE_PIXEL = 10.0

WINDOW_EXPAND_METER = 10.0
WINDOW_SIZE_METER = 10.0

MAP_HALF_SIZE = 50  # Local map's half size
AVOID_SIZE = 15     # Avoid size in grid cells when modeling social interaction
INTEREST_SIZE = 20  # Interest size in grid cells when modeling social interaction

POOLING_BEFORE_SAVING = True

# Preprocess configs
ROTATE_BIAS = 0.01
SCALE_THRESHOLD = 0.05

# Visualization configs
SMALL_POINTS = True

# Log paths and configs
LOG_FILE = './test.log'
LOG_MAX_LIST_LEN = 10
LOG_STREAM_HANDLER = logging.StreamHandler()

# Weights configs
WEIGHTS_FORMAT = '.pt'
CHECKPOINT_FILENAME = 'best_ade_epoch.txt'

# Visualization settings
# color bar in BGR format
# rgb(0, 0, 178) -> rgb(252, 0, 0) -> rgb(255, 255, 10)
DISTRIBUTION_COLORBAR = np.column_stack([
    np.interp(np.arange(256),
              np.array([0, 127, 255]),
              np.array([178, 0, 10])),
    np.interp(np.arange(256),
              np.array([0, 127, 255]),
              np.array([0, 0, 255])),
    np.interp(np.arange(256),
              np.array([0, 127, 255]),
              np.array([0, 252, 255])),
])

# Whether draw lines and text in images and videos
DRAW_LINES = False
DRAW_TEXT_IN_VIDEOS = False
DRAW_TEXT_IN_IMAGES = True


def dir_check(target_dir: str) -> str:
    """
    Used for checking if the `target_dir` exists.
    If it does not exist, it will make it.
    """
    if not os.path.exists(target_dir):
        os.makedirs(target_dir)

    return target_dir


def get_relative_path(reference_file_path: str, relative_path: str):
    return os.path.join(os.path.dirname(reference_file_path), relative_path)


def move_to_device(item, d: torch.device):
    T = type(item)
    if T in [list, tuple]:
        return [move_to_device(i, d) for i in item]
    elif issubclass(T, torch.Tensor):
        return item.to(d)
    else:
        return item


def load_from_plist(path: str) -> dict:
    """
    Load plist files into python `dict` object.

    :param path: The path of the plist file.
    :return dat: A `dict` object loaded from the file.
    """
    with open(path, 'rb') as f:
        dat = plistlib.load(f)

    return dat


def get_mask(input: torch.Tensor, dtype=torch.float32):
    return (input < 0.05 * INIT_POSITION).to(dtype=dtype)


def get_loss_mask(obs: torch.Tensor | np.ndarray,
                  label: torch.Tensor | np.ndarray,
                  return_numpy=False):
    """
    Get mask from both model predictions and labels.
    Return type: `torch.float32`.

    :param obs: Observed trajectories, shape = `(..., steps, dim)`
    :param label: Label trajectories, shape = `(..., steps, dim)`
    """
    if issubclass(type(obs), np.ndarray):
        obs = torch.from_numpy(obs)
        label = torch.from_numpy(label)

    pred_mask = get_mask(torch.sum(obs, dim=[-1, -2]))
    label_mask = get_mask(torch.sum(label, dim=[-1, -2]))
    mask = pred_mask * label_mask
    if return_numpy:
        mask = mask.numpy()
    return mask


def batch_matmul(a: torch.Tensor, b: torch.Tensor, transpose_b=False):
    """
    Run matmul operations on a batch of inputs.
    Other args will be wrapped to `torch.matmul`.

    :param a: Input, shape is `(..., a, b)`.
    :param b: Another input, shape is `(..., b, c)`.
    """
    if transpose_b:
        b = torch.transpose(b, -1, -2)
    if a.ndim <= 4:
        return torch.matmul(a, b)

    batch = a.shape[:-3]
    _a = torch.reshape(a, [-1]+list(a.shape[2:]))
    _b = torch.reshape(b, [-1]+list(b.shape[2:]))
    res = torch.matmul(_a, _b)

    return torch.reshape(res, list(batch) + list(res.shape[1:]))