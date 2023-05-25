import random
import time

def simulate_garbage_container_fill():
    capacity = 100      # Max capacity of the garbage container (in percentage)
    current_fill = 0    # Initial fill level of the garbage container (in percentage)
    
    while True:
        time.sleep(3)   # Simulate some delay between fill iterations
        
        if current_fill > 70:
            max_fill_rate = 2   # Maximum rate at which the container can be filled per iteration (in percentage)
            print("(!) GARBAGE CONTAINER FULL (!)")
        else:
            max_fill_rate = 5

        fill_rate = random.uniform(0, max_fill_rate)    # Randomly generate a fill rate for the garbage container (in percentage)
        current_fill += fill_rate
        
        if current_fill > capacity:
            # Prevent the garbage container from overflowing when completely full
            current_fill = capacity
        
        print(f"Garbage container filled: {round(current_fill)}%")

# Call the function to run the simulation
simulate_garbage_container_fill()
