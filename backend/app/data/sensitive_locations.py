"""
Sensitive locations in California - schools, hospitals, etc.
Data from California Department of Education and public records.

These are locations that require special attention for pesticide drift exposure.
"""

# Sample California schools (would be loaded from CA Dept of Education database)
# Format: (name, lat, lon, type, county)
CALIFORNIA_SCHOOLS = [
    # Fresno County (highest pesticide use)
    ("Fresno High School", 36.7468, -119.7726, "high_school", "FRESNO"),
    ("Roosevelt High School", 36.7652, -119.8442, "high_school", "FRESNO"),
    ("Sunnyside High School", 36.6985, -119.7132, "high_school", "FRESNO"),
    ("Fresno City College", 36.7570, -119.7960, "college", "FRESNO"),
    ("Calwa Elementary", 36.7058, -119.7531, "elementary", "FRESNO"),
    ("Ewing Elementary", 36.7183, -119.7048, "elementary", "FRESNO"),
    ("Malaga Elementary", 36.6763, -119.7547, "elementary", "FRESNO"),
    ("Caruthers Elementary", 36.5427, -119.8333, "elementary", "FRESNO"),
    ("Raisin City Elementary", 36.6047, -119.8983, "elementary", "FRESNO"),
    ("Tranquillity Elementary", 36.6508, -120.2567, "elementary", "FRESNO"),

    # Kern County (second highest)
    ("Bakersfield High School", 35.3769, -119.0187, "high_school", "KERN"),
    ("Arvin High School", 35.1936, -118.8356, "high_school", "KERN"),
    ("McFarland High School", 35.6756, -119.2294, "high_school", "KERN"),
    ("Wasco High School", 35.5942, -119.3406, "high_school", "KERN"),
    ("Shafter High School", 35.5006, -119.2717, "high_school", "KERN"),
    ("Delano High School", 35.7658, -119.2472, "high_school", "KERN"),
    ("Lamont Elementary", 35.2597, -118.9131, "elementary", "KERN"),
    ("Vineland Elementary", 35.3833, -119.1333, "elementary", "KERN"),

    # Tulare County
    ("Tulare Union High School", 36.2078, -119.3472, "high_school", "TULARE"),
    ("Visalia Technical Early College", 36.3302, -119.2921, "high_school", "TULARE"),
    ("Earlimart Elementary", 35.8833, -119.2667, "elementary", "TULARE"),
    ("Pixley Elementary", 35.9667, -119.2833, "elementary", "TULARE"),
    ("Tipton Elementary", 36.0583, -119.3167, "elementary", "TULARE"),

    # Monterey County
    ("Salinas High School", 36.6697, -121.6553, "high_school", "MONTEREY"),
    ("Alisal High School", 36.6528, -121.6192, "high_school", "MONTEREY"),
    ("Greenfield High School", 36.3208, -121.2428, "high_school", "MONTEREY"),
    ("King City High School", 36.2128, -121.1258, "high_school", "MONTEREY"),
    ("Chualar Elementary", 36.5703, -121.5186, "elementary", "MONTEREY"),
    ("Gonzales Elementary", 36.5064, -121.4444, "elementary", "MONTEREY"),

    # Imperial County
    ("Central Union High School", 32.7922, -115.5631, "high_school", "IMPERIAL"),
    ("Brawley Union High School", 32.9786, -115.5306, "high_school", "IMPERIAL"),
    ("Calexico High School", 32.6789, -115.4989, "high_school", "IMPERIAL"),
    ("Heber Elementary", 32.7308, -115.5247, "elementary", "IMPERIAL"),

    # San Joaquin County
    ("Stockton High School", 37.9577, -121.2908, "high_school", "SAN JOAQUIN"),
    ("Lodi High School", 38.1341, -121.2722, "high_school", "SAN JOAQUIN"),
    ("Tracy High School", 37.7397, -121.4252, "high_school", "SAN JOAQUIN"),
    ("Manteca High School", 37.7975, -121.2164, "high_school", "SAN JOAQUIN"),
    ("Escalon Elementary", 37.7967, -120.9972, "elementary", "SAN JOAQUIN"),

    # Ventura County
    ("Oxnard High School", 34.2011, -119.1803, "high_school", "VENTURA"),
    ("Rio Mesa High School", 34.2350, -119.1492, "high_school", "VENTURA"),
    ("Santa Paula High School", 34.3542, -119.0592, "high_school", "VENTURA"),
    ("Fillmore High School", 34.3992, -118.9178, "high_school", "VENTURA"),
]

