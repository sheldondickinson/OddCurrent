"""Exercise the actual scene adapter against WLED's legacy-update semantics."""
from pathlib import Path
import subprocess


def test_scene_survives_selected_segment_legacy_state(tmp_path):
    source = Path('firmware/usermods/oddcurrent/oddcurrent.cpp').read_text()
    method = source[source.index('  void applyScene('):source.index('\n  bool command(')]
    # WLED led.cpp: colorUpdated applies legacy globals TO selected segments;
    # stateUpdated instead refreshes legacy globals FROM the selected segment.
    harness = r'''
#include <cassert>
#include <cstdint>
#include <vector>
#define RGBW32(r,g,b,w) ((uint32_t(w)<<24)|(uint32_t(r)<<16)|(uint32_t(g)<<8)|b)
enum { FX_MODE_STATIC, FX_MODE_RAINBOW, FX_MODE_BREATH, FX_MODE_FREQWAVE,
       FX_MODE_2DPLASMAROTOZOOM, FX_MODE_FREQMATRIX, CALL_MODE_BUTTON };
struct Segment {
  int mode=FX_MODE_STATIC, speed=128, intensity=128;
  uint32_t colors[3]={RGBW32(0,255,0,0),0,0};
  bool isActive()const{return true;}
  bool is2D()const{return false;}
  void setMode(int value){mode=value;}
};
struct Strip {
  std::vector<Segment> segments=std::vector<Segment>(2);
  unsigned getSegmentsNum(){return segments.size();}
  Segment& getSegment(unsigned i){return segments.at(i);}
} strip;
int legacyMode=FX_MODE_STATIC,legacySpeed=128;
uint32_t legacyColor=RGBW32(0,255,0,0);
bool stateChanged=false;
void stateUpdated(int) {
  legacyMode=strip.segments[1].mode;legacySpeed=strip.segments[1].speed;
  legacyColor=strip.segments[1].colors[0];
}
void colorUpdated(int mode) {
  strip.segments[1].mode=legacyMode;strip.segments[1].speed=legacySpeed;
  strip.segments[1].colors[0]=legacyColor;stateUpdated(mode);
}
struct Adapter {
  struct Region {bool active=true;};
  std::vector<Region> regions=std::vector<Region>(1);
  uint8_t scene=0;bool music=false,dirty=false;
  uint32_t stateChanged=123; // persistence timestamp must not shadow WLED's flag
  void audio(){}
METHOD
};
int main() {
  Adapter a;
  a.applyScene(3);
  assert(strip.segments[1].mode==FX_MODE_RAINBOW);
  assert(legacyMode==FX_MODE_RAINBOW);
  assert(!a.regions[0].active && !a.music);
  a.applyScene(2);
  assert(strip.segments[1].mode==FX_MODE_STATIC);
  assert(strip.segments[1].colors[0]==RGBW32(20,100,255,0));
  assert(legacyColor==RGBW32(20,100,255,0));
  a.applyScene(5);
  assert(strip.segments[1].mode==FX_MODE_FREQWAVE && a.music);
}
'''.replace('METHOD', method)
    cpp = tmp_path / 'scene.cpp'
    cpp.write_text(harness)
    exe = tmp_path / 'scene'
    subprocess.run(['g++', '-std=c++17', str(cpp), '-o', str(exe)], check=True)
    subprocess.run([str(exe)], check=True)
