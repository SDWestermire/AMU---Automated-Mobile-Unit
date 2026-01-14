AMU — Automated Mobile Unit
Autonomous community patrol / telemetry / mission control stack
Creator: Steven “Maddog / Gunny” Westermire (USMC, Ret.)

The AMU project is a practical, end‑to‑end framework for small autonomous patrol units.
It merges sensors → fusion → transport → LoRa uplink → BaseStation, with mission control driven by a clean state machine (inspired by an “ant” game architecture).
Target: reliable, modular, and field‑repairable autonomy that can scale from one unit to a coordinated fleet.


1) Vision & Objectives

Mission‑first reliability: Favor simple, robust designs over fragile complexity.
Modularity: Sensors live on the Raspberry Pi Pico. Transport and computation live on the Raspberry Pi. Uplink and oversight live on the BaseStation Pi.
Typed messaging: A single SensorFrame envelope with distinct families:

telemetry:T — pose/position & core health
sensor:S — module events (obstacle, detection, motor/ESC, env)
mission:M — registration, heartbeat, state updates, waypointing, ACKs
priority:P — pre‑emptive notifications (E_STOP, THREAT_DETECTED)


Low airtime uplink: Compact LoRa tokens; comma‑safe parsing on the Base.
Forward path: A fleet of AMUs with assist behaviors, web dashboards, community integration, and production hardening.

2) System Overview (top → bottom)

Pico (sensor hub)
Reads BNO055 IMU (heading/roll/pitch/compass)
Reads NEO‑6M GPS (lat, lon, fix, speed)
Builds typed SensorFrame objects (T/S/M/P) and sends JSON over USB CDC to the Pi.

Pi (AMU uplink & compute)

Receives Pico JSON lines, ACKs seq, dispatches by type (on_T/S/M/P)
Maps essentials to compact LoRa tokens (e.g., FS, MS, PR, NV) for the BaseStation.

BaseStation (LoRa listener & logging)

Parses +RCV=src,len,data,RSSI,SNR safely (split from the right)
Handles REG, FS, MS, PR, etc., ACKs back, logs mission data with RSSI/SNR.

Mission Control (state machine)

Core states: STANDBY, PATROL, INVESTIGATE, REPORT, ASSIST, RETURN_HOME
Transitions driven by detections, commands, battery/safety, and timeouts.

3) Key Features
4) 
SensorFrame v1.2‑Expanded
Unified envelope {v,type,node_id,seq,ts_ms} + typed payloads. Optional nav block for telemetry:T (state, wp_idx, bearing, heading error, distance, motor L/R).

Pre‑emptive Priority
priority:P frames bypass queues and expect fast ACK (≤ 50 ms); used for E_STOP, critical alerts, and state‑transition notices.

LoRa Uplink Tokens (Pi → Base)

REG:<id> — node registration
FS:<id>:<yaw>:<lat>,<lon> — fused snapshot (compact telemetry)
MS:<id>:<state>:<code>[:detail] — mission state
PR:<id>:<code>[:args] — priority / alerts
NV:<id>:<state>:<wp_idx>:<dist_m>:<heading_err> — navigation status (optional)

Comma‑safe BaseStation parsing

Always split RSSI/SNR from the right, then src,len,data from the left; commas inside payloads won’t break parsing.

4) Repo Layout (proposed)
AMU/
├─ pico/                      # CircuitPython (Pico sensor hub)
│  ├─ main.py                 # Builds T/S/M/P frames; handles nav & safety
│  ├─ pico2rpi.py             # Transport classes & TransportLink (JSON + ACK)
│  └─ sensors/
│     ├─ imu_bno055.py        # BNO055 IMU driver
│     └─ GPS_LatLon.py        # NEO-6M GPS (GPGGA/GPRMC/GPGLL)
│
├─ botcarAMU/                 # Raspberry Pi (AMU uplink)
│  └─ rpi2pico.py             # Typed dispatcher, LoRa mapper, ACKs
│
├─ botcarBaseStation/         # BaseStation (LoRa listener)
│  └─ botcarBaseStation.py    # +RCV parser, ACKs, mission logs
│
├─ docs/
│  ├─ SensorFrame_v1.2-Expanded.rtf
│  └─ FunctionalDiagram.png
│
├─ examples/                  # Small, copy-ready JSON frames & tokens
│  ├─ telemetry_T.json
│  ├─ mission_M.json
│  ├─ priority_P.json
│  └─ nav_NV.tokens
│
└─ .github/workflows/ci.yml   # Lint + JSON schema validate (future)

Note: If you use different directories, keep the same intent: clean separation of Pico sensors, Pi uplink, and BaseStation.

5) Quick Start
   
Hardware

Raspberry Pi Pico (USB CDC enabled)
BNO055 IMU on I²C (SDA=GP0, SCL=GP1)
NEO‑6M GPS on UART (TX=GP4, RX=GP5) — 5V supply recommended for module reliability
Raspberry Pi for AMU uplink (USB CDC /dev/ttyACM*; LoRa UART /dev/ttyS0)
REYAX RYLR998 LoRa module (address/net/band set; 915 MHz in US)

Software

Pico: CircuitPython (sensor modules + hub)
Pi: Python 3.11+ with pyserial (no internet required)
Base: Python 3.11+, same serial setup

Run Order

BaseStation:
Shellpython3 botcarBaseStation/botcarBaseStation.pyShow more lines

Pi uplink:
Shellpython3 botcarAMU/rpi2pico.pyShow more lines

Pico hub: run pico/main.py (CircuitPython) → begins streaming T/S/M/P over USB.

