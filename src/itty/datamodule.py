from PIL import Image
from lightning.pytorch import LightningDataModule
from lightning import seed_everything
import torchvision.transforms as T
from pathlib import Path
from torch.utils.data import DataLoader, random_split, Dataset
from torchvision.datasets import DatasetFolder, ImageFolder
import os
import torch
from sklearn.model_selection import train_test_split
from typing import List, Tuple
import json
from icecream import ic

seed_everything(4)

class IttyDataset(Dataset):
    def __init__(self, dataset, transform=None):
        self.dataset = dataset
        self.transform = transform

    def __len__(self):
        return len(self.dataset)
    
    def __getitem__(self, idx):
        file_path, y = self.dataset[idx]
        image = Image.open(file_path).convert("RGB")
        image = self.transform(image) if self.transform else image
        return image, y

def get_label(file):
    print(file)
    print(file.stem)
    return file.stem.split('_')[-2]

def find_classes(directory: Path):
    class_mapping = {}
    idx = 0
    for file in directory.glob("**/*"):
        label = get_label(file)
        if label not in class_mapping:
            class_mapping[label] = idx
            idx += 1

    return class_mapping


class IttyDataModule(LightningDataModule):
    def __init__(
        self, 
        data_dir: str = "data/Chula-ParasiteEgg-11/data", 
        labels_path: str = "data/Chula-ParasiteEgg-11/labels.json", 
        batch_size: int = 128,
    ):
        super().__init__()
        self.data_dir = Path(data_dir)
        self.labels_file = Path(labels_path)
        self.batch_size = batch_size
        self.train_dataset = None
        self.val_dataset = None
        self.test_dataset = None
        self.transform = None
        self.setup_stage = None
        self.num_workers = os.cpu_count() // 2
        self.pin_memory = True

    def setup(self, stage=None):

        with open(self.labels_file) as f:
            label_data = json.load(f)

        ic(str(label_data.keys()))
        # ic(label_data['info'])
        # ic(label_data["categories"])
        # ic(label_data['images'][:20])
        # ic(label_data['annotations'][:20])
        self.image_files = {image_data['id']: Path(image_data['file_name']) for image_data in label_data['images']}
        self.image_to_category = {}
        for annotation in label_data['annotations']:
            image_id = annotation['image_id']
            category_id = annotation['category_id']
            if image_id not in self.image_to_category:
                self.image_to_category[image_id] = category_id
            else:
                assert self.image_to_category[image_id] == category_id, \
                    f"Image ID {image_id} found more than once in annotation data and category mismatch"


        self.class_mapping = {data['id']: data['name'] for data in label_data["categories"]}
        ic(self.class_mapping)
        
        self.dataset = [(self.data_dir/self.image_files[i], self.image_to_category[i]) for i in self.image_to_category]

        train_dataset, val_dataset = train_test_split(
            self.dataset,
            test_size=0.2, 
            random_state=42,
            stratify=[item[1] for item in self.dataset])
        self.train_dataset = IttyDataset(
            train_dataset,
            transform=T.Compose([
                T.Resize((224, 224)),
                T.ToTensor(),
                T.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
            ])
        )
        self.val_dataset = IttyDataset(
            val_dataset,
            transform=T.Compose([
                T.Resize((224, 224)),
                T.ToTensor(),
                T.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
            ])
        )
    
    def train_dataloader(self):
        return DataLoader(
            self.train_dataset,
            self.batch_size,
            shuffle=True,
            num_workers=self.num_workers,
            pin_memory=True,
            persistent_workers=True,
        )
    
    def val_dataloader(self):
        return DataLoader(
            self.val_dataset,
            self.batch_size,
            shuffle=False,
            num_workers=self.num_workers,
            pin_memory=True,
            persistent_workers=True,
        )
 
    


