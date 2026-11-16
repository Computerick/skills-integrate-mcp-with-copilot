"""
High School Management System API

A super simple FastAPI application that allows students to view and sign up
for extracurricular activities at Mergington High School.
"""

import hashlib
import logging
import os
from pathlib import Path
import secrets

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from starlette.middleware.sessions import SessionMiddleware

app = FastAPI(title="Mergington High School API",
              description="API for viewing and signing up for extracurricular activities")

logger = logging.getLogger(__name__)

SESSION_SECRET_KEY = os.getenv("SESSION_SECRET_KEY")
SESSION_COOKIE_SECURE = os.getenv("SESSION_COOKIE_SECURE", "true").lower()
if SESSION_COOKIE_SECURE not in {"true", "false"}:
    raise ValueError("SESSION_COOKIE_SECURE must be 'true' or 'false'")


def parse_password_hash(value: str | None) -> tuple[int, bytes, bytes] | None:
    if not value:
        return None

    try:
        algorithm, iterations_value, salt_value, digest_value = value.split("$")
        iterations = int(iterations_value)
        salt = bytes.fromhex(salt_value)
        digest = bytes.fromhex(digest_value)
    except ValueError:
        logger.error("ADMIN_PASSWORD_HASH has an invalid format")
        return None

    if (
        algorithm != "pbkdf2_sha256"
        or iterations < 600_000
        or len(salt) < 16
        or len(digest) != 32
    ):
        logger.error("ADMIN_PASSWORD_HASH does not meet the required format")
        return None

    return iterations, salt, digest


ADMIN_USERNAME = os.getenv("ADMIN_USERNAME")
ADMIN_PASSWORD_HASH = parse_password_hash(os.getenv("ADMIN_PASSWORD_HASH"))
ADMIN_AUTH_CONFIGURED = bool(
    ADMIN_USERNAME
    and ADMIN_PASSWORD_HASH
    and SESSION_SECRET_KEY
    and len(SESSION_SECRET_KEY) >= 32
)

if not ADMIN_AUTH_CONFIGURED:
    logger.warning(
        "Admin authentication is disabled. Configure ADMIN_USERNAME, "
        "ADMIN_PASSWORD_HASH, and a SESSION_SECRET_KEY of at least 32 characters."
    )

app.add_middleware(
    SessionMiddleware,
    secret_key=SESSION_SECRET_KEY or secrets.token_urlsafe(32),
    session_cookie="mergington_admin_session",
    max_age=8 * 60 * 60,
    same_site="lax",
    https_only=SESSION_COOKIE_SECURE == "true",
)


class AdminCredentials(BaseModel):
    username: str = Field(min_length=1, max_length=64)
    password: str = Field(min_length=1, max_length=128)


def require_admin(request: Request) -> None:
    if not ADMIN_AUTH_CONFIGURED:
        raise HTTPException(
            status_code=503,
            detail="Administrator authentication is not configured",
        )
    if request.session.get("admin_authenticated") is not True:
        raise HTTPException(status_code=401, detail="Administrator login required")


# Mount the static files directory
current_dir = Path(__file__).parent
app.mount("/static", StaticFiles(directory=os.path.join(Path(__file__).parent,
          "static")), name="static")

