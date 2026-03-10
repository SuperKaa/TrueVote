import json
from datetime import datetime
from TimeManager import *
from Blockchain import FundWallet, CreateAddress
import time
from solders.keypair import Keypair
from solders.message import MessageV0
from solders.transaction import VersionedTransaction
from solana.rpc.api import Client
from solders.pubkey import Pubkey
from spl.memo.instructions import create_memo, MemoParams
from Authentication import Password, GenerateKey, Encrypt, SendEmail
from DatabaseManager import *
from SystemLogging import *



"""create vote id"""

def CreateVoteID(title, reason, organiser_public, user_id, initiation_time): #copied then edited from createuserid
    combined = title + reason + organiser_public +user_id + initiation_time

    ascii_string = ""

    for character in combined:
        ascii_string += str(ord(character))
    
    prime = 9309317 

    variation1 = int(ascii_string) * prime

    variation2 = 0

    for i in range(0, len(str(variation1)), 8):  
        part = str(variation1)[i:i+8]
        part = int(part)  
        variation2 += part

    variation3 = variation2 + len(combined)

    if len(str(variation3)) < 8:
        final = str(variation3.zfill(8))
    elif len(str(variation3)) > 8:
        final = str(variation3)[:8]

    return final



"""create vote"""

def CreateVote(title, reason, organiser_public, start_time, end_time, options_list, user_id, vote_password=None): # resaecrh how to make a paremeter optional # removed mode parameter it is done by checking for password now
    #print("loading databases...")
    #with open("database/votes.json", "r") as file:
    #    vote_database = json.load(file)
    #with open("database/users.json", "r") as file:
    #    user_database = json.load(file)

    log(f"creating a vote with title {title} and reason {reason}")

    vote_database = OpenVotes()  #turned into function to open database to make code cleaner and easier to read and also to fix issue of file not being found because it was trying to open the file before it was created now it will only try to open the file when the function is called which is after the file is created
    user_database = OpenUsers()
    

    initiation_time = str(datetime.now())


    print("checking user...")  # user check
    if user_id not in user_database:
        print(f"User ID {user_id} not found.")
        return False

    if user_database[user_id]["vote_creations"] >= 1:  # check if user has made a vote before
        return False


    print("checking time...") #debug print

    try:
        start = datetime.strptime(start_time.replace(", ", "-").replace(",", "-"), "%Y-%m-%d-%H-%M")
        end = datetime.strptime(end_time.replace(", ", "-").replace(",", "-"), "%Y-%m-%d-%H-%M")
    except ValueError:
        print("invalid time format")
        return False

    if end <= start:
        return False

    if start < datetime.now():
        return False
    

    print("creating vote id...")
    vote_id = CreateVoteID(title, reason, organiser_public, user_id, initiation_time) # now added initiation time for more randomness

    print("checking password...")
    if vote_password:
        pwd = Password(vote_password) 
        hashed_vote_password = pwd.hashed_password
        mode = "private"
    else:
        hashed_vote_password = None
        mode = "public"

    # stopped here to create function to create a solana address
    print("creating blockchain wallet...")
    blockchain_wallet = CreateAddress()

    vote_data = {
        "title": title,
        "reason": reason,
        "organiser": organiser_public,
        "creator": user_id,
        "mode": mode,
        "hashed_vote_password": hashed_vote_password,
        "start_time": start_time,
        "end_time": end_time,
        "status": "initiated",
        "options": options_list,
        "result": "",
        "winner": "",
        "blockchain_wallet": blockchain_wallet,
        "is_funded": False,
        "vote_count": 0,
        "initiation_time": initiation_time
}           # database record structure

    vote_database[vote_id] = vote_data

    #with open("database/votes.json", "w") as file:
    #    json.dump(vote_database, file, indent=4)
    
    #with open("database/users.json", "w") as file:
    user_database[user_id]["vote_creations"] += 1
    #    json.dump(user_database, file, indent=4)

    WriteVotes(vote_database) #save the vote and the users vote creation amount
    WriteUsers(user_database)

    print("funding wallet...")

    if not FundWallet(blockchain_wallet):  #fund the wallet so it can be used
        print("Funding failed")
        return False

    print("wallet funded")

    rpc = "https://api.devnet.solana.com"
    client = Client(rpc)  #setting the rpc client to interact with the blockchain with

    print("Waiting for funding confirmation...")
    confirmed = False
    for i in range(30):  # this part confirms if the wallet has been funded by checking every second 30 times
        if client.get_balance(Pubkey.from_string(blockchain_wallet)).value > 0:
            confirmed = True
            vote_database[vote_id]["is_funded"] = True
            VoteLog("wallet has been funded", vote_id)


            break
        time.sleep(1)

    if not confirmed:   
        VoteLog("Funding confirmation timed out or failed", vote_id)
        print("Funding confirmation timed out or failed")
        return False

    memo_data = {
        "vote_id": vote_id,
        "start_time": start_time,
        "end_time": end_time,
        "organiser_public": organiser_public,
        "options": options_list,
        "mode": mode,
        "version": "1.0"
    }  # the json style memo data that will be sent to the blockchain

    memo_data_string = json.dumps(memo_data)

    #with open("database/solana.key.json", "r") as file:
    #    key_database = json.load(file)

    key_database = OpenSolanaKey()

    wallet = Keypair.from_base58_string(key_database[blockchain_wallet])


    latest_blockhash = client.get_latest_blockhash().value.blockhash

    memo_instruction = create_memo(
        MemoParams(
            program_id=Pubkey.from_string("MemoSq4gqABAXKb96qnH8TysNcWxMyWCqXgDLGmfcHr"), # define the memo program
            signer=wallet.pubkey(), #sign off transaction
            message=memo_data_string.encode("utf-8")  
        )
    )

    message = MessageV0.try_compile(
        payer=wallet.pubkey(),
        instructions=[memo_instruction],
        address_lookup_table_accounts=[],
        recent_blockhash=latest_blockhash
    )  # put the whole transaction together in variable message

    transaction = VersionedTransaction(message, [wallet])

    resp = client.send_transaction(transaction)  #finally send it off

    print(f"Transaction sent: {resp.value}")

    log(f"created a vote with id {vote_id}")

    VoteLog("This vote has been created", vote_id)

    return vote_id



