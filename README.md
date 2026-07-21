# Custom URL Shortener

A simple URL shortener built from scratch with Flask. It converts long URLs into short, shareable links using base62 encoding, supports custom aliases, and checks submitted URLs against the Google Safe Browsing API before shortening them.

## Features

- **Shorten any URL** — generates a compact base62-encoded short link for any valid URL.
- **Custom aliases** — optionally choose your own short link instead of an auto-generated one.
- **Duplicate detection** — shortening the same long URL twice returns the existing short link instead of creating a new one.
- **URL validation** — checks scheme, domain, and disallowed characters before accepting a URL.
- **Auto-prepends scheme** — automatically adds `http://` if the submitted URL is missing one.
- **Safe Browsing integration** — flags and blocks URLs identified as malware, phishing, unwanted software, or otherwise harmful via the Google Safe Browsing API.
- **Redirect endpoint** — visiting a short link redirects to the original long URL.

## Tech Stack

- Python 3
- Flask
- HTML / CSS / JavaScript (templates and static assets)
- [Google Safe Browsing API](https://developers.google.com/safe-browsing) for link safety checks

## Getting Started

### Prerequisites

- Python 3.8+
- pip

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/EXODIA05/custom_url_shortener.git
   cd custom_url_shortener
   ```

2. Install dependencies:
   ```bash
   pip install flask requests
   ```

3. Set up your Google Safe Browsing API key.

   The app expects a Safe Browsing API key to validate URLs. **Do not commit real API keys to source control.** Instead, set it as an environment variable and read it in `urs.py`, for example:

   ```python
   import os
   safe_browsing_api_key = os.environ.get("SAFE_BROWSING_API_KEY", "_GOOGLE_API_KEY_")
   ```

   Then run:
   ```bash
   export SAFE_BROWSING_API_KEY="your-api-key-here"   # on Windows: set SAFE_BROWSING_API_KEY=your-api-key-here
   ```

   If no key is configured, the app will print a warning and skip the live safety check.

4. Run the app:
   ```bash
   python urs.py
   ```

   By default, Flask runs in debug mode on `http://127.0.0.1:5000`.

## Usage

### Shorten a URL

Send a GET request to `/shorten` with a `url` parameter (and an optional `alias`):

```
http://127.0.0.1:5000/shorten?url=https://example.com/some/very/long/path
```

With a custom alias:

```
http://127.0.0.1:5000/shorten?url=https://example.com/some/very/long/path&alias=mylink
```

The response renders the generated short URL (e.g. `http://127.0.0.1:5000/aZ3f9`), or an error message if the URL is invalid, unsafe, or the alias is already taken.

### Visit a short URL

Navigate to the generated short link, and you'll be redirected to the original long URL:

```
http://127.0.0.1:5000/aZ3f9
```

## Project Structure

```
custom_url_shortener/
├── urs.py           # Main Flask application (routing, encoding, safety checks)
├── templates/        # HTML templates (e.g. index.html)
├── static/           # CSS/JS assets
└── .gitignore
```

## How It Works

1. A submitted long URL is validated for structure (valid scheme, non-empty domain, no disallowed characters) and checked against the Google Safe Browsing API.
2. If valid and safe, the URL is assigned a numeric ID from an incrementing counter, which is then base62-encoded (using digits + upper/lowercase letters) to produce a short code.
3. Visiting `/<short_code>` decodes the code back into its numeric ID (or looks it up as a custom alias) and redirects to the stored long URL.

> **Note:** This project currently stores URL mappings in memory (Python dictionaries), so all shortened links are lost when the server restarts. For persistent storage, consider adding a database (e.g. SQLite, PostgreSQL, or Redis).

## Limitations & Ideas for Improvement

- Add persistent storage instead of in-memory dictionaries.
- Add link expiration and click analytics.
- Add rate limiting to prevent abuse.
- Move the Safe Browsing API key out of source code and into environment variables/secrets management.
- Add unit tests for URL validation and encoding/decoding logic.

## License

No license has been specified for this project. Consider adding one (e.g. MIT) if you plan to share or accept contributions.
