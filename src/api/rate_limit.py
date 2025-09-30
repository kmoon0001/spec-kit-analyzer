from slowapi import Limiter
from slowapi.util import get_remote_address

# Shared global Limiter instance for the API
# Default global limit can be tuned as needed.
limiter = Limiter(key_func=get_remote_address, default_limits=["100 per minute"]) 

__all__ = ["limiter"]
