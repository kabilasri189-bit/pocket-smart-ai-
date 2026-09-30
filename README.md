# PocketSmart AI — Smart Budget & Recommendation Assistant

PocketSmart AI is a professional Flask + HTML/CSS/JavaScript Generative AI project inspired by the supplied project documentation.

## What it does

Three planners are included:

- **Home Interior Planner** — budget allocation for rooms, furniture, lighting and decor.
- **Party Planner** — budget allocation for food, venue, decoration and extras.
- **Jewelry Planner** — occasion/style recommendations with an optional outfit image.

The application uses Gemini when `GEMINI_API_KEY` is configured. If no key is configured, it automatically runs in **Demo Fallback Mode**, so the project still starts and can be demonstrated without an AI account.

There is **no database** and there are **no subfolders**. All project files are in this single folder.

## Project structure

```text
PocketSmart_AI/
├── app.py
├── index.html
├── style.css
├── script.js
├── requirements.txt
├── .env.example
├── .gitignore
├── README.md
└── test_app.py
```

## Requirements

- Python 3.10 or newer
- VS Code
- Internet connection for Gemini API calls
- A Gemini API key for real AI mode

## Run in VS Code

### 1. Open the project

Extract the ZIP and open the `PocketSmart_AI` folder in VS Code.

### 2. Create a virtual environment

Windows PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

Windows CMD:

```cmd
python -m venv .venv
.venv\Scripts\activate
```

macOS/Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Gemini

Copy `.env.example` to `.env`:

```text
GEMINI_API_KEY=your_real_key
GEMINI_MODEL=gemini-2.5-flash
```

If you do not add a key, the app still works using its built-in demo recommendations.

### 5. Start the application

```bash
python app.py
```

Open:

```text
http://127.0.0.1:5000
```

## Test the application

Run:

```bash
python test_app.py
```

The test checks:

- Flask application starts
- Home page loads
- Health API works
- Home planner returns recommendations
- Party planner returns recommendations
- Jewelry planner returns recommendations

## Gemini mode

When the key is configured, the backend sends the planner information to Gemini and requests structured JSON. The frontend then renders the response as recommendation cards.

The app deliberately does **not** claim that prices or inventory are live. Platform buttons open search-oriented links so the user can verify the current product/service details.

## Publish to GitHub

1. Create a new GitHub repository, for example `pocketsmart-ai`.
2. Keep the repository public if your professor needs to open it.
3. Upload/push the complete contents of this folder.
4. Do **not** upload `.env` or your API key.
5. Give your professor the repository URL.

Example:

```bash
git init
git add .
git commit -m "Initial PocketSmart AI project"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/pocketsmart-ai.git
git push -u origin main
```

## Deploying online

For a live demo, use a Python-compatible hosting platform such as Render, Railway, or PythonAnywhere. Configure the `GEMINI_API_KEY` as a secret/environment variable on the host. Never place the real key inside HTML, JavaScript, GitHub, or README files.

The included `gunicorn` dependency allows hosts that use a command such as:

```text
gunicorn app:app
```

## Important academic note

The supplied documentation mentions Gemini 1.5 Flash Pro, FastAPI, authentication, sessions, and third-party product sources. This implementation keeps the requested core concept but simplifies it to Flask, because the current assignment requirements specify Python frontend/backend and no database. Authentication and database persistence are intentionally omitted. Third-party platform links are search links rather than live marketplace APIs, avoiding fabricated live prices.
