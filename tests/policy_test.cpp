#include "../firmware/usermods/oddcurrent/policy.h"
#include <cassert>
using namespace oddcurrent;
int main() {
  assert(!lightingAllowed(false,false,true));
  assert(lightingAllowed(false,true,true)); // prototype control does not assert acceptance
  assert(lightingAllowed(true,false,true));
  assert(!lightingAllowed(false,true,false)); // opt-in cannot bypass invalid wiring configuration
  assert(!lightingAllowed(true,true,false));
  Button b;
  assert(b.tick(true,0)==Action::none);
  assert(b.tick(false,10)==Action::none); // bounce rejected
  b.tick(true,20);b.tick(true,60);b.tick(false,100);b.tick(false,140);
  assert(b.tick(false,491)==Action::short_press);
  Button d;d.tick(true,0);d.tick(true,35);d.tick(false,100);d.tick(false,135);d.tick(true,180);d.tick(true,215);d.tick(false,250);
  assert(d.tick(false,285)==Action::double_press);
  assert(d.tick(false,700)==Action::none);
  Button l;l.tick(true,0);l.tick(true,35);
  assert(l.tick(true,735)==Action::long_press);
  assert(l.tick(true,985)==Action::repeat);
  l.tick(false,1000);l.tick(false,1035);assert(l.tick(false,1500)==Action::none);
  Button r;r.tick(true,0,true);r.tick(true,35,true);
  assert(r.tick(true,5035,true)==Action::setup_ap);
  assert(r.tick(true,13035,true)==Action::wifi_clear_warning);
  assert(r.tick(true,15035,true)==Action::clear_wifi);
  assert(r.tick(true,16000,true)==Action::none);
  Button u;u.tick(true,0,true,true);assert(u.tick(true,20000,true,true)==Action::none);
  assert(u.tick(true,40000,true,false)==Action::none); // release required after update
  u.tick(false,40001,true,false);u.tick(false,40040,true,false);
  assert(status(true,true,true,true,false,false,false)==Status::updating);
  assert(status(false,false,false,false,true,false,true)==Status::internet_lost);
  assert(accept(2,1,110,100,true,false));
  assert(!accept(1,1,110,100,true,false));
  assert(!accept(2,1,99,100,true,false));
  assert(!accept(2,1,120,100,true,false));
  assert(!accept(2,1,110,100,false,false));
  assert(!accept(2,1,110,100,true,true));
}
