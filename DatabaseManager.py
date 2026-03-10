import json 
import threading
from SystemLogging import *

# created a file to manage all reading and writing of files so if one file name location or name changes i dont need to change everywhere and only here

# created locks for every database file to prevent corruption while writng twice
votes_lock = threading.Lock()
users_lock = threading.Lock()
uservotes_lock = threading.Lock()
votekeys_lock = threading.Lock()
solanakeys_lock = threading.Lock()
registered_lock = threading.Lock()
masterwallet_lock = threading.Lock()
privileges_lock = threading.Lock()

"""Opening functions for databases"""  
def OpenVotes():
    log("Opening votes.json")
    with votes_lock:
        with open("database/votes.json", "r") as file:
            data = json.load(file)
            return data
    
def OpenUsers():
    log("Opening users.json")
    with users_lock:
        with open("database/users.json", "r") as file:
            data = json.load(file)
            return data
    
def OpenUserVotes():
    log("Opening uservotes.json")
    with uservotes_lock:
        with open("database/uservotes.json", "r") as file:
            data = json.load(file)
            return data

def OpenVoteKeys():
    log("Opening votekeys.json")
    with votekeys_lock:
        with open("database/votekeys.json", "r") as file:
            data = json.load(file)
            return data
    
def OpenSolanaKey():
    log("Opening solanakeys.json")
    with solanakeys_lock:
        with open("database/solanakeys.json", "r") as file:
            data = json.load(file)
            return data
    
def OpenRegistered():
    log("Opening registered.json")
    with registered_lock:
        with open("database/registered.json", "r") as file:
            data = json.load(file)
            return data
    
def OpenMasterWallet():
    log("Opening masterwallet.json")
    with masterwallet_lock:
        with open("database/masterwallet.json", "r") as file:
            data = json.load(file)
            return data

def OpenPrivileges():
    log("Opening privileges.json")
    with privileges_lock:
        with open("database/privileges.json", "r") as file:
            data = json.load(file)
            return data



"""wrting functions for databases"""

def WriteVotes(data):
    log("Writing votes.json")
    with votes_lock:
        with open("database/votes.json", "w") as file:
            json.dump(data, file, indent=4)

def WriteUsers(data):
    log("Writing users.json")
    with users_lock:
        with open("database/users.json", "w") as file:
            json.dump(data, file, indent=4)

def WriteUserVotes(data):
    log("Writing uservotes.json")
    with uservotes_lock:
        with open("database/uservotes.json", "w") as file:
            json.dump(data, file, indent=4)

def WriteVoteKeys(data):
    log("Writing votekeys.json")
    with votekeys_lock:
        with open("database/votekeys.json", "w") as file:
            json.dump(data, file, indent=4)

def WriteSolanaKey(data):
    log("Writing solanakeys.json")
    with solanakeys_lock:
        with open("database/solanakeys.json", "w") as file:
            json.dump(data, file, indent=4)
    
def WriteRegistered(data):
    log("Writing registered.json")
    with registered_lock:
        with open("database/registered.json", "w") as file:
            json.dump(data, file, indent=4)

def WritePrivileges(data):
    log("Writing privileges.json")
    with privileges_lock:
        with open("database/privileges.json", "w") as file:
            json.dump(data, file, indent=4)