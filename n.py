class VoterRecordHashTable:
    """
    A Hash Table implementation for managing voter records using
    Separate Chaining, keyed by house number.
    """
    def __init__(self, size):
        """
        Initializes the hash table with a given size.
        Each slot is an empty list for chaining.
        """
        self.size = size
        self.hash_table = [[] for _ in range(self.size)]
        print(f"✅ Hash Table initialized with {self.size} slots.")

    def _hash_key(self, house_no):
        """
        Calculates the hash index (slot) based on the house number.
        """
        # The hash function is House_No modulo Size
        return house_no % self.size

    def insert_record(self, house_no, voter_id, name, address, members, age):
        """
        Inserts a new voter record into the hash table.
        """
        location = self._hash_key(house_no)
        
        if self.hash_table[location]:
            print("⚠️ Collision detected! Using Chaining to handle.")
            # 
        
        record = {
            "House_No": house_no,
            "ID": voter_id,
            "Name": name,
            "Address": address,
            "Age": age,
            "Members": members # Total members in the house
        }
        self.hash_table[location].append(record)
        print(f"🏠 Record for {name} (House {house_no}) inserted into Hash Slot {location}.")

    def search_record_by_id(self, voter_id):
        """
        Searches for a voter record using the unique Voter ID.
        Since the ID is not the hash key, we must check every slot (linear search across chains).
        """
        print(f"🔎 Searching for Voter ID: {voter_id}...")
        for i in range(self.size):
            # Iterate through the chain (list) in each slot
            for record in self.hash_table[i]:
                if record["ID"] == voter_id:
                    print("\n✅ Element found!")
                    print(f"  Hash Slot: {i}")
                    print(f"  House No: {record['House_No']}")
                    print(f"  ID: {record['ID']}")
                    print(f"  Name: {record['Name']}")
                    print(f"  Address: {record['Address']}")
                    print(f"  Age: {record['Age']}")
                    print(f"  Members in House: {record['Members']}")
                    return
        print("❌ Element not found.")

    def delete_record_by_id(self, voter_id):
        """
        Deletes a voter record using the unique Voter ID.
        """
        print(f"🗑️ Attempting to delete Voter ID: {voter_id}...")
        for i in range(self.size):
            # We use a standard for loop with index here to safely delete
            for j, record in enumerate(self.hash_table[i]):
                if record["ID"] == voter_id:
                    del self.hash_table[i][j]
                    print(f"✅ Record for Voter ID {voter_id} deleted from Hash Slot {i}.")
                    return
        print("❌ Element doesn't exist.")

    def display_table(self):
        """
        Displays the current contents of the hash table, grouped by house number
        within each hash slot for clarity.
        """
        print("\n*** 📊 HASH TABLE CONTENTS (Keyed by House No.) ***")
        # 
        for i in range(self.size):
            print(f"\n--- ➡️ Hash Slot {i} ---")
            if not self.hash_table[i]:
                print("  Empty")
            else:
                # Group records by house number within the slot
                house_groups = {}
                for record in self.hash_table[i]:
                    house_no = record["House_No"]
                    if house_no not in house_groups:
                        house_groups[house_no] = []
                    house_groups[house_no].append(record)

                # Display members of each house with full details
                for house_no, member_list in house_groups.items():
                    # member_list[0]['Members'] gives the total members count from any record in that house
                    print(f"  🏡 House {house_no} (Total Members: {member_list[0]['Members']}):")
                    for member in member_list:
                        print(f"    - Name: {member['Name']}, ID: {member['ID']}, Age: {member['Age']}, Address: {member['Address']}")
        print("**************************************************")


def get_voter_details(house_no, members_count, i):
    """Utility function to collect details for a single voter."""
    print(f"\n--- Collecting Details for Member {i+1} in House {house_no} ---")
    
    try:
        age_ip = int(input("Enter age: "))
    except ValueError:
        print("Invalid age input. Must be a number.")
        return None
    
    if age_ip >= 18:
        try:
            voter_id = int(input("Enter voter ID (must be unique): "))
            name_input = input("Enter name: ")
            address_input = input("Enter address: ")
            return {
                "house_no": house_no,
                "voter_id": voter_id,
                "name": name_input,
                "address": address_input,
                "members_count": members_count,
                "age": age_ip
            }
        except ValueError:
            print("Invalid Voter ID input. Must be a number. Record skipped.")
            return None
    else:
        print("Not eligible (under 18) - Record skipped.")
        return None

def main():
    """Main execution loop for the hash table program."""
    print("--- VOTER RECORD HASH TABLE SYSTEM ---")
    try:
        # size = int(input("Enter number of house slots for the Hash Table (Size): "))
        size = 100
        if size <= 0:
            print("Size must be a positive integer.")
            return
    except ValueError:
        print("Invalid input for size. Exiting.")
        return

    # Initialize the Hash Table
    voter_ht = VoterRecordHashTable(size)

    while True:
        print("\n*** MENU ***")
        print("1. Insert Record for a House")
        print("2. Display Table Contents")
        print("3. Search by Voter ID")
        print("4. Delete by Voter ID")
        print("5. Exit")
        print("************")
        
        try:
            choice = int(input("Enter your choice: "))
        except ValueError:
            print("Invalid input. Please enter a number.")
            continue

        if choice == 1:
            try:
                house_no = int(input("Enter house number: "))
                members_count = int(input("Enter total number of eligible (18+) members to insert from this house: "))
                
                for i in range(members_count):
                    details = get_voter_details(house_no, members_count, i)
                    if details:
                        voter_ht.insert_record(
                            details["house_no"], 
                            details["voter_id"], 
                            details["name"], 
                            details["address"], 
                            details["members_count"], 
                            details["age"]
                        )
            except ValueError:
                print("Invalid input for house number or member count.")
            
        elif choice == 2:
            voter_ht.display_table()
            
        elif choice == 3:
            try:
                key = int(input("Enter voter ID to be searched: "))
                voter_ht.search_record_by_id(key)
            except ValueError:
                print("Invalid input. Please enter a numeric ID.")

        elif choice == 4:
            try:
                key = int(input("Enter voter ID to be deleted: "))
                voter_ht.delete_record_by_id(key)
            except ValueError:
                print("Invalid input. Please enter a numeric ID.")
                
        elif choice == 5:
            print("Exited. Thank you!")
            break
            
        else:
            print("Invalid choice. Please select from 1 to 5.")

if __name__ == "__main__":
    main()