import time
import yaml
from nav_utils import get_nav_status
from simulate_botcar_navigation import simulate_segment

CONFIG_FILE = "botcar_config.yaml"

def load_config():
    with open(CONFIG_FILE, "r") as f:
        return yaml.safe_load(f)

def send_command_to_botcar(botcar_id, command, payload=None):
    # Placeholder for LoRa or mesh-based message transmission
    print(f"📡 Sending to BotCar-{botcar_id}: {command} | Payload: {payload}")

def monitor_botcar(botcar_id, position):
    status = get_nav_status(position, HOME_LOCATION)
    print(f"🛬 BotCar-{botcar_id} Status → Distance to Home: {status['distance_ft']:.1f}ft, Bearing: {status['bearing_deg']:.1f}°")

def coordinate_mission():
    config = load_config()
    botcar_ids = config.get("botcar_ids", [1, 2, 3])
    waypoints = config["waypoints"]
    deviation = config.get("allowable_heading_deviation", 15)

    for botcar_id in botcar_ids:
        print(f"\n🚦 Launching BotCar-{botcar_id}")
        for i in range(len(waypoints) - 1):
            start = tuple(waypoints[i])
            end = tuple(waypoints[i + 1])
            send_command_to_botcar(botcar_id, "NAVIGATE", {"from": start, "to": end})
            simulate_segment(start, end, deviation)
            monitor_botcar(botcar_id, end)
            time.sleep(1.5)

# Define a home location for recall/status logic
HOME_LOCATION = (33.6846, -117.8265)  # Example: Irvine HQ

if __name__ == "__main__":
    coordinate_mission()