"""register user voter"""

def RegisterUserVote(vote_id, user_id, vote_password=None):
    #with open("database/uservotes.json", "r") as file:
    #   user_vote_database = json.load(file)

    #with open("database/votes.json", "r") as file:
    #    vote_database = json.load(file)

    #with open("database/users.json", "r") as file:
    #    user_database = json.load(file)

    log(f"registering a user with id {user_id} for a vote with id {vote_id}")

    user_vote_database = OpenUserVotes()  # load all databases needed
    vote_database = OpenVotes()
    user_database = OpenUsers()

    if vote_id not in vote_database:
        return False

    if user_id not in user_database:
        return False

    if vote_database[vote_id]["creator"] == user_id:
        return False

    if vote_database[vote_id]["mode"] == "private":
        if not vote_password:
            return False
        pwd_status = Password.verify(vote_password, vote_database[vote_id]["hashed_vote_password"])
        if pwd_status == False:
            return False

    if vote_id not in user_vote_database:
        user_vote_database[vote_id] = {}

    if user_id in user_vote_database[vote_id]:
        if user_vote_database[vote_id][user_id]["has_voted"]:
            return False
        return True

    user_vote_database[vote_id][user_id] = {
        "has_voted": False,
        "voted_for": "",
        "vote_time": "",
        "vote_signature": ""
    }

    #with open("database/uservotes.json", "w") as file:
    #    json.dump(user_vote_database, file, indent=4)

    WriteUserVotes(user_vote_database)

    VoteLog(f"user {user_id} has been registered for this vote", vote_id)

    return True




"""recent votes"""

