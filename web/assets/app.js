const $ = id => document.getElementById(id);
let session = null, lamp = null, fleet = [], pending = false;
const names = {gallery:'Gallery White',sunset:'Sunset',blue:'Electric Blue',spectrum:'Spectrum',pulse:'Pulse',music:'Music'};
const accents = {gallery:'#e5d7b2',sunset:'#ff805a',blue:'#5bc8e8',spectrum:'#be9bef',pulse:'#b6e37a',music:'#be9bef'};
function notice(text) { $('notice').textContent = text; $('notice').hidden = !text; }
async function api(path, options={}) {
  const headers = {...options.headers};
  if (options.body) headers['Content-Type'] = 'application/json';
  if (session?.csrf) headers['X-CSRF-Token'] = session.csrf;
  const response = await fetch(path, {...options,headers});
  if (!response.ok) {
    let error; try { error=await response.json(); } catch {}
    throw new Error(typeof error?.detail==='string' ? error.detail : `Request failed (${response.status})`);
  }
  return response.headers.get('content-type')?.includes('json') ? response.json() : {};
}
function metric(label, value) {
  const term=document.createElement('dt'), desc=document.createElement('dd');
  term.textContent=label; desc.textContent=value ?? 'Not reported'; $('diagnostics').append(term,desc);
}
function render() {
  const r=lamp?.reported || {}, online=!!lamp?.online;
  const canControl=!!session && online && !pending;
  $('connection').textContent=lamp?.demo ? 'Local simulator' : online ? 'Connected' : 'Offline';
  $('connection').className='chip'+(online?' online':'');
  $('serial').textContent=lamp?.id || 'Your illuminated companion';
  $('access').hidden=!!session && !!lamp;
  $('advanced').hidden=session?.role!=='owner' || !lamp;
  $('power').disabled=$('brightness').disabled=$('music').disabled=!canControl;
  $('power').setAttribute('aria-pressed',String(!!r.on));
  $('power').setAttribute('aria-label',r.on?'Turn David off':'Turn David on');
  $('music').setAttribute('aria-checked',String(!!r.music));
  if(document.activeElement!==$('brightness')) $('brightness').value=r.brightness || 65;
  $('brightnessValue').textContent=r.brightness ? `${r.brightness}%` : '—';
  $('sensitivity').value=r.sensitivity || 50; $('sensitivityValue').textContent=`${r.sensitivity || 50}%`;
  $('statusBrightness').value=r.status_brightness || 5; $('statusValue').textContent=`${r.status_brightness || 5}%`;
  for(const button of document.querySelectorAll('[data-scene]')) {
    button.disabled=!canControl;
    button.setAttribute('aria-pressed',String(r.scene===button.dataset.scene));
  }
  $('statue').style.filter=`drop-shadow(0 0 32px ${accents[r.scene] || '#5bc8e8'}44)`;
  for(const id of ['sensitivity','statusBrightness']) $(id).disabled=!canControl;
  $('zoneApply').disabled=!canControl || !r.zones_ready;
  $('zoneStatus').textContent=r.zones_ready?'Measured regions available.':'Physical calibration required for independent zones.';
  $('commandStatus').textContent=pending?'Waiting for the lamp to acknowledge…':!session?'Sign in to control your lamp.':!online?'Lamp offline. Local buttons still work; cloud changes are not queued.':lamp.demo?'SIMULATOR · Changes affect this preview only.':'Ready when you are.';
  $('diagnostics').replaceChildren();
  metric('Device',lamp?.id); metric('Firmware',r.firmware); metric('Wi-Fi signal',r.rssi==null?null:`${r.rssi} dBm`);
  metric('Last seen',lamp?.last_seen ? new Date(lamp.last_seen*1000).toLocaleString() : null);
  metric('Boot reason',r.boot_reason); metric('Reconnects',r.reconnects); metric('2D map',r.xy_ready?'Calibrated':'Needs calibration');
  $('releaseStatus').textContent='Updates stay unavailable until hardware acceptance and signed release validation. Scheduling is planned for a later release.';
}
async function refresh() {
  if(!session)return;
  fleet=await api('/api/devices');
  const match=location.pathname.match(/^\/d\/([a-z0-9-]+)$/);
  lamp=match ? fleet.find(d=>d.id===match[1]) : fleet[0];
  if(match && !lamp)notice('This lamp is not in your account. Use the private ownership code to claim it, or accept its owner’s invitation.');
  render();
  $('deviceList').replaceChildren();
  for(const device of fleet) {
    const link=document.createElement('a');link.className='device-card';link.href='/d/'+encodeURIComponent(device.id);
    const title=document.createElement('h3');title.textContent=device.name;
    const identity=document.createElement('p');identity.textContent=device.id;
    const status=document.createElement('p');status.textContent=device.demo?'Local simulator':device.online?'Connected':`Offline · ${device.last_seen ? 'last seen '+new Date(device.last_seen*1000).toLocaleString() : 'never connected'}`;
    link.append(title,identity,status);$('deviceList').append(link);
  }
}
async function send(payload) {
  if(!lamp || pending)return;
  pending=true;render();
  try {
    const cmd=await api(`/api/devices/${lamp.id}/commands`,{method:'POST',body:JSON.stringify(payload)});
    let status=cmd.status;
    for(let i=0;i<22 && status==='pending';i++) {
      await new Promise(resolve=>setTimeout(resolve,500));
      status=(await api(`/api/devices/${lamp.id}/commands/${cmd.id}`)).status;
    }
    if(status!=='applied')throw new Error(status==='pending'?'No acknowledgement received':`Lamp command ${status}`);
    notice(lamp.demo?'Applied in the local simulator.': 'Lamp acknowledged the change.');
    await refresh();
  } catch(error) { notice(error.message); }
  finally { pending=false;render(); }
}
$('power').onclick=()=>send({on:!lamp.reported.on});
$('brightness').oninput=()=>{$('brightnessValue').textContent=$('brightness').value+'%';};
$('brightness').onchange=()=>send({brightness:Number($('brightness').value)});
$('music').onclick=()=>send({music:!lamp.reported.music});
for(const button of document.querySelectorAll('[data-scene]'))button.onclick=()=>send({scene:button.dataset.scene});
for(const [id,key,out] of [['sensitivity','sensitivity','sensitivityValue'],['statusBrightness','status_brightness','statusValue']]) {
  $(id).oninput=()=>{$(out).textContent=$(id).value+'%';};
  $(id).onchange=()=>send({[key]:Number($(id).value)});
}
$('zoneApply').onclick=()=>{
  if(!$('zone').value)return notice('Choose an anatomical zone.');
  send({zone:$('zone').value,scene:lamp.reported.scene || 'gallery'});
};
$('fleetButton').onclick=()=>{$('fleet').hidden=!$('fleet').hidden;if(!$('fleet').hidden)$('fleet').scrollIntoView({behavior:'smooth'});};
$('claimButton').onclick=()=>{$('claimSerial').value=location.pathname.split('/')[2]||'';$('claimDialog').showModal();};
$('closeClaim').onclick=()=>$('claimDialog').close();
$('claimForm').onsubmit=async event=>{
  event.preventDefault();
  if(!session)return $('claimStatus').textContent='Sign in before claiming your lamp.';
  const id=$('claimSerial').value;
  try {
    await api(`/api/devices/${encodeURIComponent(id)}/claim`,{method:'POST',body:JSON.stringify({code:$('claimCode').value})});
    $('claimCode').value='';location.href='/d/'+encodeURIComponent(id);
  } catch(error) { $('claimStatus').textContent=error.message; }
};
$('invite').onclick=async()=>{
  try {
    const data=await api(`/api/devices/${lamp.id}/invites`,{method:'POST',body:JSON.stringify({hours:24})});
    $('inviteUrl').hidden=false;$('inviteUrl').value=data.url;$('inviteUrl').select();
    $('permissionStatus').textContent='Copy this private one-time link to your guest. It expires in 24 hours.';
  } catch(error){notice(error.message);}
};
$('revoke').onclick=async()=>{
  try { await api(`/api/devices/${lamp.id}/guests`,{method:'DELETE'});$('inviteUrl').hidden=true;$('permissionStatus').textContent='Guest access revoked.'; }
  catch(error){notice(error.message);}
};
$('events').onclick=async()=>{
  try {
    const events=await api(`/api/devices/${lamp.id}/events`);$('eventList').replaceChildren();
    for(const event of events){const li=document.createElement('li');li.textContent=`${new Date(event.at*1000).toLocaleString()} · ${event.kind}`;$('eventList').append(li);}
  }catch(error){notice(error.message);}
};
$('demo').onclick=async()=>{
  try {
    await api('/api/demo/login',{method:'POST'});session=await api('/api/session');
    await api('/api/demo/connect',{method:'POST'});await refresh();notice('LOCAL SIMULATOR · No physical lamp is connected.');
  }catch(error){notice(error.message);}
};

