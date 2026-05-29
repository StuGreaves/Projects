const express = require('express');
const axios = require('axios');
const path = require('path');
require('dotenv').config();

const app = express();
app.use(express.json());
app.use(express.static(path.join(__dirname, 'public')));

// ─── Config ────────────────────────────────────────────────────────────────
const CLINIKO_API_KEY = process.env.CLINIKO_API_KEY || '';
const CLINIKO_SHARD   = process.env.CLINIKO_SHARD   || 'au1'; // au1, au2, uk1, ca1, sg1
const PORT            = process.env.PORT            || 3000;

const clinikoBase = `https://api.${CLINIKO_SHARD}.cliniko.com/v1`;
const clinikoAuth = Buffer.from(`${CLINIKO_API_KEY}:`).toString('base64');

const clinikoHeaders = {
  Authorization: `Basic ${clinikoAuth}`,
  Accept: 'application/json',
  'User-Agent': '3CX-Cliniko-Integration/1.0',
};

// ─── Startup Validation ─────────────────────────────────────────────────────

const BOLD  = '\x1b[1m';
const RED   = '\x1b[31m';
const GREEN = '\x1b[32m';
const AMBER = '\x1b[33m';
const RESET = '\x1b[0m';

async function validateConfig() {
  const errors = [];

  // 1. Check .env was loaded
  if (!CLINIKO_API_KEY) {
    errors.push(`${RED}✖ CLINIKO_API_KEY is not set.${RESET}\n  Copy .env.example to .env and add your key.`);
  }

  const validShards = ['au1', 'au2', 'uk1', 'ca1', 'sg1'];
  if (!validShards.includes(CLINIKO_SHARD)) {
    errors.push(`${AMBER}⚠ CLINIKO_SHARD "${CLINIKO_SHARD}" is not a recognised shard.${RESET}\n  Expected one of: ${validShards.join(', ')}`);
  }

  if (errors.length) {
    console.error(`\n${BOLD}Configuration errors:${RESET}`);
    errors.forEach(e => console.error('  ' + e));
    console.error('');
    process.exit(1);
  }

  // 2. Verify the API key actually works against Cliniko
  console.log(`\n${BOLD}Validating Cliniko API key…${RESET}`);
  try {
    const res = await axios.get(`${clinikoBase}/practitioners`, {
      headers: clinikoHeaders,
      params: { per_page: 1 },
      timeout: 8000,
    });
    const count = res.data?.practitioners?.length ?? 0;
    console.log(`${GREEN}✔ Cliniko API key is valid.${RESET} (shard: ${CLINIKO_SHARD}, practitioners found: ${count})`);
  } catch (err) {
    const status = err.response?.status;
    if (status === 401) {
      console.error(`${RED}✖ Cliniko API key is invalid or expired (401 Unauthorised).${RESET}`);
      console.error('  Go to Cliniko → Settings → Integrations → API Keys and regenerate the key.');
    } else if (status === 403) {
      console.error(`${RED}✖ Cliniko API key lacks permission (403 Forbidden).${RESET}`);
      console.error('  Ensure the key was created by an admin account.');
    } else if (err.code === 'ENOTFOUND') {
      console.error(`${RED}✖ Cannot reach Cliniko (DNS failure).${RESET}`);
      console.error(`  Check CLINIKO_SHARD is correct ("${CLINIKO_SHARD}") and you have internet access.`);
    } else {
      console.error(`${RED}✖ Cliniko API check failed: ${err.message}${RESET}`);
    }
    process.exit(1);
  }
}

// ─── Helpers ───────────────────────────────────────────────────────────────

/**
 * Normalise a phone number for comparison.
 * Strips all non-digits, then tries both local and +country variants.
 */
function normaliseNumber(raw) {
  const digits = raw.replace(/\D/g, '');
  // Build search variants: last 9 digits (works for AU/UK local matches)
  const variants = new Set([digits]);
  if (digits.length >= 9) variants.add(digits.slice(-9));
  if (digits.length >= 10) variants.add(digits.slice(-10));
  return [...variants];
}

/**
 * Search Cliniko for patients by phone number fragments.
 */
