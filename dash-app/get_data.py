from typing import Dict, List


def _get_item_by_activity(items: List[Dict],
                          activity: str) -> List[Dict]:
    """
    Select items that match (not case sensitive) an activity name
    :param items: item list
    :param activity: activity name
    :return:
    """
    items_out = []
    for item in items:
        for atrib in item['Attributes']:
            if atrib['Name'] == 'activity':
                if atrib['Value'].upper() == activity.upper():
                    items_out.append(item)
                break
    return items_out


def compute_nap_times(items: List[Dict]) -> Dict[str, float]:
    """
    Compute nap times from activity list

    :param items: database items
    :return:
    """
    naps = _get_item_by_activity(items,
                                 'Nap')
    pass
