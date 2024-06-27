import sqlite3
import sys
import getpass
from helper_func import tabulate_it
from helper_func import validate_input
from termcolor import cprint


class UserTypeDatabase:
    def __init__(self, database_name):
        """Initialize the Database with the specified SQLite database."""
        self.livewire = sqlite3.connect(database_name)
        self.create_custom_table(user_type="admin")
        self.create_custom_table(user_type="user")

    def create_custom_table(self, user_type="user"):
        """Create the custom table if it doesn't exist."""
        cursor = self.livewire.cursor()
        create_table_query = f"""
        CREATE TABLE IF NOT EXISTS {user_type} (
            sn INTEGER PRIMARY KEY AUTOINCREMENT,
            {user_type}_name TEXT CHECK(LENGTH({user_type}_name) <= 8),
            password TEXT CHECK(LENGTH(password) <= 8)
        )
        """
        cursor.execute(create_table_query)
        self.livewire.commit()
        if not self.check_user_existence("admin", user_type="admin"):
            """Add a default admin for managing admin task """
            self.add_user_to_table(
                ("admin", "admin123"), is_logged_in=True, user_type="admin"
            )
            cprint("Super user added successfully.",'green')

    def add_user_to_table(self, user_data, is_logged_in, user_type="user"):
        """Add user data to the table if it doesn't already exist and the current user is logged in."""
        if is_logged_in:
            cursor = self.livewire.cursor()
            user_name = user_data[0].strip()  # Trim leading and trailing spaces
            password = user_data[1].strip()  # Trim leading and trailing spaces

            # Check if the admin name already exists
            if not self.check_user_existence(user_name, user_type):
                add_query = f"""
                INSERT INTO {user_type} ({user_type}_name, password)
                VALUES (?, ?)
                """
                cursor.execute(add_query, (user_name, password))
                self.livewire.commit()
                cprint(f"{user_type.capitalize()} added successfully.",'green')
                self.livewire.commit()  # Update sn to rowid
                self.reassign_serial_numbers(user_type)
            else:
                cprint(f"{user_type} with the same name already exists.",'yellow')
        else:
            cprint("You are not logged in. Please log in to add another admin.",'red')

    def update_password(
        self, current_username, current_password, new_password, user_type="user"
    ):
        """Update the password of the current user."""
        cursor = self.livewire.cursor()

        # Validate user by checking if admin_name and password match any record in the database.
        if self.validate_user(current_username, current_password, user_type):
            # Update password only for the current user
            update_query = f"""
            UPDATE {user_type}
            SET password = ?
            WHERE {user_type}_name = ? AND password = ?
            """
            cursor.execute(
                update_query, (new_password, current_username, current_password)
            )
            self.livewire.commit()
            self.reassign_serial_numbers(user_type)
            cprint("Password updated successfully.",'green')
        else:
            cprint(
                "Authentication failed. Please provide correct current username and password.",'yellow'
            )

    def delete_user(self, username, password, user_type="user"):
        """Delete a user if the provided username and password are validated."""
        cursor = self.livewire.cursor()

        # Check if the user exists in the database
        if self.check_user_existence(username, user_type):
            # Validate user by checking if user_type and password match any record in the database.
            if self.validate_user(username, password, user_type):
                # Count the number of entries in the database for the given user type
                count_query = f"""
                SELECT COUNT(*) FROM {user_type}
                """
                cursor.execute(count_query)
                num_entries = cursor.fetchone()[0]

                if num_entries == 1:
                    cprint("Cannot delete the last user entry.",'yellow')
                else:
                    # Delete the user from the database
                    delete_query = f"""
                    DELETE FROM {user_type}
                    WHERE {user_type}_name = ? AND password = ?
                    """
                    cursor.execute(delete_query, (username, password))
                    self.livewire.commit()
                    self.reassign_serial_numbers(user_type)
                    cprint("User deleted successfully.",'green')
            else:
                cprint(
                    "Authentication failed. Please provide correct username and password.","yellow"
                )
        else:
            cprint("User does not exist in the database.",'red')

    def view_data_table(self, user_type="user"):
        """View the contents of the admin table."""
        cursor = self.livewire.cursor()
        view_query = f"""
        SELECT * FROM {user_type}
        """
        cursor.execute(view_query)
        user_records = cursor.fetchall()

        table_headers = ["S.N", "User Name", "Password"]
        table_data = []
        for record in user_records:
            # :<15 ensures padded with spaces to a width of 15 characters.
            table_data.append([record[0], f"{record[1]:<15}", record[2]])
        tabulate_it(table_data, table_headers, "blue")

    def reassign_serial_numbers(self, user_type="user"):
        """Reassign serial numbers based on the current order of records in the database."""
        cursor = self.livewire.cursor()
        reassign_query = f"""
        UPDATE {user_type}
        SET sn = rowid
        """
        cursor.execute(reassign_query)

        # Retrieve all records with their updated rowid as serial numbers
        updated_records_query = f"""
        SELECT rowid, * FROM {user_type}
        """
        cursor.execute(updated_records_query)
        updated_records = cursor.fetchall()

        # Update serial numbers in the database based on the updated rowid
        update_sn_query = f"""
        UPDATE {user_type}
        SET sn = ?
        WHERE rowid = ?
        """
        for index, record in enumerate(updated_records, start=1):
            cursor.execute(update_sn_query, (index, record[0]))
        self.livewire.commit()

    def close_connection(self):
        """Close the database connection."""
        self.livewire.close()

    def validate_user(self, user_name, password, user_type="user"):
        """Validate user by checking if user_name and password match any record in the database."""
        cursor = self.livewire.cursor()
        validate_query = f"""
        SELECT * FROM {user_type} WHERE {user_type}_name = ? AND password = ?
        """
        cursor.execute(validate_query, (user_name, password))
        if cursor.fetchone():
            return True
        else:
            return False

    def check_user_existence(self, user_name, user_type="user"):
        """Check if an user name is present in the database."""
        cursor = self.livewire.cursor()

        # Query to check if the user name exists in the database
        check_query = f"""
        SELECT * FROM {user_type} WHERE {user_type}_name = ?
        """
        cursor.execute(check_query, (user_name,))

        # Fetch the result
        result = cursor.fetchone()
        # If result is not None, user name exists in the database
        if result:
            return True
        else:
            return False


