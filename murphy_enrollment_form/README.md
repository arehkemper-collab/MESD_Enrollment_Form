# Murphy ESD Enrollment Form (Draft)

This is a **demo / review** version of the Murphy ESD enrollment form:
- English / Español toggle
- Typed data only (no document uploads)
- Local staging storage (SQLite)
- Internal notification email (demo: sends to Allen's district email)
- Optional parent confirmation email

## Quick start

```bash
cd murphy_enrollment_form
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Demo email settings (example)
export APP_SECRET='change-me'
export INTERNAL_NOTIFY_EMAIL='YOUR_DISTRICT_EMAIL@msdaz.org'
export FROM_EMAIL='enrollment-demo@msdaz.org'
export SMTP_HOST='smtp.yourdomain.org'
export SMTP_PORT='587'
export SMTP_USERNAME='smtp-user'
export SMTP_PASSWORD='smtp-pass'
export SMTP_USE_TLS='true'

# Optional admin password for /admin
export ADMIN_PASSWORD='set-a-demo-password'

python app.py
```

Open: http://127.0.0.1:5000

## Notes
- Submissions are saved to `enrollment.db` in the project folder by default.
- For demo/review, this should run on a local machine or internal-only VM.
- When you build the DMZ layer, keep the **database internal** and expose only the web app over HTTPS.
