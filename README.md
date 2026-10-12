# CV Parser & Skill Scorer

Parse CV PDFs, extract skills with OpenAI, and review results through a FastAPI API and React dashboard. The command-line pipeline can read a local CSV or a Google Sheet, then write a skill matrix to CSV or Google Sheets.

## Quick start: local pipeline

Requires Python 3.11+ and an OpenAI API key.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Set OPENAI_API_KEY in .env
python main.py --local --dry-run
```

The included `sample/example-workers.csv` contains fictional data only. Put CV PDFs in `cvs/`, named after the candidate's email address or name, then run `python main.py --local`. Results go to `output/results.csv`. Real CVs, outputs, credentials, and local environment files are ignored by Git.

## Web app

The web app uses PostgreSQL and Google sign-in. Set `GOOGLE_CLIENT_ID`, `VITE_GOOGLE_CLIENT_ID`, and a random `JWT_SECRET` of at least 32 characters in `.env`. Set `ALLOWED_EMAIL_DOMAIN` to restrict sign-in to one Google Workspace domain; leave it empty to allow any verified Google account. Set the matching `VITE_ALLOWED_EMAIL_DOMAIN` to show the restriction on the login page.

For local development, start PostgreSQL with `docker compose up -d db`, set `DATABASE_URL=postgresql://cvparser:cvparser@localhost:5433/cvparser`, and run:

```bash
uvicorn backend.app:app --reload
cd frontend
npm ci
npm run dev
```

Create `frontend/.env` with the `VITE_GOOGLE_CLIENT_ID` and optional `VITE_ALLOWED_EMAIL_DOMAIN` values used by the Vite development server. The example database password in Compose is for local development only.

## Google Sheets and Drive

Set `INPUT_SHEET_ID` and optionally `INPUT_SHEET_GID` in `.env`. For a service account, set `GOOGLE_SERVICE_ACCOUNT_FILE` to a local JSON key path and share the sheet with that account. For user OAuth, place your client configuration at `GOOGLE_OAUTH_CREDS_FILE` and run `python google_auth.py` once. Set `OUTPUT_SHEET_ID` to write results to Sheets. Keep all credentials outside Git.

## Deployment

`docker-compose.prod.yml` and `terraform/` are generic examples. Supply your own AWS account, Google OAuth client, credentials, domain policy, and secrets. Never commit `.env`, Terraform state, actual candidate data, or private keys. Review the infrastructure and cost before applying it.

## Privacy and contributions

Candidate CVs and extracted profiles contain personal information. Obtain appropriate permission before processing them, and do not open a public issue or pull request containing real applicant data. Contributions are welcome through issues and pull requests.
