# file had same name as a library had to change it then
from datetime import datetime

def log(text):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open("logs/system.log", "a") as file:
        file.write(f"[{timestamp}] {text}\n")
    
def VoteLog(text, vote_id):
    vote_id = str(vote_id)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(f"logs/vote_{vote_id}.log", "a") as file:
        file.write(f"[{timestamp}] {text}\n")

