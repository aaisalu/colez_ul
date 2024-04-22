import sqlite3
import sys
from helper_func import tabulate_it


class UserTypeDatabase:
    def __init__(self, database_name):
        """Initialize the AdminDatabase with the specified SQLite database."""
        self.conn = sqlite3.connect(database_name)
        self.create_custom_table(user_type="admin")
        self.create_custom_table(user_type="user")

    def create_custom_table(self, user_type="user"):
        """Create the custom table if it doesn't exist."""
        cursor = self.conn.cursor()
        create_table_query = f"""
        CREATE TABLE IF NOT EXISTS {user_type} (
            sn INTEGER PRIMARY KEY AUTOINCREMENT,
            {user_type}_name TEXT CHECK(length({user_type}_name) <= 10),
            password TEXT CHECK(length(password) <= 10)
        )
        """
        cursor.execute(create_table_query)
        self.conn.commit()
        if not self.check_user_existence("admin", user_type="admin"):
            self.add_super_user()

    def add_user_to_table(self, user_data, is_logged_in, user_type="user"):
        """Add user data to the table if it doesn't already exist and the current user is logged in."""
        if is_logged_in:
            cursor = self.conn.cursor()
            user_name = user_data[0].strip()  # Trim leading and trailing spaces
            password = user_data[1].strip()  # Trim leading and trailing spaces

            # Check if the admin name already exists
            if not self.check_user_existence(user_name, user_type):
                add_query = f"""
                INSERT INTO {user_type} ({user_type}_name, password)
                VALUES (?, ?)
                """
                cursor.execute(add_query, (user_name, password))
                self.conn.commit()
                print(f"{user_type} added successfully.")
                self.conn.commit()  # Update sn to rowid
                self.reassign_serial_numbers(user_type)
            else:
                print(f"{user_type} with the same name already exists.")
        else:
            print("You are not logged in. Please log in to add another admin.")

    def add_super_user(self):
        """Add a super user with username 'admin' and password 'admin123'."""
        self.add_user_to_table(
            ("admin", "admin123"), is_logged_in=True, user_type="admin"
        )
        print("Super user added successfully.")

    def update_password(
        self, current_username, current_password, new_password, user_type="user"
    ):
        """Update the password of the current user."""
        cursor = self.conn.cursor()

        # Validate user by checking if admin_name and password match any record in the database.
        if self.validate_user(current_username, current_password):
            # Update password only for the current user
            update_query = f"""
            UPDATE {user_type}
            SET password = ?
            WHERE {user_type}_name = ? AND password = ?
            """
            cursor.execute(
                update_query, (new_password, current_username, current_password)
            )
            self.conn.commit()
            self.reassign_serial_numbers(user_type)
            print("Password updated successfully.")
        else:
            print(
                "Authentication failed. Please provide correct current username and password."
            )

    def delete_user(self, username, password, user_type="user"):
        """Delete a user if the provided username and password are validated."""
        cursor = self.conn.cursor()

        # Check if the user exists in the database
        if self.check_user_existence(username, user_type):
            # Validate user by checking if admin_name and password match any record in the database.
            if self.validate_user(username, password):
                # Delete the user from the database
                delete_query = f"""
                DELETE FROM {user_type}
                WHERE {user_type}_name = ? AND password = ?
                """
                cursor.execute(delete_query, (username, password))
                self.conn.commit()
                self.reassign_serial_numbers(user_type)
                print("User deleted successfully.")
            else:
                print(
                    "Authentication failed. Please provide correct username and password."
                )
        else:
            print("User does not exist in the database.")

    def view_data_table(self, user_type="user"):
        """View the contents of the admin table."""
        cursor = self.conn.cursor()
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
        tabulate_it(table_data, table_headers, "green")

    def reassign_serial_numbers(self, user_type="user"):
        """Reassign serial numbers based on the current order of records in the database."""
        cursor = self.conn.cursor()
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
        self.conn.commit()

    def close_connection(self):
        """Close the database connection."""
        self.conn.close()

    def validate_user(self, user_name, password, user_type="user"):
        """Validate user by checking if user_name and password match any record in the database."""
        cursor = self.conn.cursor()
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
        cursor = self.conn.cursor()

        # Query to check if the admin name exists in the database
        check_query = f"""
        SELECT * FROM {user_type} WHERE {user_type}_name = ?
        """
        cursor.execute(check_query, (user_name,))

        # Fetch the result
        result = cursor.fetchone()

        # If result is not None, admin name exists in the database
        if result:
            return True
        else:
            return False


def display_tasks():
    """Display tasks to add user, delete user, update password, and run these tasks."""
    table_data = [
        ["1", "Add User"],
        ["2", "Delete User"],
        ["3", "Update Password"],
        ["4", "View User"],
        ["0", "Exit"],
    ]
    tabulate_it(table_data, ["S.N", "Tasks"], "green")

    choice = input("Enter your choice: ")

    if choice == "1":
        # Add User
        user_name = input("Enter user name: ")
        password = input("Enter password: ")
        user_type_db.add_user_to_table((user_name, password), is_logged_in=True)
    elif choice == "2":
        # Delete User
        user_name = input("Enter admin name: ")
        if user_type_db.check_user_existence(user_name):
            password = input("Enter password: ")
            user_type_db.delete_user(user_name, password)
        else:
            print("User does not exist")
    elif choice == "3":
        # Update Password
        current_username = input("Enter current username: ")
        if user_type_db.check_user_existence(current_username):
            current_password = input("Enter current password: ")
            new_password = input("Enter new password: ")
            user_type_db.update_password(
                current_username, current_password, new_password
            )
        else:
            print("User does not exist")
    elif choice == "4":
        user_type_db.view_data_table()
    elif choice == "0":
        print("Exiting...")
        user_type_db.close_connection()
    else:
        print("Invalid choice. Please try again.")
        display_tasks()
    # After performing all necessary operations, close the database connection
    user_type_db.close_connection()


def authenticate_user(user_type="user"):
    user_name = input("Enter user name: ")
    password = input("Enter password: ")
    if user_type_db.validate_user(user_name, password, user_type):
        print(f"Access have been granted to run {user_type} task")
    else:
        print(f"You don't have acess to run {user_type} task")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Instantiate an object of the AdminDatabase class
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
