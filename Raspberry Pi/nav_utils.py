<<<<<<< HEAD
import math

EARTH_RADIUS_MI = 3958.8
FT_PER_MI = 5280

def haversine_distance(lat1, lon1, lat2, lon2):
    """Calculate distance in feet between two lat/lon pairs."""
    # Convert degrees to radians
    lat1_rad, lon1_rad = math.radians(lat1), math.radians(lon1)
    lat2_rad, lon2_rad = math.radians(lat2), math.radians(lon2)

    # Haversine formula
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad
    a = math.sin(dlat / 2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    distance_miles = EARTH_RADIUS_MI * c
    return distance_miles * FT_PER_MI

def calculate_bearing(lat1, lon1, lat2, lon2):
    """Calculate compass bearing from (lat1, lon1) to (lat2, lon2)."""
    lat1_rad, lat2_rad = math.radians(lat1), math.radians(lat2)
    dlon_rad = math.radians(lon2 - lon1)

    x = math.sin(dlon_rad) * math.cos(lat2_rad)
    y = math.cos(lat1_rad) * math.sin(lat2_rad) - \
        math.sin(lat1_rad) * math.cos(lat2_rad) * math.cos(dlon_rad)

    bearing_rad = math.atan2(x, y)
    bearing_deg = (math.degrees(bearing_rad) + 360) % 360
    return bearing_deg

def get_nav_status(current_pos, target_pos):
    """Return distance and bearing from current GPS to target waypoint."""
    lat1, lon1 = current_pos
    lat2, lon2 = target_pos
    distance = haversine_distance(lat1, lon1, lat2, lon2)
    bearing = calculate_bearing(lat1, lon1, lat2, lon2)
    return {
        "distance_ft": round(distance, 2),
        "bearing_deg": round(bearing, 2)
    }

# Example usage
if __name__ == "__main__":
    current = (33.686379, -117.789652)
    target = (33.686636, -117.789790)
    nav = get_nav_status(current, target)
    print(f"Distance: {nav['distance_ft']} ft, Bearing: {nav['bearing_deg']}°")
=======
import math

EARTH_RADIUS_MI = 3958.8
FT_PER_MI = 5280

def haversine_distance(lat1, lon1, lat2, lon2):
    """Calculate distance in feet between two lat/lon pairs."""
    # Convert degrees to radians
    lat1_rad, lon1_rad = math.radians(lat1), math.radians(lon1)
    lat2_rad, lon2_rad = math.radians(lat2), math.radians(lon2)

    # Haversine formula
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad
    a = math.sin(dlat / 2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    distance_miles = EARTH_RADIUS_MI * c
    return distance_miles * FT_PER_MI

def calculate_bearing(lat1, lon1, lat2, lon2):
    """Calculate compass bearing from (lat1, lon1) to (lat2, lon2)."""
    lat1_rad, lat2_rad = math.radians(lat1), math.radians(lat2)
    dlon_rad = math.radians(lon2 - lon1)

    x = math.sin(dlon_rad) * math.cos(lat2_rad)
    y = math.cos(lat1_rad) * math.sin(lat2_rad) - \
        math.sin(lat1_rad) * math.cos(lat2_rad) * math.cos(dlon_rad)

    bearing_rad = math.atan2(x, y)
    bearing_deg = (math.degrees(bearing_rad) + 360) % 360
    return bearing_deg

def get_nav_status(current_pos, target_pos):
    """Return distance and bearing from current GPS to target waypoint."""
    lat1, lon1 = current_pos
    lat2, lon2 = target_pos
    distance = haversine_distance(lat1, lon1, lat2, lon2)
    bearing = calculate_bearing(lat1, lon1, lat2, lon2)
    return {
        "distance_ft": round(distance, 2),
        "bearing_deg": round(bearing, 2)
    }

# Example usage
if __name__ == "__main__":
    current = (33.686379, -117.789652)
    target = (33.686636, -117.789790)
    nav = get_nav_status(current, target)
    print(f"Distance: {nav['distance_ft']} ft, Bearing: {nav['bearing_deg']}°")
>>>>>>> bb5aae96ba06986ab46e1ab2a686263b376c0df3
