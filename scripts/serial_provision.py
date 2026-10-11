"""Virgin-device serial provisioning. Physical recessed button must be held."""
import argparse
import json
import time
from pathlib import Path
import serial

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--port',required=True)
    p.add_argument('--factory',type=Path,required=True)
    a=p.parse_args()
    if a.factory.stat().st_mode & 0o077:raise SystemExit('Factory file must be mode 0600')
    bundle=json.loads(a.factory.read_text())
    # Manufacture identity before electrical sign-off; no output activation by this tool.
    bundle['hardware_ready']=False
    bundle['status_count']=0
    body=json.dumps(bundle,separators=(',',':')).encode()+b'\n'
    if len(body)>6000:raise SystemExit('Factory bundle too large for MCU staging buffer')
    with serial.Serial(a.port,115200,timeout=1,write_timeout=5) as device:
        device.dtr=False;device.rts=False;time.sleep(1)
        device.reset_input_buffer();device.write(body);device.flush()
        deadline=time.monotonic()+10
        while time.monotonic()<deadline:
            reply=device.readline()
            if b'OC:PROVISIONED' in reply:
                print('Factory identity accepted by firmware; electrical activation remains disabled.')
                return
            if b'OC:INVALID' in reply or b'OC:TOO_LARGE' in reply:raise SystemExit('Device refused bundle')
    raise SystemExit('No provisioning acknowledgement; confirm firmware, serial port and physical service hold')

if __name__=='__main__':main()
