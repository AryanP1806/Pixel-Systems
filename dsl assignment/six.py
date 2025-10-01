# Define the Student class to store student details and next node reference
class Student:
    """Node for the linked list, representing a single student."""
    def __init__(self, rollno, name, marks):
        self.rollno = rollno  # Student roll number
        self.name = name      # Student name
        self.marks = marks    # Student marks
        self.next = None      # Pointer to the next node in the linked list

class StudentLinkedList:
    """Manages the linked list of Student nodes."""
    def __init__(self):
        self.head = None  # Initialize the head of the linked list

    def add_student(self, rollno, name, marks):
        """Adds a new student to the end of the linked list."""
        new_node = Student(rollno, name, marks)
        if not self.head:
            self.head = new_node
        else:
            temp = self.head
            while temp.next:
                temp = temp.next
            temp.next = new_node
        print(f"Student '{name}' (Roll No: {rollno}) added successfully.")

    def display_students(self):
        """Displays all student records from the linked list."""
        print("\n--- Student Records ---")
        if not self.head:
            print("(No student data added)")
        else:
            temp = self.head
            while temp:
                print(f"Roll No: {temp.rollno}, Name: {temp.name}, Marks: {temp.marks}")
                temp = temp.next
        print("-----------------------")

    def search_student(self, roll):
        """Searches for a student by their roll number."""
        temp = self.head
        while temp:
            if temp.rollno == roll:
                print("\n--- Record Found ---")
                print(f"Roll No: {temp.rollno}, Name: {temp.name}, Marks: {temp.marks}")
                print("--------------------")
                return
            temp = temp.next
        print(f"\nRecord for Roll No: {roll} not found.")

    def delete_student(self, roll):
        """Deletes a student record by their roll number."""
        temp = self.head
        previous = None

        # If the head node itself holds the roll number to be deleted
        if temp and temp.rollno == roll:
            self.head = temp.next
            print(f"Student record for Roll No: {roll} deleted successfully.")
            return

        # Search for the roll number to be deleted, keep track of the previous node
        while temp and temp.rollno != roll:
            previous = temp
            temp = temp.next

        # If roll number was not present in the linked list
        if not temp:
            print(f"Student with Roll No: {roll} not found.")
            return

        # Unlink the node from the linked list
        previous.next = temp.next
        print(f"Student record for Roll No: {roll} deleted successfully.")

    def sort_students(self):
        """Sorts the linked list by roll number using bubble sort (swapping data)."""
        if not self.head:
            print("Cannot sort an empty list.")
            return
            
        current = self.head
        while current:
            index = current.next
            while index:
                if current.rollno > index.rollno:
                    # Swap data between the two nodes
                    current.rollno, index.rollno = index.rollno, current.rollno
                    current.name, index.name = index.name, current.name
                    current.marks, index.marks = index.marks, current.marks
                index = index.next
            current = current.next
        print("Student records sorted successfully by roll number.")

# --- Main Program Loop ---
student_list = StudentLinkedList()
while True:
    print("\n--- Student Management Menu ---")
    print("1. Add Student")
    print("2. Display Students")
    print("3. Delete Student")
    print("4. Search Student")
    print("5. Sort Students (by Roll No)")
    print("6. Exit")
    choice = input("Enter your choice: ")

    if choice == '1':
        try:
            r = int(input("Enter Roll No: "))
            n = input("Enter Name: ")
            m = float(input("Enter Marks: "))
            student_list.add_student(r, n, m)
        except ValueError:
            print("Invalid input. Please enter correct data types.")
    elif choice == '2':
        student_list.display_students()
    elif choice == '3':
        try:
            r = int(input("Enter Roll No to delete: "))
            student_list.delete_student(r)
        except ValueError:
            print("Invalid input. Please enter a valid roll number.")
    elif choice == '4':
        try:
            r = int(input("Enter Roll No to search: "))
            student_list.search_student(r)
        except ValueError:
            print("Invalid input. Please enter a valid roll number.")
    elif choice == '5':
        student_list.sort_students()
    elif choice == '6':
        print("Exiting program.")
        break
    else:
        print("Invalid choice. Please select an option from 1 to 6.")
