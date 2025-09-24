import yaml
import secrets

def generate_key():
    """Generates a new encryption key."""
    return secrets.token_hex(32)

def validate_key(key):
    """Validates the encryption key."""
    if key == "{{GENERATE_YOUR_OWN_KEY}}":
        raise ValueError("Please generate a new encryption key and update your config.yaml file.")
    return key

def load_config(path="config.yaml"):
    """Loads the configuration file."""
    with open(path, 'r') as f:
        config = yaml.safe_load(f)

    # Validate the encryption key
    validate_key(config.get("ENCRYPTION_KEY"))

    return config