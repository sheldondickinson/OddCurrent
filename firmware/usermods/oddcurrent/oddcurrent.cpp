#include "wled.h"
#include <Preferences.h>
#include <WiFiClientSecure.h>
#include <WebSocketsClient.h>
#include "policy.h"

using oddcurrent::Action;
using oddcurrent::Status;

class OddCurrent : public Usermod {
  WebSocketsClient socket;
  Preferences factory;
  Preferences state;
  oddcurrent::Button keys[4];
  String serial, credential, ca, broker, session, serialBuffer;
  uint64_t lastSeq = 0;
  uint32_t lastTelemetry = 0, lastFrame = 0, nextConnect = 0, reconnects = 0;
  uint32_t backoff = 1000, warningUntil = 0, successUntil = 0;
  uint32_t stateChanged = 0, lastStateSave = 0;
  bool stateDirty = false;
  uint8_t pins[4] = {13,14,15,16}, statusCount = 0, statusBrightness = 5;
  uint8_t scene = 0, sensitivity = 50, favourite = 0;
  bool updating = false, cloud = false, music = false, ready = false, attempted = false, dirty = true;
  bool zonesReady = false, xyReady = false;
  struct Region { String name; std::vector<uint16_t> pixels; uint8_t scene=0, brightness=100; bool active=false, on=true; };
  std::vector<Region> regions;
  int8_t brightnessDirection = 1;
  static constexpr const char* scenes[6] = {"gallery","sunset","blue","spectrum","pulse","music"};

  void audio() {
    JsonDocument doc;
    JsonObject root = doc.to<JsonObject>();
    root["AudioReactive"]["enabled"] = music;
    root["AudioReactive"]["inputLevel"] = map(sensitivity,1,100,1,255);
    UsermodManager::readFromJsonState(root);
  }

  void applyScene(uint8_t n) {
    scene = n % 6;
    for(auto &r:regions)r.active=false;
    for (unsigned i=0; i<strip.getSegmentsNum(); ++i) {
      auto &seg=strip.getSegment(i);
      if (!seg.isActive()) continue;
      seg.setMode(scene==3 ? FX_MODE_RAINBOW : scene==4 ? FX_MODE_BREATH : scene==5 ? FX_MODE_FREQWAVE : FX_MODE_STATIC);
      seg.colors[0] = scene==1 ? RGBW32(255,85,35,0) : scene==2 ? RGBW32(20,100,255,0) : RGBW32(255,215,170,0);
      seg.speed=100; seg.intensity=128;
    }
    music=scene==5; audio(); colorUpdated(CALL_MODE_BUTTON); dirty=true;
  }

