import copy
import json
import stat
import subprocess
import sys
from pathlib import Path
import pytest
from scripts.profiles import validate_profile, export_map
from scripts.factory import create, wifi_escape

PROFILE=json.loads(Path('profiles/david-v1.json').read_text())

def measured():
    return {'schema_version':'1.0.0','width':15,'height':13,'output_counts':{'status':2,'body':195},
            'pixels':[{'output':'body','index':i,'zone':'torso','x':i%15,'y':i//15} for i in range(195)]}

def test_two_output_profile_and_physical_gate():
    assert len(validate_profile(PROFILE)['outputs'])==2
    with pytest.raises((AssertionError,ValueError)):validate_profile(PROFILE,wiring=True)

def test_profile_pin_collision_and_reserved():
    for gpio in (4,35,48,19):
        p=copy.deepcopy(PROFILE);p['outputs'][1]['gpio']=gpio
        with pytest.raises((AssertionError,ValueError)):validate_profile(p)

def test_fixture_map_preserves_physical_offset_and_status_exclusion():
    # These coordinates are an algorithm fixture, NOT David measurements.
    ledmap,regions=export_map(measured(),PROFILE)
    assert ledmap['map'][0]==2 and ledmap['map'][-1]==196
    assert not {0,1}.intersection(ledmap['map'])
    assert len(regions['regions']['torso'])==195

def test_exported_map_matches_pinned_wled_streaming_loader(tmp_path):
    measurement=tmp_path/'fixture.json';measurement.write_text(json.dumps(measured()))
    out=tmp_path/'out'
    subprocess.run([sys.executable,'scripts/profiles.py','profiles/david-v1.json','--calibration',str(measurement),'--out',str(out)],check=True)
    raw=(out/'ledmap.json').read_text()
    assert '"map":[' in raw and '"map": [' not in raw
    assert json.loads(raw)['map'][0]==2

@pytest.mark.parametrize('fault',['missing','duplicate-index','duplicate-cell','status','bounds','zone'])
def test_bad_maps(fault):
    m=measured()
    if fault=='missing':m['pixels'].pop()
    if fault=='duplicate-index':m['pixels'][1]['index']=0
    if fault=='duplicate-cell':m['pixels'][1]['x']=0
    if fault=='status':m['pixels'][0]['output']='status'
    if fault=='bounds':m['pixels'][0]['y']=13
    if fault=='zone':m['pixels'][0]['zone']='penis-status'
    with pytest.raises((AssertionError,ValueError)):export_map(m,PROFILE)

def test_unique_factory_bundles_secure_modes_and_nfc(tmp_path):
    ca='-----BEGIN CERTIFICATE-----\nTEST-FIXTURE-ONLY\n-----END CERTIFICATE-----'
    a=create('test-lamp-001','https://lamp.example.invalid','lamp.example.invalid',ca,tmp_path/'one')
    b=create('test-lamp-002','https://lamp.example.invalid','lamp.example.invalid',ca,tmp_path/'two')
    assert a['device_credential']!=b['device_credential'] and a['ap_password']!=b['ap_password']
    assert (tmp_path/'one/nfc-url.txt').read_text()==a['public_url']+'\n'
    assert a['claim_code'] not in (tmp_path/'one/nfc-url.txt').read_text()
    for path in (tmp_path/'one').iterdir():assert stat.S_IMODE(path.stat().st_mode)==0o600
    assert stat.S_IMODE((tmp_path/'one').stat().st_mode)==0o700
    with pytest.raises(FileExistsError):create('test-lamp-001','https://lamp.example.invalid','lamp.example.invalid',ca,tmp_path/'one')

def test_wifi_qr_escaping():
    assert wifi_escape('a;b:c\\d')==r'a\;b\:c\\d'
