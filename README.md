# Northstar Hospital Management System

A professional, full stack hospital administration workspace for receptionists, clinicians, and administrators. The project uses Django REST Framework, PostgreSQL, and React with Vite. It includes persistent patient and clinical records, role based access, search, a dashboard, and a database backed rule based query center.

## ER diagram and database design

The requested file `Hospital Management System.drawio.pdf` was not present in the project workspace when implementation began. The schema therefore preserves the entities and relationship concepts specified in the project brief; review the original diagram and adjust the initial migration if it specifies additional attributes or different cardinalities.

| ER concept | Relational implementation |
|---|---|
| Department | `Department`; unique name, location, description, manager |
| Employee | `Employee`; unique employee ID, department FK (`WORKS FOR`), job title, working hours |
| Patient | `Patient`; unique generated patient ID, DOB, age property, sex, medical history, optional department and assigned doctor |
| Person / Caretaker | `Person` plus `Caretaker` association connecting people to patients with relationship and primary-contact flag (`CARE-TAKERS`) |
| Diagnosis | `Diagnosis`; patient and employee FKs (`DIAGNOSIS`) |
| Tests | `Test`; patient and ordering employee FKs, date and status |
| Surgical Equipment | `SurgicalEquipment`; department FK records acquisition/allocation (`ACQUIRES`) |
| Medical Store / Prescription | `MedicalStore` and `Prescription`; patient, prescribing employee, store, medicine, quantity and status (`PRESCRIBE`) |
| MANAGES | Optional one-to-one manager employee on each department |

Foreign keys preserve related record integrity. Patient, employee, department, equipment, prescription, and caretaker identifiers have uniqueness constraints where appropriate. The patient age is derived from date of birth, avoiding stored age drift. Database timestamps are retained for audit and sorting.

## Features

- Login and roles: Receptionist, Doctor, Admin
- Patient registration with review step, search, edit, delete, details and clinical history
- Employee/doctor directory and department directory
- Diagnosis, test, prescription, surgical equipment, person and caretaker records
- Dashboard counts and charts loaded from the API
- Global search and a rule based query center backed by Django ORM queries
- Shared-database change revisions; open clients poll for updates from other signed-in devices every five seconds
- Server side search, filtering, ordering and pagination for patient records
- Responsive layout, loading/empty/error states, validation and confirmation prompts
- Fictional relational demo records and local demo accounts

## Stack and folders

- Backend: Python, Django, Django REST Framework, PostgreSQL (`psycopg`), `django-cors-headers`, `python-dotenv`, DRF token authentication
- Frontend: React, Vite, React Router, Tailwind CSS, Axios, Lucide React, Recharts

```text
backend/  Django project, hospital models, API, query service, seed command
frontend/ React app, reusable components, pages, API service layer
```

## Setup

### PostgreSQL and backend

Create a PostgreSQL database and a database user with permission to create tables. Copy `backend/.env.example` to `backend/.env` and set the database connection and a private `SECRET_KEY`.

For example, from a PostgreSQL prompt as a database administrator:

```sql
CREATE USER hospital_user WITH PASSWORD 'choose-a-private-password';
CREATE DATABASE hospital_db OWNER hospital_user;
```

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py seed_data
python manage.py runserver
```

The API is available at `http://localhost:8000/api/`. Local development falls back to SQLite unless `DATABASE_URL` or the `DB_NAME` PostgreSQL settings are configured. Never use the development fallback or demo credentials for a production deployment.

### Frontend

```powershell
cd frontend
npm install
npm run dev
```

Copy `frontend/.env.example` to `frontend/.env` to change `VITE_API_URL`. Vite serves the app at `http://localhost:5173` by default.

## Deploy the combined app to Vercel

The repository root `vercel.json` configures one Vercel project with two services: Vite serves the frontend, and Django serves `/api/` and `/admin/`. The backend uses `config.wsgi:application` as its Python entrypoint. Import the repository once, set the Framework Preset to **Services**, and keep Root Directory at the repository root (`./`). Do not choose `frontend/` as the project root or import the frontend as a separate project. Vercel Services may need to be enabled for the account/project.

Vercel requires a **shared PostgreSQL database** for records to remain visible across requests, devices, and function instances. Add a PostgreSQL provider through Vercel Marketplace (for example, Neon or Supabase) and make sure its `DATABASE_URL` environment variable is enabled for Production, Preview, and Development. The backend build runs migrations and seeds fictional demo data. The build generates a deployment-specific Django signing key when `SECRET_KEY` is not configured; you can set a private `SECRET_KEY` in Vercel to keep signed login tokens valid across deployments.

