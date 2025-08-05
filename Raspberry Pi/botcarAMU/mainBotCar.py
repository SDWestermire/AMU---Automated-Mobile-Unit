from _BotCarNode import BotCarNode

def main():
    config_file = "botcar_config.yaml"
    botCar02 = BotCarNode(config_path=config_file)
    botCar02.start()

    try:
        while True:
            pass  # Main thread stays alive while botCar runs in background threads
    except KeyboardInterrupt:
        print("\n[System] Shutting down botCar01...")
        botCar02.stop()

if __name__ == "__main__":
    main()
