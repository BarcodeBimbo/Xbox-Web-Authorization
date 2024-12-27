from pathlib import Path
from waitress import serve
from urllib.parse import urlencode
from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    session,
    jsonify,
)

import os, uuid, json, requests, time, logging

XboxAPI = Flask(__name__)
XboxAPI.secret_key = os.urandom(24)

# File storage configuration
STORAGE_DIR = Path("token_storage")
STORAGE_DIR.mkdir(exist_ok=True)

# Configuration
CLIENT_ID = ""  # Azure Client ID
REDIRECT_URI = "http://127.0.0.1:5965/oauth_success"

# Add logging configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add this function to handle XUID resolution
def get_xuid(xsts_token):
    """Resolve the XUID for a given Xbox account."""
    headers = {
        "Authorization": f"XBL3.0 x={xsts_token['DisplayClaims']['xui'][0]['uhs']};{xsts_token['Token']}",
        "x-xbl-contract-version": "2",
    }

    try:
        response = requests.get(
            "https://profile.xboxlive.com/users/me/id", headers=headers
        )

        if response.status_code == 200:
            data = response.json()
            logger.info(f"Resolved XUID: {data['xuid']}")
            return data["xuid"]
        else:
            logger.error(f"Failed to resolve XUID. Status: {response.status_code}")
            return None

    except requests.exceptions.RequestException as e:
        logger.error(f"Network error while resolving XUID: {e}")
        return None


def store_token_data(token_data):
    """Store token data in a file with a unique ID"""
    session_id = str(uuid.uuid4())
    file_path = STORAGE_DIR / f"{session_id}.json"

    with open(file_path, "w") as f:
        json.dump(token_data, f)

    return session_id


def get_token_data(session_id):
    """Retrieve token data from file"""
    try:
        file_path = STORAGE_DIR / f"{session_id}.json"
        if file_path.exists():
            with open(file_path, "r") as f:
                return json.load(f)
    except Exception:
        pass
    return None


def delete_token_data(session_id):
    """Delete token data file"""

    try:
        file_path = STORAGE_DIR / f"{session_id}.json"

        if file_path.exists():
            file_path.unlink()
    except Exception:
        pass


def cleanup_old_tokens():
    """Clean up token files older than 1 hour"""

    current_time = time.time()

    for file_path in STORAGE_DIR.glob("*.json"):

        if current_time - file_path.stat().st_mtime > 3600:  # 1 hour
            try:
                file_path.unlink()
            except Exception:
                pass


def get_authorization_url():
    """Generate the Xbox Live authorization URL"""

    url = "https://login.live.com/oauth20_authorize.srf"

    params = {
        "client_id": CLIENT_ID,
        "response_type": "code",
        "approval_prompt": "auto",
        "scope": "Xboxlive.signin Xboxlive.offline_access",
        "redirect_uri": REDIRECT_URI,
    }

    return f"{url}?{urlencode(params)}"


def get_access_token(authorization_code):
    """Exchange authorization code for access token"""

    url = "https://login.live.com/oauth20_token.srf"

    data = {
        "grant_type": "authorization_code",
        "client_id": CLIENT_ID,
        "scope": "Xboxlive.signin Xboxlive.offline_access",
        "code": authorization_code,
        "redirect_uri": REDIRECT_URI,
    }

    response = requests.post(url, data=data)

    if response.status_code != 200:
        raise Exception("Failed to get access token")

    return response.json()["access_token"]


def get_user_token(access_token):
    """Get Xbox Live user token"""

    url = "https://user.auth.xboxlive.com/user/authenticate"

    headers = {"x-xbl-contract-version": "1"}

    data = {
        "RelyingParty": "http://auth.xboxlive.com",
        "TokenType": "JWT",
        "Properties": {
            "AuthMethod": "RPS",
            "SiteName": "user.auth.xboxlive.com",
            "RpsTicket": f"d={access_token}",
        },
    }

    response = requests.post(url, json=data, headers=headers)

    if response.status_code != 200:
        raise Exception("Failed to get user token")

    return response.json()["Token"]


def get_xsts_token(user_token):
    """Get XSTS token"""

    url = "https://xsts.auth.xboxlive.com/xsts/authorize"

    headers = {"x-xbl-contract-version": "1"}

    data = {
        "RelyingParty": "http://xboxlive.com",
        "TokenType": "JWT",
        "Properties": {
            "UserTokens": [user_token],
            "SandboxId": "RETAIL",
        },
    }

    response = requests.post(url, json=data, headers=headers)

    if response.status_code != 200:
        raise Exception("Failed to get XSTS token")

    return response.json()


