import socket

def find_free_port(start_port=8000, end_port=9000):
    """Find the first available port in the given range."""
    for port in range(start_port, end_port + 1):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('127.0.0.1', port))
                return port
        except OSError:
            continue
    return None

if __name__ == "__main__":
    free_port = find_free_port(8000, 9000)
    if free_port:
        print(f"Found free port: {free_port}")
    else:
        print("No free ports found in range 8000-9000")