  bool command(JsonObject cmd) {
    if (!ready || !cloud || cmd["capability"] != "lighting") return false;
    uint32_t now = uint32_t(time(nullptr));
    uint64_t seq = cmd["seq"].as<uint64_t>();
    if (!oddcurrent::accept(seq,lastSeq,cmd["expires"],now,session==cmd["session"].as<String>(),updating)) return false;
    JsonObject p=cmd["payload"];
    if (p.isNull()) return false;
    if(p.containsKey("zone")) {
      if(!zonesReady)return false;
      Region* region=nullptr;
      String zone=p["zone"].as<String>();
      for(auto &r:regions)if(r.name==zone)region=&r;
      if(!region)return false;
      for(JsonPair v:p) {
        const char* k=v.key().c_str();
        if(strcmp(k,"zone") && strcmp(k,"on") && strcmp(k,"brightness") && strcmp(k,"scene"))return false;
      }
      if(p.containsKey("brightness")){int b=p["brightness"];if(b<1||b>100)return false;region->brightness=b;}
      if(p["on"].is<bool>())region->on=p["on"];
      if(p.containsKey("scene")) {
        String key=p["scene"].as<String>();int match=-1;
        for(int i=0;i<6;++i)if(key==scenes[i])match=i;
        if(match<0 || match==5)return false; // independent region audio routing needs a tested WLED segment adapter
        region->scene=match;
      }
      region->active=true;lastSeq=seq;dirty=true;return true;
    }
    for (JsonPair v:p) {
      const char* k=v.key().c_str();
      if (strcmp(k,"on") && strcmp(k,"brightness") && strcmp(k,"scene") && strcmp(k,"music") && strcmp(k,"sensitivity") && strcmp(k,"status_brightness")) return false;
    }
    if (p["on"].is<bool>()) {
      if (!p["on"].as<bool>()) { if (bri) briLast=bri; bri=0; }
      else bri=briLast ? briLast : 128;
    }
    if (p.containsKey("brightness")) {
      int b=p["brightness"];
      if (b<1 || b>100) return false;
      briLast=map(b,1,100,3,255); if (bri) bri=briLast;
    }
    if (p.containsKey("scene")) {
      String n=p["scene"].as<String>(); int match=-1;
      for(int i=0;i<6;++i) if(n==scenes[i]) match=i;
      if(match<0) return false;
      applyScene(match);
    }
    if (p["music"].is<bool>()) { music=p["music"]; audio(); if(music) applyScene(5); else if(scene==5) applyScene(0); }
    if (p.containsKey("sensitivity")) { int s=p["sensitivity"]; if(s<1||s>100)return false; sensitivity=s; audio(); }
    if (p.containsKey("status_brightness")) { int s=p["status_brightness"]; if(s<1||s>20)return false; statusBrightness=s; }
    lastSeq=seq; colorUpdated(CALL_MODE_DIRECT_CHANGE); dirty=true; return true;
  }

  void event(WStype_t type, uint8_t* payload, size_t length) {
    if(type==WStype_DISCONNECTED) {
      cloud=false; session=""; attempted=false;
      nextConnect=millis()+backoff+(esp_random()%1000);
      backoff=std::min(uint32_t(60000),backoff*2); return;
    }
    if(type!=WStype_TEXT || length>2048) return;
    JsonDocument doc;
    if(deserializeJson(doc,payload,length)) return;
    String kind=doc["type"].as<String>();
    if(kind=="hello" && doc["protocol"]==1) {
      session=doc["session"].as<String>();
      if(session.length()!=32)return;
      // Broker time is accepted only inside certificate-verified TLS.
      timeval tv={doc["time"].as<long>(),0}; settimeofday(&tv,nullptr);
      lastSeq=0; cloud=true; backoff=1000; dirty=true; successUntil=millis()+1800;
    } else if(kind=="command" && cloud) {
      bool ok=command(doc.as<JsonObject>());
      JsonDocument ack; ack["type"]="ack"; ack["id"]=doc["id"]; ack["seq"]=doc["seq"];
      ack["status"]=ok?"applied":"rejected";
      String text; serializeJson(ack,text); socket.sendTXT(text);
    }
  }

  void telemetry() {
    JsonDocument d;
    d["type"]="telemetry"; d["on"]=bri>0;
    d["brightness"]=constrain(map(bri?bri:briLast,3,255,1,100),1,100);
    d["scene"]=scenes[scene]; d["music"]=music; d["sensitivity"]=sensitivity;
    d["status_brightness"]=statusBrightness; d["rssi"]=WiFi.RSSI();
    d["firmware"]="16.0.1-oddcurrent-0.1.0";
    d["boot_reason"]=String(int(esp_reset_reason())); d["reconnects"]=reconnects;
    d["uptime_s"]=millis()/1000;
    d["zones_ready"]=zonesReady; d["xy_ready"]=xyReady;
    String text; serializeJson(d,text); socket.sendTXT(text); lastTelemetry=millis(); dirty=false;
  }

