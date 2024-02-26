import numpy as np
import torch
from torch.utils.data import Dataset
import cv2

IMAGE_SIZE = 2048
PATCH_SIZE = 128
SAMPLE_MARGIN = 64
EVAL_STEPS = 32

def read_rgb_img(path):
    bgr = cv2.imread(path)
    rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
    return rgb

class CityScaleDataset(Dataset):
    def __init__(self, is_train):
        rgb_pattern = './cityscale/20cities/region_{}_sat.png'
        keypoint_mask_pattern = './cityscale/processed/keypoint_mask_{}.png'
        road_mask_pattern = './cityscale/processed/road_mask_{}.png'
        train, val, test = self.data_partition()

        self.is_train = is_train

        train_split = train + val
        test_split = test

        tile_indices = train_split if self.is_train else test_split
        self.tile_indices = tile_indices
        
        # Stores all imgs in memory.
        self.rgbs, self.keypoint_masks, self.road_masks = [], [], []
        for tile_idx in tile_indices:
            rgb_path = rgb_pattern.format(tile_idx)
            road_mask_path = road_mask_pattern.format(tile_idx)
            keypoint_mask_path = keypoint_mask_pattern.format(tile_idx)
            self.rgbs.append(read_rgb_img(rgb_path))
            self.road_masks.append(cv2.imread(road_mask_path, cv2.IMREAD_GRAYSCALE))
            self.keypoint_masks.append(cv2.imread(keypoint_mask_path, cv2.IMREAD_GRAYSCALE))
            
        
        self.sample_min = SAMPLE_MARGIN
        self.sample_max = IMAGE_SIZE - (PATCH_SIZE + SAMPLE_MARGIN)

        eval_samples = np.linspace(start=self.sample_min, stop=self.sample_max, num=EVAL_STEPS)
        eval_samples = [round(x) for x in eval_samples]
        self.eval_patches = []
        for i in range(len(test_split)):
            for x in eval_samples:
                for y in eval_samples:
                    self.eval_patches.append(i, (x, y), (x + PATCH_SIZE, y + PATCH_SIZE))
        

    def data_partition(self):
        # dataset partition
        indrange_train = []
        indrange_test = []
        indrange_validation = []

        for x in range(180):
            if x % 10 < 8 :
                indrange_train.append(x)

            if x % 10 == 9:
                indrange_test.append(x)

            if x % 20 == 18:
                indrange_validation.append(x)

            if x % 20 == 8:
                indrange_test.append(x)
        return indrange_train, indrange_validation, indrange_test

    def __len__(self):
        if self.is_train:
            return 1000000
        else:
            return len(self.eval_patches)

    def __getitem__(self, idx):
        if self.is_train:
            img_idx = np.random.randint(low=0, high=len(self.rgbs))
            begin_x = np.random.randint(low=self.sample_min, high=self.sample_max+1)
            begin_y = np.random.randint(low=self.sample_min, high=self.sample_max+1)
            end_x, end_y = begin_x + PATCH_SIZE, begin_y + PATCH_SIZE
        else:
            # Returns eval patch
            img_idx, (begin_x, begin_y), (end_x, end_y) = self.eval_patches[idx]
        
        rgb_patch = self.rgbs[img_idx][begin_y:end_y, begin_x:end_x, :]
        keypoint_mask_patch = self.keypoint_masks[img_idx][begin_y:end_y, begin_x:end_x]
        road_mask_patch = self.road_masks[img_idx][begin_y:end_y, begin_x:end_x]
        
        # Augmentation
        if self.is_train:
            rot_index = np.random.randint(0, 4)
            rgb_patch = np.rot90(rgb_patch, rot_index, [0,1]).copy()
            keypoint_mask_patch = np.rot90(keypoint_mask_patch, rot_index, [0, 1]).copy()
            road_mask_patch = np.rot90(road_mask_patch, rot_index, [0, 1]).copy()
        
        return torch.tensor(rgb_patch), torch.tensor(keypoint_mask_patch), torch.tensor(road_mask_patch)