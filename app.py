from nicegui import ui, app
from frontend.functions import *
from frontend.pages import *
from SystemLogging import *

log("Frontend server has started")

app.state.user = None
app.state.user_email = None
app.state.user_id = None
app.state.vote_id = None
app.state.selected_option = None
app.state.verification_code = None
app.state.special_words = []
app.state.temp_register = {}


if __name__ in {"__main__", "__mp_main__"}:
    ui.run(title="TrueVote", port=8080, reload=True, show=True)