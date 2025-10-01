# Initialize the document and the stacks for undo/redo functionality.
document = ""
undo_stack = []
redo_stack = []

def make_change(new_text):
    """Applies a new change to the document."""
    global document
    # Save the current state to the undo stack before changing it.
    undo_stack.append(document)
    # Apply the new text.
    document = new_text
    # A new change invalidates the old redo history.
    redo_stack.clear()
    print("Change made.")

def undo():
    """Reverts the last change made to the document."""
    global document
    if undo_stack:
        # Save the current state for a potential redo.
        redo_stack.append(document)
        # Revert to the last state from the undo stack.
        document = undo_stack.pop()
        print("Undo successful.")
    else:
        print("Nothing to undo.")

def redo():
    """Re-applies the last change that was undone."""
    global document
    if redo_stack:
        # Save the current state for a potential undo.
        undo_stack.append(document)
        # Re-apply the change from the redo stack.
        document = redo_stack.pop()
        print("Redo successful.")
    else:
        print("Nothing to redo.")

def display_document():
    """Prints the current state of the document."""
    print("\n--- Current Document ---")
    if document:
        print(document)
    else:
        print("(empty)")
    print("------------------------")

# --- Main Program Loop ---
while True:
    print("\n--- Menu ---")
    print("1. Make a change")
    print("2. Undo")
    print("3. Redo")
    print("4. Display Document")
    print("5. Exit")
    choice = input("Enter your choice: ")

    if choice == '1':
        text = input("Enter the new text for the document: ")
        make_change(text)
    elif choice == '2':
        undo()
    elif choice == '3':
        redo()
    elif choice == '4':
        display_document()
    elif choice == '5':
        print("Exiting.")
        break
    else:
        print("Invalid choice. Please enter a number from 1 to 5.")
