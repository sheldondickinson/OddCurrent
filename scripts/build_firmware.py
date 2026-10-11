"""Prepare exact WLED source and two bounded integration hooks, then compile."""
import argparse
import json
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def replace_once(path, old, new):
    text = path.read_text()
    if new in text: return
    if text.count(old) != 1: raise RuntimeError(f'Upstream hook moved in {path.name}')
    path.write_text(text.replace(old, new))

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--source', type=Path, default=ROOT / '.local/WLED')
    p.add_argument('--prepare-only', action='store_true')
    a = p.parse_args(); source = a.source.resolve()
    lock = json.loads((ROOT / 'firmware/upstream.json').read_text())
    if not source.exists():
        subprocess.run(['git','clone','--depth','1','--branch','v'+lock['version'],lock['repository'],str(source)], check=True)
    revision = subprocess.check_output(['git','-C',str(source),'rev-parse','HEAD'], text=True).strip()
    if revision != lock['revision']: raise SystemExit('upstream revision mismatch')
    shutil.copy(ROOT / 'firmware/platformio_override.ini', source / 'platformio_override.ini')
    shutil.copytree(ROOT / 'firmware/usermods/oddcurrent', source / 'usermods/oddcurrent', dirs_exist_ok=True)
    replace_once(source/'wled00/FX_fcn.cpp', '  BusManager::show();', '''  #ifdef ODDCURRENT_BRIDGE
  extern void oddcurrentBeforeBusShow();
  oddcurrentBeforeBusShow(); // physical overlay after XY mapping; independent status brightness
  #endif
  BusManager::show();''')
    replace_once(source/'wled00/wled.cpp', '  handleSerial();', '''  #ifdef ODDCURRENT_BRIDGE
  extern bool oddcurrentFactorySerial();
  if (!oddcurrentFactorySerial()) handleSerial();
  #else
  handleSerial();
  #endif''')
    replace_once(source/'wled00/wled_server.cpp', '  server.on("/", HTTP_GET, [](AsyncWebServerRequest *request) {', '''  server.on("/", HTTP_GET, [](AsyncWebServerRequest *request) {
    #ifdef ODDCURRENT_BRIDGE
    extern bool oddcurrentSetupRoot(AsyncWebServerRequest*);
    if(oddcurrentSetupRoot(request)) return;
    #endif''')
    if a.prepare_only: return
    subprocess.run(['pio', 'run', '-d', str(source), '-e', lock['environment']], check=True)
    dest = ROOT / 'firmware/build'; dest.mkdir(exist_ok=True)
    for name in ('firmware.bin','bootloader.bin','partitions.bin'):
        file = source / '.pio/build' / lock['environment'] / name
        if file.exists(): shutil.copy(file, dest/name)
    print('Development firmware compiled; hardware, signing and OTA acceptance remain pending.')

if __name__ == '__main__': main()
