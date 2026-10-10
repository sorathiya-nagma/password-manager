# SecureVault Password Manager

SecureVault is a Django password manager with authentication, Fernet encryption, search/filtering, dashboard metrics, optional TOTP 2FA, password generation, audit logging, import/export, and a responsive Bootstrap UI.

## Features

- User registration with unique email validation.
- Secure login with remember-me, rate limiting, failed-login lockout, logout, and password reset.
- Dashboard with total passwords, recent entries, categories, favorites, health score, weak alerts, reuse detection, login history, and audit history.
- Password vault with website name, URL, username, email, password, notes, category, tags, favorite, created/updated dates, expiration date, reveal, copy, edit, and delete.
- Fernet encryption for stored username, email, password, and notes.
- Search by website/category/tag and filters for favorites, recently added, category, A-Z, newest, and oldest.
- Password generator with length, uppercase, lowercase, numbers, symbols, and exclude-similar options.
- Password health checker with suggestions.
- Optional TOTP 2FA from the Settings page.
- CSV export/import and encrypted JSON backup/restore.
- Dark mode preference.
- Admin panel for users, vault records, login attempts, audit logs, and security profiles.
- SQLite by default, with environment-based PostgreSQL configuration.

## Setup

```powershell
py -m pip install -r requirements.txt
Copy-Item .env.example .env
py -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Put the generated Fernet key into `VAULT_FERNET_KEY` in `.env`.

```powershell
py manage.py migrate
py manage.py createsuperuser
py manage.py create_sample_data
py manage.py runserver
```

Open `http://127.0.0.1:8000/`.

Sample user:

```text
username: demo
password: DemoPass123!
```

## Production Notes

- Set `DJANGO_DEBUG=False`.
- Use a strong `DJANGO_SECRET_KEY`.
- Keep `VAULT_FERNET_KEY` secret and backed up. Losing it means encrypted vault data cannot be decrypted.
- Set `DJANGO_SECURE_SSL_REDIRECT=True` and `DJANGO_SECURE_COOKIES=True` behind HTTPS.
- Use PostgreSQL by setting `DATABASE_ENGINE=postgres` and the `POSTGRES_*` variables.
- Configure a real email backend for password reset emails.

## Future Breach Check

The project is structured so a Have I Been Pwned integration can be added as a service without changing vault views. Add a service that hashes candidate passwords with SHA-1 k-anonymity and returns breach counts to the health checker.