  void button(uint8_t b, Action a) {
    if(a==Action::none)return;
    if(b==3) {
      if(a==Action::setup_ap) { WLED::instance().initAP(); warningUntil=0; }
      if(a==Action::wifi_clear_warning) warningUntil=millis()+2500;
      if(a==Action::clear_wifi) {
        multiWiFi.clear(); multiWiFi.emplace_back("", "");
        serializeConfigSec(); // only WLED Wi-Fi store; OddCurrent factory namespace retained
        WiFi.disconnect(false,true); WLED::instance().initAP();
      }
      return;
    }
    if(b==0) {
      if(a==Action::short_press) { if(bri) {briLast=bri;bri=0;} else bri=briLast?briLast:128; }
      if(a==Action::double_press) bri=briLast=13;
      if(a==Action::long_press || a==Action::repeat) {
        int value=int(bri?bri:briLast)+brightnessDirection*13;
        if(value>=255){value=255;brightnessDirection=-1;}
        if(value<=3){value=3;brightnessDirection=1;}
        bri=briLast=value;
      }
    } else if(b==1) {
      if(a==Action::short_press)applyScene((scene+1)%6);
      if(a==Action::long_press)applyScene((scene+5)%6);
      if(a==Action::double_press)applyScene(favourite);
    } else {
      if(a==Action::short_press) { music=!music; if(music)applyScene(5);else applyScene(0); }
      if(a==Action::long_press) { sensitivity=sensitivity>=100?25:sensitivity+25; audio(); }
      if(a==Action::double_press) { applyScene(5); strip.getMainSegment().palette++; }
    }
    colorUpdated(CALL_MODE_BUTTON); dirty=true;
  }

public:
  void setup() override {
    factory.begin("oddcurrent",false);
    serial=factory.getString("serial",""); credential=factory.getString("credential","");
    ca=factory.getString("ca",""); broker=factory.getString("broker","");
    ready=ready || factory.getBool("ready",false);
    statusCount=std::max(statusCount,factory.getUChar("status",0));
    for(uint8_t p:pins) if(pinManager.allocatePin(p,false,PinOwner::UM_Unspecified)) pinMode(p,INPUT_PULLUP);
    if(serial.length()) {
      strlcpy(cmDNS,serial.c_str(),sizeof(cmDNS));
      strlcpy(apSSID,factory.getString("apssid").c_str(),sizeof(apSSID));
      strlcpy(apPass,factory.getString("appass").c_str(),sizeof(apPass));
      // WLED owns connection testing and captive DNS; password is unique per factory bundle.
      serializeConfigSec();
    } else {
      // No shared public factory setup password on an unprovisioned development image.
      snprintf(apPass,sizeof(apPass),"%08lx%08lx",(unsigned long)esp_random(),(unsigned long)esp_random());
    }
    socket.onEvent([this](WStype_t t,uint8_t* p,size_t n){event(t,p,n);});
    state.begin("oc-state",false);
    if(state.isKey("scene")) {
      applyScene(state.getUChar("scene",0));
      briLast=state.getUChar("brightness",128);
      bri=state.getBool("on",false)?briLast:0;
      sensitivity=state.getUChar("sensitivity",50);
      statusBrightness=state.getUChar("status_bri",5);
      music=state.getBool("music",false);audio();
      colorUpdated(CALL_MODE_INIT);
    }
  }

  // Trusted-LAN configuration gate. Tooling creates this only after profile validation.
  bool readFromConfig(JsonObject& root) override {
    JsonObject cfg=root["OddCurrent"];
    if(!cfg.isNull()) {
      ready=cfg["hardware_ready"]|false;
      statusCount=cfg["status_count"]|0;
    }
    return true;
  }

  void addToConfig(JsonObject& root) override {
    root["OddCurrent"]["hardware_ready"]=ready;
    root["OddCurrent"]["status_count"]=statusCount;
  }

