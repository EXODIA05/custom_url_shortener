#building url shortener from scartch
from urllib.parse import urlparse
from flask import Flask, request, redirect,render_template
import sqlite3
import requests
import string
import os
from dotenv import load_dotenv

load_dotenv()
safe_browsing_api_key = os.getenv("APIKEY")
safe_browsing_url = f"https://safebrowsing.googleapis.com/v4/threatMatches:find?key={safe_browsing_api_key}"

app = Flask(__name__)

id_offset = 100000 #autoincrement starts here
scope = string.digits+string.ascii_letters

#connection to a database
def get_db_connection():
     conn = sqlite3.connect("urls.db")
     conn.row_factory = sqlite3.Row #allows accessing data by columns 
     return conn

def init_db():
     conn = get_db_connection()
     cursor = conn.cursor() # to execute sql commands
     cursor.execute("""
        CREATE TABLE IF NOT EXISTS urls (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            long_url TEXT NOT NULL UNIQUE,
            custom_alias TEXT UNIQUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
     cursor.execute("SELECT COUNT(*) FROM urls")
     if cursor.fetchone()[0] == 0:
          cursor.execute(
               "INSERT INTO sqlite_sequence(name,seq) VALUES ('urls',?)",
                         (id_offset,)
                         )
     conn.commit()
     conn.close()

def check_url_structure(url):
     try:
          parsed = urlparse(url)
        # Ensure it's web trafficn
          if parsed.scheme not in ('http', 'https'):
               return False
          domain = parsed.netloc
          if not domain:
               return False
            
        # Strip port if present (e.g., localhost:5000 -> localhost)
          if ":" in domain:
               domain = domain.split(":")[0]
            
        # Enforce your custom rules safely on the clean domain component
          special_chars = {"!", "@", "#", "$", "%", "^", "&", "*"}
          if any(char in special_chars for char in domain):
               return False
            
          if '.' not in domain and domain != "localhost":
               return False
            
          return True
     except Exception:
          return False

def is_url_safe(url):
    """
    Checks the URL against Google Safe Browsing API.
    Returns True if safe, False if malicious/dangerous.
    """
    # If you haven't set up the API key yet, temporarily let it pass
    if safe_browsing_api_key == "_GOOGLE_API_KEY_":
        print("Warning: Safe Browsing API key not set. Skipping live threat check.")
        return True

    payload = {
        "client": {
            "clientId": "my-url-shortener",
            "clientVersion": "1.0.0"
        },
        "threatInfo": {
            "threatTypes":      ["MALWARE", "SOCIAL_ENGINEERING", "UNWANTED_SOFTWARE", "POTENTIALLY_HARMFUL_APPLICATION"],
            "platformTypes":    ["ANY_PLATFORM"],
            "threatEntryTypes": ["URL"],
            "threatEntries":    [{"url": url}]
        }
    }
    try:
        response = requests.post(safe_browsing_url, json=payload, timeout=5)
        
        if response.status_code == 200:
            result = response.json()
            if "matches" in result:
                return False
            return True
        print(f"Security API unavailable (Status: {response.status_code}). Blocking request for safety.")
        return False
    except Exception as e:
        print(f"Network error during security check: {e}. Blocking request.")
        return False
     
     

def encode_base62(n):
    encoded =""
    if n==0:
          return scope[0] 
    while n>0:
         n,rem = divmod(n,62)
         encoded =scope[rem] +encoded
    return encoded
char_to_index = {char:idx for idx,char in enumerate(scope)}

def decode(y):
     real = 0
     """for i in range(len(y)):
          for j in range(len(scope)):
               if y[i]==scope[j]:
                    real = (real*62)+j
                    break"""
     for char in y:
          real =(real*62) + char_to_index[char]
     #print(real)
     return real                                                                                         

@app.route("/shorten")

def shorten():

     long_url = request.args.get('url') #to get the url only
     
     if not long_url:
          return render_template("index.html", error="No URL provided"), 400
     
     # Automatically prepend 'http://' if the user forgets it
     if not (long_url.startswith("http://") or long_url.startswith("https://")):
          long_url = "http://" + long_url
     custom_alias = request.args.get('alias')
      #security func:
     if not is_url_safe(long_url):
          return render_template("index.html", error="Security Warning: This URL has been flagged as unsafe!"), 400
     
     conn = get_db_connection()
     cursor = conn.cursor()

     if custom_alias:
               cursor.execute("SELECT 1 FROM urls where custom_alias =?",(custom_alias,))
               if cursor.fetchone():
                    conn.close()
                    return render_template("index.html",error ="alias taken"),400
               cursor.execute("INSERT INTO urls (long_url,custom_alias) VALUES (?,?)",(long_url,custom_alias,))
               conn.commit()
               conn.close()
               full_short_url = f"{request.host_url}{custom_alias}"
               return render_template("index.html", short_url=full_short_url)

     if long_url :
          cursor.execute("SELECT id,custom_alias FROM urls where long_url=?",(long_url,))
          existing = cursor.fetchone()

          if existing :
               conn.close()
               short_code = existing["custom_alias"] if existing["custom_alias"] else encode_base62(existing["id"])
               full_short_url = f"{request.host_url}{short_code}"
               return render_template("index.html",short_url = full_short_url)

          cursor.execute("INSERT INTO url (long_url) into VALUES (?)",(long_url,))
          conn.commit()
          newid = cursor.lastrowid
          short_code = encode_base62(newid)
          conn.close()

          full_short_url = f"{request.host_url}{short_code}"
          return render_template("index.html",short_url = full_short_url)

@app.route("/")

def home():
     return render_template("index.html")

@app.route("/<short_url>")

def redirect_to_long_url(short_url):
     conn = get_db_connection()
     cursor = conn.cursor()

     cursor.execute("SELECT long_url from urls where custom_alias ?",(short_url,))
     row = cursor.fetchone()
     if row :
          conn.close()
          return redirect(row["long_url"])
     try :
          decoded_id = decode(short_url)
          cursor.execute("SELECT long_url from urls where id=?",(decoded_id,))
          row = cursor.fetchone()
          if row :
               conn.close()
               return redirect(row["long_url"])
     except Exception:
          pass
     conn.close()
     return "NOT FOUND",400

if __name__ == "__main__":
    init_db()
    app.run(debug=True)