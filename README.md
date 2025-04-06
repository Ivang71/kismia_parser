# Kismia Parser

A tool for fetching and analyzing user profiles from Kismia.

## Setup

1. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

2. Prepare authentication:
   Create an `auth_token.json` file with your Kismia access credentials.

## Usage

Run the main script to start fetching users:
```
python main.py
```

The script will:
- Fetch user profiles from Kismia
- Store data in a local SQLite database
- Track liked and passed users 