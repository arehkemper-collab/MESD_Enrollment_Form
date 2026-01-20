import os
import json
import sqlite3
import smtplib
from email.message import EmailMessage
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, session, send_file, abort

APP_SECRET = os.getenv("APP_SECRET", "dev-secret-change-me")
DB_PATH = os.getenv("DB_PATH", os.path.join(os.path.dirname(__file__), "enrollment.db"))

# Demo settings
INTERNAL_NOTIFY_EMAIL = os.getenv("INTERNAL_NOTIFY_EMAIL", "")  # Allen's district email for demo
FROM_EMAIL = os.getenv("FROM_EMAIL", "enrollment-demo@msdaz.org")
SMTP_HOST = os.getenv("SMTP_HOST", "")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USERNAME = os.getenv("SMTP_USERNAME", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
SMTP_USE_TLS = os.getenv("SMTP_USE_TLS", "true").lower() in ("1", "true", "yes")

# Simple demo admin auth
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "")  # set to enable /admin

SCHOOLS = [
    ("kuban", "Kuban Elementary School"),
    ("sullivan", "Sullivan Elementary School"),
]

# Transportation options
TRANSPORT_OPTIONS_EN = [
    ("bus", "School Bus"),
    ("car", "Car/Automobile"),
    ("walk", "Walk"),
    ("bike", "Bike/Bicycle"),
    ("carpool", "Carpool"),
    ("other", "Other (please specify)"),
]
TRANSPORT_OPTIONS_ES = [
    ("bus", "Autobús Escolar"),
    ("car", "Auto/Automóvil"),
    ("walk", "Caminar"),
    ("bike", "Bicicleta"),
    ("carpool", "Viaje Compartido"),
    ("other", "Otro (por favor especifique)"),
]

