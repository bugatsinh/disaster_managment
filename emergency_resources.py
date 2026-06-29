GOVERNMENT_CONTACTS = {
    'medical': {
        'name': 'Emergency Medical Services',
        'number': '102',
        'description': 'Ambulance and medical emergency',
    },
    'fire': {
        'name': 'Fire Department',
        'number': '101',
        'description': 'Fire and rescue services',
    },
    'police': {
        'name': 'Police',
        'number': '100',
        'description': 'Law enforcement and public safety',
    },
    'disaster': {
        'name': 'Disaster Management',
        'number': '108',
        'description': 'Natural disaster and emergency response',
    },
    'accident': {
        'name': 'Traffic Police',
        'number': '100',
        'description': 'Road accident and traffic emergency',
    },
    'natural_disaster': {
        'name': 'Disaster Management Authority',
        'number': '1070',
        'description': 'Earthquake, flood, and natural disaster',
    },
    'violence': {
        'name': 'Police',
        'number': '100',
        'description': 'Violence and crime reporting',
    },
    'missing_person': {
        'name': 'Police',
        'number': '100',
        'description': 'Missing person report',
    },
}

DRASTIC_EVENT_KEYWORDS = [
    'cataclysm', 'cataclism', 'catastrophe', 'catastrophic', 'drastic', 'disaster',
    'emergency', 'crisis', 'calamity', 'tragedy', 'evacuation', 'collapse',
    'explosion', 'earthquake', 'flood', 'flooding', 'tsunami', 'landslide',
    'cyclone', 'hurricane', 'storm', 'wildfire', 'fire outbreak', 'building collapse',
    'bridge collapse', 'gas leak', 'chemical spill', 'mass casualty', 'pandemic',
    'epidemic', 'outbreak', 'terror', 'terrorist', 'bomb', 'hostage', 'riot',
    'stampede', 'drought', 'severe', 'critical', 'life-threatening', 'trapped',
    'buried', 'missing', 'stranded', 'homeless', 'destroyed', 'devastation',
]

PROBLEM_KEYWORD_MAP = {
    'medical': ['medical', 'injury', 'injured', 'sick', 'health', 'hospital', 'ambulance'],
    'fire': ['fire', 'burn', 'smoke', 'wildfire', 'blaze'],
    'accident': ['accident', 'crash', 'collision', 'traffic', 'vehicle'],
    'violence': ['violence', 'attack', 'assault', 'crime', 'robbery', 'hostage'],
    'natural_disaster': [
        'flood', 'earthquake', 'landslide', 'storm', 'disaster', 'cyclone',
        'hurricane', 'tsunami', 'drought', 'cataclysm', 'cataclism', 'catastrophe',
    ],
    'missing_person': ['missing', 'lost', 'abduction', 'kidnap'],
}

SHELTERS_AND_CENTERS = [
    {
        'name': 'Central Disaster Relief Shelter',
        'areas': ['central', 'downtown', 'city center', 'main city', 'metro'],
        'address': 'Central Civic Relief Center, Main District',
        'phone': '1070',
        'type': 'Disaster Relief Shelter',
        'capacity': '500+ people',
    },
    {
        'name': 'North Zone Emergency Shelter',
        'areas': ['north', 'northern', 'uptown', 'north zone', 'north side'],
        'address': 'North Community Hall, Relief Block A',
        'phone': '108',
        'type': 'Emergency Shelter',
        'capacity': '300 people',
    },
    {
        'name': 'South Zone Helping Center',
        'areas': ['south', 'southern', 'south zone', 'south side', 'suburb south'],
        'address': 'South District Relief Camp, Sector 12',
        'phone': '108',
        'type': 'Helping Center',
        'capacity': '250 people',
    },
    {
        'name': 'East Emergency Response Center',
        'areas': ['east', 'eastern', 'east zone', 'east side', 'industrial east'],
        'address': 'East Emergency Hub, Industrial Area Road',
        'phone': '101',
        'type': 'Fire & Rescue Center',
        'capacity': '200 people',
    },
    {
        'name': 'West Community Shelter',
        'areas': ['west', 'western', 'west zone', 'west side', 'coastal west'],
        'address': 'West Community Center, Riverside Avenue',
        'phone': '108',
        'type': 'Community Shelter',
        'capacity': '350 people',
    },
    {
        'name': 'Delhi NCR Relief Shelter',
        'areas': ['delhi', 'new delhi', 'ncr', 'gurgaon', 'gurugram', 'noida', 'faridabad'],
        'address': 'NDMA Relief Point, Rajpath Area, New Delhi',
        'phone': '1070',
        'type': 'Disaster Relief Shelter',
        'capacity': '800+ people',
    },
    {
        'name': 'Mumbai Coastal Relief Center',
        'areas': ['mumbai', 'bombay', 'andheri', 'bandra', 'dadar', 'thane', 'navi mumbai'],
        'address': 'Mumbai Disaster Management Center, Bandra East',
        'phone': '108',
        'type': 'Coastal Relief Center',
        'capacity': '600 people',
    },
    {
        'name': 'Bangalore Urban Shelter',
        'areas': ['bangalore', 'bengaluru', 'whitefield', 'koramangala', 'electronic city'],
        'address': 'BBMP Emergency Shelter, MG Road Zone',
        'phone': '108',
        'type': 'Urban Relief Shelter',
        'capacity': '400 people',
    },
    {
        'name': 'Chennai Flood Relief Center',
        'areas': ['chennai', 'madras', 't nagar', 'adyar', 'anna nagar'],
        'address': 'Tamil Nadu State Relief Camp, Egmore',
        'phone': '1070',
        'type': 'Flood Relief Center',
        'capacity': '500 people',
    },
    {
        'name': 'Kolkata Emergency Shelter',
        'areas': ['kolkata', 'calcutta', 'howrah', 'salt lake', 'park street'],
        'address': 'Kolkata Municipal Relief Shelter, Park Circus',
        'phone': '108',
        'type': 'Emergency Shelter',
        'capacity': '450 people',
    },
    {
        'name': 'General National Relief Helpline',
        'areas': [],
        'address': 'Nearest district relief office (contact 1070 for routing)',
        'phone': '1070',
        'type': 'National Helpline',
        'capacity': 'Varies by district',
    },
]


