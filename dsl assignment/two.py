def linear_search(array, target):
    """Iterates through the list to find the target's index."""
    for i, item in enumerate(array):
        if item == target:
            return i
    return -1

def binary_search(array, target):
    """Finds target in a sorted version of the list. Returns index from sorted list."""
    sorted_array = sorted(array)
    low, high = 0, len(sorted_array) - 1
    while low <= high:
        mid = (low + high) // 2
        mid_val = sorted_array[mid]
        if mid_val == target:
            return mid
        elif mid_val < target:
            low = mid + 1
        else:
            high = mid - 1
    return -1

# --- Main Program ---

# Take input for all customer IDs using a list comprehension
try:
    num_customers = int(input("Enter the total number of customer IDs: "))
    customers = [input(f"Enter customer ID {i + 1}: ") for i in range(num_customers)]
except ValueError:
    print("Invalid number. Please restart.")
    exit()

print("\nCustomer ID List:", customers)

# Menu loop
while True:
    print("\n---Menu---")
    print("1. Linear Search")
    print("2. Binary Search")
    print("3. Exit")
    choice = input("Enter your choice: ")

    if choice == '1':
        print("\nYou chose Linear Search.")
        search_id = input("Enter the customer ID to search: ")
        index = linear_search(customers, search_id)
        result = f"Customer ID found at position {index + 1}." if index != -1 else "Customer ID not found."
        print(result)

    elif choice == '2':
        print("\nYou chose Binary Search.")
        search_id = input("Enter the customer ID to search: ")
        index = binary_search(customers, search_id)
        result = "Customer ID found." if index != -1 else "Customer ID not found."
        print(result)
        if index != -1:
            print("(Note: Original list remains unsorted.)")

    elif choice == '3':
        print("Exiting.")
        break

    else:
        print("Invalid choice. Please enter 1, 2, or 3.")
