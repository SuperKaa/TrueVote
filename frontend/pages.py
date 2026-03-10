from nicegui import ui, app
from frontend.functions import *
from datetime import datetime

# most formatting of ui items done through drag and drop tool.

# main header for the site, shows on most pages
def header():
    with ui.header().classes("bg-indigo-600 text-white"):
        with ui.row().classes("w-full justify-between items-center px-4 py-3"):
            with ui.row().classes("items-center gap-2 cursor-pointer").on("click", lambda: ui.navigate.to("/")):
                ui.icon("how_to_vote", size="28px")
                ui.label("TrueVote").classes("text-xl font-bold")
            with ui.row().classes("gap-2 items-center"):
                ui.button("Home", on_click=lambda: ui.navigate.to("/")).props("flat color=white")
                ui.button("Votes", on_click=lambda: ui.navigate.to("/votes")).props("flat color=white")
                ui.button("Create", on_click=lambda: ui.navigate.to("/create")).props("flat color=white")
                with ui.button("More").props("flat color=white"):
                    with ui.menu():
                        ui.menu_item("Audit Panel", lambda: ui.navigate.to("/audit"))
                        ui.menu_item("Admin Panel", lambda: ui.navigate.to("/admin"))
                        ui.separator()
                        ui.menu_item("Logout", lambda: do_logout())
            if app.state.user:
                ui.label(f"Hi, {app.state.user}").classes("text-sm ml-4")

# the home page, what users see first
@ui.page("/")
def page_home():
    header()
    with ui.column().classes("w-full items-center justify-center").style("min-height: 90vh"):
        ui.icon("how_to_vote", size="120px").classes("text-indigo-600 mb-4")
        ui.label("TrueVote").classes("text-5xl font-bold text-gray-800 mb-2")
        ui.label("Blockchain Voting Platform").classes("text-xl text-gray-500 mb-8")
        with ui.row().classes("gap-4"):
            ui.button("Browse Votes", on_click=lambda: ui.navigate.to("/votes")).classes("bg-indigo-600 text-white px-8 py-3 text-lg")
            if not app.state.user:
                ui.button("Login", on_click=lambda: ui.navigate.to("/login")).classes("bg-indigo-600 text-white px-8 py-3 text-lg")
            else:
                ui.button("Create Vote", on_click=lambda: ui.navigate.to("/create")).classes("bg-green-600 text-white px-8 py-3 text-lg")

# login page for existing users
@ui.page("/login")
def page_login():
    with ui.column().classes("w-full items-center justify-center").style("min-height: 90vh"):
        with ui.card().classes("w-80 p-6"):
            ui.label("Login").classes("text-2xl font-bold text-center mb-4")
            email = ui.input("Email").classes("w-full mb-3")
            password = ui.input("Password", password=True).classes("w-full mb-4")
            error_label = ui.label("").classes("text-red-500 text-sm mb-2").style("display: none")
            
            # function to handle the login logic
            def do_login():
                error_label.style("display: none")
                if not email.value or not password.value:
                    error_label.set_text("Please fill all fields")
                    error_label.style("display: block")
                    return
                
                with ui.dialog() as dlg:
                    ui.label("Logging in...").classes("text-lg p-4")
                dlg.open()
                ui.update()
                
                # call the api to attempt a login
                result = api_get("/login", {"email": email.value, "password": password.value})
                dlg.close()
                
                if result == "locked":
                    error_label.set_text("Account locked for 1 hour")
                    error_label.style("display: block")
                elif is_true(result):
                    app.state.user_email = email.value
                    app.state.user = email.value.split("@")[0]
                    
                    user_result = api_get("/userbyemail", {"email": email.value})
                    if isinstance(user_result, dict) and "user_id" in user_result:
                        app.state.user_id = user_result["user_id"]

                    ui.notify("Login successful!", color="positive")
                    ui.navigate.to("/votes")
                else:
                    error_label.set_text("Invalid email or password")
                    error_label.style("display: block")
            
            ui.button("Login", on_click=do_login).classes("w-full bg-indigo-600 text-white py-2 mb-3")
            error_label
            ui.link("Don't have an account? Register", "/register").classes("text-indigo-600 text-sm")