  void connected() override {
    configTime(0,0,"pool.ntp.org","time.cloudflare.com");
    if(ready && !regions.size() && WLED_FS.exists("/regions.json")) {
      File file=WLED_FS.open("/regions.json","r");JsonDocument d;
      if(deserializeJson(d,file)){file.close();return;}file.close();
      if(d["schema_version"]!="1.0.0" || int(d["status_count"])!=statusCount)return;
      std::vector<uint16_t> seen;
      JsonObject masks=d["regions"];
      for(JsonPair pair:masks) {
        Region r;r.name=pair.key().c_str();
        if(r.name=="penis-status")return;
        for(JsonVariant v:pair.value().as<JsonArray>()) {
          if(!v.is<unsigned>())return;
          unsigned index=v.as<unsigned>();
          if(index<statusCount || index>=strip.getLengthTotal() || std::find(seen.begin(),seen.end(),index)!=seen.end())return;
          seen.push_back(index);r.pixels.push_back(index);
        }
        regions.push_back(r);
      }
      zonesReady=seen.size()==strip.getLengthTotal()-statusCount;
      if(!zonesReady)regions.clear();
      xyReady=zonesReady && WLED_FS.exists("/ledmap.json");
    }
  }

  void loop() override {
    uint32_t now=millis();
    for(int b=0;b<4;++b) button(b,keys[b].tick(digitalRead(pins[b])==LOW,now,b==3,updating));
    if(!updating && ready && WLED_CONNECTED && serial.length() && credential.length() && ca.length()) {
      if(!attempted && int32_t(now-nextConnect)>=0) {
        // NEVER setInsecure. Public-root CA + hostname validation and SNTP are required.
        if(time(nullptr)<1700000000) return;
        String path="/ws/devices/"+serial;
        String header="Authorization: Bearer "+credential;
        socket.setExtraHeaders(header.c_str());
        socket.beginSslWithCA(broker.c_str(),443,path.c_str(),ca.c_str());
        socket.setReconnectInterval(60000); socket.enableHeartbeat(15000,5000,2);
        attempted=true; ++reconnects;
      }
      socket.loop();
      if(cloud && (dirty || uint32_t(now-lastTelemetry)>15000))telemetry();
    } else if(attempted) { socket.disconnect(); cloud=false; attempted=false; }
    if(ready && statusCount && uint32_t(now-lastFrame)>80 && !strip.isUpdating() && !updating) {
      strip.trigger(); lastFrame=now;
    }
    // Save only settled changes, no more than once a minute; NVS is wear-levelled.
    if(!updating && stateDirty && uint32_t(now-stateChanged)>10000 && uint32_t(now-lastStateSave)>60000) {
      state.putUChar("scene",scene);state.putUChar("brightness",bri?bri:briLast);
      state.putBool("on",bri>0);state.putBool("music",music);
      state.putUChar("sensitivity",sensitivity);state.putUChar("status_bri",statusBrightness);
      stateDirty=false;lastStateSave=now;
    }
  }

  bool handleButton(uint8_t b) override { return b<4; } // prevent duplicate native gestures
  void onUpdateBegin(bool init) override { updating=init; if(init)socket.disconnect(); }
  void onStateChange(uint8_t) override { dirty=true;stateDirty=true;stateChanged=millis(); }
  void addToJsonInfo(JsonObject& obj) override {
    obj["oddcurrent"]["serial"]=serial;
    obj["oddcurrent"]["hardware_ready"]=ready;
    obj["oddcurrent"]["cloud_connected"]=cloud;
    // no credentials, AP password, Wi-Fi values, or audio data
  }

