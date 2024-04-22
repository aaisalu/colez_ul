#  subprocess module is very powerful and is commonly used for tasks such as running system commands, launching other programs, or even for more complex interactions like creating pipelines of commands.

import random
import subprocess
import helper_func
from helper_func import tabulate_it

# Refrence command for executing:  netsh wlan show profile name="network name" key=clear


def get_wifi_profiles():
    try:
        # decoding the output of the command from bytes to a UTF-8 encoded string. output of subprocess.check_output is a byte string, and .decode("utf-8") is converting it into a human-readable string.
        output = subprocess.check_output(["netsh", "wlan", "show", "profiles"]).decode(
            "utf-8"
        )
        profiles = [
            line.split(":")[1].strip()
            for line in output.split("\n")
            if "All User Profile" in line
        ]
        return profiles
    except subprocess.CalledProcessError:
        return []


def get_wifi_data(profile):
    """
    Retrieve the wifi data for a specific WiFi profile.
    """
    try:
        output = subprocess.check_output(
            ["netsh", "wlan", "show", "profile", profile, "key=clear"]
        ).decode(
            "utf-8", errors="ignore"
        )  # Ignore errors while decoding
        # find the password type from raw data
        password_lines = [
            line.split(":")[1].strip()
            for line in output.split("\n")
            if "Key Content" in line
        ]
        # find the encryption type from raw data
        authentication = [
            line.split(":")[1].strip()
            for line in output.split("\n")
            if "Authentication" in line
        ][0]
        return [
            authentication if authentication else "",
            # password lines is in list so we slice to get the value
            password_lines[0] if password_lines else "",
        ]
    except subprocess.CalledProcessError as e:
        print(f"Error occurred while retrieving data for {profile}: {e}")
        return None


def main():
    headers = ["S.N", "Wi-Fi Name", "Authentication", "Password"]
    random_number = random.randint(0, 100)
    profiles = get_wifi_profiles()
    if not profiles:
        print("No WiFi profiles found.")
        return

    result_list = []
    for i, profile in enumerate(profiles, start=1):
        wifi_data = get_wifi_data(profile)
        if wifi_data is None:
            continue  # Skip this profile and move to the next one
        result_list.append([i, profile, wifi_data[0], wifi_data[1]])
    tabulate_it(result_list, headers, "green")
    wifi_directory = helper_func.create_folder("WiFi_keys")
    with open(rf"{wifi_directory}/wifi_{random_number}.csv", "w") as file:
        # Write the headers to the file
        file.write(",".join(headers) + "\n")
        for row in result_list:
            file.write(",".join(map(str, row)) + "\n")


if __name__ == "__main__":
    main()

# FOR DEBUG ONLY

# encoded data to be decoded by UTF 8
# b"\r\nProfiles on interface Wi-Fi:\r\n\r\nGroup policy profiles (read only)\r\n---------------------------------\r\n    <None>\r\n\r\nUser profiles\r\n-------------\r\n    All User Profile     : Wifi One\r\n    All User Profile     : TP-Link_A205\r\n    All User Profile     : Wifi Three\r\n    All User Profile     : Wifi Five\r\n    All User Profile     : Wifi Six\r\n\r\n"


# profiles = [
#     "",
#     "Profiles on interface Wi-Fi:",
#     "",
#     "Group policy profiles (read only)",
#     "---------------------------------",
#     "    <None>",
#     "",
#     "User profiles",
#     "-------------",
#     "    All User Profile     : Wifi One",
#     "    All User Profile     : Wifi Two",
#     "    All User Profile     : Wifi Three",
#     "    All User Profile     : Wifi Four",
#     "    All User Profile     : Wifi Five",
#     "",
# ]