# registration page, first step
@ui.page("/register")
def page_register():
    with ui.column().classes("w-full items-center justify-center").style("min-height: 90vh"):
        with ui.card().classes("w-80 p-6"):
            ui.label("Register").classes("text-2xl font-bold text-center mb-4")
            name = ui.input("Full Name").classes("w-full mb-2")
            email = ui.input("Email").classes("w-full mb-2")
            phone = ui.input("Phone Number").classes("w-full mb-2")
            password = ui.input("Password", password=True).classes("w-full mb-2")
            confirm = ui.input("Confirm Password", password=True).classes("w-full mb-4")
            error_label = ui.label("").classes("text-red-500 text-sm mb-2").style("display: none")
            
            # moves to the next step of registration
            def next_step():
                error_label.style("display: none")
                
                if not all([name.value, email.value, phone.value, password.value]):
                    error_label.set_text("Please fill all fields")
                    error_label.style("display: block")
                    return
                
                if password.value != confirm.value:
                    error_label.set_text("Passwords don't match")
                    error_label.style("display: block")
                    return
                
                if len(password.value) < 8:
                    error_label.set_text("Password must be at least 8 characters")
                    error_label.style("display: block")
                    return
                
                app.state.temp_register = {
                    "name": name.value,
                    "email": email.value,
                    "phone": phone.value,
                    "password": password.value
                }
                ui.navigate.to("/register/words")
            
            ui.button("Continue", on_click=next_step).classes("w-full bg-indigo-600 text-white py-2 mb-3")
            error_label
            ui.link("Already have an account? Login", "/login").classes("text-indigo-600 text-sm")

# registration page for the security words
@ui.page("/register/words")
def page_register_words():
    if not app.state.temp_register.get("email"):
        ui.navigate.to("/register")
        return
    
    with ui.column().classes("w-full items-center justify-center").style("min-height: 90vh"):
        with ui.card().classes("w-96 p-6"):
            ui.label("Safety Words").classes("text-2xl font-bold text-center mb-2")
            ui.label("Enter 3 BIP39 words for security").classes("text-sm text-gray-500 text-center mb-4")
            w1 = ui.input("Word 1").classes("w-full mb-2")
            w2 = ui.input("Word 2").classes("w-full mb-2")
            w3 = ui.input("Word 3").classes("w-full mb-4")
            error_label = ui.label("").classes("text-red-500 text-sm mb-2").style("display: none")

            def gen_words(): # added button to generate random words
                res = api_get("/genwords")
                if isinstance(res, list) and len(res) == 3:
                    w1.value = res[0]
                    w2.value = res[1]
                    w3.value = res[2]
            
            ui.button("Generate Random Words", on_click=gen_words).classes("w-full bg-gray-500 text-white py-2 mb-2")

            
            # verifies the words are valid bip39 words
            def verify():
                error_label.style("display: none")
                
                if not all([w1.value, w2.value, w3.value]):
                    error_label.set_text("Please enter all 3 words")
                    error_label.style("display: block")
                    return
                
                with ui.dialog() as dlg:
                    ui.label("Verifying words...").classes("text-lg p-4")
                dlg.open()
                ui.update()
                
                result = api_get("/verifywords", {
                    "special_word1": w1.value,
                    "special_word2": w2.value,
                    "special_word3": w3.value
                })
                dlg.close()
                
                if is_true(result):
                    app.state.special_words = [w1.value, w2.value, w3.value]
                    ui.navigate.to("/register/otp")
                else:
                    error_label.set_text("Invalid words. Use valid BIP39 words.")
                    error_label.style("display: block")
            
            ui.button("Continue", on_click=verify).classes("w-full bg-indigo-600 text-white py-2")
            error_label

# registration page for the one-time password (OTP) from email
@ui.page("/register/otp")
def page_register_otp():
    if not app.state.temp_register.get("email"):
        ui.navigate.to("/register")
        return
    
    app.state.verification_code = "123456"
    # get the verification code from the api
    result = api_get("/verify", {"email": app.state.temp_register["email"]})
    if isinstance(result, (list, tuple)) and len(result) >= 1:
        app.state.verification_code = str(result[0])
    elif isinstance(result, dict) and "code" in result:
        app.state.verification_code = str(result["code"])
    
    with ui.column().classes("w-full items-center justify-center").style("min-height: 90vh"):
        with ui.card().classes("w-80 p-6"):
            ui.label("Verify Email").classes("text-2xl font-bold text-center mb-2")
            ui.label(f"Code sent to {app.state.temp_register['email']}").classes("text-sm text-gray-500 text-center mb-4")
            otp = ui.input("Enter OTP").classes("w-full mb-4")
            error_label = ui.label("").classes("text-red-500 text-sm mb-2").style("display: none")
            
            # verify the otp and create the account
            def verify():
                error_label.style("display: none")
                
                if not otp.value:
                    error_label.set_text("Please enter the OTP")
                    error_label.style("display: block")
                    return
                
                if otp.value != str(app.state.verification_code):
                    error_label.set_text("Incorrect OTP code")
                    error_label.style("display: block")
                    return
                
                with ui.dialog() as dlg:
                    ui.label("Creating account...").classes("text-lg p-4")
                dlg.open()
                ui.update()
                
                # all data for the new user
                data = {
                    "name": app.state.temp_register["name"],
                    "user_email": app.state.temp_register["email"],
                    "phone": app.state.temp_register["phone"],
                    "user_password": app.state.temp_register["password"],
                    "confirm_password": app.state.temp_register["password"],
                    "special_word1": app.state.special_words[0],
                    "special_word2": app.state.special_words[1],
                    "special_word3": app.state.special_words[2]
                }

                # post the data to the api to create the user
                result = api_post("/register", data)
                dlg.close()
                
                if is_true(result):
                    ui.notify("Registration successful! Please login.", color="positive")
                    app.state.temp_register = {}
                    app.state.special_words = []
                    ui.navigate.to("/login")
                else:
                    error_label.set_text("Registration failed. Try again.")
                    error_label.style("display: block")
            
            ui.button("Verify", on_click=verify).classes("w-full bg-indigo-600 text-white py-2")
            error_label

