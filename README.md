# GitHub Webhook Event Tracker (Flask + MongoDB)

## Requirements
- Python 3.x
- MongoDB (local or hosted)

## Setup

1) Create a virtual environment and install dependencies:

```bash
python -m venv venv
# Windows (PowerShell):
venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

2) Set your MongoDB URI (must include a DB name):

```bash
# Windows (PowerShell)
$env:MONGO_URI="mongodb://localhost:27017/webhook_repo"
```

3) Run the server:

```bash
python app.py
```

Open `http://localhost:5000`.

## GitHub Webhook

In your GitHub repository settings, add a webhook:
- **Payload URL**: `http://<your-host>:5000/webhook`
- **Content type**: `application/json`
- **Events**: push + pull requests (or “send me everything”, the app will ignore unsupported events)

The backend stores only normalized fields (no raw payload dumps) in MongoDB collection `events`.
