import toml

CONFIG_PATH = "config.toml"

def load_config(config_path):
    with open(config_path, "r", encoding="utf-8") as f:
        config = toml.load(f)
    return config