def GetVotes():
    #with open("database/votes.json", "r") as file:
    #    vote_database = json.load(file)
    
    vote_database = OpenVotes()

    list_format = {"id": "", "title": "", "reason": "", "votes": 0, "options": 0, "result": "", "winner": "", "end_time": "", "start_time": "", "status": "", "blockchain_wallet": "", "organiser": ""}

    recent_votes = []

    for vote_id, vote_data in vote_database.items():
        
        formatted_vote = list_format.copy()
        formatted_vote["id"] = vote_id
        formatted_vote["title"] = vote_data.get("title", "")
        formatted_vote["reason"] = vote_data.get("reason", "")
        formatted_vote["votes"] = vote_data.get("vote_count", 0)
        formatted_vote["options"] = len(vote_data.get("options", []))
        formatted_vote["result"] = vote_data.get("result", "")
        formatted_vote["winner"] = vote_data.get("winner", "")
        formatted_vote["end_time"] = vote_data.get("end_time", "")
        formatted_vote["start_time"] = vote_data.get("start_time", "")
        formatted_vote["organiser_public"] = vote_data.get("organiser", "")

        formatted_vote["start_time"] = ConvertToNormal(formatted_vote["start_time"])
        formatted_vote["end_time"] = ConvertToNormal(formatted_vote["end_time"])

        formatted_vote["status"] = vote_data.get("status", "")
        formatted_vote["blockchain_wallet"]= vote_data.get("blockchain_wallet", "")
        
        recent_votes.append(formatted_vote)
    
    recent_votes.reverse()
    return recent_votes



"""cast vote"""

def SendToBlockchain(data, vote_id):
    #with open("database/votes.json", "r") as file:
    #    vote_database = json.load(file)
    #with open("database/solana.key.json", "r") as file:
    #    key_database = json.load(file)
    
    vote_database = OpenVotes()
    key_database = OpenSolanaKey()

    address = vote_database[vote_id]["blockchain_wallet"]

    wallet = Keypair.from_base58_string(key_database[address])

    print(wallet.pubkey())

    memo_text = str(data)

    client = Client("https://api.devnet.solana.com")


    rpc = "https://api.devnet.solana.com"
    client = Client(rpc)


    latest_blockhash = client.get_latest_blockhash().value.blockhash

    memo_instruction = create_memo(
        MemoParams(
            program_id=Pubkey.from_string("MemoSq4gqABAXKb96qnH8TysNcWxMyWCqXgDLGmfcHr"),
            signer=wallet.pubkey(),
            message=memo_text.encode("utf-8")
        )
    )

    message = MessageV0.try_compile(
        payer=wallet.pubkey(),
        instructions=[memo_instruction],
        address_lookup_table_accounts=[],
        recent_blockhash=latest_blockhash
    )

    transaction = VersionedTransaction(message, [wallet])

    signature_resp = client.send_transaction(transaction)
    tx_sig = signature_resp.value

    vote_database[vote_id]["vote_count"] += 1

    WriteVotes(vote_database)

    return str(tx_sig)   #after first test it was a success the signature is 3755yu8WTXX4JDSejByockQekigfvMUznng9P1R1MHHiqJfjyH7qDUL4CwFgT8sy1Faf5LDmYuVRT5jNFTJbC1qi currently id is not encrypted meaing it can s till be traced back so now i will add sncryption for the id 