# page to show all available votes
@ui.page("/votes")
def page_votes():
    header()
    
    with ui.column().classes("w-full items-center mt-6 px-4"):
        ui.label("Available Votes").classes("text-3xl font-bold mb-4")
        
        with ui.row().classes("w-full max-w-2xl gap-2 mb-6"):
            search = ui.input("Search by Vote ID").classes("flex-1").props("outlined")
            def do_search():
                if search.value:
                    ui.navigate.to(f"/vote/{search.value}")
            ui.button("Search", icon="search", on_click=do_search).classes("bg-indigo-600 text-white")
        
        votes_container = ui.column().classes("w-full max-w-2xl gap-3")
        
        with ui.dialog() as loading_dlg:
            ui.label("Loading votes...").classes("text-lg p-4")
        loading_dlg.open()
        ui.update()
        
        # get all votes from the api
        result = api_get("/getvotes")
        loading_dlg.close()
        
        with votes_container:
            if isinstance(result, list) and len(result) > 0:
                for vote in result:
                    status = vote.get("status", "unknown")
                    # different colours for different statuses
                    status_colors = {
                        "started": "green",
                        "initiated": "orange",
                        "ended": "gray"
                    }
                    status_color = status_colors.get(status, "gray")
                    
                    with ui.card().classes("w-full p-4 cursor-pointer hover:shadow-lg transition").on("click", lambda v=vote: ui.navigate.to(f"/vote/{v['id']}")):
                        with ui.row().classes("w-full justify-between items-center"):
                            with ui.column():
                                ui.label(vote.get("title", "Untitled Vote")).classes("text-lg font-bold text-gray-800")
                                ui.label(f"By: {vote.get('organiser_public', 'Unknown')}").classes("text-sm text-gray-500")
                            with ui.column().classes("items-end"):
                                ui.badge(status.upper(), color=status_color).classes("mb-1")
                                ui.label(f"{vote.get('votes', 0)} votes").classes("text-sm text-gray-400")
            else:
                with ui.column().classes("w-full items-center py-12"):
                    ui.icon("how_to_vote", size="64px").classes("text-gray-300 mb-4")
                    ui.label("No votes available").classes("text-xl text-gray-400")
                    ui.button("Create First Vote", on_click=lambda: ui.navigate.to("/create")).classes("bg-indigo-600 text-white mt-4 px-6")