def get_profile_data(xsts_token, xuid):
    """Fetch Xbox profile picture and gamertag"""

    headers = {
        "Authorization": f"XBL3.0 x={xsts_token['DisplayClaims']['xui'][0]['uhs']};{xsts_token['Token']}",
        "Accept-Encoding": "gzip, deflate",
        "x-xbl-contract-version": "5",
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Host": "peoplehub.xboxlive.com",
        "Connection": "Keep-Alive",
        "signature": "AAAAAQHZ0KSooB/TQ+yRliNEK6HICXOWmZ3DzsLyUWNTy0d9qQ1voXWGLoyY6Rn4PgVMlxJ2d1FbW60twBMX4QxYgzl7af6wFXTM5Q==",
        "accept-language": "en-US",
    }

    try:
        response = requests.get(
            f"https://peoplehub.xboxlive.com/users/me/people/xuids({xuid})/decoration/detail",
            headers=headers,
        )

        if response.status_code == 200:
            data = response.json()
            profile_info = {
                "gamertag": data["people"][0]["gamertag"],
                "profile_pic": data["people"][0]["displayPicRaw"],
            }
            return profile_info
        else:
            logger.error(f"Failed to fetch profile. Status: {response.status_code}")
            return None

    except Exception as e:
        logger.error(f"Error fetching profile: {e}")
        return None


@XboxAPI.route("/fetch_profile")
def fetch_profile():
    """Handle profile data fetch request"""
    if "session_id" not in session:
        return jsonify({"error": "Not authenticated"}), 401

    token_data = get_token_data(session["session_id"])
    if not token_data or "xuid" not in token_data:
        return jsonify({"error": "Token data or XUID not found"}), 401

    profile_data = get_profile_data(token_data["xsts_token"], token_data["xuid"])
    if profile_data:
        # Update token data with profile info
        token_data.update(profile_data)
        store_token_data(token_data)
        return jsonify(profile_data)
    else:
        return jsonify({"error": "Failed to fetch profile data"}), 500


@XboxAPI.route("/")
def index():
    token_data = None
    if "session_id" in session:
        token_data = get_token_data(session["session_id"])
        if token_data:
            # Create a safe version of token_data with only the needed fields
            token_data_safe = {
                "access_token": token_data.get("access_token", ""),
                "xuid": token_data.get("xuid", ""),
                "profile_pic": token_data.get("profile_pic", ""),
                "gamertag": token_data.get("gamertag", ""),
            }
        else:
            session.pop("session_id", None)
            token_data_safe = None
    else:
        token_data_safe = None

    return render_template("index.html", token_data=token_data_safe)


@XboxAPI.route("/login")
def login():
    """Initiate the OAuth flow"""
    auth_url = get_authorization_url()
    return redirect(auth_url)


@XboxAPI.route("/oauth_success")
def oauth_callback():
    """Handle the OAuth callback"""
    error = request.args.get("error")
    if error:
        flash(f"Authentication error: {error}", "danger")
        return redirect(url_for("index"))

    code = request.args.get("code")
    if not code:
        flash("No authorization code received", "danger")
        return redirect(url_for("index"))

    try:
        # Get all tokens
        access_token = get_access_token(code)
        user_token = get_user_token(access_token)
        xsts_token = get_xsts_token(user_token)

        # Get XUID
        xuid = get_xuid(xsts_token)
        if not xuid:
            raise Exception("Failed to resolve XUID")

        # Get profile data
        profile_data = get_profile_data(xsts_token, xuid)
        if not profile_data:
            raise Exception("Failed to fetch profile data")

        # Store all data
        token_data = {
            "access_token": access_token,
            "user_token": user_token,
            "xsts_token": xsts_token,
            "xuid": xuid,
            "gamertag": profile_data["gamertag"],
            "profile_pic": profile_data["profile_pic"],
        }
        session_id = store_token_data(token_data)
        session["session_id"] = session_id

        return redirect(url_for("index"))

    except Exception as e:
        flash(f"Authentication failed: {str(e)}", "danger")
        return redirect(url_for("index"))


@XboxAPI.route("/logout")
def logout():
    """Clear the session and log out"""
    if "session_id" in session:
        delete_token_data(session["session_id"])
    session.clear()
    flash("Successfully logged out", "success")
    return redirect(url_for("index"))


@XboxAPI.route("/resolve_xuid")
def resolve_xuid():
    """Handle XUID resolution request"""
    if "session_id" not in session:
        return jsonify({"error": "Not authenticated"}), 401

    token_data = get_token_data(session["session_id"])
    if not token_data:
        return jsonify({"error": "Token data not found"}), 401

    xuid = get_xuid(token_data["xsts_token"])
    if xuid:
        # Update token data with XUID
        token_data["xuid"] = xuid
        store_token_data(token_data)
        return jsonify({"xuid": xuid})
    else:
        return jsonify({"error": "Failed to resolve XUID"}), 500


if __name__ == "__main__":
    serve(XboxAPI, host="127.0.0.1", port=5965)
