import torch
import argparse
import yaml
import os

parser = argparse.ArgumentParser()
parser.add_argument(
    "--config",
    type=str,
    required=True,
    help="Path to YAML config file",
)

args = parser.parse_args()
print(args.config)

# load training hyperparams from config.yaml
