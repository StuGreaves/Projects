# 3CX ↔ Cliniko Integration – Setup Guide

Displays Cliniko patient details automatically when an incoming call arrives in 3CX.

---

## How It Works

```
Incoming call → 3CX detects caller ID → Opens popup URL on staff PC
                                           ↓
                              Node.js middleware receives number
                                           ↓
                              Queries Cliniko REST API
                                           ↓
                              Returns patient name, DOB, appointments
```

---

## 1. Prerequisites

- Node.js 18 or later  
- A server or PC that is always on and reachable by 3CX (can be a local machine on the same network)
- Cliniko API key (Settings → Integrations → API Keys)
- 3CX admin access

---

## 2. Install & Configure the Middleware

```bash
# Clone / copy the project folder, then:
cd 3cx-cliniko
npm install

# Copy the env template and fill in your values
cp .env.example .env
nano .env          # add CLINIKO_API_KEY and CLINIKO_SHARD
```

### Find your Cliniko shard

Look at your Cliniko URL in a browser:
- `app.au1.cliniko.com` → set `CLINIKO_SHARD=au1`
- `app.uk1.cliniko.com` → set `CLINIKO_SHARD=uk1`
- etc.

```bash
# Start the server
npm start
# Server will listen on http://localhost:3000
```

**Test the lookup:**
```
http://localhost:3000/lookup?number=+441234567890
```
You should get a JSON response with patient data.

---

## 3. Configure 3CX – Popup on Incoming Call

3CX can open a web page (popup) whenever a call comes in. You configure this per-extension or globally.

### 3CX v20 (Web Client / Desktop App)

1. Log in to the **3CX Management Console**
2. Go to **Settings → CRM Integration** (or **Advanced → CRM**)
3. Choose **"Generic"** or **"Custom"** integration
4. Set the **Contact Lookup URL** to:
   ```
   http://YOUR_SERVER_IP:3000/lookup?number=[Number]
   ```
   3CX will replace `[Number]` with the real caller ID automatically.

### For a visual browser popup (recommended)

1. In 3CX Management Console → **Settings → Advanced → Calls**
2. Under **"Open URL on incoming call"**, enter:
   ```
   http://YOUR_SERVER_IP:3000/popup?number=[Number]
   ```
3. Set **"Open in"** → Browser / New Tab

> Replace `YOUR_SERVER_IP` with the actual IP or hostname of the machine  
> running the Node.js server. If 3CX and the server are on the same machine,  
> use `localhost` or `127.0.0.1`.

---

## 4. Per-Extension Configuration (optional)

To enable the popup for specific extensions only:

1. Go to **Extensions** in the 3CX admin panel
2. Open the extension → **Forwarding Rules** or **Settings**
3. Add the popup URL under **"Open URL on answered / ringing"**

---

## 5. Running as a Service (Production)

Use PM2 to keep the server running:

```bash
npm install -g pm2
pm2 start server.js --name cliniko-integration
pm2 save
pm2 startup   # follow the printed command to auto-start on boot
```

---

## 6. Expose Over HTTPS (if 3CX is cloud-hosted)

If your 3CX instance is in the cloud and can't reach a local server, use a reverse proxy:

**Option A – nginx on a VPS:**
```nginx
server {
    listen 443 ssl;
    server_name your-domain.com;
    location / {
        proxy_pass http://localhost:3000;
    }
}
```

**Option B – Cloudflare Tunnel (free, no open ports):**
```bash
cloudflared tunnel --url http://localhost:3000
```
This gives you a public HTTPS URL instantly.

---

## 7. What the Popup Shows

| Field | Source |
|-------|--------|
| Patient full name | Cliniko patient record |
| Age & date of birth | Cliniko patient record |
| Email address | Cliniko patient record |
| Last 3 appointments | Cliniko appointment history |
| Appointment status | Booked / DNA / Cancelled |
| Practitioner name | Cliniko appointment record |
| "Open in Cliniko" button | Direct link to patient profile |

---

## 8. Troubleshooting

| Symptom | Fix |
|---------|-----|
| "No patient found" for a known patient | Check the phone number format in Cliniko – the search strips non-digits and tries the last 9/10 digits |
| 401 error in server logs | Invalid or missing `CLINIKO_API_KEY` in `.env` |
| Popup doesn't open in 3CX | Confirm the URL in 3CX settings uses the correct IP/port; check firewall allows port 3000 |
| Works locally but not from 3CX cloud | Use HTTPS reverse proxy (see section 6) |

---

## API Endpoints

| Endpoint | Purpose |
|----------|---------|
| `GET /lookup?number=XXX` | Returns JSON patient data |
| `GET /popup?number=XXX` | HTML popup page for 3CX to open |
| `GET /health` | Health check |