# page to show the details of a single vote
@ui.page("/vote/{vote_id}")
def page_vote_detail(vote_id: str):
    app.state.vote_id = vote_id
    
    header()
    
    with ui.column().classes("w-full items-center mt-6 px-4"):
        back_btn = ui.button("Back to Votes", icon="arrow_back", on_click=lambda: ui.navigate.to("/votes")).classes("mb-4 self-start bg-gray-600 text-white")
        
        content = ui.column().classes("w-full max-w-2xl gap-4")
        
        with ui.dialog() as loading_dlg:
            ui.label("Loading vote details...").classes("text-lg p-4")
        loading_dlg.open()
        ui.update()
        
        # find the specific vote from the list of all votes
        result = api_get("/getvotes")
        vote = None
        if isinstance(result, list):
            for v in result:
                if v.get("id") == vote_id:
                    vote = v
                    break
        
        loading_dlg.close()
        
        with content:
            if vote:
                ui.label(vote.get("title", "Vote")).classes("text-3xl font-bold text-gray-800")
                
                status = vote.get("status", "unknown")
                status_colors = {"started": "green", "initiated": "orange", "ended": "gray"}
                status_color = status_colors.get(status, "gray")
                
                with ui.card().classes("w-full p-4"):
                    with ui.grid(columns=2).classes("w-full gap-y-2"):
                        ui.label("Organiser:").classes("text-gray-500")
                        ui.label(vote.get("organiser_public", "Unknown")).classes("text-gray-800")
                        ui.label("Wallet:").classes("text-gray-500")
                        ui.label(vote.get("blockchain_wallet", "N/A")).classes("text-xs font-mono text-gray-800 break-all")
                        ui.label("Status:").classes("text-gray-500")
                        ui.badge(status.upper(), color=status_color)
                        ui.label("Starts:").classes("text-gray-500")
                        ui.label(vote.get("start_time", "N/A"))
                        ui.label("Ends:").classes("text-gray-500")
                        ui.label(vote.get("end_time", "N/A"))
                        ui.label("Total Votes:").classes("text-gray-500")
                        ui.label(str(vote.get("votes", 0))).classes("text-gray-800 font-bold")
                
                with ui.card().classes("w-full p-4"):
                    ui.label("Description").classes("text-lg font-bold text-gray-800 mb-2")
                    ui.label(vote.get("reason", "No description available.")).classes("text-gray-600")
                
                with ui.row().classes("w-full gap-3"):
                    # function to show the results of the vote in a dialog
                    def show_results():
                        result = api_get("/countvotes", {"vote_id": vote_id})
                        if isinstance(result, dict) and "error" not in result:
                            with ui.dialog() as dlg, ui.card().classes("w-80 p-4"):
                                ui.label("Vote Results").classes("text-xl font-bold mb-3")
                                for opt, count in result.items():
                                    with ui.row().classes("w-full justify-between py-1"):
                                        ui.label(opt)
                                        ui.label(f"{count} votes").classes("font-bold text-indigo-600")
                                ui.button("Close", on_click=dlg.close).classes("w-full bg-gray-200 text-gray-700 mt-3")
                            dlg.open()
                        else:
                            ui.notify("Results not available yet", color="negative")
                    
                    ui.button("View Results", icon="bar_chart", on_click=show_results).classes("flex-1 bg-gray-100 text-gray-700")
                
                # show different options based on the vote status
                if status == "started":
                    def participate():
                        if not app.state.user_id:
                            ui.notify("Please login first", color="negative")
                            ui.navigate.to("/login")
                            
                            return
                        
                        ui.navigate.to(f"/vote/{vote_id}/participate")
                    
                    ui.button("Participate in Vote", icon="how_to_vote", on_click=participate).classes("w-full bg-indigo-600 text-white py-3 text-lg mt-2")
                elif status == "initiated":
                    with ui.card().classes("w-full p-4 bg-yellow-50 border border-yellow-200"):
                        with ui.row().classes("w-full items-center justify-center gap-2"):
                            ui.icon("schedule", size="20px").classes("text-yellow-600")
                            ui.label("This vote has not started yet").classes("text-yellow-700")
                else:
                    with ui.card().classes("w-full p-4 bg-gray-50 border border-gray-200"):
                        with ui.row().classes("w-full items-center justify-center gap-2"):
                            ui.icon("check_circle", size="20px").classes("text-gray-500")
                            ui.label("This vote has ended").classes("text-gray-600")
            else:
                ui.label("Vote not found").classes("text-red-500 text-xl")
                ui.button("Back to Votes", on_click=lambda: ui.navigate.to("/votes")).classes("bg-indigo-600 text-white mt-4")

# page for a user to confirm they want to participate in a vote
@ui.page("/vote/{vote_id}/participate")
def page_vote_participate(vote_id: str):
    header()
    
    with ui.column().classes("w-full items-center mt-6 px-4"):
        ui.button("Back", icon="arrow_back", on_click=lambda: ui.navigate.to(f"/vote/{vote_id}")).classes("mb-4 self-start bg-gray-600 text-white")
        
        # Fetch vote details to check if its a private vote
        vote_details = api_get("/votedetails", {"vote_id": vote_id})
        is_private = False
        if isinstance(vote_details, dict) and vote_details.get("mode") == "private":
            is_private = True

        with ui.card().classes("w-full max-w-md p-6 text-center"):
            ui.label("Confirm Participation").classes("text-2xl font-bold text-gray-800 mb-4")
            ui.label("By participating, your name will be added to the list of voters for this vote.").classes("text-gray-600 mb-2")
            ui.label("Your vote will be securely recorded on the blockchain.").classes("text-gray-500 mb-6")
            
            pwd_input = None
            if is_private:
                pwd_input = ui.input("Vote Password").classes("w-full mb-4").props("outlined")
            
            # confirm participation and register the user for the vote
            def confirm():
                if not app.state.user_id:
                    ui.notify("Please login first", color="negative")
                    ui.navigate.to("/login")
                    return
                
                with ui.dialog() as dlg:
                    ui.label("Registering...").classes("text-lg p-4")
                dlg.open()
                ui.update()
                
                params = {"vote_id": vote_id, "user_id": app.state.user_id}
                if is_private and pwd_input:
                    params["vote_password"] = pwd_input.value
                
                result = api_get("/registervoter", params)
                dlg.close()
                
                if is_true(result):
                    ui.navigate.to(f"/vote/{vote_id}/cast")
                else:
                    ui.notify("Already registered or error occurred", color="negative")
            
            with ui.row().classes("w-full gap-4 justify-center"):
                ui.button("Yes, Continue", on_click=confirm).classes("bg-indigo-600 text-white px-6")
                ui.button("Cancel", on_click=lambda: ui.navigate.to(f"/vote/{vote_id}")).classes("bg-gray-200 text-gray-700 px-6")

