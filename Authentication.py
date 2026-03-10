import json
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
import re
from random import randint
from dotenv import load_dotenv #d02 researched how to get from dotenv files
import os
from datetime import datetime, timedelta #d03 research how to get time and get time differences
import smtplib
import email.message
from cryptography.fernet import Fernet
import random
from DatabaseManager import *
from SystemLogging import *


"""generate random words"""

def GenRandomWords():
    try:
        with open("assets/bip39.txt", "r") as file:
            words = [word.strip() for word in file.readlines() if word.strip()] # puts all words into a list by reading each line
        
        random_words = random.sample(words, 3)
        return random_words
    
    except:
        return []
    

"""encryption functions"""

def GenerateKey():
    try:
        return Fernet.generate_key().decode() 
    except:
        return None

def IsKeyValid(key):
    try:
        Fernet(key.encode())
        return True
    except:
        return False

def Encrypt(text, key):
    if not IsKeyValid(key):
        return None

    try:
        fernet = Fernet(key.encode() if isinstance(key, str) else key)
        encrypted_message = fernet.encrypt(text.encode())
        return encrypted_message.decode()
    except:
        return None

def Decrypt(encrypted_message, key):
    if not IsKeyValid(key):
        return None

    try:
        fernet = Fernet(key.encode() if isinstance(key, str) else key)
        decrypted_message = fernet.decrypt(encrypted_message.encode())
        return decrypted_message.decode()
    except:
        return None





"""user id"""

def CreateUserID(name, special_word1, special_word2, special_word3):
    name = name.lower()
    special_word1 = special_word1.lower()
    special_word2 = special_word2.lower()
    special_word3 = special_word3.lower()

    if name and special_word1 and special_word2 and special_word3:
        pass

    else:
        return False

    combined = name + special_word1 + special_word2 + special_word3

    ascii_string = ""

    for character in combined:
        ascii_string += str(ord(character))
    
    prime = 5165628373 #D01: from https://bigprimes.org/

    variation1 = int(ascii_string) * prime

    variation2 = 0

    for i in range(0, len(str(variation1)), 8):  #D02: TypeError tried to get len of int
        part = str(variation1)[i:i+8]
        part = int(part)  # D03: TypeError int object is not subscriptable
        variation2 += part

    variation3 = variation2 + len(combined)

    if len(str(variation3)) < 8:
        final = str(variation3.zfill(8))
    elif len(str(variation3)) > 8:
        final = str(variation3)[:8]

    return final



"""verify email"""

def SendEmail(user_email, subject, message_html):  # turned the send email part into qa function and separated it from the verify email function to make it more modular and easier to test
    log(f"sending email to a user with email: {user_email}")
    load_dotenv()

    sender_email = os.getenv("SENDER_EMAIL")
    sender_password = os.getenv("SENDER_PASSWORD")
    smtp_server = os.getenv("SMTP_SERVER")
    port = int(os.getenv("PORT"))

    message = email.message.EmailMessage()
    message["From"] = sender_email
    message["To"] = user_email
    message["Subject"] = subject
    
    message.add_alternative(message_html, subtype="html")

    try:
        with smtplib.SMTP_SSL(smtp_server, port) as server:
            server.login(sender_email, sender_password)
            server.send_message(message)

    except Exception as e:
        print(f"Error sending email: {e}")
        return False



def VerifyEmail(user_email): #d05 had to change variable email to user_email to prevent clahing with email.message library
    if user_email:
        pass
    else:
        return False

    num = randint(100000, 999999)
    creation_time = datetime.now()
    expiry_time = timedelta(minutes = 10)
    expiry_datetime = creation_time + expiry_time

    #D01: wont store email credentials here, put in .env file for security


    message_html = f"""
    <html>
        <body>
            <h1 style="color: #4CAF50;">Your TrueVote Verification Code</h1>
            <p>Your code is: <strong style="font-size: 20px; color: #2196F3;">{num}</strong></p>
            <p>This code is valid for <strong>10 minutes</strong>.</p>
            <p>If you did not request this code, please ignore this email.</p>
            <hr>
            <p style="font-size: 12px; color: #888;">This is an automated message. Please do not reply.</p>
        </body>
    </html>
    """  #d04 html builder

    email_status = SendEmail(user_email, "Your TrueVote Verification Code", message_html)

    log(f"sent email to a user with email: {user_email}")

    return str(num), str(expiry_datetime) #CONVERTED TO STRINGS FOR API


"""password"""

class Password:
    def __init__(self, password):
        self.password = password
        self.hasher = PasswordHasher()
        self.hashed_password = self.hash()

    def hash(self):
        return self.hasher.hash(self.password)

    @staticmethod
    def verify(plain_password, hashed_password):
        hasher = PasswordHasher()
        try:
            hasher.verify(hashed_password, plain_password)
            return True
        except VerifyMismatchError:
            return False



"""login"""

def EmailToID(email):
    #with open("database/registered.json", "r") as file:
    #    registered = json.load(file)

    registered = OpenRegistered()

    try:
        user_id = registered[email]
        return user_id

    except KeyError:
        return False    

