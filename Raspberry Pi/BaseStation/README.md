
# botcarBaseStation Ver 1.1 — Quick Start

## Requirements
- Python 3.8+
- `pyserial` and `pyyaml` installed (`pip install pyserial pyyaml`)

## Files
- `botcarBaseStation.py` — Base station listener, ACK + mission logging.
- `baseStation_config.yaml` — Runtime settings (serial port, logging, etc.).
- `CHANGELOG.md` — Summary of changes.
- `README.md` — This file.

## Run
```bash
python3 botcarBaseStation.py
```
Expected console:
```
[BaseStation] Mission logging enabled. Log file: ./logs/mission_log_YYYYMMDD_HHMMSS.txt
[BaseStation] LoRa module initialized.
[BaseStation] Listening for botCar transmissions...
```

## Notes
- Logs are written under `./logs/` in the same directory.
- The base responds to registration `REG:<id>` with `ACKREG:<id>` and to waypoints `<id>:<idx>:lat,lon` with `ACK:<id>:<idx>`.
- Use distinct LoRa addresses for base and each AMU and ensure matching `NETWORKID` and `BAND` on all radios.
