import yaml
import time
from simulate_botcar_navigation import simulate_segment
from nav_utils import get_nav_status

CONFIG_FILE = "botcar_config.yaml"

def load_config():
    with open(CONFIG_FILE, "r") as f:
        return yaml.safe_load(f)

def run_full_route():
    config = load_config()
    print("🚗 Simulating full route...")
    deviation = config.get("allowable_heading_deviation", 15)
    waypoints = config["waypoints"]

    for i in range(len(waypoints) - 1):
        start = tuple(waypoints[i])
        end = tuple(waypoints[i + 1])
        simulate_segment(start, end, deviation)
        time.sleep(1.5)

def run_from_waypoint():
    config = load_config()
    waypoints = config["waypoints"]
    deviation = config.get("allowable_heading_deviation", 15)

    try:
        index = int(input(f"Enter starting waypoint index (0–{len(waypoints)-1}): "))
        if index < 0 or index >= len(waypoints) - 1:
            print("Invalid index.")
            return
        simulate_segment(tuple(waypoints[index]), tuple(waypoints[index + 1]), deviation)
    except ValueError:
        print("Please enter a valid integer.")

def simulate_recall():
    config = load_config()
    waypoints = config["waypoints"]
    deviation = config.get("allowable_heading_deviation", 15)

    print("🔁 Recalling botCar to Home...")
    for i in reversed(range(1, len(waypoints))):
        start = tuple(waypoints[i])
        end = tuple(waypoints[i - 1])
        simulate_segment(start, end, deviation)
        time.sleep(1.5)

def launch_multiple_botcars():
    config = load_config()
    count = int(input("Number of botCars to launch: "))
    interval = float(input("Launch interval (sec): "))
    deviation = config.get("allowable_heading_deviation", 15)
    waypoints = config["waypoints"]

    for c in range(count):
        print(f"\n🚀 Launching botCar {c+1}")
        for i in range(len(waypoints) - 1):
            start = tuple(waypoints[i])
            end = tuple(waypoints[i + 1])
            simulate_segment(start, end, deviation)
            time.sleep(1.0)
        time.sleep(interval)

def preview_waypoints():
    config = load_config()
    waypoints = config["waypoints"]
    current_position = tuple(waypoints[0])  # assume starting at first waypoint

    print(f"\n📍 Preview from current position: {current_position}")
    for i, wp in enumerate(waypoints[1:], start=1):
        status = get_nav_status(current_position, tuple(wp))
        print(f"Waypoint {i}: {wp} → Distance: {status['distance_ft']:.1f}ft, Bearing: {status['bearing_deg']:.1f}°")
