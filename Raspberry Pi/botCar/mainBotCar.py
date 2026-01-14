
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Project: AMU / botCar
File: mainBotCar.py
Description: Entry point for botCar AMU. Loads YAML config and starts BotCarNode.

Version: v1.0.3 Baseline Patch
Date: 2025-12-03
Author: Steven Westermire (Maddog / Gunny)
Co-Author: M365 Copilot (Microsoft)

Copyright (c) 2025 Steven Westermire. All rights reserved.
"""

from _BotCarNode import BotCarNode
import time

def main():
    config_file = "botcar_config.yaml"
    botCar = BotCarNode(config_path=config_file)
    botCar.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[System] Shutting down botCar...")
        botCar.stop()

if __name__ == "__main__":
    main()