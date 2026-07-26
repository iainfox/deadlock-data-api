from collections import Counter


def summarize(heroes):
    avail = Counter(item.get('available_in', 'unknown') for item in heroes.values())
    total_abilities = sum(
        len(item.get('abilities', {}))
        for item in heroes.values()
    )
    return dict(avail), total_abilities
