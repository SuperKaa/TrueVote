"""This file runs continuously in the background"""

import json
from datetime import datetime
import threading
import time
from Voting import EndProcedure
from DatabaseManager import *
from SystemLogging import *


"""vote status handler"""

def VoteStatusHandler():
    vote_database = OpenVotes()

    current_time = datetime.now()
    updates = {}

    for vote_id, vote_data in vote_database.items():
        if not vote_data:
            print(f"Warning: vote_id key missing for {vote_id}")
            continue

        if vote_data.get("status") == "initiated":
            try:
                start_time_str = vote_data.get("start_time")
                if not start_time_str:
                    print(f"Warning: start_time missing for vote {vote_id}")
                    continue

                start_time = datetime.strptime(start_time_str.replace(", ", "-").replace(",", "-").replace(":", "-"), "%Y-%m-%d-%H-%M")

                if current_time >= start_time:
                    updates[vote_id] = "started"
                    log(f"Vote {vote_id} has been started")


            except Exception as e:
                print(f"Error parsing start_time for vote {vote_id}: {e}")
                continue

        elif vote_data.get("status") == "started": # added ending
            try:
                end_time_str = vote_data.get("end_time")
                if not end_time_str:
                    print(f"Warning: end_time missing for vote {vote_id}")
                    continue

                end_time = datetime.strptime(end_time_str.replace(", ", "-").replace(",", "-").replace(":", "-"), "%Y-%m-%d-%H-%M")

                if current_time >= end_time:
                    updates[vote_id] = "ended"
                    log(f"Vote {vote_id} has been ended")


            except Exception as e:
                print(f"Error parsing end_time for vote {vote_id}: {e}")
                continue

    if updates:
        try:
           
            vote_database = OpenVotes()
            for vid, status in updates.items():
                if vid in vote_database:
                    vote_database[vid]["status"] = status
                    if status == "ended":
                        threading.Thread(target=EndProcedure, args=(vid,), daemon=True).start()
                        print(f"Vote {vid} has been ended")
                    elif status == "started":
                        print(f"Vote {vid} has been started")
            
            WriteVotes(vote_database)
            print("votes.json has been updated")
            return True
        except Exception as e:
            print(f"Error saving votes.json: {e}")
            return False

    return False


def VoteStarterListener():
    print("VoteStarter listener started. Checking every 30 seconds...")
    try:
        while True:
            VoteStatusHandler()
            time.sleep(30)
    except KeyboardInterrupt:
        print("\nVoteStarter listener stopped.")


if __name__ == "__main__":
    log("VoteStarter listener started")
    VoteStarterListener()