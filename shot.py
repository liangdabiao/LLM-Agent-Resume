import json, base64, sys, urllib.request, os

out_path = sys.argv[1]
selector = sys.argv[2] if len(sys.argv) > 2 else None
body = {"action": "screenshot", "args": {"format": "png"}, "session": "resume"}
if selector:
    body["args"]["selector"] = selector
req = urllib.request.Request(
    "http://127.0.0.1:10086/command",
    data=json.dumps(body).encode(),
    headers={"Content-Type": "application/json"},
)
resp = json.loads(urllib.request.urlopen(req, timeout=60).read())
data = resp.get("data", {})
b64 = data.get("data", "")
os.makedirs(os.path.dirname(out_path), exist_ok=True)
with open(out_path, "wb") as f:
    f.write(base64.b64decode(b64))
print(json.dumps({"saved": out_path, "bytes": os.path.getsize(out_path), "format": data.get("format")}))