def CastVote(user_id, vote_id, option_chosen, special_word1, special_word2, special_word3, vote_password=None):
    #with open("database/votes.json", "r") as file:
    #    vote_database = json.load(file)
    #with open("database/users.json", "r") as file:
    #    user_database = json.load(file)
    #with open("database/uservotes.json", "r") as file:
    #    user_vote_database = json.load(file)
    #with open("database/votekeys.json", "r") as file:
    #    vote_keys_database = json.load(file)

    log(f"casting a vote for a user with id {user_id} for a vote with id {vote_id}")
    
    vote_database = OpenVotes()
    user_database = OpenUsers()
    user_vote_database = OpenUserVotes()
    vote_keys_database = OpenVoteKeys()

    if vote_database[vote_id]["status"] != "started":
        return False
    
    if user_id not in user_database:
        return False
    
    if vote_id not in vote_database:
        return False
    
    now_time = datetime.now()
    start_time = vote_database[vote_id]["start_time"]
    end_time = vote_database[vote_id]["end_time"]

    start_time = datetime.strptime(start_time.replace(", ", "-").replace(",", "-"), "%Y-%m-%d-%H-%M")
    end_time = datetime.strptime(end_time.replace(", ", "-").replace(",", "-"), "%Y-%m-%d-%H-%M")

    if now_time < start_time:
        return False
    
    if now_time > end_time:
        return False

    if user_vote_database[vote_id][user_id]["has_voted"] == True:
        return False

    special_word1 = special_word1.strip()
    special_word2 = special_word2.strip()
    special_word3 = special_word3.strip()
    option_chosen = option_chosen.strip()

    if vote_password:
        vote_password = vote_password.strip()

    if vote_database[vote_id]["mode"] == "private":
        if not vote_password:
            return False
        pwd_status = Password.verify(vote_password, vote_database[vote_id]["hashed_vote_password"])

        if pwd_status == False:
            return False

    if option_chosen not in vote_database[vote_id]["options"]:
        return False
    
    combined_words = special_word1 + special_word2 + special_word3


    word_status = Password.verify(combined_words, user_database[user_id]["hashed_special_words"]) #accidentaly put vote id not user id

    if word_status == False:
        return False
    elif word_status == True:
        pass

    encryption_key = GenerateKey()

    encrypted_user_id = Encrypt(user_id, encryption_key)

    #with open("database/votekeys.json", "w") as file:
    #
    #    if vote_id not in vote_keys_database:
    #        vote_keys_database[vote_id] = {}
    #        
    #    vote_keys_database[vote_id][user_id] = encryption_key
    #
    #    json.dump(vote_keys_database, file, indent=4)
    
    if vote_id not in vote_keys_database:
        vote_keys_database[vote_id] = {}
        
    vote_keys_database[vote_id][user_id] = encryption_key

    WriteVoteKeys(vote_keys_database)


    cast_data = {
        "for": option_chosen,
        "vote_id": vote_id,
        "encrypted_user_id": encrypted_user_id,  # stppoed here to go create encryption algorithm
        "timestamp": str(datetime.now().strftime("%Y, %m, %d, %H, %M")),
        "version": "1.0"
    }

    cast_data_string = json.dumps(cast_data)

    signature = SendToBlockchain(cast_data_string, vote_id)

    if vote_id not in user_vote_database:
        user_vote_database[vote_id] = {}

    user_vote_database[vote_id][user_id] = {
        "has_voted": True,
        "voted_for": option_chosen,
        "vote_time": str(datetime.now().strftime("%Y, %m, %d, %H, %M")),
        "vote_signature": signature
    }

    #with open("database/uservotes.json", "w") as file:
    #    json.dump(user_vote_database, file, indent=4)
    
    WriteUserVotes(user_vote_database)

    log(f"{user_id} voted on vote with id {vote_id} signatre is {signature}")
    VoteLog(f"{user_id} voted", vote_id)


    return signature

def CastFakeVoteTest(user_id, vote_id, option_chosen):
    vote_keys_database = OpenVoteKeys()

    encryption_key = GenerateKey()

    encrypted_user_id = Encrypt(user_id, encryption_key)
    
    if vote_id not in vote_keys_database:
        vote_keys_database[vote_id] = {}
        
    vote_keys_database[vote_id][user_id] = encryption_key

    WriteVoteKeys(vote_keys_database)

    cast_data = {
        "for": option_chosen,
        "vote_id": vote_id,
        "encrypted_user_id": encrypted_user_id,  # stppoed here to go create encryption algorithm
        "timestamp": str(datetime.now().strftime("%Y, %m, %d, %H, %M")),
        "version": "1.0"
    }

    cast_data_string = json.dumps(cast_data)

    signature = SendToBlockchain(cast_data_string, vote_id)

    return signature


"""count votes"""

