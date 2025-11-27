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