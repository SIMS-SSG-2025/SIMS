import torch
from torch.utils.data import DataLoader
import torch.optim as optim
from torch.utils.tensorboard import SummaryWriter
from data.dataset import SafetyDataset
from ultralytics.data.dataset import YOLODataset
from ultralytics.nn.tasks import DetectionModel
import argparse
import yaml
from types import SimpleNamespace
import numpy as np
from utils.loss import DetectionLoss
import copy

parser = argparse.ArgumentParser()
parser.add_argument(
    "--config",
    type=str,
    required=True,
    help="Path to YAML config file",
)

args = parser.parse_args()

with open(args.config, 'r') as file:
    config=yaml.safe_load(file)

TRAIN_IMAGES_DIR = config['data']['train']['images_dir']
TRAIN_LABELS_DIR = config['data']['train']['labels_dir']
TRAIN_BATCH_SIZE = config['data']['train']['batch_size']

VALIDATION_IMAGES_DIR = config['data']['valid']['images_dir']
VALIDATION_LABELS_DIR = config['data']['valid']['labels_dir']
VALIDATION_BATCH_SIZE = config['data']['valid']['batch_size']

LEARNING_RATE = config['training']['optimizer']['lr']
EPOCHS = config['training']['epochs']
DEVICE = config['training']['device']

if DEVICE == "cuda:0":
    DEVICE = "cuda:0" if torch.cuda.is_available() else "cpu"
else:
    DEVICE = "cpu"

BASE_MODEL = config['model']['base_model']
MODEL_CHECKPOINT = config['model']['model_checkpoint']
MODEL_CONFIG = config['model']['model_config']
LOG_DIR = config['training']['log_dir']
print(LEARNING_RATE)

# Dataset and dataloaders

train_dataset = SafetyDataset(
    images_dir=TRAIN_IMAGES_DIR,
    labels_dir=TRAIN_LABELS_DIR,
)

val_dataset = SafetyDataset(
    images_dir=VALIDATION_IMAGES_DIR,
    labels_dir=VALIDATION_LABELS_DIR,
)

train_loader = DataLoader(
    dataset=train_dataset,
    batch_size=TRAIN_BATCH_SIZE,
    shuffle=True,
    collate_fn=YOLODataset.collate_fn,
)

val_loader = DataLoader(
    dataset=val_dataset,
    batch_size=VALIDATION_BATCH_SIZE,
    shuffle=True,
    collate_fn=YOLODataset.collate_fn,
)

# Load model

if config["training"]["train_from_checkpoint"]:
    with open(MODEL_CONFIG, 'r') as file:
        model_config = yaml.safe_load(file)
    num_classes = model_config["nc"]
    model = DetectionModel(cfg=model_config, nc=num_classes)
    model.load_state_dict(torch.load(MODEL_CHECKPOINT, map_location=lambda storage, loc: storage))
    print("continue from checkpoint")
else:
    model_checkpoint = torch.load(BASE_MODEL)
    model_config = model_checkpoint['model'].yaml
    num_classes = model_config["nc"]
    model = DetectionModel(cfg=model_config, nc=num_classes, verbose=True)
    model.load(model_checkpoint)
    print("base model")


model = model.to(DEVICE)

# Freeze layers

unfreeze = [-1]

for param in model.parameters():
    param.requires_grad = False

for layer_id in unfreeze:
    for name, param in model.model[layer_id].named_parameters():
        param.requires_grad = True

for name, param in model.named_parameters():
    if param.requires_grad:
        print(f"Trainable: {name}")

# Training

loss_hyp = SimpleNamespace(
    box=7.5,
    cls=0.5,
    dfl=1.5
)

criterion = DetectionLoss(model, hyp=loss_hyp)

optimizer = optim.AdamW(model.parameters(), lr=LEARNING_RATE)

lr_scheduler = optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=EPOCHS, eta_min=0.0000001)

