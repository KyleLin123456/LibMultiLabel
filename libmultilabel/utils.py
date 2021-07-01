import copy
import json
import logging
import os
import time

import numpy as np
import torch
from pytorch_lightning.utilities.seed import seed_everything


class Timer(object):
    """Computes elasped time."""

    def __init__(self):
        self.reset()

    def reset(self):
        self.running = True
        self.total = 0
        self.start = time.time()
        return self

    def resume(self):
        if not self.running:
            self.running = True
            self.start = time.time()
        return self

    def stop(self):
        if self.running:
            self.running = False
            self.total += time.time() - self.start
        return self

    def time(self):
        if self.running:
            return self.total + time.time() - self.start
        return self.total


def dump_log(log_path, metrics=None, split=None, config=None):
    """Write log including config and the evaluation scores.

    Args:
        log_path(str): path to log path
        metrics (dict): metric and scores in dictionary format, defaults to None
        split (str): val or test, defaults to None
        config (dict): config to save, defaults to None
    """
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    if os.path.isfile(log_path):
        with open(log_path) as fp:
            result = json.load(fp)
    else:
        result = dict()

    if config:
        config_to_save = copy.deepcopy(dict(config))
        config_to_save.pop('device', None)  # delete if device exists
        result['config'] = config_to_save
    if split and metrics:
        if split in result:
            result[split].append(metrics)
        else:
            result[split] = [metrics]

    with open(log_path, 'w') as fp:
        json.dump(result, fp)

    logging.info(f'Finish writing log to {log_path}.')


def save_top_k_predictions(class_names, y_pred, predict_out_path, k=100):
    """Save top k predictions to the predict_out_path. The format of this file is:
    <label1>:<value1> <label2>:<value2> ...

    Args:
        class_names (list): list of class names
        y_pred (ndarray): predictions (shape: number of samples * number of classes)
        k (int): number of classes considered as the correct labels
    """
    assert predict_out_path, "Please specify the output path to the prediction results."

    logging.info(f'Save top {k} predictions to {predict_out_path}.')
    with open(predict_out_path, 'w') as fp:
        for pred in y_pred:
            label_ids = np.argsort(-pred).tolist()[:k]
            out_str = ' '.join([f'{class_names[i]}:{pred[i]:.4}' for i in label_ids])
            fp.write(out_str+'\n')


def set_seed(seed):
    """Set seeds for numpy and pytorch."""
    if seed is not None:
        if seed >= 0:
            seed_everything(seed=seed)
            torch.set_deterministic(True)
            torch.backends.cudnn.benchmark = False
        else:
            logging.warning(
                f'the random seed should be a non-negative integer')


def init_device(use_cpu=False):
    if not use_cpu and torch.cuda.is_available():
        # Set a debug environment variable CUBLAS_WORKSPACE_CONFIG to ":16:8" (may limit overall performance) or ":4096:8" (will increase library footprint in GPU memory by approximately 24MiB).
        # https://docs.nvidia.com/cuda/cublas/index.html
        os.environ['CUBLAS_WORKSPACE_CONFIG'] = ":4096:8"
        device = torch.device('cuda')
    else:
        device = torch.device('cpu')
        # https://github.com/pytorch/pytorch/issues/11201
        torch.multiprocessing.set_sharing_strategy('file_system')
    logging.info(f'Using device: {device}')
    return device
