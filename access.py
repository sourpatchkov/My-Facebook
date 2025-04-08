import os
import sys

database = {
    "lists": {},  
    "pictures": {},
    "current_friend": None, 
    "profile_owner": None,  
}

# Track if the first command has been executed
firstTime = False

#Function to log actions to audit.txt and print them to the console
def log(action):
    with open("audit.txt", "a") as file:
        file.write(action + "\n")
    print(action)

#Save the current state of pictures and lists to their files
def save_data():
    with open("pictures.txt", "w") as file:
        for name, data in database["pictures"].items():
            file.write(f"{name}: {data['owner']} {data['list']} {data['perms']}\n")  

    with open("lists.txt", "w") as f:
        for listname, members in database["lists"].items():
            f.write(f"{listname}: {' '.join(members)}\n")

#Check if the name is valid 
def nameCheck(name):
    if len(name) > 30:
        log(f"Error: {name} is too long.")
        return False

    invalid_chars = ['/', ':', ' ', '\r', '\n', '\t', '\x0b', '\x0c']  

    for char in name:
        if char in invalid_chars:
            log(f"Error: {name} contains invalid characters")
            return False
    
    return True

#Add a friend to the friends list and set the profile owner
def friendadd(friendname):
    global firstTime

    if not firstTime:
        if not nameCheck(friendname):
            return

        with open("friends.txt", "a") as f:
            f.write(friendname + "\n")

        database["profile_owner"] = friendname  
        firstTime = True
        log(f"Friend {friendname} added")
        return

    if database["current_friend"] != database["profile_owner"]:
        log("Error: only the profile owner may issue friendadd command")
        return

    if not nameCheck(friendname):
        return

    with open("friends.txt", "r") as file:
        friends = file.read().splitlines()

    if friendname not in friends:
        with open("friends.txt", "a") as file:
            file.write(friendname + "\n")
        log(f"Friend {friendname} added")
    else:
        log(f"Error: Friend {friendname} already exists")

#Change viewing friend
def viewby(friendname):
    with open("friends.txt", "r") as file:
        friends = file.read().splitlines()
    if friendname in friends:
        database["current_friend"] = friendname  
        log(f"Friend {friendname} views the profile")
    else:
        log(f"Login failed: invalid friend name")

#Logout the current friend
def logout():
    if database["current_friend"]:
        log(f"Friend {database['current_friend']} logged out")
        database["current_friend"] = None  # Clear the current friend
    else:
        log("Error: No one is logged in.")

#Add a list to the database
def listadd(listname):
    if not database["current_friend"]:
        log("Error: No one is viewing the profile.")
        return

    if database["current_friend"] != database["profile_owner"]:
        log("Error: only the profile owner may issue listadd command")
        return

    if not nameCheck(listname):
        return
    
    if listname == "nil":
        log("Error: List name cannot be 'nil'.")
        return

    if listname not in database["lists"]:
        database["lists"][listname] = []
        log(f"List {listname} added")
    else:
        log(f"Error: list {listname} already exists")

#Add friend to a list
def friendlist(friendname, listname):
    if database["current_friend"] != database["profile_owner"]:
        log("Error: Only the profile owner can add friends to a list.")
        return

    with open("friends.txt", "r") as f:
        friends = f.read().splitlines()
    if friendname not in friends:
        log(f"Error: Friend '{friendname}' does not exist.")
        return

    if listname not in database["lists"]:
        log(f"Error: List '{listname}' does not exist.")
        return

    if friendname in database["lists"][listname]:
        log(f"Error: Friend '{friendname}' is already in the list '{listname}'.")
        return

    database["lists"][listname].append(friendname)
    log(f"Friend {friendname} added to list {listname}")

#Post a picture to the database
def postpicture(picturename):
    if not database["current_friend"]:
        log("Error: No one is viewing the profile. Cannot post picture.")
        return

    if not nameCheck(picturename):
        return

    if picturename in database["pictures"]:
        log(f"Error: file {picturename} already exists.")
        return

    try:
        with open(picturename, "w") as file:
            file.write(picturename + "\n")  
    except Exception as e:
        log(f"Error: Could not create picture file {picturename}. {e}")
        return

    database["pictures"][picturename] = {
        "owner": database["current_friend"],
        "list": "nil",
        "perms": "rw -- --"
    }
    log(f"File {picturename} with owner {database['current_friend']} and default permissions added")

#Add a picture to a list
def chlst(picturename, listname):
    if not database["current_friend"]:
        log("Error with chlst: No one is viewing the profile. Cannot change list.")
        return

    if picturename not in database["pictures"]:
        log(f"Error with chlst: Picture '{picturename}' does not exist.")
        return

    if listname != "nil" and listname not in database["lists"]:
        log(f"Error with chlst: List '{listname}' does not exist.")
        return

    picture = database["pictures"][picturename]
    current_user = database["current_friend"]

    if current_user != database["profile_owner"]:  
        if picture["owner"] != current_user:
            log(f"Error: Only the profile owner or the picture owner can change the list for '{picturename}'.")
            return
        if listname != "nil" and current_user not in database["lists"].get(listname, []):
            log(f"Error with chlst: User {current_user} is not a member of list {listname}")
            return

    picture["list"] = listname
    log(f"List for {picturename} changed to {listname} by {current_user}")

