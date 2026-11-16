# Mergington High School Activities API

A super simple FastAPI application that allows students to view and sign up for extracurricular activities.

## Features

- View all available extracurricular activities
- Teacher sign-in to manage student registrations
- Sign up for or unregister students from activities (teachers only)

## Getting Started

1. Install the dependencies:

   ```
   pip install fastapi uvicorn itsdangerous
   ```

2. Configure teacher authentication. Do not commit credentials or secrets to the repository.

   Generate a PBKDF2-SHA256 password hash and a session signing key:

   ```powershell
   python -c 'import hashlib,getpass,secrets; password=getpass.getpass("Teacher password: "); salt=secrets.token_bytes(16); iterations=600000; digest=hashlib.pbkdf2_hmac("sha256",password.encode(),salt,iterations).hex(); print("pbkdf2_sha256${}${}${}".format(iterations,salt.hex(),digest))'
   python -c "import secrets; print(secrets.token_urlsafe(32))"
   ```

   Set the resulting values as `ADMIN_USERNAME`, `ADMIN_PASSWORD_HASH`, and `SESSION_SECRET_KEY` in the server environment. The app keeps activity listings public but disables administrator actions until all three values are valid. For local HTTP development only, set `SESSION_COOKIE_SECURE=false`; the default is `true` and should be retained when serving over HTTPS.

   Example for a local PowerShell session (replace the placeholders and keep these values out of source control):

   ```powershell
   $env:ADMIN_USERNAME = "teacher"
   $env:ADMIN_PASSWORD_HASH = "<generated password hash>"
   $env:SESSION_SECRET_KEY = "<generated session key>"
   $env:SESSION_COOKIE_SECURE = "false"
   ```

3. Run the application:

   ```
   uvicorn src.app:app --reload
   ```

4. Open your browser and go to:
   - API documentation: http://localhost:8000/docs
   - Alternative documentation: http://localhost:8000/redoc

## API Endpoints

| Method | Endpoint                                                          | Description                                                |
| ------ | ----------------------------------------------------------------- | ---------------------------------------------------------- |
| GET    | `/activities`                                                     | Public activity list with participant details              |
| GET    | `/admin/session`                                                  | Check whether the current browser has an admin session     |
| POST   | `/admin/login`                                                    | Sign in with the configured teacher username and password  |
| POST   | `/admin/logout`                                                   | End the current admin session                              |
| POST   | `/activities/{activity_name}/signup?email=student@mergington.edu` | Sign up a student (admin session required)                 |
| DELETE | `/activities/{activity_name}/unregister?email=student@mergington.edu` | Unregister a student (admin session required)            |

## Data Model

The application uses a simple data model with meaningful identifiers:

1. **Activities** - Uses activity name as identifier:

   - Description
   - Schedule
   - Maximum number of participants allowed
   - List of student emails who are signed up

2. **Students** - Uses email as identifier:
   - Name
   - Grade level

All data is stored in memory, which means data will be reset when the server restarts.

## Running Tests

Install the development dependencies and run the focused API tests:

```powershell
pip install -r requirements-dev.txt
pytest
```
