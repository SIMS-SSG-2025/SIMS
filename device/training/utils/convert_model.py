import argparse
import torch
import yaml
from ultralytics.nn.tasks import DetectionModel
import subprocess

def export_onnx(model, dummy_input, output_path):
    model.eval()
    torch.onnx.export(model, dummy_input, output_path, do_constant_folding=True)
    print(f"Exported model to ONNX: {output_path}")


def build_trt(onnx_path, trt_path, fp16=True):
    cmd = [
        "trtexec",
        f"--onnx={onnx_path}",
        f"--saveEngine={trt_path}",
        "--explicitBatch",
        "--fp16",
        "--workspace=512",
    ]
    if fp16:
        cmd.append("--fp16")

    print(f"Building TensorRT engine: {' '.join(cmd)}")
    subprocess.run(cmd, check=True)
    print(f"Saved TensorRT engine: {trt_path}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--weights_path", type=str, required=True)
    parser.add_argument("--config", type=str, required=True)
    parser.add_argument("--onnx_path", type=str, required=True)
    parser.add_argument("--trt_path", type=str)
    parser.add_argument("--build_trt", action="store_true")
    parser.add_argument("--fp16", action="store_true")
    args = parser.parse_args()

    model_path = args.weights_path
    model_config = args.config
    with open(model_config, 'r') as file:
        model_config = yaml.safe_load(file)

    num_classes = model_config["nc"]
    model = DetectionModel(cfg=model_config, nc=num_classes)
    model.load_state_dict(torch.load(model_path, map_location=lambda storage, loc: storage))

    dummy_input = torch.randn(1, 3, 640, 640).half()

    export_onnx(model, dummy_input, args.onnx_path)

    if args.build_trt:
        build_trt(args.onnx_path, args.trt_path, fp16=args.fp16)



# usage: .\utils\convert_model.py --weights_path models/yolo_ppe.pth --config models/yolo11_ppe_cfg.yaml --onnx_path models/yolo_ppe.onnx --trt_path yolo_ppe.trt --build_trt --fp16