Expected:

BaseStation prints REG and FS, with ACK lines and a mission log file under ./logs/mission_log_*.txt.

6) SensorFrame (short spec)
Envelope (all types):
JSON{  "v": 1,  "type": "telemetry:T | sensor:S | mission:M | priority:P",  "node_id": 2,  "seq": 145,  "ts_ms": 582341}Show more lines
Telemetry (T) (core pose/position, steady cadence):
JSON{  "v":1, "type":"telemetry:T", "node_id":2, "seq":145, "ts_ms":582341,  "Q":"0x03",  "imu":{"heading":92.4,"compass":"E","roll":-1.0,"pitch":0.5},  "gps":{"lat":33.686377,"lon":-117.789653,"spd_mps":0.84,"hdop":0.9,"fix":3},  "rng":{"f_cm":85,"l_cm":null,"r_cm":120},  "batt":{"v":7.46},  "nav":{"state":"PATROL","wp_idx":3,"bearing_to_wp":87.2,"heading_error":5.2,         "distance_m":12.4,"motor_l":0.48,"motor_r":0.52}}Show more lines
Sensor (S) (events / periodic module data):
JSON{  "v":1, "type":"sensor:S", "node_id":2, "seq":990, "ts_ms":600123,  "evt":{"class":"ultrasonic","front_cm":78}}Show more lines
Mission (M) (state control, heartbeat, ACKs):
JSON{  "v":1, "type":"mission:M", "node_id":2, "seq":50, "ts_ms":300000,  "ms":{"state":"PATROL","code":0,"wp_idx":3,"ack_cmd":null}}Show more lines
Priority (P) (pre‑emptive/emergency):
JSON{  "v":1, "type":"priority:P", "node_id":2, "seq":777, "ts_ms":605010,  "prio":{"code":"E_STOP","level":"CRIT","detail":"user_press"}}Show more lines
ACK & pacing

Pi responds ACK:<seq>\r\n to valid frames.
Optional SLOW:<ms> advisories may be sent to slow down a type or globally.
Pico may resend if no ACK within a window (e.g., 250 ms), bounded retries.

7) Pi ↔ Pico Command Protocol (JSON lines)
Pi → Pico:
JSON{"cmd":"START_PATROL","args":{"waypoints":[[33.686377,-117.789653],[33.685965,-117.790052]],"speed":0.5},"seq":100}Show more lines
Pico → Pi ACK via Mission:
JSON{"v":1,"type":"mission:M","node_id":2,"seq":101,"ts_ms":12345, "ms":{"ack_cmd":"START_PATROL","ack_seq":100,"status":"OK","msg":"patrol initialized"}}Show more lines
Core commands: START_PATROL, HALT, GOTO_WAYPOINT, SET_MODE, ASSIST, RETURN_HOME, CANCEL_ASSIST, EMERGENCY_STOP.

8) Mission Control (state machine)

States: STANDBY ↔ PATROL → INVESTIGATE → REPORT; ASSIST; RETURN_HOME
Transitions:

PATROL → INVESTIGATE on threat detection (confidence > 0.7)
INVESTIGATE → REPORT when evidence collected or timeout
REPORT → PATROL / STANDBY / ASSIST based on base commands
Any state → STANDBY on priority:P E_STOP

Pico skeleton: AMUStateMachine with AMUStatePatrol, AMUStateInvestigate, AMUStateReport, AMUStateAssist, AMUStateReturnHome, AMUStateStandby.

9) Roadmap (10 weeks @ ~20 h/week)

Weeks 1–2: Transport T/S/M/P, Pi dispatcher, basic state machine, manual command tests
Weeks 3–4: Navigation math + motor control; waypoint patrol; safety guards
Weeks 5–6: Investigation/Reporting flows; multi‑AMU assist orchestration
Weeks 7–8: Camera triggers (motion/person/vehicle), reliability/security hardening; battery/RTH
Weeks 9–10: Performance tuning, collision avoidance, fleet ops, docs & releases

Success criteria include: stable T/S/M/P transmissions; waypoint patrol accuracy (< 1 m), reliable E_STOP handling, multi‑AMU assist demonstrated, 24‑hour endurance test.

10) Contributing

Fork and create a feature branch: feature/<short_desc>
Commit convention: type(scope): summary (e.g., feat(pico): add nav block)
Keep changes small; include doc updates (SensorFrame examples, README sections)
Open a PR with what/why/how; include bench/field notes if applicable.

Accreditations: All Python file headers should include Steven Westermire as creator and acknowledgments per project policy.

11) License & Acknowledgments

License: (choose MIT/BSD/Apache‑2.0; pending)
Hardware datasheets: BNO055, NEO‑6M, REYAX RYLR998 (LoRa)
Thanks to the CH‑53 community ethos—mission‑first and systems‑reliable.

12) Contact
Steven “Maddog / Gunny” Westermire
Issues → GitHub tracker (preferred)
For coordination, you can also drop a line in the repo discussions (when enabled).

13) Appendix — Tips & Known Notes

GPS Power: Many NEO‑6M boards behave poorly on 3.3V—use 5V for stable fixes.
Base parsing: Always split from right for RSSI,SNR to avoid comma collisions in payloads.
LoRa airtime: Keep tokens compact; favor short, rate‑limited updates.
Resets/reconnects: If USB CDC or LoRa links stall, perform a graceful stop then relaunch both ends; avoid power cycles where possible by flushing buffers.


Semper Fi — let’s patrol smart, respond fast, and log everything.
