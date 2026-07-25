from collections import Counter


def summarize(items):
    tiers = Counter(item['tier'] for item in items.values())
    slots = Counter(item['slot'] for item in items.values())
    activations = Counter(item['activation'] for item in items.values())
    return dict(sorted(tiers.items())), dict(slots), dict(activations)
