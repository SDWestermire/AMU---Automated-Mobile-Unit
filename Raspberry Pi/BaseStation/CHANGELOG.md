
# CHANGELOG — botcarBaseStation Ver 1.1 (2026-01-13)

- Restore mission logging: ensures `./logs` exists and opens a timestamped file on start.
- Fix `+RCV` parsing for payloads containing commas (e.g., `lat,lon`):
  - Split `RSSI,SNR` from the **right** using `rsplit(',', 2)`,
  - Then split the left side into `src,len,data` using `split(',', 2)`.
- Preserve baseline behavior: no radio reconfiguration at startup; ACK lines logged as `ACK=Sent`.
