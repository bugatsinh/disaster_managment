def normalize_phone(phone):
    """Normalize a phone number to digits for comparison."""
    digits = ''.join(character for character in (phone or '') if character.isdigit())
    if len(digits) >= 10:
        return digits[-10:]
    return digits


def _location_tokens(location):
    location_lower = (location or '').strip().lower()
    if not location_lower:
        return set()

    cleaned = location_lower.replace(',', ' ').replace('-', ' ')
    return {
        token
        for token in cleaned.split()
        if len(token) > 2
    }


def location_similarity(origin, destination):
    """Return a higher score when two location strings are more similar."""
    origin_lower = (origin or '').strip().lower()
    destination_lower = (destination or '').strip().lower()
    if not origin_lower or not destination_lower:
        return 0

    if origin_lower == destination_lower:
        return 1000

    if origin_lower in destination_lower or destination_lower in origin_lower:
        return 500 + min(len(origin_lower), len(destination_lower))

    origin_tokens = _location_tokens(origin_lower)
    destination_tokens = _location_tokens(destination_lower)
    if not origin_tokens or not destination_tokens:
        return 0

    shared_tokens = origin_tokens & destination_tokens
    if not shared_tokens:
        return 0

    return len(shared_tokens) * 20 + sum(len(token) for token in shared_tokens)


def distance_rank_label(score):
    """Convert a similarity score into a human-readable distance label."""
    if score >= 500:
        return 'Very near you'
    if score >= 80:
        return 'Near you'
    if score >= 30:
        return 'Moderate distance'
    if score > 0:
        return 'Farther away'
    return 'Distance unknown'


def sort_by_nearest(origin, items, location_key='location'):
    """Sort items nearest to farthest from the origin location."""
    scored_items = []
    for item in items:
        location_value = item[location_key] if isinstance(item, dict) else getattr(item, location_key)
        score = location_similarity(origin, location_value)
        scored_items.append((score, item))

    scored_items.sort(key=lambda entry: (-entry[0], entry[1].get('id', 0) if isinstance(entry[1], dict) else 0))
    return [
        {
            **item,
            'distance_score': score,
            'distance_label': distance_rank_label(score),
        }
        for score, item in scored_items
    ]
