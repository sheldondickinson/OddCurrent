"""Generate a measured development WLED configuration only after wiring gates."""
import argparse
import json
from pathlib import Path
from profiles import validate_profile, export_map

p=argparse.ArgumentParser()
p.add_argument('--profile',type=Path,required=True)
p.add_argument('--calibration',type=Path,required=True)
p.add_argument('--current-limit-ma',type=int,required=True)
p.add_argument('--out',type=Path,required=True)
a=p.parse_args()
profile=validate_profile(json.loads(a.profile.read_text()),wiring=True)
calibration=json.loads(a.calibration.read_text())
ledmap,regions=export_map(calibration,profile)
if profile['profile_id']!='david-v1' or len(profile['outputs'])!=2:raise SystemExit('This WLED adapter currently accepts David two-output builds only')
if profile['outputs'][0]['key']!='status':raise SystemExit('Protected status must be physical bus0')
types={'WS2812_RGB':22,'SK6812_RGBW':30}
if profile['pixels']['type']=='WS2811_RGB':
    hz=profile['pixels'].get('protocol_hz')
    if hz not in (400000,800000):raise SystemExit('WS2811 timing must be confirmed as 400kHz or 800kHz')
    types['WS2811_RGB']=24 if hz==400000 else 22
if profile['pixels']['type'] not in types:raise SystemExit('Chipset has no tested WLED bus adapter')
orders={'GRB':0,'RGB':1,'BRG':2,'RBG':3,'BGR':4,'GBR':5}
order=profile['pixels'].get('colour_order')
if order not in orders:raise SystemExit('Measured colour order required')
if not 100<=a.current_limit_ma<=15000:raise SystemExit('Current limit outside supported range')
counts=calibration['output_counts'];start=0;outputs=[]
for output in profile['outputs']:
    count=counts[output['key']]
    outputs.append({'pin':[output['gpio']],'start':start,'len':count,'type':types[profile['pixels']['type']],
                    'order':orders[order],'rev':False,'skip':0,'drv':0})
    start+=count
config={'hw':{'led':{'total':start,'maxpwr':a.current_limit_ma,'ledma':60,'ins':outputs}},
        'um':{'OddCurrent':{'hardware_ready':True,'status_count':counts['status']},
              'AudioReactive':{'enabled':True,'digitalmic':{'type':1,'pin':[12,11,10,-1]}}}}
a.out.mkdir(parents=True,exist_ok=False)
for name,data in [('cfg.fragment.json',config),('ledmap.json',ledmap),('regions.json',regions)]:
    (a.out/name).write_text(json.dumps(data,indent=2)+'\n')
print('Validated development configuration generated. Review/import fragment locally; do not replace sec.json or factory identity.')
