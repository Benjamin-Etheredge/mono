from torchvision.models import resnet18
from lightning.pytorch import LightningModule
import torch
import torchmetrics


class Model(LightningModule):
    def __init__(
        self,
        lr=0.001, 
        wd=0.,
        num_classes=11, 
        pretrained=True,
        **kwargs,
    ):
        super().__init__()
        self.save_hyperparameters()
        self.model = resnet18(pretrained=pretrained)
        self.model.fc = torch.nn.Linear(self.model.fc.in_features, num_classes)
        self.train_acc = torchmetrics.Accuracy(task="multiclass", num_classes=num_classes)
        self.val_acc = torchmetrics.Accuracy(task="multiclass", num_classes=num_classes)
    
    def forward(self, x):
        return self.model(x)
    
    def training_step(self, batch, batch_idx):
        x, y = batch
        logits = self.forward(x)

        self.train_acc.update(logits, y)
        self.log('train/acc', self.train_acc.compute())

        loss = torch.nn.functional.cross_entropy(logits, y)
        self.log('train/loss', loss)
        return loss
    
    def configure_optimizers(self):
        optimizer = torch.optim.Adam(
            self.parameters(), 
            lr=self.hparams.lr,
            weight_decay=self.hparams.wd,
        )
        return optimizer
    
    def validation_step(self, batch, batch_idx):
        x, y = batch
        logits = self.forward(x)

        self.val_acc.update(logits, y)
        self.log('val/acc', self.val_acc.compute())

        loss = torch.nn.functional.cross_entropy(logits, y)
        self.log('val/loss', loss)

        return loss


