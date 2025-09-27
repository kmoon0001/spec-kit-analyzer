import secrets

if __name__ == "__main__":
    # Generate a 32-byte (256-bit) random key and represent it as a hex string
    new_key = secrets.token_hex(32)
    print(f"Your new encryption key is: {new_key}")
    print("Please copy this key and update your config.yaml file.")
