import pygeohash as pgh

def geohash_neighbors(user_lat, user_lng, precision=5):
    # Precision 5 creates a geographical bounding box roughly 5km x 5km.
    # Adjust to 6 (~1.2km) if your data density is incredibly tight (e.g., downtown core)
    center_geohash = pgh.encode(user_lat, user_lng, precision=precision)
    
    # Expand calculates the center geohash box AND all 8 adjacent bordering boxes
    top = pgh.get_adjacent(center_geohash, 'top')
    bottom = pgh.get_adjacent(center_geohash, 'bottom')
    left = pgh.get_adjacent(center_geohash, 'left')
    right = pgh.get_adjacent(center_geohash, 'right')

    # The 4 diagonal adjacent blocks
    top_right = pgh.get_adjacent(right, 'top')
    top_left = pgh.get_adjacent(left, 'top')
    bottom_right = pgh.get_adjacent(right, 'bottom')
    bottom_left = pgh.get_adjacent(left, 'bottom')

    # Collect all 8 neighbors in a list
    neighborhood_boxes = [
        center_geohash, top, bottom, left, right, 
        top_right, top_left, bottom_right, bottom_left
    ]
    return neighborhood_boxes