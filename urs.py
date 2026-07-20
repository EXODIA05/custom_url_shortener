#building url shortener from scartch
from urllib.parse import urlparse
from flask import Flask, request, redirect,render_template
import random  
import requests
import string
import os
from dotenv import load_dotenv

load_dotenv()
safe_browsing_api_key = os.getenv("APIKEY")
safe_browsing_url = f"https://safebrowsing.googleapis.com/v4/threatMatches:find?key={safe_browsing_api_key}"

app = Flask(__name__)

global_counter = random.randint(1000000,99999999)
scope=string.digits+string.ascii_letters

url_to_id ={}
id_to_url = {}
alias_to_url = {}
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

     global global_counter
     long_url = request.args.get('url') #to get the url only
     custom_alias = request.args.get('alias')
     #security func:
     if not is_url_safe(long_url):
          return render_template("index.html", error="Security Warning: This URL has been flagged as unsafe!"), 400

     if not long_url:
          return render_template("index.html", error="No URL provided"), 400
     
     # Automatically prepend 'http://' if the user forgets it
     if not (long_url.startswith("http://") or long_url.startswith("https://")):
          long_url = "http://" + long_url

     if custom_alias:
          if custom_alias in alias_to_url:
               return render_template("index.html",error ="alias taken"),400
               
          alias_to_url[custom_alias]=long_url
          full_short_url = f"{request.host_url}{custom_alias}"
          return render_template("index.html",short_url= full_short_url)
     
     if long_url in url_to_id:
          existing_id = url_to_id[long_url]
          short_url = encode_base62(existing_id)
          full_short_url = f"{request.host_url}{short_url}"
          return render_template("index.html", short_url=full_short_url)

     if check_url_structure(long_url): 
          short_url = encode_base62(global_counter)
          id_to_url[global_counter] = long_url
          url_to_id[long_url] = global_counter
          global_counter += 1
          full_short_url = f"{request.host_url}{short_url}"
          return render_template("index.html", short_url=full_short_url)
          
     return render_template("index.html", error="Invalid URL structure"), 400

@app.route("/")
def home():
     return render_template("index.html")

@app.route("/<short_url>")
def redirect_to_longurl(short_url):
     if short_url in alias_to_url:
          return redirect(alias_to_url[short_url])
     try:
          decoded = decode(short_url)
          longurl = id_to_url.get(decoded)
          if longurl :
               return redirect(longurl)
     except Exception:
          pass

     return "Not found",404

if __name__ == "__main__":
     app.run(debug=True)