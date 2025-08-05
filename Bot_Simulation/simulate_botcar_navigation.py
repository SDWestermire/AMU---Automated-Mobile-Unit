import yaml
import time
import random
from datetime import datetime
from nav_utils import get_nav_status

def interpolate_path(start, end, steps=5):
    """Returns intermediate GPS points from start to end (inclusive)."""
    lat1, lon1 = start
    lat2, lon2 = end
    path = []
    for i in range(steps):
        ratio = i / (steps - 1)
        lat = lat1 + (lat2 - lat1) * ratio
        lon = lon1 + (lon2 - lon1) * ratio
        path.append((round(lat, 7), round(lon, 7)))
    return path

def simulate_segment(start, end, allowed_deviation_deg, segment_time_sec=180):
    checkpoints = interpolate_path(start, end, steps=5)
    bearing_target = get_nav_status(start, end)['bearing_deg']
    print(f"📍 Navigating segment {start} → {end}")
    print(f"Expected bearing: {bearing_target:.2f}°")

    for i, current_cp in enumerate(checkpoints):
        checkpoint_index = i + 1
        next_cp = checkpoints[i + 1] if i + 1 < len(checkpoints) else end

        for tick in range(4):
            now = datetime.now()
            nav_to_target_wp = get_nav_status(current_cp, end)
            nav_to_cp = get_nav_status(current_cp, current_cp)
            nav_to_next_cp = get_nav_status(current_cp, next_cp)
            nav_to_start_wp = get_nav_status(current_cp, start)
            actual_bearing = nav_to_target_wp['bearing_deg']
            deviation = abs(actual_bearing - bearing_target)

            data_string = (
                f"GPS={current_cp[0]:.6f},{current_cp[1]:.6f}; "
                f"Current_Waypoint=({start[0]:.6f},{start[1]:.6f}); "
                f"→Dist={nav_to_start_wp['distance_ft']:.1f}ft | "
                f"Checkpoint=({current_cp[0]:.6f},{current_cp[1]:.6f}); "
                f"→Dist={nav_to_cp['distance_ft']:.1f}ft | "
                f"Next_Checkpoint=({next_cp[0]:.6f},{next_cp[1]:.6f}); "
                f"→Dist={nav_to_next_cp['distance_ft']:.1f}ft | "
                f"Target_Waypoint=({end[0]:.6f},{end[1]:.6f}); "
                f"→Dist={nav_to_target_wp['distance_ft']:.1f}ft | "
                f"Bearing={actual_bearing:.2f}° | "
                f"Deviation={deviation:.2f}°; "
                f"Timestamp={now.strftime('%Y-%m-%d %H:%M:%S')}"
            )

            print(f"📡 TX to base: {data_string}")
            time.sleep(2)

        if deviation > allowed_deviation_deg:
            print(f"⚠️ Heading correction needed: deviation {deviation:.2f}° > allowed {allowed_deviation_deg}°")
        else:
            print(f"✅ On course: deviation {deviation:.2f}° within allowed {allowed_deviation_deg}°")

        checkpoint_pause = random.uniform(1.0, 3.0)
        print(f"🛑 Pausing {checkpoint_pause:.1f}s at checkpoint {checkpoint_index}...\n")
        time.sleep(checkpoint_pause)