# page for casting a vote
@ui.page("/vote/{vote_id}/cast")
def page_vote_cast(vote_id: str):
    header()
    
    with ui.column().classes("w-full items-center mt-6 px-4"):
        ui.button("Back", icon="arrow_back", on_click=lambda: ui.navigate.to(f"/vote/{vote_id}/participate")).classes("mb-4 self-start bg-gray-600 text-white")
        
        content = ui.column().classes("w-full max-w-md gap-4")
        
        with ui.dialog() as loading_dlg:
            ui.label("Loading options...").classes("text-lg p-4")
        loading_dlg.open()
        ui.update()
        
        # get vote details to show options
        result = api_get("/votedetails", {"vote_id": vote_id})
        loading_dlg.close()
        
        options = []
        title = "Cast Your Vote"
        
        if isinstance(result, dict) and "error" not in result:
            options = result.get("options", ["Option 1", "Option 2"])
            title = result.get("title", "Cast Your Vote")
        else:
            options = ["Option 1", "Option 2", "Option 3"]
        
        with content:
            ui.label(title).classes("text-2xl font-bold text-gray-800 text-center")
            ui.label("Select your choice:").classes("text-gray-600 text-center")
            
            selected = ui.radio(options=options, value=options[0] if options else None).classes("w-full")
            
            # move to the final verification step
            def next_step():
                if not selected.value:
                    ui.notify("Please select an option", color="negative")
                    return
                app.state.selected_option = selected.value
                ui.navigate.to(f"/vote/{vote_id}/verify")
            
            ui.button("Continue", on_click=next_step).classes("w-full bg-indigo-600 text-white py-3 mt-4")

# page to verify user identity with their 3 safety words
@ui.page("/vote/{vote_id}/verify")
def page_vote_verify(vote_id: str):
    header()
    
    with ui.column().classes("w-full items-center mt-6 px-4"):
        ui.button("Back", icon="arrow_back", on_click=lambda: ui.navigate.to(f"/vote/{vote_id}/cast")).classes("mb-4 self-start bg-gray-600 text-white")
        
        with ui.card().classes("w-full max-w-md p-6"):
            ui.label("Verify Identity").classes("text-2xl font-bold text-center text-gray-800 mb-2")
            ui.label("Enter your 3 safety words to confirm it's you").classes("text-gray-500 text-center mb-6")
            
            with ui.row().classes("w-full gap-2 justify-center"):
                w1 = ui.input("Word 1").classes("w-24")
                w2 = ui.input("Word 2").classes("w-24")
                w3 = ui.input("Word 3").classes("w-24")

            vote_pwd_input = ui.input("Vote Password (If Private)").classes("w-full mt-2").props("outlined")
            
            error_label = ui.label("").classes("text-red-500 text-sm text-center mt-2").style("display: none")
            
            # submit the vote after verification
            def submit():
                error_label.style("display: none")
                
                w1_val = w1.value.strip()
                w2_val = w2.value.strip()
                w3_val = w3.value.strip()
                
                if not all([w1_val, w2_val, w3_val]):
                    error_label.set_text("Please enter all 3 words")
                    error_label.style("display: block")
                    return
                
                with ui.dialog() as dlg:
                    ui.label("Verifying...").classes("text-lg p-4")
                dlg.open()
                ui.update()
                
                # first, verify the user's words
                verify_result = api_get("/verifyuserwords", {
                    "special_word1": w1_val,
                    "special_word2": w2_val,
                    "special_word3": w3_val,
                    "user_id": app.state.user_id
                })
                
                if not is_true(verify_result):
                    dlg.close()
                    error_label.set_text("Words verification failed")
                    error_label.style("display: block")
                    return
                
                # then, cast the vote
                data = {
                    "vote_id": vote_id,
                    "user_id": app.state.user_id,
                    "option_chosen": app.state.selected_option,
                    "vote_password": vote_pwd_input.value if vote_pwd_input.value else None,
                    "special_word1": w1_val,
                    "special_word2": w2_val,
                    "special_word3": w3_val
                }
                
                cast_result = api_post("/castvote", data)
                dlg.close()
                
                if isinstance(cast_result, str) and len(cast_result) > 10:
                    app.state.vote_signature = cast_result
                    ui.navigate.to(f"/vote/{vote_id}/success")
                elif is_true(cast_result):
                    ui.navigate.to(f"/vote/{vote_id}/success")
                else:
                    error_label.set_text("Vote failed. You may have already voted.")
                    error_label.style("display: block")
            
            ui.button("Submit Vote", on_click=submit).classes("w-full bg-green-600 text-white py-3 mt-4")
            error_label

