import urllib.request

url = 'https://github.com/yukiyanA-Git/login-manager/releases/download/v1.0.1/LoginManager.zip'
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
try:
    res = urllib.request.urlopen(req)
    print("DIRECT_URL:", res.geturl())
except Exception as e:
    print("ERROR:", e)