# Bilingual labels (keep keys stable; labels swap by lang)
LABELS = {
    "en": {
        "title": "Student Enrollment",
        "lang_toggle": "Español",
        "school": "School",
        "yes": "Yes",
        "no": "No",
        "student_info": "Student Information",
        "first_name": "Student First Name",
        "last_name": "Student Last Name",
        "middle_name": "Student Middle Name (optional)",
        "dob": "Date of Birth",
        "sex": "Sex",
        "male": "Male",
        "female": "Female",
        "birth_state": "State of Birth",
        "birth_country": "Country of Birth",
        "address": "Residential Address",
        "apt": "Apt # (optional)",
        "city": "City",
        "zip": "Zip Code",
        "mailing_address": "Mailing Address (if different)",
        "history": "School History",
        "az_school": "Has the student attended school in Arizona?",
        "murphy_before": "Has the student attended Murphy District before?",
        "preschool": "Attended preschool / Head Start?",
        "last_school": "Last school attended",
        "last_school_city_state": "Last school city/state",
        "grade": "Grade",
        "demographics": "Demographics",
        "ethnicity": "Is the student Hispanic/Latino?",
        "race": "Race (select all that apply)",
        "tribal": "Does your family claim American Indian tribal affiliation?",
        "transport": "Transportation",
        "transport_placeholder": "e.g., Bus stop location or transportation type",
        "siblings": "Siblings",
        "siblings_has_murphy": "Do you have other siblings attending or enrolling in Murphy ESD?",
        "siblings_count": "How many siblings are attending or enrolling in Murphy ESD?",
        "sibling_name": "Full Name",
        "sibling_grade": "Grade",
        "sibling_school": "School",
        "sibling_lives": "Lives with enrolling child?",
        "custody": "Custody / Living Situation",
        "custody_type": "Student custody",
        "temp_address": "Is the current address only temporary?",
        "entry_us": "Entry date to the U.S. (if not born in the U.S.)",
        "services": "Services",
        "sped": "Special Education (IEP)",
        "plan504": "504 Plan",
        "gifted": "Gifted services",
        "refugee": "Refugee",
        "migrant": "Migrant",
        "immigrant": "Immigrant",
        "language": "Home Language",
        "home_language": "Primary language spoken at home",
        "discipline": "Discipline History",
        "expelled": "Has the student been expelled?",
        "suspended10": "Has the student been suspended more than 10 days?",
        "considered": "Has the student been considered for expulsion?",
        "parent": "Parent/Guardian",
        "parent_name": "Parent/Guardian Name",
        "parent_phone": "Cell Phone",
        "parent_cell": "Cell Phone",
        "parent_email": "Email (optional)",
        "custody_placeholder": "e.g., Mother, Father, Grandparent, etc.",
        "attest": "I certify I am a resident of Murphy ESD and that the information provided is true and correct.",
        "attestation": "Attest",
        "agree_text": "I certify I am a resident of Murphy ESD and that the information provided is true and correct.",
        "typed_signature": "Typed signature (full name)",
        "submit": "Submit Enrollment",
        "fix_errors": "Please fix the following errors:",
        "back": "Back",
        "continue_no_email": "Continue Without Email",
        "email_missing_title": "Email is recommended",
        "email_missing_body": "Providing an email helps us confirm we received your submission.",
        "email_modal": "Email is recommended. Would you like to continue without providing an email?",
        "email_warning_title": "Email is recommended",
        "email_warning_body": "Providing an email helps us confirm we received your submission and contact you if information is missing.",
        "go_back": "Go Back",
        "continue": "Continue Without Email",
        "success_title": "Submission Received",
        "next_steps": "Next steps: Please bring required documents to the school front office.",
    },
    "es": {
        "title": "Inscripción Estudiantil",
        "lang_toggle": "English",
        "school": "Escuela",
        "yes": "Sí",
        "no": "No",
        "student_info": "Información del Estudiante",
        "first_name": "Nombre del Estudiante",
        "last_name": "Apellido del Estudiante",
        "middle_name": "Segundo Nombre (opcional)",
        "dob": "Fecha de Nacimiento",
        "sex": "Sexo",
        "male": "Masculino",
        "female": "Femenino",
        "birth_state": "Estado de Nacimiento",
        "birth_country": "País de Nacimiento",
        "address": "Dirección Residencial",
        "apt": "Apt # (opcional)",
        "city": "Ciudad",
        "zip": "Código postal",
        "mailing_address": "Dirección postal (si es diferente)",
        "history": "Historial Escolar",
        "az_school": "¿Ha asistido a una escuela en Arizona?",
        "murphy_before": "¿Ha asistido al Distrito Murphy antes?",
        "preschool": "¿Asistió a preescolar / Head Start?",
        "last_school": "Última escuela a la que asistió",
        "last_school_city_state": "Ciudad/Estado de la última escuela",
        "grade": "Grado",
        "demographics": "Datos Demográficos",
        "ethnicity": "¿El estudiante es Hispano/Latino?",
        "race": "Raza (seleccione todas las que correspondan)",
        "tribal": "¿Su familia reclama afiliación tribal nativa americana?",
        "transport": "Transporte",
        "transport_placeholder": "por ejemplo, parada de autobús o tipo de transporte",
        "siblings": "Hermanos",
        "siblings_has_murphy": "¿Tiene otros hermanos que asistan o se inscriban en Murphy ESD?",
        "siblings_count": "¿Cuántos hermanos asisten o se inscriben en Murphy ESD?",
        "sibling_name": "Nombre completo",
        "sibling_grade": "Grado",
        "sibling_school": "Escuela",
        "sibling_lives": "¿Vive con el niño inscrito?",
        "custody": "Custodia / Situación de Vivienda",
        "custody_type": "Custodia del estudiante",
        "temp_address": "¿La dirección actual es temporal?",
        "entry_us": "Fecha de entrada a EE.UU. (si no nació en EE.UU.)",
        "services": "Servicios",
        "sped": "Educación Especial (IEP)",
        "plan504": "Plan 504",
        "gifted": "Niños Dotados",
        "refugee": "Refugiado",
        "migrant": "Migrante",
        "immigrant": "Inmigrante",
        "language": "Idioma en Casa",
        "home_language": "Idioma principal que se habla en casa",
        "discipline": "Historial Disciplinario",
        "expelled": "¿Ha sido expulsado?",
        "suspended10": "¿Suspendido por más de 10 días?",
        "considered": "¿Considerado para expulsión?",
        "parent": "Padre/Tutor",
        "parent_name": "Nombre del Padre/Tutor",
        "parent_phone": "Número de celular",
        "parent_cell": "Número de celular",
        "parent_email": "Correo electrónico (opcional)",
        "custody_placeholder": "por ejemplo, Madre, Padre, Abuelo, etc.",
        "attest": "Certifico que soy residente del Distrito Escolar Primario Murphy y que la información proporcionada es verdadera y correcta.",
        "attestation": "Atestación",
        "agree_text": "Certifico que soy residente del Distrito Escolar Primario Murphy y que la información proporcionada es verdadera y correcta.",
        "typed_signature": "Firma escrita (nombre completo)",
        "submit": "Enviar",
        "fix_errors": "Por favor, corrija los siguientes errores:",
        "back": "Atrás",
        "continue_no_email": "Continuar sin correo",
        "email_missing_title": "Se recomienda correo",
        "email_missing_body": "Proporcionar un correo ayuda a confirmar la recepción.",
        "email_modal": "Se recomienda correo. ¿Desea continuar sin proporcionar un correo?",
        "email_warning_title": "Se recomienda correo",
        "email_warning_body": "Proporcionar un correo ayuda a confirmar la recepción y a comunicarnos si falta información.",
        "go_back": "Regresar",
        "continue": "Continuar sin correo",
        "success_title": "Solicitud recibida",
        "next_steps": "Próximos pasos: Por favor traiga los documentos requeridos a la oficina de la escuela.",
    },
}

