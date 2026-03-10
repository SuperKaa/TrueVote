import json
from DatabaseManager import *
from solders.keypair import Keypair
from solders.pubkey import Pubkey
from solders.system_program import transfer, TransferParams
from solders.transaction import Transaction
from solders.message import Message
from solana.rpc.api import Client
from SystemLogging import *

import base58

"""fund wallet"""

def FundWallet(address):
    log(f"Funding wallet {address}")
    rpc = "https://api.devnet.solana.com"
    try:
        #with open("database/masterwallet.json", "r") as file:
        #    master_data = json.load(file)

        master_data = OpenMasterWallet()
        
        b58_key = list(master_data.values())[0]

        wallet = Keypair.from_base58_string(b58_key)
        
        client = Client(rpc)
        
        recipient_pubkey = Pubkey.from_string(address)

        latest_blockhash_resp = client.get_latest_blockhash()
        blockhash = latest_blockhash_resp.value.blockhash
        
        transfer_instruction = transfer(
            TransferParams(
                from_pubkey=wallet.pubkey(),
                to_pubkey=recipient_pubkey,
                lamports=3000000
            )
        )
        
        message = Message([transfer_instruction], wallet.pubkey())
        
        transaction = Transaction([wallet], message, blockhash)
        
        signature_resp = client.send_transaction(transaction)
        tx_sig = signature_resp.value

        log(f"Wallet funded with signature {tx_sig}")

        return str(tx_sig)
            
    except Exception as e:
        print(e)
        return
    


"""create address"""

def CreateAddress(debug=False): #added debug so i can create wallets for myself to test on, was alo used to create master wallet
    #with open("database/solana.key.json", "r") as file:
    #    solana_database = json.load(file)

    log("Creating wallet")

    solana_database = OpenSolanaKey()

    wallet = Keypair()
    address = str(wallet.pubkey())


    raw_byte = bytes(wallet)
    b58_key = base58.b58encode(raw_byte).decode()


    solana_database[address] = b58_key

    if not debug:
        #with open("database/solana.key.json", "w") as file:
        #    json.dump(solana_database, file, indent=4)

        WriteSolanaKey(solana_database)

    log(f"Wallet created with address {address}")

    return address