from spatialdata import SpatialData
import torch
from torch.utils.data import DataLoader
from pytorch_lightning import LightningDataModule, LightningModule
from torch.nn import CrossEntropyLoss
from torch.optim import Adam
from monai.networks.nets import DenseNet121


def tile_transform(sdata: SpatialData) -> tuple[torch.Tensor, torch.Tensor]:
    cell_types = sdata["table"].obs["celltype_major"].cat.categories.tolist()
    tile = sdata["CytAssist_FFPE_Human_Breast_Cancer_full_image"].data.compute()
    tile = torch.tensor(tile, dtype=torch.float32)

    expected_category = sdata["table"].obs["celltype_major"].values[0]
    expected_idx = cell_types.index(expected_category)
    return tile, torch.tensor(expected_idx)


class TilesDataModule(LightningDataModule):
    def __init__(
        self, batch_size: int, num_workers: int, dataset: torch.utils.data.Dataset
    ):
        super().__init__()

        self.batch_size = batch_size
        self.num_workers = num_workers
        self.dataset = dataset

    def setup(self, stage=None):
        n_train = int(len(self.dataset) * 0.7)
        n_val = int(len(self.dataset) * 0.2)
        n_test = len(self.dataset) - n_train - n_val
        self.train, self.val, self.test = torch.utils.data.random_split(
            self.dataset,
            [n_train, n_val, n_test],
            generator=torch.Generator().manual_seed(42),
        )

    def train_dataloader(self):
        return DataLoader(
            self.train,
            batch_size=self.batch_size,
            num_workers=self.num_workers,
            shuffle=True,
        )

    def val_dataloader(self):
        return DataLoader(
            self.val,
            batch_size=self.batch_size,
            num_workers=self.num_workers,
            shuffle=False,
        )

    def test_dataloader(self):
        return DataLoader(
            self.test,
            batch_size=self.batch_size,
            num_workers=self.num_workers,
            shuffle=False,
        )

    def predict_dataloader(self):
        return DataLoader(
            self.dataset,
            batch_size=self.batch_size,
            num_workers=self.num_workers,
            shuffle=False,
        )


class DenseNetModel(LightningModule):
    def __init__(self, learning_rate: float, in_channels: int, num_classes: int):
        super().__init__()

        self.save_hyperparameters()

        self.loss_function = CrossEntropyLoss()

        self.model = DenseNet121(
            spatial_dims=2, in_channels=in_channels, out_channels=num_classes
        )

    def forward(self, x) -> torch.Tensor:
        return self.model(x)

    def _compute_loss_from_batch(
        self, batch: dict[str | int, torch.Tensor], batch_idx: int
    ) -> float:
        inputs = batch[0]
        labels = batch[1]

        outputs = self.model(inputs)
        return self.loss_function(outputs, labels)

    def training_step(
        self, batch: dict[str | int, torch.Tensor], batch_idx: int
    ) -> dict[str, float]:
        loss = self._compute_loss_from_batch(batch=batch, batch_idx=batch_idx)

        self.log("training_loss", loss, batch_size=len(batch[0]))

        return {"loss": loss}

    def validation_step(
        self, batch: dict[str | int, torch.Tensor], batch_idx: int
    ) -> float:
        loss = self._compute_loss_from_batch(batch=batch, batch_idx=batch_idx)

        imgs, labels = batch
        acc = self.compute_accuracy(imgs, labels)
        self.log("test_acc", acc)

        return loss

    def test_step(self, batch, batch_idx):
        imgs, labels = batch
        acc = self.compute_accuracy(imgs, labels)
        self.log("test_acc", acc)

    def predict_step(self, batch, batch_idx: int, dataloader_idx: int = 0):
        imgs, labels = batch
        preds = self.model(imgs).argmax(dim=-1)
        return preds

    def compute_accuracy(self, imgs, labels) -> float:
        preds = self.model(imgs).argmax(dim=-1)

        acc = (labels == preds).float().mean()
        return acc

    def configure_optimizers(self) -> Adam:
        return Adam(self.model.parameters(), lr=self.hparams.learning_rate)