def is_drastic_event(problem, medical_emergency='no'):
    """Return True when the report describes a catastrophe or drastic emergency."""
    if not problem:
        return False

    problem_lower = problem.lower()
    if any(keyword in problem_lower for keyword in DRASTIC_EVENT_KEYWORDS):
        return True

    return medical_emergency == 'yes' and any(
        word in problem_lower
        for word in ['emergency', 'critical', 'severe', 'injury', 'injured', 'hurt', 'bleeding']
    )


def get_government_contacts(problem_keyword):
    """Return government contacts matched to the reported problem."""
    if not problem_keyword:
        return []

    problem_lower = problem_keyword.lower()
    contacts = [
        GOVERNMENT_CONTACTS[key]
        for key, keywords in PROBLEM_KEYWORD_MAP.items()
        if any(word in problem_lower for word in keywords)
    ]

    if not contacts:
        contacts = [GOVERNMENT_CONTACTS['police'], GOVERNMENT_CONTACTS['disaster']]

    unique_contacts = []
    seen = set()
    for contact in contacts:
        if contact['number'] not in seen:
            seen.add(contact['number'])
            unique_contacts.append(contact)

    return unique_contacts


def get_all_helplines():
    """Return the main emergency helpline numbers for victims to call immediately."""
    priority_keys = ['police', 'fire', 'medical', 'disaster', 'natural_disaster']
    helplines = []
    seen = set()

    for key in priority_keys:
        contact = GOVERNMENT_CONTACTS[key]
        if contact['number'] not in seen:
            seen.add(contact['number'])
            helplines.append(contact)

    return helplines


def _location_match_score(location_lower, areas):
    """Score how well a shelter matches a free-text location."""
    if not location_lower:
        return 0

    score = 0
    for area in areas:
        area_lower = area.lower()
        if area_lower in location_lower:
            score += len(area_lower)

    location_tokens = [token for token in location_lower.replace(',', ' ').split() if len(token) > 2]
    for token in location_tokens:
        for area in areas:
            if token in area.lower() or area.lower() in token:
                score += 3

    return score


def find_nearest_shelter(location):
    """Find the best-matching shelter or helping center for a location string."""
    location_lower = (location or '').strip().lower()
    best_match = None
    best_score = -1

    for shelter in SHELTERS_AND_CENTERS:
        if not shelter['areas']:
            continue
        score = _location_match_score(location_lower, shelter['areas'])
        if score > best_score:
            best_score = score
            best_match = shelter

    if best_match is None or best_score == 0:
        fallback = next(
            (shelter for shelter in SHELTERS_AND_CENTERS if not shelter['areas']),
            SHELTERS_AND_CENTERS[-1],
        )
        return {
            **fallback,
            'match_note': 'No exact local match found. Contact the national helpline for the nearest center.',
        }

    return {
        **best_match,
        'match_note': f'Matched to your location: {location}',
    }


def get_emergency_resources(problem, location, medical_emergency='no'):
    """Build helplines and optional shelter info after a victim submits a report."""
    contacts = get_government_contacts(problem)
    if medical_emergency == 'yes':
        medical = GOVERNMENT_CONTACTS['medical']
        if not any(contact['number'] == medical['number'] for contact in contacts):
            contacts.insert(0, medical)

    drastic = is_drastic_event(problem, medical_emergency)
    resources = {
        'is_drastic_event': drastic,
        'government_contacts': contacts,
        'location': location,
        'problem_summary': problem[:180] + ('...' if len(problem) > 180 else ''),
    }

    if drastic:
        resources['nearest_shelter'] = find_nearest_shelter(location)

    return resources
