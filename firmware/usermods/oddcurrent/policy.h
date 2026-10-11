#pragma once
#include <stdint.h>

namespace oddcurrent {
enum class Action { none, short_press, double_press, long_press, repeat, setup_ap, wifi_clear_warning, clear_wifi };

// Independent of Arduino: deterministic debounce and gesture policy for host tests.
class Button {
  bool raw_ = false, down_ = false, long_ = false, pending_ = false;
  uint32_t edge_ = 0, pressed_ = 0, released_ = 0, repeat_ = 0;
  bool setup_ = false, warned_ = false, cleared_ = false;
  bool locked_ = false;
public:
  Action tick(bool raw, uint32_t now, bool recovery = false, bool updating = false) {
    if (updating) {
      raw_ = raw; down_ = raw; edge_ = pressed_ = repeat_ = now;
      pending_ = false; long_ = raw; setup_ = warned_ = cleared_ = false;
      locked_ = raw;
      return Action::none;
    }
    if (locked_) {
      if(raw!=raw_){raw_=raw;edge_=now;}
      if(!raw && uint32_t(now-edge_)>=35){locked_=false;down_=false;long_=false;}
      return Action::none;
    }
    if (raw != raw_) { raw_ = raw; edge_ = now; }
    if (raw_ != down_ && uint32_t(now-edge_) >= 35) {
      down_ = raw_;
      if (down_) { pressed_ = repeat_ = now; long_ = setup_ = warned_ = cleared_ = false; }
      else if (!recovery && !long_) {
        if (pending_ && uint32_t(now-released_) <= 350) { pending_ = false; return Action::double_press; }
        pending_ = true; released_ = now;
      }
    }
    if (recovery && down_) {
      uint32_t held = now-pressed_;
      if (held >= 15000 && !cleared_) { cleared_ = true; return Action::clear_wifi; }
      if (held >= 13000 && !warned_) { warned_ = true; return Action::wifi_clear_warning; }
      if (held >= 5000 && !setup_) { setup_ = true; return Action::setup_ap; }
    }
    if (!recovery && down_) {
      if (!long_ && uint32_t(now-pressed_) >= 700) { long_ = true; pending_ = false; repeat_ = now; return Action::long_press; }
      if (long_ && uint32_t(now-repeat_) >= 250) { repeat_ = now; return Action::repeat; }
    }
    if (!recovery && pending_ && !down_ && uint32_t(now-released_) > 350) { pending_ = false; return Action::short_press; }
    return Action::none;
  }
};

enum class Status { setup, wifi, standby, active, internet_lost, warning, fault, updating, provisioned };
inline Status status(bool updating, bool fault, bool warning, bool ap, bool wifi, bool cloud, bool on) {
  if (updating) return Status::updating;
  if (fault) return Status::fault;
  if (warning) return Status::warning;
  if (ap) return Status::setup;
  if (!wifi) return Status::wifi;
  if (!cloud) return Status::internet_lost;
  return on ? Status::active : Status::standby;
}

inline bool accept(uint64_t sequence, uint64_t last, uint32_t expires, uint32_t now,
                   bool session_matches, bool updating) {
  return session_matches && !updating && sequence > last && expires > now && expires <= now + 15;
}
} // namespace oddcurrent
