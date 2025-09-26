import torch
from ultralytics.utils.loss import BboxLoss, TaskAlignedAssigner
from ultralytics.utils.loss import v8DetectionLoss
import torch.nn as nn


class DetectionLoss(v8DetectionLoss):
    def __init__(self, model, hyp, tal_topk=10):

        device = next(model.parameters()).device
        h = hyp
        m = model.model[-1]
        self.bce = nn.BCEWithLogitsLoss(reduction="none")
        self.hyp = h
        self.stride = m.stride
        self.nc = m.nc
        self.no = m.nc + m.reg_max * 4
        self.reg_max = m.reg_max
        self.device = device

        self.use_dfl = m.reg_max > 1

        self.assigner = TaskAlignedAssigner(topk=tal_topk, num_classes=self.nc, alpha=0.5, beta=6.0)
        self.bbox_loss = BboxLoss(m.reg_max).to(device)
        self.proj = torch.arange(m.reg_max, dtype=torch.float, device=device)
