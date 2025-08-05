import yaml
import time
import random
from datetime import datetime
from simulate_botcar_navigation import simulate_segment

def load_config(path="botcar_config.yaml"):
    """Load botcar configuration from YAML file."""
    with open(path, "r") as file:
        return yaml.safe_load(file)

def run_simulation(config):
    """Run full navigation simulation with pacing delays."""
    waypoints = config["waypoints"]
    deviation_limit = config.get("allowable_heading_deviation", 10)
    botcar_id = config.get("node_id", "Unknown")

    print(f"\n?? Initiating simulation for BotCar {botcar_id}")
    sim_start_time = datetime.now()
    print(f"?? Start Time: {sim_start_time.strftime('%Y-%m-%d %H:%M:%S')}\n")

    for i in range(len(waypoints) - 1):
        wp_start = tuple(waypoints[i])
        wp_end = tuple(waypoints[i + 1])

        # Run segment simulation
        simulate_segment(
            start=wp_start,
            end=wp_end,
            allowed_deviation_deg=deviation_limit,
            segment_time_sec=180  # 3 minutes per segment
        )

        # ?? Variable pacing between segments
        sleep_interval = random.uniform(3.0, 3.0)
        print(f"?? Pausing {sleep_interval:.1f}s before starting next segment...\n")
        time.sleep(sleep_interval)

    sim_end_time = datetime.now()
    duration = (sim_end_time - sim_start_time).total_seconds()
    print(f"\n? Simulation complete at {sim_end_time.strftime('%H:%M:%S')}")
    print(f"?? Total Duration: {duration:.2f} seconds")

def main():
    config = load_config()
    run_simulation(config)

if __name__ == "__main__":
    main()
