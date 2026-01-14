
# AMU / AAMU Phase Two — Pico USB CDC boot configuration
# Created by: Steven Westermire (“Maddog” / “Gunny”) — 2025-12-04
# Co-Author: Nikola (M365 Copilot)
# License: MIT
# Purpose: Enable console and data CDC endpoints for CircuitPython.

import usb_cdc
import storage

# Enable both console (REPL) and data serial endpoints.
usb_cdc.enable(console=True, data=True)

# Development: keep writable; for production consider readonly.
storage.remount("/", readonly=False)