async function searchPatients(number) {
  const variants = normaliseNumber(number);
  const results = [];

  for (const variant of variants) {
    try {
      // Cliniko supports RANSACK-style query params
      const res = await axios.get(`${clinikoBase}/patients`, {
        headers: clinikoHeaders,
        params: {
          'q[phone_numbers_number_cont]': variant,
          per_page: 5,
        },
      });

      const patients = res.data?.patients || [];
      for (const p of patients) {
        if (!results.find(r => r.id === p.id)) results.push(p);
      }
    } catch (err) {
      console.error('Cliniko search error:', err.response?.data || err.message);
    }
  }

  return results;
}

/**
 * Fetch upcoming / recent appointments for a patient.
 */
async function getPatientAppointments(patientId) {
  try {
    const res = await axios.get(`${clinikoBase}/patients/${patientId}/appointments`, {
      headers: clinikoHeaders,
      params: { per_page: 3, sort: 'starts_at', order: 'desc' },
    });
    return res.data?.appointments || [];
  } catch {
    return [];
  }
}

// ─── SSE Client Registry ────────────────────────────────────────────────────
// Keeps track of all open wallboard browser tabs so we can push events to them
const sseClients = new Map(); // id → res
let sseIdCounter = 0;

function broadcastToWallboards(event, data) {
  const payload = `event: ${event}\ndata: ${JSON.stringify(data)}\n\n`;
  for (const [id, res] of sseClients) {
    try {
      res.write(payload);
    } catch {
      sseClients.delete(id);
    }
  }
  console.log(`[SSE] Broadcast "${event}" to ${sseClients.size} wallboard(s)`);
}

// ─── Routes ────────────────────────────────────────────────────────────────

/**
 * GET /events
 * Wallboard page subscribes here via Server-Sent Events.
 * The connection stays open and receives push events when calls arrive.
 */
app.get('/events', (req, res) => {
  res.setHeader('Content-Type',  'text/event-stream');
  res.setHeader('Cache-Control', 'no-cache');
  res.setHeader('Connection',    'keep-alive');
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.flushHeaders();

  const id = ++sseIdCounter;
  sseClients.set(id, res);
  console.log(`[SSE] Wallboard connected (id=${id}, total=${sseClients.size})`);

  // Keep-alive ping every 20s
  const ping = setInterval(() => {
    try { res.write(': ping\n\n'); } catch { clearInterval(ping); }
  }, 20000);

  req.on('close', () => {
    clearInterval(ping);
    sseClients.delete(id);
    console.log(`[SSE] Wallboard disconnected (id=${id}, remaining=${sseClients.size})`);
  });
});

/**
 * GET /crm-lookup?CallerNumber=+441234567890&CallType=Inbound&...
 * Called by 3CX CRM Template when a call arrives (works for ANY phone type).
 * Returns 3CX-compatible JSON and simultaneously pushes patient data to wallboards.
 */
app.get('/crm-lookup', async (req, res) => {
  // 3CX sends CallerNumber for inbound, DialledNumber for outbound
  const number = req.query.CallerNumber || req.query.DialledNumber || '';
  console.log(`[crm-lookup] 3CX call event — number: "${number}"`);

  if (!number || number === 'Anonymous') {
    broadcastToWallboards('call', { found: false, number: 'Unknown / Anonymous' });
    // Return empty 3CX CRM response
    return res.json({ contacts: [] });
  }

  const patients = await searchPatients(number);

  if (!patients.length) {
    broadcastToWallboards('call', { found: false, number });
    return res.json({ contacts: [] });
  }

  const patient   = patients[0];
  const appointments = await getPatientAppointments(patient.id);

  const callData = {
    found: true,
    number,
    patient: {
      id:        patient.id,
      firstName: patient.first_name,
      lastName:  patient.last_name,
      fullName:  `${patient.first_name} ${patient.last_name}`,
      dob:       patient.date_of_birth,
      email:     patient.email,
      phones:    patient.phone_numbers || [],
      gender:    patient.gender,
      profileUrl:`https://app.cliniko.com/patients/${patient.id}`,
    },
    appointments: appointments.map(a => ({
      id:           a.id,
      startsAt:     a.starts_at,
      endsAt:       a.ends_at,
      type:         a.appointment_type?.name,
      practitioner: a.practitioner
        ? `${a.practitioner.first_name} ${a.practitioner.last_name}`
        : null,
      status: a.did_not_arrive ? 'DNA'
            : a.cancelled_at   ? 'Cancelled'
            : a.invoice_status || 'Booked',
    })),
    allMatches: patients.length,
  };

  // Push to all open wallboard tabs instantly
  broadcastToWallboards('call', callData);

  // Return 3CX CRM JSON format (so 3CX also stores the contact name)
  return res.json({
    contacts: [{
      id:         String(patient.id),
      firstName:  patient.first_name,
      lastName:   patient.last_name,
      phoneNumbers: (patient.phone_numbers || []).map(p => p.number),
      // ContactUrl is opened in 3CX web client if staff happen to have it open
      contactUrl: `http://localhost:${PORT}/popup?number=${encodeURIComponent(number)}`,
    }],
  });
});