# success page after a vote is submitted
@ui.page("/vote/{vote_id}/success")
def page_vote_success(vote_id: str):
    header()
    
    with ui.column().classes("w-full items-center justify-center").style("min-height: 70vh"):
        with ui.card().classes("w-full max-w-md p-8 text-center"):
            ui.icon("check_circle", size="80px").classes("text-green-500 mb-4")
            ui.label("Vote Submitted!").classes("text-3xl font-bold text-gray-800 mb-2")
            ui.label(f"You voted for:").classes("text-gray-600")
            ui.label(app.state.selected_option).classes("text-xl font-bold text-indigo-600 mb-6")
            
            with ui.card().classes("w-full p-4 bg-green-50 border border-green-200 mb-6"):
                ui.label("Your vote has been recorded on the blockchain").classes("text-sm text-green-700")
                if app.state.vote_signature:
                    ui.link("View on Solscan (Devnet)", f"https://solscan.io/tx/{app.state.vote_signature}?cluster=devnet", new_tab=True).classes("text-xs text-indigo-600 break-all mt-2 block")
            
            with ui.row().classes("w-full gap-3"):
                ui.button("View Vote", on_click=lambda: ui.navigate.to(f"/vote/{vote_id}")).classes("flex-1 bg-indigo-600 text-white")
                ui.button("Home", on_click=lambda: ui.navigate.to("/")).classes("flex-1 bg-gray-200 text-gray-700")

# page for creating a new vote
@ui.page("/create")
def page_create():
    header()
    
    with ui.column().classes("w-full items-center mt-6 px-4"):
        ui.label("Create New Vote").classes("text-3xl font-bold mb-4")
        
        with ui.card().classes("w-full max-w-2xl p-6"):
            with ui.row().classes("w-full gap-4"):
                with ui.column().classes("flex-1 gap-3"):
                    title = ui.input("Vote Title *").classes("w-full").props("outlined")
                    reason = ui.textarea("Description/Reason *").classes("w-full").props("outlined")
                    organiser = ui.input("Organiser Name").classes("w-full").props("outlined")
                
                with ui.column().classes("flex-1 gap-3"):
                    ui.label("Start Date/Time * (YYYY-MM-DD-HH-MM)").classes("text-sm text-gray-500")
                    with ui.row().classes("w-full gap-2"):
                        start = ui.input("").classes("flex-1").props("outlined placeholder='2026-02-15-09-00'")
                        ui.button("Now", on_click=lambda: start.set_value(datetime.now().strftime("%Y-%m-%d-%H-%M"))).props("flat dense")
                    
                    ui.label("End Date/Time * (YYYY-MM-DD-HH-MM)").classes("text-sm text-gray-500")
                    end = ui.input("").classes("w-full").props("outlined placeholder='2026-02-20-18-00'")
                    
                    ui.label("Options (comma separated) *").classes("text-sm text-gray-500")
                    options = ui.input("Option A, Option B, Option C").classes("w-full").props("outlined")

                    vote_pwd = ui.input("Vote Password (Optional)").classes("w-full").props("outlined") # added password option
            
            error_label = ui.label("").classes("text-red-500 text-sm mt-2").style("display: none")
            
            # function to handle the creation of the vote
            def do_create():
                error_label.style("display: none")
                
                if not app.state.user_id:
                    ui.notify("Please login first", color="negative")
                    ui.navigate.to("/login")
                    return
                
                if not all([title.value, reason.value, start.value, end.value, options.value]):
                    error_label.set_text("Please fill all required fields")
                    error_label.style("display: block")
                    return
                
                opts = [o.strip() for o in options.value.split(",") if o.strip()]
                if len(opts) < 2:
                    error_label.set_text("Need at least 2 options")
                    error_label.style("display: block")
                    return
                
                with ui.dialog() as dlg:
                    ui.label("Creating vote...").classes("text-lg p-4")
                dlg.open()
                ui.update()
                
                # data for the new vote
                data = {
                    "title": title.value,
                    "reason": reason.value,
                    "organiser_public": organiser.value or app.state.user or "Anonymous",
                    "start_time": start.value,
                    "end_time": end.value,
                    "options_list": opts,
                    "user_id": app.state.user_id,
                    "vote_password": vote_pwd.value if vote_pwd.value else None
                }
                
                # post the data to the api
                result = api_post("/create", data)
                dlg.close()
                
                if isinstance(result, str) and len(result) == 8:
                    ui.notify(f"Vote created! ID: {result}", color="positive")
                    ui.navigate.to(f"/vote/{result}")
                elif is_true(result):
                    ui.notify("Vote created successfully!", color="positive")
                    ui.navigate.to("/votes")
                else:
                    error_label.set_text("Failed to create vote. Check your inputs or try again later. Please note if you have created a vote before you can not create another. Also check if your end time is before your start time or if your start time is before the current time.")
                    error_label.style("display: block")
            
            ui.button("Create Vote", icon="add", on_click=do_create).classes("w-full bg-indigo-600 text-white py-3 mt-4")
            error_label

