"""Exercise the actual physical overlay through on, standby and fault transitions."""
from pathlib import Path
import subprocess


def test_status_follows_body_then_restores_standby_and_fault(tmp_path):
    source = Path('firmware/usermods/oddcurrent/oddcurrent.cpp').read_text()
    method = source[source.index('  void beforeBusShow()'):source.index('\n  bool factorySerial()')]
    policy = Path('firmware/usermods/oddcurrent/policy.h').resolve().as_posix()
    harness = r'''
#include <cassert>
#include <algorithm>
#include <cstdint>
#include <vector>
#include "POLICY"
#define RGBW32(r,g,b,w) ((uint32_t(w)<<24)|(uint32_t(r)<<16)|(uint32_t(g)<<8)|b)
uint32_t fakeNow=0;
uint32_t millis(){return fakeNow;}
int map(int v,int a,int b,int c,int d){return (v-a)*(d-c)/(b-a)+c;}
uint32_t color_fade(uint32_t c,int){return c;}
uint8_t bri=32,errorFlag=0;
struct Bus {
  unsigned start,len,pin;uint8_t brightness=0;
  std::vector<uint32_t> pixels;
  unsigned getLength(){return len;}
  unsigned getStart(){return start;}
  unsigned getPins(uint8_t *p){p[0]=pin;return 1;}
  void setBrightness(uint8_t b){brightness=b;}
  void setPixelColor(unsigned i,uint32_t c){pixels.at(i)=c;}
  uint32_t getPixelColor(unsigned i){return pixels.at(i);}
};
Bus statusBus{0,2,4,0,{0,0}},bodyBus{2,3,5,0,{0x123456,0x654321,0xABCDEF}};
namespace BusManager {
 Bus* getBus(unsigned i){return i==0?&statusBus:&bodyBus;}
 void setPixelColor(unsigned,uint32_t){}
}
struct Segment {uint32_t color_wheel(uint8_t){return 0;}};
struct Strip {
 uint8_t brightness=32;Segment segment;
 uint8_t getBrightness(){return brightness;}
 Segment& getMainSegment(){return segment;}
} strip;
struct Adapter {
 struct Region {bool active=false,on=true;int scene=0,brightness=100;std::vector<uint16_t> pixels;};
 std::vector<Region> regions;
 uint8_t statusCount=2,statusBrightness=5;
 uint32_t identifyUntil=0,locateUntil=0;uint16_t locateIndex=0;
 oddcurrent::StatusDisplay statusDisplayMode=oddcurrent::StatusDisplay::standby;
 uint32_t statusFrame[2]={0,0};
 bool lightingReady(){return true;}
 uint8_t breath8(uint8_t p){return oddcurrent::breathe(p);}
METHOD
};
int main() {
 Adapter a;
 a.beforeBusShow();
 assert(a.statusDisplayMode==oddcurrent::StatusDisplay::body);
 assert(statusBus.pixels[0]==bodyBus.pixels[0] && statusBus.pixels[1]==bodyBus.pixels[1]);
 assert(statusBus.brightness==strip.brightness);
 bri=0;strip.brightness=0;a.beforeBusShow();
 assert(a.statusDisplayMode==oddcurrent::StatusDisplay::standby);
 assert(statusBus.pixels[0]!=statusBus.pixels[1] && statusBus.brightness>0);
 uint32_t first=statusBus.pixels[0];fakeNow=2400;a.beforeBusShow();
 assert(statusBus.pixels[0]!=first);
 bri=50;strip.brightness=50;a.beforeBusShow();
 assert(statusBus.brightness==50 && statusBus.pixels[0]==bodyBus.pixels[0]);
 errorFlag=1;a.beforeBusShow();
 assert(a.statusDisplayMode==oddcurrent::StatusDisplay::fault);
 assert(statusBus.pixels[0]==0x500000 && statusBus.pixels[1]==0x500000);
 bri=0;strip.brightness=0;a.beforeBusShow();
 assert(statusBus.pixels[0]==0x500000 && statusBus.brightness>0);
 errorFlag=0;a.beforeBusShow();
 assert(a.statusDisplayMode==oddcurrent::StatusDisplay::standby);
 a.locateIndex=1;a.locateUntil=fakeNow+3000;a.beforeBusShow();
 assert(bodyBus.pixels[0]==0 && bodyBus.pixels[1]==0x005050 && bodyBus.pixels[2]==0);
 assert(bodyBus.brightness>=24);
 fakeNow+=3001;a.beforeBusShow();assert(bodyBus.brightness==0);
}
'''.replace('POLICY', policy).replace('METHOD', method)
    cpp = tmp_path / 'status.cpp'
    cpp.write_text(harness)
    exe = tmp_path / 'status'
    subprocess.run(['g++', '-std=c++17', str(cpp), '-o', str(exe)], check=True)
    subprocess.run([str(exe)], check=True)
