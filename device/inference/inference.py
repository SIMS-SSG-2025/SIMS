from device.training.data.transforms import letterbox
import torch
from ultralytics.utils.ops import non_max_suppression, xyxy2xywh



def post_process(output, letterbox_info):
    ratio, dw, dh = letterbox_info
    nms_results = non_max_suppression(
            output[0],
            conf_thres=0.7,
            iou_thres=0.8,
            max_det=1000
        )

    preds = []
    if len(nms_results[0]) > 0:
        for pred in nms_results[0]:
            # undo letterboxing
            pred[0] = (pred[0] - dw) / ratio  # x1
            pred[1] = (pred[1] - dh) / ratio  # y1
            pred[2] = (pred[2] - dw) / ratio  # x2
            pred[3] = (pred[3] - dh) / ratio  # y2
            bbox = xyxy2xywh(pred[:4].unsqueeze(0))[0].cpu().numpy().tolist()
            conf = pred[4].item()
            cls = int(pred[5].item())
            preds.append((bbox, conf, cls))

    return preds

def pre_process(frame):
    img_padded, _, letterbox_info = letterbox(frame)
    img_tensor = torch.from_numpy(img_padded).permute(2, 0, 1).float() / 255.0
    img_tensor = img_tensor.unsqueeze(0)
    return img_tensor, letterbox_info


def run_inference(frame, model):
    img_tensor, letterbox_info = pre_process(frame)
    with torch.no_grad():
        output = model.forward(img_tensor)

    return post_process(output, letterbox_info)


