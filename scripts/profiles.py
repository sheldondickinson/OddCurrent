"""Validate hardware declarations and export measured sparse XY maps."""
import argparse
import json
from pathlib import Path

RESERVED = {0, 3, 19, 20, 45, 46, 48, *range(26, 38)}

def validate_profile(profile, wiring=False):
    if not (profile['schema_version'] == '1.0.0'): raise ValueError('unsupported profile schema')
    if not (profile['profile_id'].replace('-', '').isalnum()): raise ValueError('invalid profile ID')
    pins = [o['gpio'] for o in profile['outputs']] + [b['gpio'] for b in profile['buttons']]
    mic = profile['hardware'].get('microphone')
    if mic:
        pins += [mic[k] for k in ('sck_gpio', 'ws_gpio', 'sd_gpio')]
    if not (len(pins) == len(set(pins))): raise ValueError('peripheral pin collision')
    if not (all(type(p) is int and 0 <= p <= 48 and p not in RESERVED for p in pins)): raise ValueError('reserved GPIO')
    if not (len({x['key'] for x in profile['outputs']}) == len(profile['outputs'])): raise ValueError('duplicate output')
    statuses = [o for o in profile['outputs'] if o.get('priority') == 'system-overrides-effects']
    if not (len(statuses) == 1 and statuses[0]['key'] == 'status'): raise ValueError('one protected status required')
    zones = [z for o in profile['outputs'] for z in o['zones']]
    if not (len(zones) == len(set(zones))): raise ValueError('duplicate logical zone')
    if wiring:
        gates={'carrier','pixels','concurrent_peripherals','electrical','thermal'}
        if not gates.issubset(profile['validation']) or any(profile['validation'][g] is not True for g in gates):
            raise ValueError('physical validation gates incomplete')
        if not (profile['pixels']['voltage_v'] is not None and 'UNKNOWN' not in profile['pixels']['type']): raise ValueError('pixel specification unknown')
    return profile

def export_map(calibration, profile):
    validate_profile(profile)
    if not (calibration['schema_version'] == '1.0.0'): raise ValueError('unsupported map schema')
    width, height = calibration['width'], calibration['height']
    if not (type(width) is int and type(height) is int and 1 <= width <= 128 and 1 <= height <= 128): raise ValueError('invalid dimensions')
    counts = calibration['output_counts']
    if not (set(counts) == {o['key'] for o in profile['outputs']}): raise ValueError('all outputs require actual counts')
    if not (all(type(c) is int and 1 <= c <= 1000 for c in counts.values())): raise ValueError('invalid count')
    if not (counts['status'] in (1, 2)): raise ValueError('David status count')
    offsets, total = {}, 0
    for output in profile['outputs']:
        offsets[output['key']] = total
        total += counts[output['key']]
    if not (profile['pixels']['estimated_total_min'] <= total <= profile['pixels']['estimated_total_max']): raise ValueError('unexpected count: revise measured profile')
    grid = [-1] * (width * height)
    physical, regions = set(), {}
    for led in calibration['pixels']:
        output = next((x for x in profile['outputs'] if x['key'] == led['output']), None)
        if not (output and output['key'] != 'status'): raise ValueError('status excluded from decorative map')
        i, x, y = led['index'], led['x'], led['y']
        if not (all(type(n) is int for n in (i, x, y))): raise ValueError('integer coordinates/index required')
        if not (0 <= i < counts[output['key']] and 0 <= x < width and 0 <= y < height): raise ValueError('out of bounds')
        if not (led['zone'] in output['zones']): raise ValueError('unknown zone')
        absolute = offsets[output['key']] + i
        if not (absolute not in physical and grid[y * width + x] == -1): raise ValueError('duplicate pixel/cell')
        physical.add(absolute); grid[y * width + x] = absolute
        regions.setdefault(led['zone'], []).append(absolute)
    if not (len(physical) == total - counts['status']): raise ValueError('every decorative pixel must be measured')
    return {'width': width, 'height': height, 'map': grid}, {'schema_version': '1.0.0', 'regions': regions, 'status_count': counts['status'], 'total': total}

def main():
    p = argparse.ArgumentParser()
    p.add_argument('profile', type=Path)
    p.add_argument('--wiring', action='store_true')
    p.add_argument('--calibration', type=Path)
    p.add_argument('--out', type=Path)
    a = p.parse_args()
    profile = validate_profile(json.loads(a.profile.read_text()), a.wiring)
    if a.calibration:
        if not a.out: p.error('--out required')
        ledmap, regions = export_map(json.loads(a.calibration.read_text()), profile)
        a.out.mkdir(parents=True, exist_ok=True)
        # Pinned WLED's streaming loader searches for the exact token '"map":['.
        (a.out / 'ledmap.json').write_text(json.dumps(ledmap,separators=(',',':')) + '\n')
        (a.out / 'regions.json').write_text(json.dumps(regions) + '\n')
    print('Profile valid' + (' for physical wiring' if a.wiring else '; wiring approval remains separate'))

if __name__ == '__main__': main()
