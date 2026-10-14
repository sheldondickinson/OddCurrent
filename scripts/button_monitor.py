"""Read fixed OddCurrent button inputs over native serial JSON; never set GPIOs."""
import argparse
import json
import time

import serial


def button_snapshot(document):
    """Accept only the explicit button diagnostic schema, ignoring all other info."""
    info = document.get('info', {}).get('oddcurrent', {})
    if info.get('button_diagnostics_version') != 1:
        raise ValueError('Installed firmware does not expose button diagnostics')
    rows = info.get('button_inputs', [])
    if len(rows) != 4 or {row.get('gpio') for row in rows} != {13, 14, 15, 16}:
        raise ValueError('Unexpected button pin set')
    result = []
    for row in sorted(rows, key=lambda r: r['gpio']):
        if type(row.get('level')) is not int or row['level'] not in (0, 1):
            raise ValueError('Invalid input level')
        if type(row.get('allocated')) is not bool:
            raise ValueError('Missing input allocation status')
        result.append({'gpio': row['gpio'], 'level': row['level'],
                       'pressed': row['level'] == 0, 'allocated': row['allocated']})
    return result


def read_info(device, timeout=2):
    device.write(b'{"v":true}\n')
    device.flush()
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        line = device.readline()
        try:
            document = json.loads(line)
        except (ValueError, UnicodeDecodeError):
            continue
        if isinstance(document, dict) and isinstance(document.get('info'), dict):
            return document
    raise RuntimeError('No native serial info response')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', required=True)
    parser.add_argument('--seconds', type=int, default=60)
    args = parser.parse_args()
    if not 1 <= args.seconds <= 300:
        parser.error('Duration must be 1–300 seconds')
    # Set control lines before opening to avoid intentionally resetting the board.
    device = serial.Serial(port=None, baudrate=115200, timeout=0.1, write_timeout=2)
    device.dtr = False
    device.rts = False
    device.port = args.port
    device.open()
    changes = {pin: 0 for pin in (13, 14, 15, 16)}
    previous = None
    started = time.monotonic()
    try:
        device.reset_input_buffer()
        while time.monotonic() - started < args.seconds:
            current = button_snapshot(read_info(device))
            if current != previous:
                if previous is not None:
                    for old, new in zip(previous, current):
                        if old['level'] != new['level']:
                            changes[new['gpio']] += 1
                print(json.dumps({'elapsed_s': round(time.monotonic() - started, 2),
                                  'inputs': current}), flush=True)
                previous = current
            time.sleep(0.2)
        print(json.dumps({'transitions': changes}), flush=True)
    finally:
        device.close()


if __name__ == '__main__':
    main()
