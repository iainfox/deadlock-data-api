"""Simple breakdown counts used for the end-of-run console summary."""

from collections import Counter


def summarize(items):
    """Return (tier_counts, slot_counts, activation_counts) for a dict of
    item records, each a dict sorted/ready for display."""
    tiers = Counter(item['tier'] for item in items.values())
    slots = Counter(item['slot'] for item in items.values())
    activations = Counter(item['activation'] for item in items.values())
    return dict(sorted(tiers.items())), dict(slots), dict(activations)