/**
 * GET /lookup?number=+441234567890
 * Called by 3CX (or the popup page) with the raw caller ID.
 * Returns JSON with patient details.
 */
app.get('/lookup', async (req, res) => {
  const { number } = req.query;
  if (!number) return res.status(400).json({ error: 'number param required' });

  console.log(`[lookup] Incoming number: ${number}`);

  const patients = await searchPatients(number);

  if (!patients.length) {
    return res.json({ found: false, number });
  }

  // Enrich first match with appointments
  const patient = patients[0];
  const appointments = await getPatientAppointments(patient.id);

  const payload = {
    found: true,
    number,
    patient: {
      id:          patient.id,
      firstName:   patient.first_name,
      lastName:    patient.last_name,
      fullName:    `${patient.first_name} ${patient.last_name}`,
      dob:         patient.date_of_birth,
      email:       patient.email,
      phones:      patient.phone_numbers || [],
      gender:      patient.gender,
      notes:       patient.notes,
      profileUrl:  `https://app.cliniko.com/patients/${patient.id}`,
    },
    appointments: appointments.map(a => ({
      id:           a.id,
      startsAt:     a.starts_at,
      endsAt:       a.ends_at,
      type:         a.appointment_type?.name,
      practitioner: a.practitioner
        ? `${a.practitioner.first_name} ${a.practitioner.last_name}`
        : null,
      status:       a.did_not_arrive ? 'DNA'
                  : a.cancelled_at   ? 'Cancelled'
                  : a.invoice_status || 'Booked',
    })),
    allMatches: patients.length,
  };

  res.json(payload);
});

/**
 * GET /popup?number=+441234567890
 * Returns an HTML page that auto-loads patient data (manual lookup).
 */
app.get('/popup', (req, res) => {
  res.sendFile(path.join(__dirname, 'public', 'popup.html'));
});

/**
 * GET /wallboard
 * The always-open reception PC tab. Listens for SSE and shows patient cards
 * automatically whenever a call comes in — works with physical IP phones.
 */
app.get('/wallboard', (req, res) => {
  res.sendFile(path.join(__dirname, 'public', 'wallboard.html'));
});

/**
 * GET /health  – simple health check
 */
app.get('/health', (_req, res) => res.json({ ok: true, ts: new Date() }));

// ─── Start ──────────────────────────────────────────────────────────────────
async function start() {
  await validateConfig();

  app.listen(PORT, () => {
    console.log(`\n${GREEN}${BOLD}✔ 3CX-Cliniko integration is running${RESET}`);
    console.log(`  Wallboard (open this on reception PC): http://YOUR_SERVER:${PORT}/wallboard`);
    console.log(`  3CX CRM Lookup URL:                    http://YOUR_SERVER:${PORT}/crm-lookup?CallerNumber=[CallerNumber]`);
    console.log(`  Manual lookup JSON:                    http://YOUR_SERVER:${PORT}/lookup?number=[Number]`);
    console.log(`  Health check:                          http://YOUR_SERVER:${PORT}/health\n`);
  });
}

start();
