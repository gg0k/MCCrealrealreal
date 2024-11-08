import os
import time
import random
from datetime import datetime


def create_and_write_to_file(file_name):
    # Create the 'datos' directory if it doesn't exist
    directory = os.path.join(os.getcwd(), 'datos')
    if not os.path.exists(directory):
        os.makedirs(directory)

    # Get the current date and time
    current_time = datetime.now().strftime("%H_%M_%d_%m")

    # Create the full file path with the date, time, and user-provided name
    file_path = os.path.join(directory, f"{current_time}_{file_name}.txt")

    print(f"Creating file: {file_path}")

    # Open the file in append mode
    with open(file_path, 'a') as file:
        while True:
            # Generate random data
            random_data = str(random.randint(1, 100))
            # Write data to the file
            file.write(random_data + '\n')
            print(f"Data added: {random_data}")
            # Wait for a period (e.g., 1 second)
            time.sleep(1)


# Get file name from user
file_name = input("Enter the name of the text file: ")

# Start adding random data periodically
create_and_write_to_file(file_name)