RACE_OPTIONS_EN = [
    ("asian", "Asian"),
    ("african_american", "African American"),
    ("white", "White"),
    ("american_indian_alaska", "American Indian/Alaska Native"),
    ("hawaiian_pacific_islander", "Native Hawaiian/Pacific Islander"),
]
RACE_OPTIONS_ES = [
    ("asian", "Asiático"),
    ("african_american", "Afroamericano"),
    ("white", "Blanco"),
    ("american_indian_alaska", "Indio Americano/Nativo de Alaska"),
    ("hawaiian_pacific_islander", "Nativo de Hawái u otra isla del Pacífico"),
]

CUSTODY_OPTIONS_EN = ["Shared", "Mother", "Father", "DCS", "Other"]
CUSTODY_OPTIONS_ES = ["Compartida", "Madre", "Padre", "DCS", "Otro"]


def db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    conn = db()
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS submissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            submission_id TEXT UNIQUE,
            created_at TEXT,
            lang TEXT,
            school TEXT,
            student_first TEXT,
            student_last TEXT,
            dob TEXT,
            parent_name TEXT,
            parent_email TEXT,
            parent_phone TEXT,
            payload_json TEXT
        );
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS counters (
            year INTEGER PRIMARY KEY,
            seq INTEGER NOT NULL
        );
        """
    )
    conn.commit()
    conn.close()


def next_submission_id(year: int) -> str:
    conn = db()
    cur = conn.cursor()
    cur.execute("SELECT seq FROM counters WHERE year=?", (year,))
    row = cur.fetchone()
    if row is None:
        seq = 1
        cur.execute("INSERT INTO counters(year, seq) VALUES(?, ?)", (year, seq))
    else:
        seq = int(row[0]) + 1
        cur.execute("UPDATE counters SET seq=? WHERE year=?", (seq, year))
    conn.commit()
    conn.close()
    return f"MUR-{year}-{seq:05d}"


def send_email(to_addr: str, subject: str, body: str) -> None:
    if not SMTP_HOST or not to_addr:
        return

    msg = EmailMessage()
    msg["From"] = FROM_EMAIL
    msg["To"] = to_addr
    msg["Subject"] = subject
    msg.set_content(body)

    if SMTP_USE_TLS:
        server = smtplib.SMTP(SMTP_HOST, SMTP_PORT)
        server.starttls()
    else:
        server = smtplib.SMTP(SMTP_HOST, SMTP_PORT)

    if SMTP_USERNAME:
        server.login(SMTP_USERNAME, SMTP_PASSWORD)

    server.send_message(msg)
    server.quit()


def require_admin():
    if not ADMIN_PASSWORD:
        abort(404)
    pw = request.args.get("pw") or request.headers.get("X-Admin-PW")
    if pw != ADMIN_PASSWORD:
        abort(401)


app = Flask(__name__)
app.secret_key = APP_SECRET


@app.route("/")
def home():
    return redirect(url_for("enroll", lang=request.args.get("lang", "en")))


@app.route("/enroll", methods=["GET", "POST"])
def enroll():
    lang = request.args.get("lang", "en")
    if lang not in ("en", "es"):
        lang = "en"

    labels = LABELS[lang]
    race_options = RACE_OPTIONS_EN if lang == "en" else RACE_OPTIONS_ES
    custody_options = CUSTODY_OPTIONS_EN if lang == "en" else CUSTODY_OPTIONS_ES
    transport_options = TRANSPORT_OPTIONS_EN if lang == "en" else TRANSPORT_OPTIONS_ES

    if request.method == "GET":
        return render_template(
            "enroll.html",
            lang=lang,
            labels=labels,
            schools=SCHOOLS,
            race_options=race_options,
            custody_options=custody_options,
            transport_options=transport_options,
            values={},
            email_warning=False,
        )

    data = request.form.to_dict(flat=True)

    # Collect multi-select race
    data["race"] = request.form.getlist("race")

    # Basic required fields
    required = ["school", "student_first", "student_last", "dob", "parent_name", "parent_phone", "typed_signature", "attest_check"]
    missing = [k for k in required if not data.get(k)]

    # Email warning flow
    parent_email = (data.get("parent_email") or "").strip()
    email_skip_confirmed = data.get("email_skip_confirmed") == "1"
    if not parent_email and not email_skip_confirmed:
        # Render same page with warning modal
        return render_template(
            "enroll.html",
            lang=lang,
            labels=labels,
            schools=SCHOOLS,
            race_options=race_options,
            custody_options=custody_options,
            transport_options=transport_options,
            values=data,
            missing=missing,
            email_warning=True,
        )

    if missing:
        return render_template(
            "enroll.html",
            lang=lang,
            labels=labels,
            schools=SCHOOLS,
            race_options=race_options,
            custody_options=custody_options,
            transport_options=transport_options,
            values=data,
            missing=missing,
            email_warning=False,
        ), 400

    # Create submission
    now = datetime.now()
    year = now.year
    submission_id = next_submission_id(year)

    payload = data.copy()
    payload["race"] = data.get("race", [])
    
    # Filter out any non-serializable values from payload
    for key in list(payload.keys()):
        try:
            json.dumps(payload[key])
        except (TypeError, ValueError):
            # Remove non-serializable values
            del payload[key]

    conn = db()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO submissions(
            submission_id, created_at, lang, school,
            student_first, student_last, dob,
            parent_name, parent_email, parent_phone,
            payload_json
        ) VALUES(?,?,?,?,?,?,?,?,?,?,?)
        """,
        (
            submission_id,
            now.isoformat(timespec="seconds"),
            lang,
            data.get("school"),
            data.get("student_first"),
            data.get("student_last"),
            data.get("dob"),
            data.get("parent_name"),
            parent_email,
            data.get("parent_phone"),
            json.dumps(payload, ensure_ascii=False),
        ),
    )
    conn.commit()
    conn.close()

    # Emails
    # Internal notification (demo = Allen)
    if INTERNAL_NOTIFY_EMAIL:
        subj = f"New Enrollment Submission: {data.get('student_last')}, {data.get('student_first')} ({data.get('school')})"
        body = (
            f"Submission ID: {submission_id}\n"
            f"Language: {lang}\n"
            f"School: {data.get('school')}\n"
            f"Student: {data.get('student_first')} {data.get('student_last')}\n"
            f"DOB: {data.get('dob')}\n"
            f"Parent/Guardian: {data.get('parent_name')}\n"
            f"Parent Phone: {data.get('parent_phone')}\n"
            f"Parent Email: {parent_email or '(not provided)'}\n\n"
            "(Demo mode) Full payload stored locally in the staging DB."
        )
        send_email(INTERNAL_NOTIFY_EMAIL, subj, body)

    # Parent confirmation if email provided
    if parent_email:
        subj = "Murphy ESD Enrollment Submission Received" if lang == "en" else "Murphy ESD - Confirmación de inscripción recibida"
        body = (
            ("We received your enrollment submission.\n\n" if lang == "en" else "Hemos recibido su solicitud de inscripción.\n\n")
            + f"Submission ID: {submission_id}\n"
            + f"Student: {data.get('student_first')} {data.get('student_last')}\n"
            + f"DOB: {data.get('dob')}\n"
            + f"School: {data.get('school')}\n\n"
            + ("Next steps: Please bring required documents to the school front office.\n" if lang == "en" else "Próximos pasos: Por favor traiga los documentos requeridos a la oficina de la escuela.\n")
        )
        send_email(parent_email, subj, body)

    # Success page
    return redirect(url_for("success", submission_id=submission_id, lang=lang))