def update_password(user_type_db, user_type=None):
    current_username = input("Enter username to change: ")
    if user_type_db.check_user_existence(current_username, user_type):
        current_password = getpass.getpass(prompt="Enter current password: ")
        if (user_type_db.validate_user(current_username, current_password, user_type)):
            user_info(type='password')
            new_password = getpass.getpass(prompt="Enter new password: ")
            # Validate new password
            if validate_input(new_password, type="password"):
                user_type_db.update_password(
                    current_username, current_password, new_password, user_type=user_type
                )
                display_tasks()
            else:
                cprint("Invalid new password format. Please try again.", "yellow")
                display_tasks()
        else:
            cprint(
                f"{user_type.capitalize()}'s account credentials are incorrect.",
                "red",
            )
            display_tasks()
    else:
        cprint(f"{user_type.capitalize()} account does not exist", "red")
        display_tasks()


def user_info(type="both"):
    cprint("\n-- Account validation info --")
    if type in ["both", "username"]:
        cprint(
            "Usernames should be between 3 and 8 characters long and should only contain letters.",'green'
        )
    if type in ["both", "password"]:
        cprint(
            "Password needs to be between 6 and 12 characters long and include at least one number.",'green'
        )
    print("")


def display_tasks():
    """Display tasks to add user, delete user, update password, and run these tasks."""
    table_data = [
        ["1", "Add user account"],
        ["2", "Delete user account"],
        ["3", "Change user passwords"],
        ["4", "Update admin password"],
        ["5", "View user credentials"],
        ["0", "Exit"],
    ]
    tabulate_it(table_data, ["S.N", "Tasks"], "green")

    choice = input("Enter your choice: ")

    if choice == "1":
        user_info()
        # Add User
        user_name = input("Enter user name: ")
        password = getpass.getpass(prompt="Enter password: ")
        # Debugging code
        # print(validate_input(user_name), validate_input(password, type="password"))
        # Validate username and password
        if validate_input(user_name) and validate_input(password, type="password"):
            user_type_db.add_user_to_table((user_name, password), is_logged_in=True)
            display_tasks()
        else:
            cprint("Invalid username or password format. Please try again.", "yellow")
            display_tasks()
    elif choice == "2":
        # Delete User
        user_name = input("Enter user name: ")
        if user_type_db.check_user_existence(user_name):
            password = getpass.getpass(prompt="Enter password: ")
            user_type_db.delete_user(user_name, password)
            display_tasks()
        else:
            cprint("User does not exist", "red")
            display_tasks()
    elif choice == "3":
        # Update User Password
        update_password(user_type_db, user_type="user")
    elif choice == "4":
        # Change Admin Password
        update_password(user_type_db, user_type="admin")
    elif choice == "5":
        user_type_db.view_data_table()
        display_tasks()
    elif choice == "0":
        cprint("Exiting admin control panel", "red")
    else:
        cprint("Invalid choice. Please try again.", "yellow")
        display_tasks()
    # After performing all necessary operations, close the database connection
    user_type_db.close_connection()


def authenticate_user(user_type="user"):
    user_name = input(f"Enter {user_type} name: ")
    password = getpass.getpass(prompt="Enter password: ")
    if user_type_db.validate_user(user_name, password, user_type):
        cprint(f"Access have been granted to run {user_type} task",'green')
        sys.exit(0)
    else:
        sys.exit(1)  # Return exit code 1 for False


if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Instantiate an object of the database class
        user_type_db = UserTypeDatabase("admin_database.db")
        if sys.argv[1] == "admin_level":
            authenticate_user(user_type="admin")
        elif sys.argv[1] == "user_level":
            authenticate_user(user_type="user")
        elif sys.argv[1] == "admin_task":
            display_tasks()
        else:
            print("Invalid argument.")
        user_type_db.close_connection()
    else:
        print("Please provide an argument")
