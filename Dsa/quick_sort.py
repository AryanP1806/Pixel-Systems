def quick_sort(arr):
    """Sorts an array using the QuickSort algorithm.

    Args:
        arr: The list of elements to be sorted.

    Returns:
        The sorted list.
    """
    if len(arr) <= 1: # Base case: an array with 0 or 1 element is already sorted.
        return arr

    pivot = arr[-1]  # Choose the last element as the pivot.
    smaller = []
    equal = []
    larger = []

    for num in arr:
        if num < pivot:
            smaller.append(num)
        elif num == pivot:
            equal.append(num)
        else: # num > pivot:
            larger.append(num)

    # Recursively sort the smaller and larger sub-arrays, and combine with the equal elements.
    return quick_sort(smaller) + equal + quick_sort(larger)

# Example usage
my_list = [8, 7, 2, 1, 0, 9, 6]
print("Unsorted Array:", my_list)
sorted_list = quick_sort(my_list)
print("Sorted Array:", sorted_list)