# Change the permissions of a picture
def chmod(picturename, perms):
    if not database["current_friend"]:
        log("Error with chmod: No one is viewing the profile. Cannot change permissions.")
        return

    if picturename not in database["pictures"]:
        log(f"Error with chmod: file {picturename} not found")
        return

    with open("friends.txt", "r") as f:
        friends = f.read().splitlines()
    if database["current_friend"] not in friends:
        log(f"Error with chmod: Current friend {database['current_friend']} does not exist.")
        return

    perms_parts = perms.split()
    # Check if there are exactly 3 parts and each part is of length 2
    # and contains valid characters ('r', 'w', '-')
    if len(perms_parts) != 3 or not all(len(part) == 2 and part[0] in "r-" and part[1] in "w-" for part in perms_parts):
        log(f"Error: Invalid permission format {perms}.")
        return

    picture = database["pictures"][picturename]
    current_user = database["current_friend"]

    if current_user != database["profile_owner"] and picture["owner"] != current_user:
        log(f"Error: Only the profile owner or the picture owner can change permissions for '{picturename}'.")
        return

    picture["perms"] = perms
    log(f"Permissions for {picturename} set to {perms} by {current_user}")

#Change the owner of a picture
def chown(picturename, friendname):
    if database["current_friend"] != database["profile_owner"]:
        log("Error: Only the profile owner can change the owner of a picture.")
        return

    if picturename not in database["pictures"]:
        log(f"Error with chown: file {picturename} not found")
        return

    with open("friends.txt", "r") as f:
        friends = f.read().splitlines()
    if friendname not in friends:
        log(f"Error: Friend '{friendname}' does not exist.")
        return

    database["pictures"][picturename]["owner"] = friendname
    log(f"Owner of {picturename} changed to {friendname}")

#Read comments from a picture
def readcomments(picturename):
    if not database["current_friend"]:
        log("Error: No one is viewing the profile. Cannot read comments.")
        return

    if picturename not in database["pictures"]:
        log(f"Error: Picture '{picturename}' does not exist.")
        return

    picture = database["pictures"][picturename]
    current_user = database["current_friend"]

    if current_user == picture["owner"] and "r" in picture["perms"][0:2]:
        pass  # Owner has read access
    elif picture["list"] != "nil" and current_user in database["lists"].get(picture["list"], []) and "r" in picture["perms"][3:5]:
        pass  # List member has read access
    elif "r" in picture["perms"][6:]:
        pass  # Others have read access
    else:
        log(f"Friend {current_user} denied read access to {picturename}")
        return

    try:
        with open(picturename, "r") as file:
            content = file.read().strip()
        log(f"Friend {current_user} reads {picturename} as:\n{content}")
    except Exception as e:
        log(f"Error: Could not read comments from '{picturename}'. {e}")

# Write comments to a picture
def writecomments(picturename, text):
    if not database["current_friend"]:
        log("Error: No one is viewing the profile. Cannot write comments.")
        return

    if picturename not in database["pictures"]:
        log(f"Error: Picture '{picturename}' does not exist.")
        return

    picture = database["pictures"][picturename]
    current_user = database["current_friend"]

    if current_user == picture["owner"] and "w" in picture["perms"][0:2]:
        pass  # Owner has write access
    elif picture["list"] != "nil" and current_user in database["lists"].get(picture["list"], []) and "w" in picture["perms"][3:5]:
        pass  # List member has write access
    elif "w" in picture["perms"][6:]:
        pass  # Others have write access
    else:
        log(f"Friend {current_user} denied write access to {picturename}")
        return

    try:
        with open(picturename, "a") as file:
            file.write(text + "\n")
        if current_user == database["profile_owner"]:
            log(f"User {current_user} wrote a comment to {picturename}: {text}")
        else:
            log(f"Friend {current_user} wrote to {picturename}: {text}")
    except Exception as e:
        log(f"Error: Could not write comment to '{picturename}'. {e}")


#Read line input from user
def lineReader(command):
    parts = command.split()
    if not parts:
        return
    command = parts[0].lower()
    args = parts[1:]
    
    if command == "end":
        save_data()
        log("Program terminated.")
        return False
    elif command == "friendadd" and len(args) == 1:
        friendadd(args[0])
    elif command == "viewby" and len(args) == 1:
        viewby(args[0])  
    elif command == "logout":
        logout()
    elif command == "listadd" and len(args) == 1:
        listadd(args[0])
    elif command == "friendlist" and len(args) == 2:
        friendlist(args[0], args[1])
    elif command == "postpicture" and len(args) == 1:
        postpicture(args[0])
    elif command == "chlst" and len(args) == 2:
        chlst(args[0], args[1])
    elif command == "chmod" and len(args) == 4:
        chmod(args[0], " ".join(args[1:]))
    elif command == "chown" and len(args) == 2:
        chown(args[0], args[1])
    elif command == "readcomments" and len(args) == 1:
        readcomments(args[0])
    elif command == "writecomments" and len(args) >= 2:  
        writecomments(args[0], " ".join(args[1:]))
    else:
        log(f"Error: Unknown or invalid command.")
    return True

def main():
    open("audit.txt", "w").close()
    open("pictures.txt", "w").close()
    open("lists.txt", "w").close()
    open("friends.txt", "w").close()
    
    if len(sys.argv) > 1:  # Read from file if provided
        filename = sys.argv[1]
        if os.path.exists(filename):
            with open(filename, "r") as f:
                commands = f.read().splitlines()
            for command in commands:
                if not lineReader(command):
                    break
        else:
            print(f"Error: File '{filename}' not found.")
    else:  # Interactive mode
        while True:
            command = input("Enter a command: ").strip()
            if not lineReader(command):
                break

if __name__ == "__main__":
    main()