# audit pannel for auditors and admins
@ui.page("/audit")
def page_audit():
    header()
    
    with ui.column().classes("w-full items-center mt-6 px-4"):
        ui.label("Audit Panel").classes("text-3xl font-bold mb-4")
        
        if not app.state.user:
            with ui.card().classes("w-full max-w-md p-8 text-center"):
                ui.icon("lock", size="64px").classes("text-gray-300 mb-4")
                ui.label("Access Denied").classes("text-xl text-gray-600 mb-2")
                ui.label("Please login to access the audit panel.").classes("text-gray-500")
                ui.button("Login", on_click=lambda: ui.navigate.to("/login")).classes("bg-indigo-600 text-white mt-4")
            return
        
        # Check if user is an auditor or admin
        is_auditor = api_get("/isuserp", {
            "user_id": app.state.user_id,
            "role": "auditor"
        })
        is_admin = api_get("/isuserp", {
            "user_id": app.state.user_id,
            "role": "admin"
        })
        
        if not is_true(is_auditor) and not is_true(is_admin):
            with ui.card().classes("w-full max-w-md p-8 text-center"):
                ui.icon("block", size="64px").classes("text-red-400 mb-4")
                ui.label("Access Denied").classes("text-xl text-red-600 mb-2")
                ui.label("You must be an auditor or admin to access this panel.").classes("text-gray-500 mb-4")
                ui.label(f"Your user ID: {app.state.user_id}").classes("text-sm text-gray-400")
                ui.button("Back to Home", on_click=lambda: ui.navigate.to("/")).classes("bg-indigo-600 text-white mt-4")
            return
        
        with ui.card().classes("w-full max-w-2xl p-6"):
            ui.label("Search Vote").classes("text-lg font-bold mb-3")
            with ui.row().classes("w-full gap-2"):
                audit_input = ui.input("Vote ID").classes("flex-1").props("outlined")
                search_btn = ui.button("Search", icon="search").classes("bg-indigo-600 text-white")

        with ui.card().classes("w-full max-w-2xl p-6 mt-4"): # log viewer for auditors
            ui.label("Vote Logs").classes("text-lg font-bold mb-3")
            
            log_select = ui.select(options=[], label="Select Log File").classes("w-full mb-2")
            log_content = ui.textarea().classes("w-full h-64").props("readonly")
            
            def load_log_list():
                res = api_get("/getvotelogs")
                if res and "logs" in res:
                    log_select.options = res["logs"]
                    log_select.update()
                    
            def view_log():
                if not log_select.value:
                    return
                res = api_get("/readvotelog", {"filename": log_select.value})
                if res and "log" in res:
                    log_content.value = res["log"]
            
            def search_log():
                if not audit_input.value:
                    ui.notify("Please enter a Vote ID", color="warning")
                    return
                
                filename = f"vote_{audit_input.value}.log"
                res = api_get("/readvotelog", {"filename": filename})
                
                if res and "log" in res and res["log"] != "Log file not found.":
                    log_content.value = res["log"]
                    if filename in log_select.options:
                        log_select.value = filename
                else:
                    ui.notify("Log not found", color="negative")
                    log_content.value = "Log file not found."
                    
            load_log_list()
            with ui.row().classes("gap-2"):
                ui.button("Refresh List", on_click=load_log_list)
                ui.button("View Log", on_click=view_log)
            
            search_btn.on_click(search_log)

