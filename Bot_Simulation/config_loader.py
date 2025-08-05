import yaml

def load_yaml_config(file_path):
    with open(file_path, 'r') as f:
        return yaml.safe_load(f)

# Example usage:
# config = load_yaml_config("mission.yaml")
