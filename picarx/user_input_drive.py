from picarx_improved import Picarx

if __name__ == "__main__":
    px = Picarx()
    while True:
        user_command = input(f"Which function would you like to complete?\n1. Forward\n2. Backward\n3. Parallel parking\n4. K=turning\n\n")
        if user_command == "1" or user_command == "2":
            user_angle = int(input("At what angle would you like to drive? "))
            if user_command == "1":
                px.move_forward_with_steering(25, user_angle, 2)
            elif user_command == "2":
                px.move_backward_with_steering(25, user_angle, 2)
        elif user_command == "3" or user_command == "4":
            user_direction = input("Which direction would you like to park/k-turn? ")
            if user_command == "3":
                px.parallel_park(user_direction)
            elif user_command == "3":
                px.k_turn(user_direction)
        else:
            break