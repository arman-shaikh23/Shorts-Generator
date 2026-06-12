import sys
import os

# Ensure we can import main
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from main import app
from starlette.routing import Mount, Route

def print_routes():
    print("=== Route Table ===")
    for route in app.routes:
        if isinstance(route, Mount):
            print(f"Mount: {route.path} -> {route.name}")
        elif isinstance(route, Route):
            print(f"Route: {route.path} [{', '.join(route.methods)}]")
        else:
            print(f"Other: {route}")

if __name__ == "__main__":
    print_routes()