train_box_loss = []
train_cls_loss = []
train_dfl_loss = []

val_box_loss = []
val_cls_loss = []
val_dfl_loss = []


# Early stopping
patience = 5
best_val_loss = float("inf")
epochs_no_improve = 0
best_model_state = None

# Tensorboard
writer = SummaryWriter(log_dir=LOG_DIR)


# Training loop

for epoch in range(EPOCHS):

    print(f'Epoch: {epoch+1}/{EPOCHS}')

    training_loss = []
    validation_loss = []

    epoch_train_box = []
    epoch_train_cls = []
    epoch_train_dfl = []

    epoch_val_box = []
    epoch_val_cls = []
    epoch_val_dfl = []


    model.train()
    for batch in train_loader:
        batch = {k: v.to(DEVICE) if isinstance(v, torch.Tensor) else v for k, v in batch.items()}
        images = batch['img']

        # Forward
        output = model.forward(images)

        loss, loss_items = criterion(output, batch)
        loss = loss.sum()

        # Backward
        loss.backward()

        optimizer.step()
        optimizer.zero_grad()

        training_loss.append(loss.item())
        epoch_train_box.append(loss_items[0].item())
        epoch_train_cls.append(loss_items[1].item())
        epoch_train_dfl.append(loss_items[2].item())



    lr_scheduler.step()

    model.eval()
    with torch.no_grad():
        for batch in val_loader:
            batch = {k: v.to(DEVICE) if isinstance(v, torch.Tensor) else v for k, v in batch.items()}
            images = batch['img']
            # Forward
            output = model.forward(images)

            loss, loss_items = criterion(output, batch)
            loss = loss.sum()

            validation_loss.append(loss.item())
            epoch_val_box.append(loss_items[0].item())
            epoch_val_cls.append(loss_items[1].item())
            epoch_val_dfl.append(loss_items[2].item())


    mean_train_loss = np.mean(training_loss)
    mean_val_loss = np.mean(validation_loss)

    mean_train_box = np.mean(epoch_train_box)
    mean_train_cls = np.mean(epoch_train_cls)
    mean_train_dfl = np.mean(epoch_train_dfl)

    mean_val_box = np.mean(epoch_val_box)
    mean_val_cls = np.mean(epoch_val_cls)
    mean_val_dfl = np.mean(epoch_val_dfl)

    print(
        f"Training: total {mean_train_loss:.4f} "
        f"(box {mean_train_box:.4f}, cls {mean_train_cls:.4f}, dfl {mean_train_dfl:.4f}) | "
        f"Validation: total {mean_val_loss:.4f} "
        f"(box {mean_val_box:.4f}, cls {mean_val_cls:.4f}, dfl {mean_val_dfl:.4f})"
    )

    # Tensorboard logging
    writer.add_scalar("Loss/train_total", mean_train_loss, epoch)
    writer.add_scalar("Loss/val_total", mean_val_loss, epoch)

    writer.add_scalar("Loss/train_box", mean_train_box, epoch)
    writer.add_scalar("Loss/train_cls", mean_train_cls, epoch)
    writer.add_scalar("Loss/train_dfl", mean_train_dfl, epoch)

    writer.add_scalar("Loss/val_box", mean_val_box, epoch)
    writer.add_scalar("Loss/val_cls", mean_val_cls, epoch)
    writer.add_scalar("Loss/val_dfl", mean_val_dfl, epoch)

    if mean_val_loss < best_val_loss:
        best_val_loss = mean_val_loss
        epochs_no_improve = 0
        best_model_state = copy.deepcopy(model.state_dict())
    else:
        epochs_no_improve += 1

    if epochs_no_improve >= patience:
        print(f"Early stopping at epoch: {epoch}. Saving best model...")
        model.load_state_dict(best_model_state)
        break


torch.save(model.state_dict(), "yolo11_ppe_best.pt")
writer.close()