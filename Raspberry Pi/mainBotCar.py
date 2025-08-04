from botcar_node import BotCarNode

def main():
    config_file = "botcar_config.yaml"
    botCar01 = BotCarNode(config_path=config_file)
    botCar01.start()

    try:
        while True:
            pass  # Main thread stays alive while botCar runs in background threads
    except KeyboardInterrupt:
        print("\n[System] Shutting down botCar01...")
        botCar01.stop()

if __name__ == "__main__":
    main()