  void beforeBusShow() {
    if(!ready || !statusCount)return;
    Bus* bus=BusManager::getBus(0);
    uint8_t gpio[5]={0};
    if(!bus || bus->getLength()!=statusCount || bus->getStart()!=0 || bus->getPins(gpio)!=1 || gpio[0]!=4)return;
    // Region masks operate on final physical indexes after the sparse XY projection.
    // Status indexes never appear in these masks. Music is full-body until individually bench-tested.
    for(auto &r:regions)if(r.active) {
      uint32_t color=r.scene==1?RGBW32(255,85,35,0):r.scene==2?RGBW32(20,100,255,0):RGBW32(255,215,170,0);
      uint8_t scale=uint16_t(r.brightness)*255/100;
      if(r.scene==4)scale=uint16_t(scale)*(32+sin8(millis()/16)*223/255)/255;
      for(unsigned i=0;i<r.pixels.size();++i) {
        uint32_t c=color;
        if(r.scene==3)c=strip.getMainSegment().color_wheel(uint8_t(i*255/std::max(size_t(1),r.pixels.size())+millis()/25));
        if(!r.on)c=0;
        BusManager::setPixelColor(r.pixels[i],color_fade(c,scale));
      }
    }
    Status s=oddcurrent::status(updating,errorFlag!=0,int32_t(warningUntil-millis())>0,apActive,WLED_CONNECTED,cloud,bri>0);
    if(!updating && int32_t(successUntil-millis())>0)s=Status::provisioned;
    uint8_t pulse=8+(sin8(uint8_t(millis()/(s==Status::wifi?4:16)))>>2);
    uint32_t color=0;
    if(s==Status::setup)color=((millis()/600)%2)?RGBW32(pulse,0,0,0):RGBW32(0,0,pulse,0);
    if(s==Status::wifi || s==Status::standby)color=RGBW32(0,0,pulse,0);
    if(s==Status::active)color=RGBW32(10,4,2,0);
    if(s==Status::internet_lost)color=RGBW32(8,5,0,0); // connectivity warning, local operation stays usable
    if(s==Status::warning)color=((millis()/200)%2)?RGBW32(60,15,0,0):0;
    if(s==Status::fault)color=RGBW32(80,0,0,0);
    if(s==Status::updating)color=RGBW32(pulse,pulse/3,0,0);
    if(s==Status::provisioned)color=RGBW32(0,50,2,0);
    bus->setBrightness(map(statusBrightness,1,20,13,255));
    for(unsigned i=0;i<statusCount;++i)bus->setPixelColor(i,color);
  }

  bool factorySerial() {
    // Physical service hold + virgin factory namespace. Existing identity cannot be overwritten here.
    if(serial.length() || digitalRead(16)!=LOW || updating)return false;
    while(Serial.available()) {
      char c=Serial.read();
      if(c=='\n') {
        JsonDocument d; bool ok=!deserializeJson(d,serialBuffer);
        serialBuffer="";
        String id=d["serial"].as<String>();
        ok=ok && id.length()>=4 && id.length()<=32 && d["ap_password"].as<String>().length()>=12
          && d["device_credential"].as<String>().length()>=32 && d["ca_pem"].as<String>().indexOf("BEGIN CERTIFICATE")>=0;
        if(!ok) {Serial.println("OC:INVALID");continue;}
        factory.putString("serial",id); factory.putString("credential",d["device_credential"].as<String>());
        factory.putString("ca",d["ca_pem"].as<String>()); factory.putString("broker",d["broker_host"].as<String>());
        factory.putString("apssid",d["ap_ssid"].as<String>()); factory.putString("appass",d["ap_password"].as<String>());
        // Hardware outputs stay disabled until a separately validated local configuration is accepted.
        factory.putBool("ready",d["hardware_ready"]|false); factory.putUChar("status",d["status_count"]|0);
        Serial.println("OC:PROVISIONED"); Serial.flush(); ESP.restart();
      } else if(serialBuffer.length()<6000)serialBuffer+=c;
      else {serialBuffer="";Serial.println("OC:TOO_LARGE");}
    }
    return true;
  }
};

constexpr const char* OddCurrent::scenes[6];
static OddCurrent oddcurrent_mod;
void oddcurrentBeforeBusShow() { oddcurrent_mod.beforeBusShow(); }
bool oddcurrentFactorySerial() { return oddcurrent_mod.factorySerial(); }
REGISTER_USERMOD(oddcurrent_mod);
