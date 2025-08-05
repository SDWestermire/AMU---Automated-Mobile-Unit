from simulation_tasks import (
    run_full_route,
    run_from_waypoint,
    simulate_recall,
    launch_multiple_botcars,
    preview_waypoints
)

def show_menu():
    print("\n=== BotCar Simulation Menu ===")
    print("1. Start Full Navigation Route")
    print("2. Start at Specific Waypoint")
    print("3. Recall to Home")
    print("4. Launch Multiple Vehicles")
    print("5. Preview Waypoints (Heading + Distance)")
    print("6. Exit")

def main():
    while True:
        show_menu()
        choice = input("Select option (1–6): ").strip()

        if choice == "1":
            run_full_route()
        elif choice == "2":
            run_from_waypoint()
        elif choice == "3":
            simulate_recall()
        elif choice == "4":
            launch_multiple_botcars()
        elif choice == "5":
            preview_waypoints()
        elif choice == "6":
            print("Mission control shutting down.")
            break
        else:
            print("Invalid selection. Try again.")

if __name__ == "__main__":
    main()
