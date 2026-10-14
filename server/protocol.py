"""Strict, capability-limited cloud contract. No arbitrary WLED JSON passthrough."""
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, StrictBool, StrictInt, model_validator

SCENES = ('gallery', 'sunset', 'blue', 'spectrum', 'pulse', 'music')

class Lighting(BaseModel):
    model_config = ConfigDict(extra='forbid')
    on: StrictBool | None = None
    brightness: StrictInt | None = Field(default=None, ge=1, le=100)
    scene: Literal['gallery', 'sunset', 'blue', 'spectrum', 'pulse', 'music'] | None = None
    music: StrictBool | None = None
    sensitivity: StrictInt | None = Field(default=None, ge=1, le=100)
    status_brightness: StrictInt | None = Field(default=None, ge=1, le=20)
    zone: str | None = Field(default=None, pattern=r'^[a-z][a-z0-9-]{0,31}$')

    @model_validator(mode='after')
    def meaningful(self):
        values = self.model_dump(exclude_none=True)
        if not values or set(values) == {'zone'}:
            raise ValueError('empty command')
        if self.zone and set(values) - {'zone', 'on', 'brightness', 'scene'}:
            raise ValueError('zone accepts only on, brightness and scene')
        if self.zone and self.scene == 'music':
            raise ValueError('music is whole-body until region audio adapter acceptance')
        return self

class Claim(BaseModel):
    model_config = ConfigDict(extra='forbid')
    code: str = Field(min_length=16, max_length=128)

class Invite(BaseModel):
    model_config = ConfigDict(extra='forbid')
    hours: StrictInt = Field(default=24, ge=1, le=168)

class Telemetry(BaseModel):
    model_config = ConfigDict(extra='forbid')
    type: Literal['telemetry']
    on: StrictBool
    brightness: StrictInt = Field(ge=1, le=100)
    scene: Literal['gallery', 'sunset', 'blue', 'spectrum', 'pulse', 'music']
    music: StrictBool
    sensitivity: StrictInt = Field(default=50, ge=1, le=100)
    status_brightness: StrictInt = Field(default=5, ge=1, le=20)
    rssi: StrictInt = Field(ge=-127, le=0)
    firmware: str = Field(max_length=64, pattern=r'^[a-zA-Z0-9._+-]+$')
    boot_reason: str = Field(max_length=32, pattern=r'^[a-zA-Z0-9_-]+$')
    reconnects: StrictInt = Field(ge=0, le=2147483647)
    uptime_s: StrictInt = Field(ge=0, le=4294967295)
    zones_ready: StrictBool = False
    xy_ready: StrictBool = False
    lighting_ready: StrictBool = False
    hardware_ready: StrictBool = False

class Ack(BaseModel):
    model_config = ConfigDict(extra='forbid')
    type: Literal['ack']
    id: str = Field(pattern=r'^[a-f0-9]{32}$')
    seq: StrictInt = Field(ge=1)
    status: Literal['applied', 'rejected']
