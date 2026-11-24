# SPECS-MASTER

FastAPI application for browsing and comparing CPU and GPU specifications, with user accounts and an administrator component catalog.

## Run locally

1. Use Python 3.14 and install dependencies with `pip install -r requirements.txt`.
2. Create the MySQL database and import `specs_master_db.sql`, or point the app to an existing compatible database.
3. Configure the environment variables below, then start the app with `uvicorn main:app --reload`.
4. Open `http://127.0.0.1:8000`.

| Variable | Purpose | Default |
| --- | --- | --- |
| `DATABASE_URL` | SQLAlchemy async database URL | `mysql+aiomysql://root@MySQL-8.4:3306/specs_master_db` |
| `SESSION_SECRET` | Secret used to sign login session cookies; configure a persistent random value outside development | Random value generated at process startup |
| `ADMIN_EMAIL` | Email address for the initial administrator account | Empty (no admin account is bootstrapped) |
| `ADMIN_PASSWORD` | Initial administrator password; at least 10 characters and required with `ADMIN_EMAIL` | Empty |
| `ADMIN_NICKNAME` | Nickname for a newly bootstrapped administrator | `Specs Admin` |
| `SESSION_HTTPS_ONLY` | Set to `true` when the app is served over HTTPS | `false` |

The application creates missing tables and adds the `users.role` column to an existing users table on startup. When both admin variables are configured, it creates the initial admin account if needed. If that email already exists, the configured password must match the account's password before it is granted the administrator role. Regular registration cannot grant administrator access. Admins can add CPU/GPU records at `/admin`; signed-in users can manage their account at `/lk`.

Passwords are stored as PBKDF2-SHA256 hashes. Session cookies are HTTP-only and use `SameSite=Lax`; configure `SESSION_SECRET` and enable `SESSION_HTTPS_ONLY` for a deployment behind HTTPS.

## Images

CPU/GPU images can be uploaded from the admin panel; avatars are optional during registration and can also be changed in the profile. Uploads accept valid JPG, PNG, or WebP images up to 2 MiB. Component images are stored under `static/images/site/cpus/` or `static/images/site/gpus/`; avatars are stored under `static/images/users/`. Names are generated from the product name or nickname, transliterated to lowercase ASCII with underscores. A slug already in use is rejected rather than overwriting another image. The UI uses `static/images/site/base_specs_master_img.png` and `static/images/users/base_user_img.png` as fallbacks.