# admin pannel for managing the system
@ui.page("/admin")
def page_admin():
    header()
    
    with ui.column().classes("w-full items-center mt-6 px-4"):
        ui.label("Admin Panel").classes("text-3xl font-bold mb-4")
        
        if not app.state.user:
            with ui.card().classes("w-full max-w-md p-8 text-center"):
                ui.icon("lock", size="64px").classes("text-gray-300 mb-4")
                ui.label("Admin Access Required").classes("text-xl text-gray-600 mb-2")
                ui.label("Please login with an admin account.").classes("text-gray-500")
                ui.button("Login", on_click=lambda: ui.navigate.to("/login")).classes("bg-indigo-600 text-white mt-4")
            return
        
        # Check if user is an admin
        is_admin = api_get("/isuserp", {
            "user_id": app.state.user_id,
            "role": "admin"
        })
        
        if not is_true(is_admin):
            with ui.card().classes("w-full max-w-md p-8 text-center"):
                ui.icon("block", size="64px").classes("text-red-400 mb-4")
                ui.label("Access Denied").classes("text-xl text-red-600 mb-2")
                ui.label("You are not an admin.").classes("text-gray-500 mb-4")
                ui.label(f"Your user ID: {app.state.user_id}").classes("text-sm text-gray-400")
                ui.button("Back to Home", on_click=lambda: ui.navigate.to("/")).classes("bg-indigo-600 text-white mt-4")
            return
        
        # Admin Management Section
        with ui.card().classes("w-full max-w-2xl p-6 mb-6"):
            ui.label("Manage Admins").classes("text-lg font-bold mb-4")
            
            # Add new admin
            with ui.row().classes("w-full gap-2 items-end"): 
                new_admin_input = ui.input("User ID to add").classes("flex-1").props("outlined")
                
                def add_admin():
                    if not new_admin_input.value:
                        ui.notify("Please enter a user ID", type="negative")
                        return
                    
                    result = api_get("/adduserp", {
                        "user_id": new_admin_input.value,
                        "role": "admin"
                    })
                    
                    if is_true(result):
                        ui.notify(f"Added {new_admin_input.value} as admin", type="positive")
                        new_admin_input.value = ""
                        refresh_admins()
                    else:
                        ui.notify("Failed to add admin", type="negative")
                
                ui.button("Add Admin", on_click=add_admin, icon="person_add").classes("bg-green-600 text-white")
            
            # Display admin list
            ui.separator()
            ui.label("Current Admins").classes("text-md font-semibold mt-4 mb-2")
            admin_list_container = ui.column().classes("w-full")
            
            def refresh_admins(): 
                admin_list_container.clear()
                
                # Fetch admins from API
                admins_result = api_get("/getprivileges", {"role": "admin"})
                admins = admins_result if isinstance(admins_result, list) else []
                
                if not admins:
                    with admin_list_container:
                        ui.label("No admins assigned").classes("text-gray-500 italic")
                else:
                    for admin_id in admins:
                        with admin_list_container:
                            with ui.row().classes("w-full items-center justify-between bg-gray-100 p-3 rounded"):
                                ui.label(admin_id).classes("text-sm font-mono flex-1")
                                
                                def remove_admin(user_id=admin_id):
                                    result = api_get("/removeuserp", {
                                        "user_id": user_id,
                                        "role": "admin"
                                    })
                                    
                                    if is_true(result):
                                        ui.notify(f"Removed {user_id} from admins", type="positive")
                                        refresh_admins()
                                    else:
                                        ui.notify("Failed to remove admin", type="negative")
                                
                                ui.button(icon="close", on_click=remove_admin).props("flat dense").classes("text-red-600")
            
            refresh_admins()
        
        # Auditor Management Section
        with ui.card().classes("w-full max-w-2xl p-6 mb-6"):
            ui.label("Manage Auditors").classes("text-lg font-bold mb-4")
            
            # Add new auditor
            with ui.row().classes("w-full gap-2 items-end"): 
                new_auditor_input = ui.input("User ID to add").classes("flex-1").props("outlined")
                
                def add_auditor():
                    if not new_auditor_input.value:
                        ui.notify("Please enter a user ID", type="negative")
                        return
                    
                    result = api_get("/adduserp", {
                        "user_id": new_auditor_input.value,
                        "role": "auditor"
                    })
                    
                    if is_true(result):
                        ui.notify(f"Added {new_auditor_input.value} as auditor", type="positive")
                        new_auditor_input.value = ""
                        refresh_auditors()
                    else:
                        ui.notify("Failed to add auditor", type="negative")
                
                ui.button("Add Auditor", on_click=add_auditor, icon="person_add").classes("bg-blue-600 text-white")
            
            # Display auditor list
            ui.separator()
            ui.label("Current Auditors").classes("text-md font-semibold mt-4 mb-2")
            auditor_list_container = ui.column().classes("w-full")
            
            def refresh_auditors(): 
                auditor_list_container.clear()
                
                # fetch auditors from API
                auditors_result = api_get("/getprivileges", {"role": "auditor"})
                auditors = auditors_result if isinstance(auditors_result, list) else []
                
                if not auditors:
                    with auditor_list_container:
                        ui.label("No auditors assigned").classes("text-gray-500 italic")
                else:
                    for auditor_id in auditors:
                        with auditor_list_container:
                            with ui.row().classes("w-full items-center justify-between bg-gray-100 p-3 rounded"):
                                ui.label(auditor_id).classes("text-sm font-mono flex-1")
                                
                                def remove_auditor(user_id=auditor_id):
                                    result = api_get("/removeuserp", {
                                        "user_id": user_id,
                                        "role": "auditor"
                                    })
                                    
                                    if is_true(result):
                                        ui.notify(f"Removed {user_id} from auditors", type="positive")
                                        refresh_auditors()
                                    else:
                                        ui.notify("Failed to remove auditor", type="negative")
                                
                                ui.button(icon="close", on_click=remove_auditor).props("flat dense").classes("text-red-600")
            
            refresh_auditors()

        with ui.card().classes("w-full max-w-2xl p-6 mb-6"): # system log 8viewer
            ui.label("System Logs").classes("text-lg font-bold mb-4")
            log_area = ui.textarea().classes("w-full h-64").props("readonly")
            
            def refresh_logs():
                res = api_get("/getsystemlog")
                if res and "log" in res:
                    log_area.value = res["log"]
            
            ui.button("Refresh Logs", on_click=refresh_logs).classes("bg-gray-600 text-white mb-2")
            refresh_logs()
