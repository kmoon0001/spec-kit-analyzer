from src.utils import generate_key

if __name__ == "__main__":
    new_key = generate_key()
    print(f"Your new encryption key is: {new_key}")
    print("Please update your config.yaml file with this key.")