@app.route("/success/<submission_id>")
def success(submission_id: str):
    lang = request.args.get("lang", "en")
    if lang not in ("en", "es"):
        lang = "en"
    labels = LABELS[lang]

    conn = db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM submissions WHERE submission_id=?", (submission_id,))
    row = cur.fetchone()
    conn.close()
    if not row:
        abort(404)

    safe = {
        "submission_id": row["submission_id"],
        "created_at": row["created_at"],
        "school": row["school"],
        "student_first": row["student_first"],
        "student_last": row["student_last"],
        "dob": row["dob"],
        "parent_name": row["parent_name"],
        "parent_email": row["parent_email"],
    }

    return render_template("success.html", lang=lang, labels=labels, safe=safe)


@app.route("/admin")
def admin():
    require_admin()
    lang = request.args.get("lang", "en")
    conn = db()
    cur = conn.cursor()
    cur.execute("SELECT submission_id, created_at, lang, school, student_last, student_first, dob, parent_name, parent_email, parent_phone FROM submissions ORDER BY id DESC LIMIT 200")
    rows = cur.fetchall()
    conn.close()
    return render_template("admin.html", rows=rows)


@app.route("/admin/export.csv")
def export_csv():
    require_admin()
    import csv
    from io import StringIO

    conn = db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM submissions ORDER BY id DESC")
    rows = cur.fetchall()
    conn.close()

    # Minimal export now; later we map to Synergy import fields.
    out = StringIO()
    writer = csv.writer(out)
    writer.writerow([
        "submission_id",
        "created_at",
        "lang",
        "school",
        "student_first",
        "student_last",
        "dob",
        "parent_name",
        "parent_email",
        "parent_phone",
        "payload_json",
    ])
    for r in rows:
        writer.writerow([
            r["submission_id"], r["created_at"], r["lang"], r["school"],
            r["student_first"], r["student_last"], r["dob"],
            r["parent_name"], r["parent_email"], r["parent_phone"], r["payload_json"],
        ])

    csv_bytes = out.getvalue().encode("utf-8")
    tmp_path = os.path.join(os.path.dirname(__file__), "export.csv")
    with open(tmp_path, "wb") as f:
        f.write(csv_bytes)

    return send_file(tmp_path, mimetype="text/csv", as_attachment=True, download_name="enrollment_export.csv")


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5000")), debug=True)
