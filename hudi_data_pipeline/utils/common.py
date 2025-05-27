import yaml


def get_config(path):
    with open(path, "r") as f:
        return yaml.safe_load(f)