def GetMemos(address):
    rpc = "https://devnet.helius-rpc.com/?api-key=efd784bd-0370-4478-b996-6c2d7aec403d"
    client = Client(rpc)

    pubkey = Pubkey.from_string(address)

    signatures = client.get_signatures_for_address(pubkey)

    if not signatures:
        return []
    
    sigs = signatures.value if hasattr(signatures, "value") else signatures

    all_memos = []  # collect (memo_obj, sender) for all transactions

    

    for sig in sigs:
        if sig.memo:
            tx_response = client.get_transaction(
                sig.signature,
                encoding="jsonParsed",
                max_supported_transaction_version=0
            )

            if not tx_response or not tx_response.value:
                continue

            tx = tx_response.value.transaction
            account_keys = tx.transaction.message.account_keys

            sender = str(account_keys[0].pubkey) if hasattr(account_keys[0], "pubkey") else str(account_keys[0])

            try:
                json_start = sig.memo.find('{')
                if json_start != -1:
                    memo_obj = json.loads(sig.memo[json_start:])
                    all_memos.append((memo_obj, sender))
            except:
                pass

    chronological = list(reversed(all_memos))

    # Find the end message cutoff (regardless of who sent it)
    cutoff = len(chronological)
    for i, (memo, sender) in enumerate(chronological):
        if memo.get("message") == "Vote has ended":
            cutoff = i  # exclude end message and anything after
            break


    # Only return memos sent by the given address, up to the cutoff
    return [memo for memo, sender in chronological[:cutoff] if sender == address]


def CountVotes(vote_id):
    #with open("database/votes.json", "r") as file:
    #    vote_database = json.load(file)
    
    vote_database = OpenVotes()

    try:
        vote_database[vote_id]
    except KeyError:
        return False
    
    if vote_database[vote_id]["status"] != "ended":
        return False
    
    try:
        results = vote_database[vote_id]["result"]
        winner = vote_database[vote_id].get("winner")
        if isinstance(results, dict) and results and winner:
            VoteLog("votes have already been counted", vote_id)
            return results   # added caching so re-count does not need to be completed everytime wasting time
        
    except KeyError:
        pass

    

    address = vote_database[vote_id]["blockchain_wallet"]

    memo_list = GetMemos(address)

    try:
        start_memo = memo_list[0]

        
        if start_memo["vote_id"] == vote_id:
            end_time = start_memo["end_time"]
            options = start_memo["options"]
        
        else:
            return False
        
        memo_list.pop(0)

    except:
        return False

    parsed_time = datetime.strptime(end_time.replace(", ", "-").replace(",", "-"), "%Y-%m-%d-%H-%M")

    now_time = datetime.now()

    if now_time < parsed_time:
        return False
    
    option_counts = {option: 0 for option in options}

    for memo in memo_list:
        timestamp = memo["timestamp"]
        timestamp = datetime.strptime(timestamp.replace(", ", "-").replace(",", "-"), "%Y-%m-%d-%H-%M")

        if timestamp > parsed_time:
            count = False

        elif timestamp < parsed_time:
            count = True

        else:
            count = False

        vote_for = memo["for"]  #

        if count:
            option_counts[vote_for] += 1

    vote_database[vote_id]["result"] = option_counts

    # get winner with tie detection
    if option_counts:
        max_votes = max(option_counts.values())
        winners = [opt for opt, count in option_counts.items() if count == max_votes]
        
        if len(winners) > 1:
            winner = "No Winner, Tie"
        else:
            winner = winners[0]
    else:
        winner = ""

    vote_database[vote_id]["winner"] = winner

    WriteVotes(vote_database)

    VoteLog("votes have been counted first time", vote_id)

    return option_counts

"""send ending email to users who voted"""

def SendEndEmail(vote_id): 
    log(f"sending end email for a vote with id {vote_id}")

    vote_id = str(vote_id)
    uservotes_database = OpenUserVotes()
    user_database = OpenUsers()

    try:
        data = uservotes_database[vote_id]
    except KeyError:
        return False

    user_ids = []
    user_emails = []  # linked lists with user id and emails of each.
    pointer = 0

    for user in data:  #tested to see if it worked and it did it printed the user ids of the users who voted in the vote with the id 62427593
        user_ids.append(user)

    for id in user_ids:
        user_email = user_database[id]["email"]
        user_emails.append(user_email)
        


    for i in range(0, len(user_emails)):
        user_id = user_ids[i]
        user_email = user_emails[i]

        user_email1 = user_email

        message_html1 = f"""
        <html>
            <body>
                <h1 style="color: #4CAF50;">TrueVote: Vote With ID {vote_id} Has Ended</h1>
                <p>A vote you registered for has ended! <strong style="font-size: 20px; color: #2196F3;"></strong></p>
                <p>Please view our website for results, <strong>Results can take up to 24h to be processed!</strong>.</p>
                <p>If you did not register for this Vote, please ignore this email.</p>
                <hr>
                <p style="font-size: 12px; color: #888;">This is an automated message. Please do not reply. Your account ID is {user_id}</p>
            </body>
        </html>
        """  # copied from other message for code now used for this

        SendEmail(user_email=user_email1, subject=f"TrueVote: Vote With ID {vote_id} Has Ended", message_html=message_html1) # had an error was trying to use position based arguments after keyword arguments now fixed it by using keyword arguments for all # also added user id to the email for more security so users can know which account it was if they have multiple accounts or forgot which email they used also added debugging line to print vars at every step to debug the issue

    log(f"sent end email for a vote with id {vote_id}")
    VoteLog("end email has been sent", vote_id)


    return True




