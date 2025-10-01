# The library dictionary will store member names and their list of borrowed books.
library = {}

# --- 1. Data Input ---
try:
    n = int(input("Enter the total number of members: "))
except ValueError:
    print("Invalid input. Please enter a whole number.")
    exit()

for i in range(n):
    name = input(f"Enter name for member {i+1}: ")
    books_input = input(f"Enter books borrowed by {name} (separated by a period '.'): ")
    
    # Clean up the input: split by '.', strip whitespace from each book,
    # and remove any empty entries that result from extra periods.
    # This makes the data reliable for the rest of the script.
    books_list = [book.strip() for book in books_input.split('.') if book.strip()]
    library[name] = books_list

# Time Complexity: O(n * m), where n is the number of members and m is the number of characters in the book string.
# Space Complexity: O(n * b), where n is the number of members and b is the average number of books per member.

print("\n" + "="*20)
print("LIBRARY REPORT")
print("="*20)

# --- 2. Calculate Total and Average Books ---
total_books = 0
members_with_no_books = 0
for books in library.values():
    # CORRECTION: Changed 'total_book =+' to 'total_books +='.
    # The original was just reassigning the value in each loop.
    total_books += len(books)
    
    # CORRECTION: This is a more robust way to check for members who borrowed nothing.
    # The original 'len(books) == ""' would never be true, as len() returns an integer.
    if not books: # An empty list evaluates to False
        members_with_no_books += 1

# Avoid division by zero if n=0
avg_books = total_books / n if n > 0 else 0

print(f"Total number of members: {len(library)}")
print(f"Total number of books borrowed: {total_books}")
print(f"Average books per member: {avg_books:.2f}")
print(f"Members who borrowed no books: {members_with_no_books}")

# Time Complexity: O(n)
# Space Complexity: O(1)

# --- 3. Calculate Book Borrowing Frequency ---
book_counts = {}
for books in library.values():
    for book in books:
        # The book names are already clean from the input stage
        book_counts[book] = book_counts.get(book, 0) + 1

if book_counts:
    print("\nBook borrowing frequency:")
    # Pretty print the dictionary
    for book, count in book_counts.items():
        print(f"- {book}: {count} time(s)")
else:
    print("\nNo books were borrowed in total.")

# Time Complexity: O(n * b), where b is the average number of books per member.
# Space Complexity: O(k), where k is the number of unique book titles.

# --- 4. Find Most and Least Borrowed Books ---
# CORRECTION: Wrapped all logic in the 'if book_counts:' block to prevent
# errors if no books were entered at all.
if book_counts:
    max_count = max(book_counts.values())
    min_count = min(book_counts.values())

    # This logic finds ALL books that are tied for most/least borrowed.
    most_borrowed = [book for book, count in book_counts.items() if count == max_count]
    least_borrowed = [book for book, count in book_counts.items() if count == min_count]
    
    print(f"\nMost frequently borrowed book(s) (borrowed {max_count} times): {', '.join(most_borrowed)}")
    print(f"Least frequently borrowed book(s) (borrowed {min_count} times): {', '.join(least_borrowed)}")

# Time Complexity: O(k), where k is the number of unique books.
# Space Complexity: O(k) in the worst case (if all books are most/least borrowed).