def Login(user_email, user_password):  # d01 i want it to login with email not uiser_id so i will create function to turn email into user id
    log(f"logging in a user with email: {user_email}")

    user_email = user_email.lower()

    #with open("database/users.json", "r") as file:
    #    user_database = json.load(file)

    user_database = OpenUsers()

    user_id = EmailToID(user_email)

    if user_id == False:
        return False

    try:
        user_data = user_database[user_id]
    except KeyError:
        return False

    if user_data["login_attempts"] >= 10:
        last_login_str = user_data.get("last_login", "")
        try:
            if last_login_str:
                last_login = datetime.strptime(last_login_str, "%Y-%m-%d %H:%M:%S")
                if datetime.now() < last_login + timedelta(hours=1):
                    return "locked"
                else:
                    user_database[user_id]["login_attempts"] = 0
            else:
                user_database[user_id]["login_attempts"] = 0
        except ValueError:
            user_database[user_id]["login_attempts"] = 0

    user_hashed_password = user_data["hashed_password"]

    status = Password.verify(user_password, user_hashed_password)

    if status == True:
        user_database[user_id]["login_attempts"] = 0
        user_database[user_id]["last_login"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        WriteUsers(user_database)
        return True
    
    elif status == False:
        user_database[user_id]["login_attempts"] += 1
        user_database[user_id]["last_login"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        WriteUsers(user_database)
        return False

    else:
        return False



"""register"""

def RegisterUser(name, user_email, phone, user_password, confirm_password, special_word1, special_word2, special_word3, debug=False):  #d05 had to change variable name password to user_password to prevent clahing with password hasher
    #with open("database/users.json", "r") as file:
    #    user_database = json.load(file)

    log(f"registering a user with email: {user_email}")


    user_email = user_email.lower()
    user_database = OpenUsers()

    if user_password != confirm_password:
        return False
    
    if len(user_password) < 8:
        return False

    if len(re.findall(r"\d", user_password)) < 3:  #d01 researched how to find items in a string
        return False

    special_chars = r"[/\\?!@£*()+=\[\]{}%]" #d04 raw string error fixed - escaped brackets for regex
    if len(re.findall(special_chars, user_password)) < 1:
        return False

    userid = CreateUserID(name, special_word1, special_word2, special_word3) #d02 had to change order to userid made first before cvhcekinh if in database to use as primary key

    try:
        user_database[userid]
        exists = True
    except KeyError:
        exists = False

    if exists:
        return False
    
    #d03 stopped making this algorithm and moved to make hashing algorithm first

    pwd = Password(user_password)
    words = Password(special_word1 + special_word2 + special_word3)

    user_database[userid] = {
        "name": name,
        "email": user_email,
        "hashed_password": pwd.hashed_password,
        "hashed_special_words": words.hashed_password,
        "phone": phone,
        "vote_creations": 0, #d06 added vote creations to hold creation amount
        "login_attempts": 0,
        "last_login": "",
        "account_created": str(datetime.now().date())
    }

    #with open("database/users.json", "w") as file:
    #    json.dump(user_database, file, indent=4)

    WriteUsers(user_database)

    #with open("database/registered.json", "r") as file:
    #    registered = json.load(file)

    registered = OpenRegistered()

    registered[user_email] = userid

    #with open("database/registered.json", "w") as file:
    #    json.dump(registered, file)

    WriteRegistered(registered)

    log(f"registered a user with email: {user_email}")


    return True



"""verify 3 words validity"""

def VerifyWords(word1, word2, word3):
    with open("assets/bip39.txt", "r") as file: #simply just check if all words are valid by look if they are present in the wordlist 
        words = [word.strip() for word in file.readlines()]

    try:
        if word1 in words and word2 in words and word3 in words:
            return True
        else:
            return False
    except:
        return False



"""verify 3 words belong to user"""

def VerifyWordsToUser(word1, word2, word3, user_id):
    word1 = word1.strip().lower()
    word2 = word2.strip().lower()
    word3 = word3.strip().lower()


    try:
        if VerifyWords(word1, word2, word3) == True: # first check validity of words
            #print("words are valid")
            pass
        else:
            #print("words are not valid")
            return False
    except:
        return False
    
    user_database = OpenUsers()

    try:
        user_data = user_database[user_id]
    except:
        #print("user not found")
        return False

    user_hashed_words = user_data["hashed_special_words"]

    status = Password.verify(word1 + word2 + word3, user_hashed_words) # now check if words belong to that specific user

    if status == True:
        return True

    else:
        #print("words do not belong to user")
        return False
    



"""privileges system"""

def IsUserInPrivileges(user_id, role):
     # converts plural versions to singular if input is wrong
    if role == "admins":
        role = "admin"
    elif role == "auditors":
        role = "auditor"
    
    if role not in ["admin", "auditor"]:
        return False

    privileges_database = OpenPrivileges()
    
    if user_id in privileges_database.get(role, []):
        return True
    return False

def RemoveUserFromPrivileges(user_id, role):
    if role == "admins":
        role = "admin"
    elif role == "auditors":
        role = "auditor"
    
    if role not in ["admin", "auditor"]:
        return False
    
    privileges_database = OpenPrivileges()
    
    if user_id in privileges_database.get(role, []):
        privileges_database[role].remove(user_id)
        
        WritePrivileges(privileges_database)
        
        return True
    
    return False

def AddUserToPrivileges(user_id, role):
    if role == "admins":
        role = "admin"
    elif role == "auditors":
        role = "auditor"
    
    if role not in ["admin", "auditor"]:
        return False
    
    privileges_database = OpenPrivileges()
    
    if user_id not in privileges_database.get(role, []):
        privileges_database[role].append(user_id)
        
        WritePrivileges(privileges_database)
        
        return True
    
    return False


def GetPrivileges(role="admin"):
    """Get all user IDs for a specific role"""
    if role == "admins":
        role = "admin"
    elif role == "auditors":
        role = "auditor"
    
    if role not in ["admin", "auditor"]:
        return []
    
    privileges_database = OpenPrivileges()
    
    return privileges_database.get(role, [])


"""admin panel"""
