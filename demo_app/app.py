from __future__ import annotations
from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse
import uvicorn

app = FastAPI(title="Legacy Core Banking Demo")
MEMBERS = {
    "12345": {"name": "Demo Member", "savings": "$12,430.18", "checking": "$2,188.40"},
    "77777": {"name": "Read Only Member", "savings": "$91.00", "checking": "$0.00"},
}

def shell(body: str) -> str:
    return f"""<!doctype html><html><head><title>CoreServ 7</title><style>
    body{{font-family:Arial;background:#ddd}} table{{background:white;border:2px solid #777;margin:30px auto;padding:18px;width:700px}}
    td{{padding:8px}} .err{{color:#a00;font-weight:bold}} .ok{{color:#064}} input{{width:260px}}</style></head>
    <body><table role='presentation'><tr><td><b>CoreServ 7 :: Member Servicing</b></td></tr><tr><td>{body}</td></tr></table></body></html>"""

@app.get("/", response_class=HTMLResponse)
def home():
    return shell("""<form method='post' action='/lookup'><table role='presentation'>
    <tr><td>Member ID</td><td><input aria-label='Member ID' name='member_id'></td></tr>
    <tr><td></td><td><button type='submit'>Find Member</button></td></tr></table></form>""")

@app.post("/lookup", response_class=HTMLResponse)
def lookup(member_id: str = Form(...)):
    if member_id == "timeout":
        return shell("<div class='err'>Session expired. Please retry.</div><a href='/'>Return to search</a>")
    if member_id not in MEMBERS:
        return shell(f"<div class='err'>No member found for ID {member_id}</div><a href='/'>Return to search</a>")
    m = MEMBERS[member_id]
    permission = "<div class='err'>Permission denied: account changes disabled</div>" if member_id == "77777" else ""
    return shell(f"""<h2>Member Detail</h2><div>Member: <span>{m['name']}</span></div>
    <table><tr><th>Account</th><th>Balance</th></tr>
    <tr><td>Savings</td><td><span role='status' aria-label='Savings Balance'>{m['savings']}</span></td></tr>
    <tr><td>Checking</td><td><span role='status' aria-label='Checking Balance'>{m['checking']}</span></td></tr></table>
    {permission}<a href='/subaccount/{member_id}'>Open New Sub-Account</a>""")

@app.get("/subaccount/{member_id}", response_class=HTMLResponse)
def subaccount(member_id: str):
    if member_id == "77777": return shell("<div class='err'>Permission denied</div>")
    return shell(f"""<h2>New Sub-Account</h2><form method='post' action='/review/{member_id}'>
    <label>Nickname <input name='nickname' aria-label='Nickname'></label>
    <button type='submit'>Continue to Review</button></form>""")

@app.post("/review/{member_id}", response_class=HTMLResponse)
def review(member_id: str, nickname: str = Form(...)):
    if len(nickname.strip()) < 2: return shell("<div class='err'>Validation error: nickname too short</div>")
    return shell(f"""<h2>Review New Sub-Account</h2><p>Member ID: {member_id}</p><p>Nickname: {nickname}</p>
    <p class='ok'>Review ready. No account has been created.</p><button>Confirm & Create (disabled in demo)</button>""")

def main():
    uvicorn.run("demo_app.app:app", host="127.0.0.1", port=8000, reload=False)

if __name__ == "__main__": main()
