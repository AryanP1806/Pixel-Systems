# Initialize an empty list to function as the event queue.
event_queue = []

def add_event(event_name):
    """Adds a new event to the end of the queue."""
    event_queue.append(event_name)
    print(f"Event '{event_name}' added successfully.")

def display_events():
    """Displays all pending events in the queue."""
    print("\n--- Pending Events ---")
    if not event_queue:
        print("(No pending events)")
    else:
        # Loop through events, showing a 1-based index for readability.
        for i, event in enumerate(event_queue, 1):
            print(f"{i}: {event}")
    print("----------------------")

def cancel_event(event_name):
    """Removes a specific event from the queue by its name."""
    if event_name in event_queue:
        event_queue.remove(event_name)
        print(f"Event '{event_name}' cancelled successfully.")
    else:
        print(f"Error: Event '{event_name}' not found in the queue.")

def process_next_event():
    """Processes the next event in the queue (FIFO - First-In, First-Out)."""
    if event_queue:
        # Remove and get the first event from the queue.
        processed_event = event_queue.pop(0)
        print(f"Processing event: '{processed_event}'")
    else:
        print("No events to process.")

# --- Main Program Loop ---
while True:
    print("\n--- Event Queue Menu ---")
    print("1. Add event")
    print("2. Display pending events")
    print("3. Process next event")
    print("4. Cancel an event")
    print("5. Exit")
    
    choice = input("Enter your choice: ")

    if choice == '1':
        event = input("Enter the event name to add: ")
        add_event(event)
    elif choice == '2':
        display_events()
    elif choice == '3':
        process_next_event()
    elif choice == '4':
        event = input("Enter the event name to cancel: ")
        cancel_event(event)
    elif choice == '5':
        print("Exiting program.")
        break
    else:
        print("Invalid choice. Please enter a number from 1 to 5.")
