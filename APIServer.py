from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Optional 
import uvicorn

from dotenv import load_dotenv
import os

from Authentication import Login, RegisterUser, VerifyEmail, VerifyWords, VerifyWordsToUser, EmailToID, AddUserToPrivileges, IsUserInPrivileges, RemoveUserFromPrivileges, GetPrivileges, GenRandomWords
from Voting import CreateVote, RegisterUserVote, GetVotes, CastVote, CountVotes, VoteDetails
import os

from SystemLogging import *


#uvicorn APIServer:app --reload

#now adding api key system to prevent unauthorised access.

app = FastAPI()

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    body = await request.body()
    print(f"Validation Error: {exc.errors()}")
    print(f"Request Body: {body.decode()}")
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors()},
    )  # made this to return the error in case of failire

load_dotenv()

api_key = os.getenv("API_KEY")
#api key moved to .env file for safety

@app.get("/{key}")
def root(key: str):
    if key != api_key:
        return {"error": "Invalid API key"}
    return {"Hello": "World"}
    
@app.get("/login/{key}")
def Login_user(email: str, password: str, key: str):#error accidentaly called Login same as Login fucntion and route on api
    if key != api_key:
        return {"error": "Invalid API key"}
    return Login(email, password)

@app.get("/verify/{key}")
def Verify_email(email: str, key: str):
    if key != api_key:
        return {"error": "Invalid API key"}
    return VerifyEmail(email)

class RegisterUserRequest(BaseModel):
    name: str
    user_email: str
    phone: str
    user_password: str
    confirm_password: str
    special_word1: str
    special_word2: str
    special_word3: str

@app.post("/register/{key}")   
def Register_user(request: RegisterUserRequest, key: str):
    if key != api_key:
        return {"error": "Invalid API key"}
    return RegisterUser(
        request.name,
        request.user_email,
        request.phone,
        request.user_password,
        request.confirm_password,
        request.special_word1,
        request.special_word2,
        request.special_word3)

@app.get("/getvotes/{key}")
def Get_votes(key: str):
    if key != api_key:
        return {"error": "Invalid API key"}
    return GetVotes()

class CreateVoteRequest(BaseModel):
    title: str
    reason: str
    organiser_public: str
    start_time: str
    end_time: str
    options_list: List[str]
    user_id: str
    vote_password: Optional[str] = None

@app.post("/create/{key}")
def Create_vote(request: CreateVoteRequest, key: str):
    if key != api_key:
        return {"error": "Invalid API key"}
    return CreateVote(
        request.title,
        request.reason,
        request.organiser_public,
        request.start_time,
        request.end_time,
        request.options_list,
        request.user_id,
        request.vote_password
    )

@app.get("/registervoter/{key}")
def Register_user_vote(vote_id: str, user_id: str, key: str, vote_password: Optional[str] = None):
    if key != api_key:
        return {"error": "Invalid API key"}
    return RegisterUserVote(vote_id, user_id, vote_password)

class CastVoteRequest(BaseModel):
    vote_id: str
    user_id: str
    option_chosen: str
    vote_password: Optional[str] = None
    special_word1: str
    special_word2: str
    special_word3: str

@app.post("/castvote/{key}")
def Cast_vote(request: CastVoteRequest, key: str):
    if key != api_key:
        return {"error": "Invalid API key"}
    return CastVote(
        request.user_id,
        request.vote_id,
        request.option_chosen,
        request.special_word1,
        request.special_word2,
        request.special_word3,
        request.vote_password
    )

@app.get("/countvotes/{key}")
def Count_votes(vote_id: str, key: str):
    if key != api_key:
        return {"error": "Invalid API key"}
    return CountVotes(vote_id)

@app.get("/verifywords/{key}") #made fucntion to verify words and api route for it.
def Verify_words(special_word1: str, special_word2: str, special_word3: str, key: str):
    if key != api_key:
        return {"error": "Invalid API key"}
    return VerifyWords(special_word1, special_word2, special_word3)

@app.get("/verifyuserwords/{key}")
def Verify_user_words(special_word1: str, special_word2: str, special_word3: str, user_id: str, key: str):
    if key != api_key: 
        return {"error": "Invalid API key"}
    return VerifyWordsToUser(special_word1, special_word2, special_word3, user_id)

@app.get("/userbyemail/{key}")
def Get_user_by_email(email: str, key: str):
    if key != api_key:
        return {"error": "Invalid API key"}
    user_id = EmailToID(email.lower())
    if user_id:
        return {"user_id": user_id}
    return {}

@app.get("/votedetails/{key}")
def Get_vote_details(vote_id: str, key: str):
    if key != api_key:
        return {"error": "Invalid API key"}
    return VoteDetails(vote_id)

@app.get("/adduserp/{key}")
def Add_user_to_privileges(user_id: str, role: str, key: str):
    if key != api_key:
        return {"error": "Invalid API key"}
    return AddUserToPrivileges(user_id, role)

@app.get("/removeuserp/{key}")
def Remove_user_from_privileges(user_id: str, role: str, key: str):
    if key != api_key:
        return {"error": "Invalid API key"}
    return RemoveUserFromPrivileges(user_id, role)

@app.get("/isuserp/{key}")
def Is_user_in_privileges(user_id: str, role: str, key: str):
    if key != api_key:
        return {"error": "Invalid API key"}
    return IsUserInPrivileges(user_id, role)

@app.get("/getprivileges/{key}")
def Get_privileges_endpoint(role: str, key: str):
    if key != api_key:
        return {"error": "Invalid API key"}
    return GetPrivileges(role)

@app.get("/genwords/{key}")
def Gen_random_words(key: str):
    if key != api_key:
        return {"error": "Invalid API key"}
    return GenRandomWords()

@app.get("/getsystemlog/{key}")
def Get_system_log(key: str):
    if key != api_key:
        return {"error": "Invalid API key"}
    try:
        with open("logs/system.log", "r") as f:
            return {"log": f.read()}
    except:
        return {"log": "Log file not found."}

@app.get("/getvotelogs/{key}")
def Get_vote_logs(key: str):
    if key != api_key:
        return {"error": "Invalid API key"}
    try:
        files = [f for f in os.listdir("logs") if f.startswith("vote_") and f.endswith(".log")]
        return {"logs": files}
    except:
        return {"logs": []}

@app.get("/readvotelog/{key}")
def Read_vote_log(filename: str, key: str):
    if key != api_key:
        return {"error": "Invalid API key"}
    if ".." in filename or "/" in filename or "\\" in filename: # security check
        return {"error": "Invalid filename"}
    try:
        with open(f"logs/{filename}", "r") as f:
            return {"log": f.read()}
    except:
        return {"log": "Log file not found."}


if __name__ == "__main__":
    log("Api server has started")
    uvicorn.run("APIServer:app", host="0.0.0.0", port=7070, reload=True)
    log("Api server has stopped")
    
    #os.system("uvicorn APIServer:app --reload")