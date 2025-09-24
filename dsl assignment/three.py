def bubble_sort(array):
    """Sorts an array using the Bubble Sort algorithm."""
    n = len(array)
    # Traverse through all array elements
    for i in range(n):
        # Last i elements are already in place
        for j in range(0, n - i - 1):
            # Traverse the array from 0 to n-i-1
            # Swap if the element found is greater than the next element
            if array[j] > array[j + 1]:
                array[j], array[j + 1] = array[j + 1], array[j]
    return array

def selection_sort(array):
    """Sorts an array using the Selection Sort algorithm."""
    n = len(array)
    # Traverse through all array elements
    for i in range(n):
        # Find the minimum element in the remaining unsorted array
        min_idx = i
        for j in range(i + 1, n):
            if array[j] < array[min_idx]:
                min_idx = j
        # Swap the found minimum element with the first element
        array[i], array[min_idx] = array[min_idx], array[i]
    return array

# --- Main Program ---
employees = []
try:
    n = int(input("Enter the total number of employees: "))
    for i in range(n):
        salary = float(input(f"Enter salary for employee {i+1}: "))
        employees.append(salary)
except ValueError:
    print("Invalid input. Please enter numbers only.")
    exit()

print("\nOriginal Salary List:", employees)

while True:
    print("\n---Sort Menu---")
    print("1. Bubble Sort")
    print("2. Selection Sort")
    print("3. Exit")
    choice = input("Enter your choice: ")

    # Make a copy to sort, so the original list is not changed
    temp_salaries = employees.copy()

    if choice == '1':
        print("\nYou chose Bubble Sort.")
        sorted_salaries = bubble_sort(temp_salaries)
        print("Sorted Salaries:", sorted_salaries)
        
        # Get the last 5 elements and reverse them for descending order
        top_5 = sorted_salaries[-5:][::-1]
        print("Top 5 highest salaries:", top_5)

    elif choice == '2':
        print("\nYou chose Selection Sort.")
        sorted_salaries = selection_sort(temp_salaries)
        print("Sorted Salaries:", sorted_salaries)

        # Get the last 5 elements and reverse them for descending order
        top_5 = sorted_salaries[-5:][::-1]
        print("Top 5 highest salaries:", top_5)

    elif choice == '3':
        print("Exiting.")
        break

    else:
        print("Invalid choice. Please enter 1, 2, or 3.")
