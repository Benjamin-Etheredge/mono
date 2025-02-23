from lightning.pytorch.cli import LightningCLI
from lightning.pytorch.callbacks import EarlyStopping, ModelCheckpoint
from datamodule import IttyDataModule
from model import Model
from lightning.pytorch.loggers import WandbLogger
from jsonargparse import lazy_instance


def cli_main():
    cli = LightningCLI(
        Model,
        IttyDataModule,
        trainer_defaults=dict(
            max_epochs=10000,
            accelerator='gpu',
            logger=lazy_instance(WandbLogger, project="itty"),
            callbacks=[
                EarlyStopping(monitor="val/loss", patience=10),
                ModelCheckpoint("checkpoints", filename="best"),
            ],
        ))


if __name__ == "__main__":
    cli_main()