# In-memory activity database
activities = {
    "Chess Club": {
        "description": "Learn strategies and compete in chess tournaments",
        "schedule": "Fridays, 3:30 PM - 5:00 PM",
        "max_participants": 12,
        "participants": ["michael@mergington.edu", "daniel@mergington.edu"]
    },
    "Programming Class": {
        "description": "Learn programming fundamentals and build software projects",
        "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
        "max_participants": 20,
        "participants": ["emma@mergington.edu", "sophia@mergington.edu"]
    },
    "Gym Class": {
        "description": "Physical education and sports activities",
        "schedule": "Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM",
        "max_participants": 30,
        "participants": ["john@mergington.edu", "olivia@mergington.edu"]
    },
    "Soccer Team": {
        "description": "Join the school soccer team and compete in matches",
        "schedule": "Tuesdays and Thursdays, 4:00 PM - 5:30 PM",
        "max_participants": 22,
        "participants": ["liam@mergington.edu", "noah@mergington.edu"]
    },
    "Basketball Team": {
        "description": "Practice and play basketball with the school team",
        "schedule": "Wednesdays and Fridays, 3:30 PM - 5:00 PM",
        "max_participants": 15,
        "participants": ["ava@mergington.edu", "mia@mergington.edu"]
    },
    "Art Club": {
        "description": "Explore your creativity through painting and drawing",
        "schedule": "Thursdays, 3:30 PM - 5:00 PM",
        "max_participants": 15,
        "participants": ["amelia@mergington.edu", "harper@mergington.edu"]
    },
    "Drama Club": {
        "description": "Act, direct, and produce plays and performances",
        "schedule": "Mondays and Wednesdays, 4:00 PM - 5:30 PM",
        "max_participants": 20,
        "participants": ["ella@mergington.edu", "scarlett@mergington.edu"]
    },
    "Math Club": {
        "description": "Solve challenging problems and participate in math competitions",
        "schedule": "Tuesdays, 3:30 PM - 4:30 PM",
        "max_participants": 10,
        "participants": ["james@mergington.edu", "benjamin@mergington.edu"]
    },
    "Debate Team": {
        "description": "Develop public speaking and argumentation skills",
        "schedule": "Fridays, 4:00 PM - 5:30 PM",
        "max_participants": 12,
        "participants": ["charlotte@mergington.edu", "henry@mergington.edu"]
    }
}


@app.get("/")
def root():
    return RedirectResponse(url="/static/index.html")


@app.get("/activities")
def get_activities():
    return activities


@app.get("/admin/session")
def get_admin_session(request: Request):
    return {
        "authenticated": ADMIN_AUTH_CONFIGURED
        and request.session.get("admin_authenticated") is True
    }


@app.post("/admin/login")
def admin_login(credentials: AdminCredentials, request: Request):
    if not ADMIN_AUTH_CONFIGURED:
        raise HTTPException(
            status_code=503,
            detail="Administrator authentication is not configured",
        )

    request.session.clear()
    username_matches = secrets.compare_digest(
        credentials.username.encode("utf-8"),
        ADMIN_USERNAME.encode("utf-8"),
    )
    iterations, salt, expected_digest = ADMIN_PASSWORD_HASH
    provided_digest = hashlib.pbkdf2_hmac(
        "sha256",
        credentials.password.encode("utf-8"),
        salt,
        iterations,
    )
    password_matches = secrets.compare_digest(provided_digest, expected_digest)

    if not username_matches or not password_matches:
        raise HTTPException(status_code=401, detail="Invalid username or password")

    request.session["admin_authenticated"] = True
    return {"authenticated": True}


@app.post("/admin/logout")
def admin_logout(request: Request):
    request.session.clear()
    return {"authenticated": False}


@app.post("/activities/{activity_name}/signup")
def signup_for_activity(activity_name: str, email: str, request: Request):
    """Sign up a student for an activity"""
    require_admin(request)

    # Validate activity exists
    if activity_name not in activities:
        raise HTTPException(status_code=404, detail="Activity not found")

    # Get the specific activity
    activity = activities[activity_name]

    # Validate student is not already signed up
    if email in activity["participants"]:
        raise HTTPException(
            status_code=400,
            detail="Student is already signed up"
        )

    # Add student
    activity["participants"].append(email)
    return {"message": f"Signed up {email} for {activity_name}"}


@app.delete("/activities/{activity_name}/unregister")
def unregister_from_activity(activity_name: str, email: str, request: Request):
    """Unregister a student from an activity"""
    require_admin(request)

    # Validate activity exists
    if activity_name not in activities:
        raise HTTPException(status_code=404, detail="Activity not found")

    # Get the specific activity
    activity = activities[activity_name]

    # Validate student is signed up
    if email not in activity["participants"]:
        raise HTTPException(
            status_code=400,
            detail="Student is not signed up for this activity"
        )

    # Remove student
    activity["participants"].remove(email)
    return {"message": f"Unregistered {email} from {activity_name}"}