"""get vote details"""

def VoteDetails(vote_id):
    vote_database = OpenVotes()
    
    if vote_id not in vote_database:
        return {"error": "Vote not found"}
    
    vote_data = vote_database[vote_id]
    
    return {
        "vote_id": vote_id,
        "title": vote_data.get("title", ""),
        "reason": vote_data.get("reason", ""),
        "organiser_public": vote_data.get("organiser", ""),
        "start_time": vote_data.get("start_time", ""),
        "end_time": vote_data.get("end_time", ""),
        "status": vote_data.get("status", ""),
        "options": vote_data.get("options", []),
        "mode": vote_data.get("mode", "public"),
        "blockchain_wallet": vote_data.get("blockchain_wallet", ""),
        "vote_count": vote_data.get("vote_count", 0),
        "winner": vote_data.get("winner", "")
    }

"""send the end message on the blockchain to mark end"""

def SendEndMessage(vote_id):
    vote_database = OpenVotes()
    key_database = OpenSolanaKey()

    log(f"sending end message for a vote with id {vote_id}")

    address = vote_database[vote_id]["blockchain_wallet"]

    wallet = Keypair.from_base58_string(key_database[address])

    print(wallet.pubkey())

    data = {
        "vote_id": vote_id,
        "end_time": vote_database[vote_id]["end_time"],
        "winner": vote_database[vote_id].get("winner", ""),
        "message": "Vote has ended",
        "version": "1.0"
    }

    memo_text = str(data)

    rpc = "https://api.devnet.solana.com"
    client = Client(rpc)


    latest_blockhash = client.get_latest_blockhash().value.blockhash

    memo_instruction = create_memo(
        MemoParams(
            program_id=Pubkey.from_string("MemoSq4gqABAXKb96qnH8TysNcWxMyWCqXgDLGmfcHr"),
            signer=wallet.pubkey(),
            message=memo_text.encode("utf-8")
        )
    )

    message = MessageV0.try_compile(
        payer=wallet.pubkey(),
        instructions=[memo_instruction],
        address_lookup_table_accounts=[],
        recent_blockhash=latest_blockhash
    ) # D8

    transaction = VersionedTransaction(message, [wallet])

    signature_resp = client.send_transaction(transaction)
    tx_sig = signature_resp.value

    log(f"sent end message for a vote with id {vote_id}")
    VoteLog("end message has been sent", vote_id)


    return str(tx_sig)


"""combining both send end message, send end email and count votes"""

def EndProcedure(vote_id):   #added all ending funbctions into one so it can only be called once and not all of them one by one 
    log(f"begining end procedure for a vote with id {vote_id}")
    VoteLog("begining end procedure", vote_id)

    try:
        SendEndMessage(vote_id)
        end_message = True
    except:
        end_message = False
        pass

    try:
        SendEndEmail(vote_id)
        end_email = True
    except:
        end_email = False
        pass
    
    try:
        CountVotes(vote_id)
        end_count = True
    except:
        end_count = False
        pass

    if end_message and end_email and end_count:
        log(f"end procedure for a vote with id {vote_id} completed successfully")
        VoteLog("end procedure completed successfully", vote_id)
        return True
        
    else:
        log(f"end procedure for a vote with id {vote_id} failed")
        VoteLog("end procedure failed", vote_id)
        return False