Do not use SQLite on Vercel: function filesystems are temporary and isolated, so writes can disappear or be invisible to another request. This app will now fail with a clear database configuration message if Vercel has no PostgreSQL `DATABASE_URL`, instead of silently creating an isolated database.

1. Create one Vercel project from this GitHub repository, with Framework Preset **Services** and Root Directory `./`.
2. From the Vercel project, add a PostgreSQL provider under **Storage** and connect it to the project. Confirm `DATABASE_URL` is available to the Production deployment and redeploy. The build applies migrations and inserts fictional seed/demo data.
3. Optionally set a private `SECRET_KEY` in **Settings → Environment Variables** to keep login tokens valid across deployments; otherwise the build generates one for each deployment.
4. If using a custom domain, set `ALLOWED_HOSTS` to include that hostname and `CSRF_TRUSTED_ORIGINS` to include its `https://` origin. Vercel deployment hostnames are allowed automatically.

The frontend uses same-domain relative `/api` requests, so no production API URL or cross-origin setup is needed. See [Vercel Services](https://vercel.com/docs/services), [Vercel's SQLite guidance](https://vercel.com/kb/guide/is-sqlite-supported-in-vercel), and [Vercel Python deployment](https://vercel.com/docs/functions/runtimes/python).
## Demo logins

`seed_data` creates fictional accounts (change these passwords before exposing the app beyond local development):

| Role | Username | Password |
|---|---|---|
| Receptionist | `receptionist` | `Reception123!` |
| Doctor | `doctor` | `Doctor123!` |
| Admin | `admin` | `Admin123!` |

The backend returns DRF opaque auth tokens from `POST /api/auth/token/`; send them as `Authorization: Token <token>`. Roles are resolved from the `UserProfile` model; superusers always have Admin access.

## API endpoints

- `POST /api/auth/token/`, `GET /api/auth/me/`
- Patients CRUD: `/api/patients/`; patient detail includes `/api/patients/{id}/history/`
- Employees CRUD (role limited): `/api/employees/`
- Departments CRUD (role limited): `/api/departments/`; department staffing/equipment at `/api/departments/{id}/detail_data/`
- Diagnoses CRUD: `/api/diagnoses/`
- Tests CRUD: `/api/tests/`
- Prescriptions CRUD: `/api/prescriptions/`
- Medical store CRUD: `/api/medical-stores/`
- Surgical equipment CRUD: `/api/equipment/`
- People and caretaker links: `/api/people/`, `/api/caretakers/`
- Dashboard: `GET /api/dashboard/`
- Shared data revision (for cross-device refresh): `GET /api/changes/`
- Global search: `GET /api/search/?q=Ananya`
- Query engine: `POST /api/query/` with `{"query":"Which doctors work in Cardiology?"}`

Run the backend checks with `python manage.py check`, `python manage.py makemigrations --check --dry-run`, and `python manage.py test hospital`.

List APIs use DRF pagination (`count`, `next`, `previous`, `results`), `?search=` and ordering where configured. Filters include department, status, and related records as supported by each viewset.

## Query center examples

- `Which doctors work in Cardiology?`
- `Find patient Aarav Sharma`
- `Show tests for Aarav Sharma`
- `Who manages Neurology?`
- `Show equipment in Cardiology`
- `What are Dr. Ananya Mehta's working hours?`
- `How many patients are registered?`
- `Show patients diagnosed with hypertension.`

## Receptionist workflow

Sign in as `receptionist`, review the live dashboard, register a patient, then search or open the patient record. Add tests from the Tests module, connect a caretaker, and use Query Center to find relevant doctors, records, and equipment. Each successful change is persisted through the REST API and appears in subsequent API reads.

## Role access

- Receptionists can manage patient registration and records, add diagnoses, create tests and caretaker links, and read other hospital directories and clinical modules.
- Doctors can read assigned patient records and create/update their diagnoses and tests.
- Admins can manage all hospital records and user-facing modules. Create staff accounts through Django admin; set each account's role in `UserProfile`.

## Security and production notes

Set `DEBUG=False`, a strong secret, explicit `ALLOWED_HOSTS`, HTTPS, secure token storage, database backups, and production-grade logging before deployment. The demo uses DRF token authentication for a simple local setup; token expiration/rotation and audit-event retention are not configured.