# Hospitals and medical facilities
HOSPITALS = [
    ("Community Regional Medical Center", 36.7378, -119.7871, "hospital", "FRESNO"),
    ("Kaiser Permanente Fresno", 36.8194, -119.8031, "hospital", "FRESNO"),
    ("Kern Medical", 35.3669, -119.0178, "hospital", "KERN"),
    ("Bakersfield Memorial Hospital", 35.3847, -119.0203, "hospital", "KERN"),
    ("Kaweah Health Medical Center", 36.3308, -119.2911, "hospital", "TULARE"),
    ("Salinas Valley Memorial", 36.6744, -121.6350, "hospital", "MONTEREY"),
    ("Natividad Medical Center", 36.6917, -121.6333, "hospital", "MONTEREY"),
]

# Nursing homes and elder care (vulnerable population)
ELDER_CARE = [
    ("Fresno Nursing Center", 36.7500, -119.7833, "nursing_home", "FRESNO"),
    ("Palm Village Retirement", 36.6833, -119.7500, "retirement", "FRESNO"),
    ("Bakersfield Healthcare Center", 35.3833, -119.0167, "nursing_home", "KERN"),
]

# Parks and recreation areas
PARKS = [
    ("Roeding Park", 36.7431, -119.8181, "park", "FRESNO"),
    ("Woodward Park", 36.8333, -119.7667, "park", "FRESNO"),
    ("Kern River County Park", 35.3500, -118.9833, "park", "KERN"),
    ("Mooney Grove Park", 36.2833, -119.3333, "park", "TULARE"),
]

def get_all_sensitive_locations():
    """Get all sensitive locations as a list of dicts"""
    locations = []

    for name, lat, lon, loc_type, county in CALIFORNIA_SCHOOLS:
        locations.append({
            "name": name,
            "lat": lat,
            "lon": lon,
            "type": loc_type,
            "category": "school",
            "county": county,
            "icon": "school"
        })

    for name, lat, lon, loc_type, county in HOSPITALS:
        locations.append({
            "name": name,
            "lat": lat,
            "lon": lon,
            "type": loc_type,
            "category": "healthcare",
            "county": county,
            "icon": "hospital"
        })

    for name, lat, lon, loc_type, county in ELDER_CARE:
        locations.append({
            "name": name,
            "lat": lat,
            "lon": lon,
            "type": loc_type,
            "category": "healthcare",
            "county": county,
            "icon": "elder"
        })

    for name, lat, lon, loc_type, county in PARKS:
        locations.append({
            "name": name,
            "lat": lat,
            "lon": lon,
            "type": loc_type,
            "category": "recreation",
            "county": county,
            "icon": "park"
        })

    return locations

def get_locations_by_county(county: str):
    """Get sensitive locations for a specific county"""
    all_locs = get_all_sensitive_locations()
    return [loc for loc in all_locs if loc["county"].upper() == county.upper()]

def get_locations_as_geojson(county: str = None, category: str = None):
    """Get locations as GeoJSON FeatureCollection"""
    locations = get_all_sensitive_locations()

    if county:
        locations = [loc for loc in locations if loc["county"].upper() == county.upper()]
    if category:
        locations = [loc for loc in locations if loc["category"] == category]

    features = []
    for loc in locations:
        features.append({
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [loc["lon"], loc["lat"]]
            },
            "properties": {
                "name": loc["name"],
                "type": loc["type"],
                "category": loc["category"],
                "county": loc["county"],
                "icon": loc["icon"]
            }
        })

    return {"type": "FeatureCollection", "features": features}