// Calibration starts with an empty grid. No coordinates are treated as measurements.
let pixels=[], width=24,height=48;
for(const option of $('zone').options)if(option.value)$('mapZone').append(option.cloneNode(true));
function drawMap() {
  const grid=$('mapGrid');grid.replaceChildren();grid.style.gridTemplateColumns=`repeat(${width},minmax(18px,1fr))`;
  for(let y=0;y<height;y++)for(let x=0;x<width;x++) {
    const led=pixels.find(p=>p.x===x&&p.y===y),button=document.createElement('button');button.type='button';button.setAttribute('role','gridcell');
    button.setAttribute('aria-label',`Column ${x}, row ${y}${led?`, body pixel ${led.index}, ${led.zone}`:', empty'}`);
    button.textContent=led?led.index:'';if(led)button.className='assigned';
    button.onclick=()=>{
      const index=Number($('mapIndex').value),count=Number($('mapCount').value);
      if(!Number.isInteger(index)||index<0||index>=count)return notice('Pixel index is outside the measured body count.');
      pixels=pixels.filter(p=>p.index!==index&&!(p.x===x&&p.y===y));
      pixels.push({output:'body',index,zone:$('mapZone').value,x,y});
      $('mapIndex').value=Math.min(count-1,index+1);drawMap();
    };grid.append(button);
  }
  $('mapProgress').textContent=`${pixels.length} of ${$('mapCount').value} decorative pixels measured. Status is excluded.`;
}
$('mapReset').onclick=()=>{
  const w=Number($('mapWidth').value),h=Number($('mapHeight').value);
  if(!Number.isInteger(w)||!Number.isInteger(h)||w<1||h<1||w>128||h>128)return notice('Dimensions must be whole numbers between 1 and 128.');
  width=w;height=h;pixels=[];drawMap();
};
$('mapExport').onclick=()=>{
  const map={schema_version:'1.0.0',width,height,output_counts:{status:Number($('mapStatus').value),body:Number($('mapCount').value)},pixels};
  const url=URL.createObjectURL(new Blob([JSON.stringify(map,null,2)],{type:'application/json'}));
  const link=document.createElement('a');link.href=url;link.download='david-measurements.json';link.click();URL.revokeObjectURL(url);
  notice('Measurements exported. Run scripts/profiles.py to validate completeness and generate the WLED map.');
};
$('mapImport').onchange=async event=>{
  try {
    const file=event.target.files[0];if(!file)return;if(file.size>250000)throw new Error('Measurement file too large');
    const map=JSON.parse(await file.text());
    if(map.schema_version!=='1.0.0'||!Number.isInteger(map.width)||!Number.isInteger(map.height)||map.width<1||map.height<1||map.width>128||map.height>128||!Array.isArray(map.pixels))throw new Error('Invalid measurement file');
    for(const p of map.pixels)if(p.output!=='body'||![p.x,p.y,p.index].every(Number.isInteger)||p.x<0||p.x>=map.width||p.y<0||p.y>=map.height||p.index<0||p.index>=map.output_counts.body||![...$('mapZone').options].some(o=>o.value===p.zone))throw new Error('Invalid pixel coordinate or zone');
    width=map.width;height=map.height;pixels=map.pixels;$('mapWidth').value=width;$('mapHeight').value=height;$('mapCount').value=map.output_counts.body;$('mapStatus').value=map.output_counts.status;drawMap();
  }catch(error){notice(error.message);}
};
async function start() {
  if(location.pathname==='/calibrate'){$('calibration').hidden=false;drawMap();}
  if(location.pathname==='/invite') {
    const token=location.hash.slice(1);history.replaceState(null,'','/invite');
    if(token){try{await api('/api/invites/redeem',{method:'POST',body:JSON.stringify({code:token})});location.href='/';return;}catch(error){notice(error.message);}}
  }
  try { const health=await api('/healthz');$('demo').hidden=health.mode!=='demo'; }catch{}
  try { session=await api('/api/session');await refresh(); }
  catch(error) { if(session)notice(error.message);render(); }
  if(location.pathname.startsWith('/pair/')) {
    notice('Setup uses the unique Wi-Fi QR on the base. Join that network, then open http://4.3.2.1. This page does not collect home Wi-Fi passwords.');
  }
  setInterval(()=>{if(session&&!pending)refresh().catch(error=>notice(error.message));},15000);
}
start();
