# Security Policy

## Supported

- Latest `main` branch (functional prototype).

## Reporting a vulnerability

Do **not** open a public issue. Instead open a **private** GitHub Security Advisory
(Repository → Security → Report a vulnerability) describing:

- affected endpoint / file
- minimal reproduction steps
- impact

## Security baseline (shipped in this code)

- PBKDF2 password hashing (Werkzeug default)
- Role-based access control on admin-only routes
- CSRF protection via Flask-WTF
- Jinja2 autoescaping against XSS
- SQLAlchemy ORM (no raw SQL concatenation)
- `next=` redirect parameter validated to relative paths only (open-redirect fix)
- Debug mode gated behind `FLASK_DEBUG=1`
- `SECRET_KEY` required outside development environments

## Responsible disclosure

We'll acknowledge within a few days and fix within a reasonable window depending on severity.
Prototype code — no security guarantees, but findings are taken seriously.