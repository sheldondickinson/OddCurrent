const $=id=>document.getElementById(id);
let session=null,fleet=[],selected=null,pending=false;
const date=value=>value?new Date(value*1000).toLocaleString():'Never';
const bytes=value=>value==null?'Not reported':`${Math.round(value/1024).toLocaleString()} KiB`;
const duration=value=>value==null?'Not reported':`${Math.floor(value/86400)}d ${Math.floor(value%86400/3600)}h ${Math.floor(value%3600/60)}m`;
const status=d=>d.online?(d.reported.error_code?'Fault':'Online'):d.last_seen?'Offline':'Never connected';
const attention=d=>!d.online || !!d.reported.error_code || !d.reported.lighting_ready;
function notice(message){$('notice').textContent=message;$('notice').hidden=!message;}
async function api(path,options={}){
 const response=await fetch(path,{...options,headers:{'Content-Type':'application/json','X-CSRF-Token':session?.csrf||'',...options.headers}});
 if(!response.ok){let error;try{error=await response.json();}catch{}throw new Error(error?.detail||`Request failed (${response.status})`);}
 return response.json();
}
function textElement(tag,text,className){const el=document.createElement(tag);el.textContent=text;if(className)el.className=className;return el;}
function current(){return fleet.find(d=>d.id===selected);}
function fact(label,value,href){const term=textElement('dt',label),desc=document.createElement('dd');if(href){const a=textElement('a',value);a.href=href;a.target='_blank';a.rel='noopener noreferrer';desc.append(a);}else desc.textContent=value??'Not reported';$('deviceFacts').append(term,desc);}
function badge(d){return 'c313-badge '+(d.online?(d.reported.error_code?'c313-status--critical':'c313-status--success'):'c313-status--unavailable');}
function render(){
 $('totalCount').textContent=fleet.length;$('onlineCount').textContent=fleet.filter(d=>d.online).length;
 $('attentionCount').textContent=fleet.filter(attention).length;$('unclaimedCount').textContent=fleet.filter(d=>!d.claimed).length;
 const focusedCard=document.activeElement?.closest('.fleet-card')?.dataset.device;
 $('fleetCards').replaceChildren();const query=$('search').value.toLowerCase(),filter=$('filter').value;
 const visible=fleet.filter(d=>`${d.id} ${d.profile} ${d.reported.firmware||''}`.toLowerCase().includes(query)).filter(d=>filter==='all'||filter==='online'&&d.online||filter==='offline'&&!d.online||filter==='attention'&&attention(d));
 $('empty').hidden=visible.length>0;
 for(const d of visible){const r=d.reported,button=document.createElement('button');button.className='fleet-card c313-card';button.type='button';button.dataset.device=d.id;button.setAttribute('aria-pressed',String(d.id===selected));button.setAttribute('aria-label',`${d.id} · ${status(d)}`);
 button.append(textElement('span',status(d),badge(d)),textElement('h3',d.name),textElement('span',d.id,'serial'),textElement('p',`${r.local_ip||'IP awaiting telemetry'} · ${r.rssi==null?'Wi-Fi not reported':r.rssi+' dBm'}`),textElement('p',`Last seen ${date(d.last_seen)}`),textElement('p',`${r.firmware||'Firmware not reported'} · ${d.claimed?'Claimed':'Unclaimed'}`));
 button.onclick=()=>{selected=d.id;history.replaceState(null,'','/admin?device='+encodeURIComponent(d.id));render();};$('fleetCards').append(button);}
 if(focusedCard)[...$('fleetCards').children].find(el=>el.dataset.device===focusedCard)?.focus({preventScroll:true});
 const d=current();$('devicePanel').hidden=!d;if(!d)return;
 const r=d.reported;$('deviceName').textContent=d.name;$('deviceIdentity').textContent=d.id+' / '+d.profile;$('deviceStatus').textContent=status(d);$('deviceStatus').className=badge(d);
 $('controlsLink').href='/d/'+encodeURIComponent(d.id);$('mappingLink').href='/calibrate?device='+encodeURIComponent(d.id);
 $('deviceFacts').replaceChildren();fact('Local IP',r.local_ip,r.local_ip?'http://'+r.local_ip+'/':null);fact('Last seen',date(d.last_seen));fact('Firmware',r.firmware);fact('Uptime',duration(r.uptime_s));fact('Wi-Fi signal',r.rssi==null?'Not reported':r.rssi+' dBm');fact('Reconnects',r.reconnects);fact('Free heap',bytes(r.free_heap));fact('Free PSRAM',bytes(r.free_psram));fact('Device error',r.management_protocol===1?r.error_code:'Not reported');fact('Lighting',r.lighting_ready?'Enabled':'Setup required');fact('Hardware acceptance',r.hardware_ready?'Complete':'Prototype · testing pending');fact('Pixels',r.pixel_count==null?'Not reported':`${r.pixel_count} total / ${r.status_count} status / ${r.body_count} body`);fact('Status display',r.status_display);fact('Anatomical regions',r.zones_ready?'Mapped':'Needs calibration');fact('2D projection',r.xy_ready?'Mapped':'Needs calibration');
 const maintenance=d.online&&r.management_protocol===1&&!pending;
 $('requestDiagnostics').disabled=$('restart').disabled=!maintenance;$('identify').disabled=!maintenance||!r.lighting_ready;
 $('music').disabled=pending||!d.online||!r.lighting_ready;$('music').textContent=r.music?'Disable Music':'Enable Music';
 $('audioMeter').value=r.audio_level||0;$('audioValue').textContent=r.management_protocol!==1?'Not reported':r.audio_active?`${r.audio_level}/255 · window peak ${r.audio_peak}`:'Processing off';
 $('audioStatus').textContent=!d.online?'Offline · showing the last reported values.':r.audio_active?'Processing enabled. Compare quiet and sound; a nonzero or pinned reading alone does not prove the microphone works.':'Enable Music to collect real audio-module level diagnostics. No simulated input is used for this meter.';
 $('actionStatus').textContent=pending?'Waiting for the device acknowledgement…':!d.online?'Offline. Remote actions are not queued.':r.management_protocol!==1?'Firmware update required for identify, restart and fresh diagnostics.':'Actions expire if they cannot reach the device. Identify stops automatically.';
 $('commands').replaceChildren();for(const c of d.recent_commands){$('commands').append(textElement('li',`#${c.seq} ${c.status} · ${JSON.stringify(c.payload)}`));}
 $('events').replaceChildren();for(const e of d.events)$('events').append(textElement('li',`${date(e.at)} · ${e.kind}`));
 $('ownership').textContent=`${d.claimed?'Ownership claimed.':'Unclaimed; no owner account assigned.'} ${d.guest_count} active guest session(s).`;$('revokeGuests').disabled=pending;
}
async function refresh(){fleet=await api('/api/admin/devices');if(!fleet.some(d=>d.id===selected))selected=fleet[0]?.id;render();$('updated').textContent='Updated '+new Date().toLocaleTimeString();}
async function command(path,payload){if(pending||!current())return;const id=current().id;pending=true;render();try{const c=await api(path,{method:'POST',body:JSON.stringify(payload)});let result=c.status;for(let n=0;n<22&&result==='pending';n++){await new Promise(resolve=>setTimeout(resolve,500));result=(await api(`/api/devices/${encodeURIComponent(id)}/commands/${c.id}`)).status;}if(result!=='applied')throw new Error(`Device command ${result==='pending'?'timed out':result}`);notice('Device acknowledged the action.');await refresh();}catch(error){notice(error.message);}finally{pending=false;render();}}
const action=name=>{const d=current();if(d)return command(`/api/admin/devices/${encodeURIComponent(d.id)}/actions`,{action:name});};
$('requestDiagnostics').onclick=()=>action('refresh');$('identify').onclick=()=>action('identify');$('restart').onclick=()=>{if(confirm(`Restart ${current().id}? Wi-Fi and identity are retained. The lamp will briefly disconnect.`))action('reboot');};
$('music').onclick=()=>{const d=current();if(d)command(`/api/devices/${encodeURIComponent(d.id)}/commands`,d.reported.music?{music:false}:{on:true,music:true,brightness:12});};
$('revokeGuests').onclick=async()=>{const d=current();if(!d||!confirm(`Expire all guest sessions and unused invitations for ${d.id}?`))return;try{await api(`/api/devices/${encodeURIComponent(d.id)}/guests`,{method:'DELETE'});notice('Guest access revoked.');await refresh();}catch(e){notice(e.message);}};
$('download').onclick=()=>{const d=current();if(!d)return;const u=URL.createObjectURL(new Blob([JSON.stringify({exported_at:new Date().toISOString(),device:d},null,2)],{type:'application/json'}));const a=document.createElement('a');a.href=u;a.download=d.id+'-diagnostics.json';a.click();URL.revokeObjectURL(u);};
$('logout').onclick=async()=>{try{await api('/api/logout',{method:'POST'});location.href='/';}catch(e){notice(e.message);}};
$('refresh').onclick=()=>refresh().catch(e=>notice(e.message));$('search').oninput=$('filter').onchange=render;
async function start(){try{session=await api('/api/session');if(session.role!=='admin')throw new Error('Administrator access required');selected=new URLSearchParams(location.search).get('device');await refresh();setInterval(()=>{if(!pending&&!document.hidden)refresh().catch(e=>notice(e.message));},5000);}catch(e){notice(e.message);}}
start();
