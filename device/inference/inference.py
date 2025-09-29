from device.training.data.transforms import letterbox
import torch
from ultralytics.utils.ops import non_max_suppression, xyxy2xywh
import time

def post_process(output, letterbox_info):
    ratio, dw, dh = letterbox_info
    nms_results = non_max_suppression(
            output,
            conf_thres=0.2,
            iou_thres=0.5,
            max_det=1000
        )

    preds = []
    if len(nms_results[0]) > 0:
        for pred in nms_results[0]:
            # undo letterboxing
            pred[0] = (pred[0] - dw) / ratio
            pred[1] = (pred[1] - dh) / ratio
            pred[2] = (pred[2] - dw) / ratio
            pred[3] = (pred[3] - dh) / ratio
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


def run_inference(frame, session):
    img_tensor, letterbox_info = pre_process(frame)
    img_numpy = img_tensor.cpu().numpy()

    input_name = session.get_inputs()[0].name
    output_name = session.get_outputs()[0].name
    preds = session.run([output_name], {input_name: img_numpy})
    output_tensor = torch.from_numpy(preds[0])

    return post_process(output_tensor, letterbox_info)


