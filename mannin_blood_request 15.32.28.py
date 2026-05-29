#!/usr/bin/env python3
"""
Mannin Doctors Ltd — Nationwide Pathology Blood Request Tool
Run: python3 mannin_blood_request.py
Opens automatically in your browser. Press Ctrl+C to stop.
"""

import http.server
import json
import urllib.request
import urllib.parse
import urllib.error
import base64
import threading
import webbrowser
import socket
import ssl
import xml.etree.ElementTree as ET

PORT = 8765
API_BASE = "https://api.uk1.cliniko.com/v1"

HTML = """<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>Mannin Blood Request</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: #f5f5f5; color: #1a1a1a; font-size: 14px; }
  .topbar { background: white; border-bottom: 1px solid #e0e0e0; padding: 12px 24px; display: flex; align-items: center; justify-content: space-between; position: sticky; top: 0; z-index: 10; }
  .logo { background: #cc0000; color: white; font-weight: 600; font-size: 15px; padding: 6px 14px; border-radius: 6px; }
  .subtitle { font-size: 13px; color: #666; margin-left: 12px; }
  .btn-settings { background: none; border: 1px solid #ddd; border-radius: 6px; padding: 6px 12px; font-size: 13px; cursor: pointer; color: #555; }
  .main { max-width: 980px; margin: 0 auto; padding: 24px 16px; }
  .steps { display: flex; align-items: center; gap: 8px; margin-bottom: 24px; }
  .step { width: 28px; height: 28px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 12px; font-weight: 600; background: #e0e0e0; color: #888; flex-shrink: 0; }
  .step.active { background: #0066cc; color: white; }
  .step.done { background: #2a9d5c; color: white; }
  .step-line { flex: 1; height: 1px; background: #e0e0e0; }
  .card { background: white; border: 1px solid #e8e8e8; border-radius: 10px; padding: 20px; margin-bottom: 16px; }
  .section-title { font-size: 11px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.06em; color: #888; margin-bottom: 14px; padding-bottom: 8px; border-bottom: 1px solid #f0f0f0; }
  .field-row { display: grid; gap: 12px; margin-bottom: 12px; }
  .field-row.c2 { grid-template-columns: 1fr 1fr; }
  .field-row.c3 { grid-template-columns: 1fr 1fr 1fr; }
  label { display: block; font-size: 12px; color: #666; margin-bottom: 4px; }
  input[type=text], input[type=date], input[type=password], input[type=number] { width: 100%; border: 1px solid #ddd; border-radius: 6px; padding: 8px 10px; font-size: 14px; background: white; color: #1a1a1a; }
  input:focus { outline: none; border-color: #0066cc; box-shadow: 0 0 0 2px rgba(0,102,204,0.1); }
  .radio-group { display: flex; gap: 16px; margin-top: 8px; }
  .radio-group label { display: flex; align-items: center; gap: 6px; font-size: 14px; color: #1a1a1a; margin: 0; cursor: pointer; }
  .search-bar { display: flex; gap: 8px; margin-bottom: 12px; }
  .search-bar input { flex: 1; }
  .patient-result { padding: 10px 14px; border: 1px solid #e8e8e8; border-radius: 8px; cursor: pointer; margin-bottom: 6px; }
  .patient-result:hover { background: #f0f7ff; border-color: #0066cc; }
  .patient-result .pname { font-size: 14px; font-weight: 600; }
  .patient-result .pdetail { font-size: 12px; color: #666; margin-top: 2px; }
  .tests-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 0; }
  .test-col-left { padding-right: 20px; border-right: 1px solid #f0f0f0; }
  .test-col-right { padding-left: 20px; }
  .test-section { margin-bottom: 14px; }
  .test-section-label { font-size: 11px; font-weight: 600; background: #f5f5f5; color: #555; padding: 3px 8px; border-radius: 4px; display: inline-block; margin-bottom: 6px; }
  .test-item { display: flex; align-items: center; gap: 8px; padding: 3px 0; }
  .test-item input[type=checkbox] { width: 14px; height: 14px; flex-shrink: 0; accent-color: #0066cc; }
  .test-item .test-label { font-size: 12px; color: #333; flex: 1; cursor: pointer; }
  .test-item .code { font-size: 11px; color: #999; font-family: monospace; min-width: 55px; }
  .qty-wrap { display: none; align-items: center; gap: 4px; }
  .qty-wrap.visible { display: flex; }
  .qty-wrap span { font-size: 12px; color: #888; }
  .qty-wrap input[type=number] { width: 48px; padding: 3px 6px; font-size: 13px; text-align: center; }
  .clinician-grid { display: grid; grid-template-columns: repeat(7, 1fr); gap: 8px; }
  .clinician-grid label { font-size: 11px; color: #666; }
  .clinician-grid input[type=checkbox] { width: 18px; height: 18px; accent-color: #0066cc; margin-top: 4px; }
  .action-row { display: flex; gap: 10px; margin-top: 16px; flex-wrap: wrap; }
  .btn { padding: 10px 20px; border-radius: 8px; font-size: 14px; font-weight: 500; cursor: pointer; border: none; }
  .btn-primary { background: #0066cc; color: white; }
  .btn-success { background: #2a9d5c; color: white; }
  .btn-purple { background: #6b46c1; color: white; }
  .btn-neutral { background: white; color: #333; border: 1px solid #ddd; }
  .status { font-size: 13px; padding: 10px 14px; border-radius: 8px; margin-top: 10px; }
  .status.info { background: #e8f0fe; color: #1a56cc; }
  .status.success { background: #e6f4ec; color: #1a7a3c; }
  .status.error { background: #fce8e8; color: #b00020; }
  .label-preview { border: 1px dashed #ccc; border-radius: 8px; padding: 14px 18px; margin: 12px 0; background: #fafafa; line-height: 2; font-size: 13px; }
  .label-preview .lpname { font-size: 15px; font-weight: 600; }
  .note { font-size: 11px; color: #999; margin-top: 4px; }
  .hidden { display: none !important; }
  .key-row { display: flex; gap: 6px; }
  .key-row input { flex: 1; }
</style>
</head>
<body>
<div class="topbar">
  <div style="display:flex;align-items:center;">
    <div class="logo">Nationwide Pathology</div>
    <span class="subtitle">Mannin Doctors Ltd</span>
  </div>
  <button class="btn-settings" onclick="showSettings()">&#9881; Settings</button>
</div>
<div class="main">
  <div class="steps">
    <div class="step active" id="s1">1</div><div class="step-line"></div>
    <div class="step" id="s2">2</div><div class="step-line"></div>
    <div class="step" id="s3">3</div>
  </div>

  <div id="panel-api" class="card">
    <div class="section-title">Cliniko API setup</div>
    <div class="field-row c2">
      <div>
        <label>Cliniko subdomain</label>
        <input type="text" id="cliniko-sub" placeholder="e.g. mannindoctors">
        <p class="note">The part before .cliniko.com in your browser URL</p>
      </div>
      <div>
        <label>API key (including the trailing colon)</label>
        <div class="key-row">
          <input type="password" id="cliniko-key" placeholder="Paste API key here" style="font-family:monospace;font-size:12px;">
          <button class="btn btn-neutral" onclick="toggleKey()">Show</button>
        </div>
        <p class="note">Stays on your Mac — never sent anywhere else</p>
      </div>
    </div>
    <div style="display:flex;gap:10px;">
      <button class="btn btn-primary" onclick="saveConfig()">Save and search patients</button>
      <button class="btn btn-neutral hidden" id="cancel-btn" onclick="cancelSettings()">Cancel</button>
    </div>
    <div id="api-status" class="hidden status"></div>
  </div>

  <div id="panel-patient" class="card hidden">
    <div class="section-title">Patient search</div>
    <div class="search-bar">
      <input type="text" id="search-input" placeholder="Surname, or date of birth as DD/MM/YYYY" onkeydown="if(event.key==='Enter')searchPatient()">
      <button class="btn btn-primary" onclick="searchPatient()">Search</button>
    </div>
    <div id="search-results"></div>
    <div id="search-status" class="hidden status"></div>
  </div>

  <div id="panel-form" class="hidden">
    <div class="card">
      <div class="section-title">Patient details</div>
      <div class="field-row c3">
        <div><label>Surname</label><input type="text" id="f-surname" oninput="updateLabel()"></div>
        <div><label>Forename</label><input type="text" id="f-forename" oninput="updateLabel()"></div>
        <div><label>Date of birth</label><input type="date" id="f-dob" onchange="updateLabel()"></div>
      </div>
      <div class="field-row c3">
        <div><label>Reference number</label><input type="text" id="f-ref"></div>
        <div><label>Sample date</label><input type="date" id="f-sample-date"></div>
        <div><label>Sex</label>
          <div class="radio-group">
            <label><input type="radio" name="sex" value="Male"> Male</label>
            <label><input type="radio" name="sex" value="Female"> Female</label>
          </div>
        </div>
      </div>
    </div>

    <div class="card">
      <div class="section-title">Tests requested — tick then set vial quantity</div>
      <div class="tests-grid">
        <div class="test-col-left">
          <div class="test-section"><div class="test-section-label">Routine profiles</div><div id="tests-profiles"></div></div>
          <div class="test-section"><div class="test-section-label">Haematology and chemistry</div><div id="tests-haem"></div></div>
          <div class="test-section"><div class="test-section-label">Other</div><div id="tests-other"></div></div>
        </div>
        <div class="test-col-right">
          <div class="test-section"><div class="test-section-label">Infectious disease</div><div id="tests-infect"></div></div>
          <div class="test-section"><div class="test-section-label">Routine microbiology</div><div id="tests-micro"></div></div>
          <div class="test-section"><div class="test-section-label">Autoimmune and other</div><div id="tests-auto"></div></div>
        </div>
      </div>
      <div style="margin-top:14px;">
        <label>Additional requests / notes</label>
        <input type="text" id="f-additional" placeholder="Free text">
      </div>
    </div>

    <div class="card">
      <div class="section-title">Clinician section</div>
      <div class="clinician-grid">
        <div><label>Fasting</label><input type="checkbox" id="c-fasting"></div>
        <div><label>EDTA</label><input type="checkbox" id="c-edta"></div>
        <div><label>SST</label><input type="checkbox" id="c-sst"></div>
        <div><label>Grey</label><input type="checkbox" id="c-grey"></div>
        <div><label>MSU</label><input type="checkbox" id="c-msu"></div>
        <div><label>Others</label><input type="checkbox" id="c-others"></div>
        <div><label>Initials</label><input type="text" id="c-initials" style="width:60px;"></div>
      </div>
      <div style="margin-top:10px;">
        <label>Sample taker's name</label>
        <input type="text" id="f-sample-taker" style="max-width:300px;">
      </div>
    </div>

    <div class="card">
      <div class="section-title">Dymo label preview</div>
      <div class="label-preview">
        <div class="lpname" id="lp-name">-</div>
        <div id="lp-dob">DOB: -</div>
        <div id="lp-date">-</div>
        <div>Mannin Doctors Ltd</div>
      </div>
      <div class="action-row">
        <button class="btn btn-primary" onclick="generatePDF()">Print PDF form</button>
        <button class="btn btn-purple" onclick="saveToClinico()">Save form to Cliniko</button>
        <button class="btn btn-success" onclick="printDymoLabel()">Print Dymo label</button>
        <button class="btn btn-neutral" onclick="resetForm()">New patient</button>
      </div>
      <div id="form-status" class="hidden status"></div>
    </div>
  </div>
</div>

<script>
var TESTS = {
  profiles:[
    {name:'VBIP (FBC, LFT, RFT, Lipids, UA, Glu)',code:'VBIP',tube:'ABC'},
    {name:'VBPP (FBC, LFT, RFT, Lipids, UA, PSA, Glu)',code:'VBPP',tube:'ABC'},
    {name:'MBIP (FBC, LFT, RFT, Lipids, UA, FT4, TSH, Glu)',code:'MBIP',tube:'ABC'},
    {name:'MBPP (FBC, LFT, RFT, Lipids, UA, PSA, FT4, TSH, Glu)',code:'MBPP',tube:'ABC'},
    {name:'Well Man',code:'WELM',tube:'ABC'},{name:'Well Woman',code:'WELW',tube:'ABC'},
    {name:'Female Hormone Panel',code:'FHP',tube:'B'},{name:'Male Hormone Panel',code:'MHP',tube:'B'}
  ],
  haem:[
    {name:'Full blood count',code:'FBC',tube:'A'},{name:'ESR',code:'ESR',tube:'A'},
    {name:'Blood Group',code:'BG',tube:'A'},{name:'Immunoglobulins',code:'IGP',tube:'B'},
    {name:'C-Reactive Protein',code:'CRP',tube:'B'},{name:'Glucose',code:'GLU',tube:'C'},
    {name:'HbA1C',code:'GHB',tube:'A'},{name:'Lipid Screen',code:'LIP',tube:'B'},
    {name:'Liver Function Test',code:'LFT',tube:'B'},{name:'Renal Function',code:'UEC',tube:'B'},
    {name:'Thyroid Function',code:'TFT',tube:'B'},{name:'Ferritin',code:'FER',tube:'B'},
    {name:'Folate (serum)',code:'FOL',tube:'B'},{name:'Iron',code:'FE',tube:'B'},
    {name:'Vitamin B12',code:'B12',tube:'B'},{name:'Vitamin D 25-OH',code:'VITD',tube:'B'},
    {name:'CEA',code:'CEA',tube:'B'},{name:'CA 19-9',code:'C19',tube:'B'},
    {name:'CA 15-3',code:'CA15',tube:'B'},{name:'CA 125',code:'CA1',tube:'B'},
    {name:'PSA',code:'PSA',tube:'B'},{name:'B-HCG',code:'HCG',tube:'B'}
  ],
  other:[
    {name:'Haemoglobin Electrophoresis',code:'HBEL',tube:'A'},
    {name:'Protein Electrophoresis',code:'PE',tube:'B'},
    {name:'Rheumatoid Factor',code:'RF',tube:'B'},
    {name:'Sickle Cell Screen',code:'SC',tube:'A'}
  ],
  infect:[
    {name:'Hepatitis A Antibodies (IgG/IgM)',code:'HAA',tube:'B'},
    {name:'Hepatitis A IgM Antibody',code:'HAM',tube:'B'},
    {name:'Hepatitis B Surface Antibody',code:'HIT',tube:'B'},
    {name:'Hepatitis B Surface Antigen',code:'HAG',tube:'B'},
    {name:'Hepatitis B Core Antibodies (IgG/IgM)',code:'HBC',tube:'B'},
    {name:'HIV I and II Antibodies P24 Antigen',code:'HIV',tube:'B'},
    {name:'Hepatitis C Antibody',code:'HEC',tube:'B'},
    {name:'Hepatitis C RNA (PCR)',code:'RNA',tube:'BB'},
    {name:'Hepatitis C (RNA, HIV I RNA, HBV DNA PCR)',code:'ED',tube:'AABB'},
    {name:'Measles IgG (Immunity)',code:'MEA',tube:'B'},
    {name:'Mumps IgG (Immunity)',code:'MUM',tube:'B'},
    {name:'Rubella IgG (Immunity)',code:'RUB',tube:'B'},
    {name:'Varicella zoster IgG (Immunity)',code:'VAR',tube:'B'},
    {name:'Syphilis Antibodies',code:'RPR',tube:'B'},
    {name:'Malaria Parasites',code:'MP',tube:'A'},
    {name:'Zika Virus Antibodies',code:'ZKAB',tube:'B'},
    {name:'TB Quantiferon Gold',code:'TBQ',tube:'J/D'}
  ],
  micro:[
    {name:'Urine culture and sensitivities',code:'MSU',tube:'E'},
    {name:'Swab for Culture (MCS)',code:'CUL',tube:'G'},
    {name:'Faecal Occult Blood',code:'HS',tube:'F'},
    {name:'Faecal Immunochemical Test',code:'FIT',tube:'F'},
    {name:'Gastrointestinal Panel',code:'GPCR',tube:'F'},
    {name:'Urine Microalbumin/Creatinine Ratio',code:'RAT',tube:'E'},
    {name:'STI Screen PCR',code:'STI8',tube:'E/H'},
    {name:'Chlamydia and Gonorrhoea PCR',code:'GC',tube:'E/H'}
  ],
  auto:[
    {name:'Anti-Nuclear Antibody',code:'ANA',tube:'B'},
    {name:'Connective Tissue Disease Screen',code:'CTD',tube:'B'},
    {name:'Coeliac Screen',code:'CS',tube:'B'}
  ]
};

var apiKey = '', prevPanel = '', currentPatientId = '';

function buildTests() {
  Object.keys(TESTS).forEach(function(s) {
    var el = document.getElementById('tests-'+s);
    if (!el) return;
    TESTS[s].forEach(function(t) {
      var d = document.createElement('div');
      d.className = 'test-item';
      d.innerHTML = '<input type="checkbox" id="t-' + t.code + '" onchange="toggleQty(\\'' + t.code + '\\', this.checked)">' +
        '<label class="test-label" for="t-' + t.code + '">' + t.name + '</label>' +
        '<span class="code">' + t.code + '/' + t.tube + '</span>' +
        '<div class="qty-wrap" id="qw-' + t.code + '"><span>x</span>' +
        '<input type="number" id="qty-' + t.code + '" value="1" min="1" max="9"></div>';
      el.appendChild(d);
    });
  });
}

function toggleQty(code, checked) {
  var w = document.getElementById('qw-'+code);
  if (w) { if (checked) w.classList.add('visible'); else w.classList.remove('visible'); }
}

function getSelected() {
  return Object.values(TESTS).flat().filter(function(t) {
    var cb = document.getElementById('t-'+t.code); return cb && cb.checked;
  }).map(function(t) {
    var qi = document.getElementById('qty-'+t.code);
    return {name:t.name, code:t.code, tube:t.tube, qty: qi ? (parseInt(qi.value)||1) : 1};
  });
}

function toggleKey() {
  var inp = document.getElementById('cliniko-key');
  inp.type = inp.type === 'password' ? 'text' : 'password';
  event.target.textContent = inp.type === 'password' ? 'Show' : 'Hide';
}

function showSettings() {
  prevPanel = !document.getElementById('panel-patient').classList.contains('hidden') ? 'patient'
    : !document.getElementById('panel-form').classList.contains('hidden') ? 'form' : '';
  show('panel-api'); hide('panel-patient'); hide('panel-form');
  document.getElementById('cliniko-key').value = apiKey;
  if (prevPanel) document.getElementById('cancel-btn').classList.remove('hidden');
}

function cancelSettings() {
  hide('panel-api');
  if (prevPanel === 'patient') show('panel-patient');
  else if (prevPanel === 'form') show('panel-form');
}

function saveConfig() {
  apiKey = document.getElementById('cliniko-key').value.trim();
  var sub = document.getElementById('cliniko-sub').value.trim();
  if (!sub || !apiKey) { showStatus('api-status','Please fill in both fields.','error'); return; }
  hide('panel-api'); show('panel-patient'); hide('panel-form');
  setStep(1,'done'); setStep(2,'active'); setStep(3,'');
  document.getElementById('cancel-btn').classList.remove('hidden');
}

async function searchPatient() {
  var q = document.getElementById('search-input').value.trim();
  if (!q) return;
  document.getElementById('search-results').innerHTML = '';
  showStatus('search-status','Searching Cliniko...','info');
  try {
    var params;
    if (/^\d{2}\/\d{2}\/\d{4}$/.test(q)) {
      var parts = q.split('/');
      params = 'dob=' + parts[2] + '-' + parts[1] + '-' + parts[0];
    } else {
      params = 'name=' + encodeURIComponent(q);
    }
    var resp = await fetch('/search?' + params + '&key=' + encodeURIComponent(apiKey));
    var data = await resp.json();
    if (data.error) throw new Error(data.error);
    hide('search-status');
    var patients = data.patients || [];
    if (!patients.length) { showStatus('search-status','No patients found.','error'); return; }
    patients.forEach(function(p) {
      var div = document.createElement('div');
      div.className = 'patient-result';
      var dob = p.date_of_birth ? new Date(p.date_of_birth).toLocaleDateString('en-GB') : '-';
      div.innerHTML = '<div class="pname">' + p.last_name + ', ' + p.first_name + '</div><div class="pdetail">DOB: ' + dob + ' | ID: ' + p.id + '</div>';
      div.onclick = function() { selectPatient(p); };
      document.getElementById('search-results').appendChild(div);
    });
  } catch(e) { showStatus('search-status','Error: '+e.message,'error'); }
}

function selectPatient(p) {
  currentPatientId = p.id;
  hide('panel-patient'); show('panel-form');
  setStep(2,'done'); setStep(3,'active');
  document.getElementById('f-surname').value = p.last_name || '';
  document.getElementById('f-forename').value = p.first_name || '';
  if (p.date_of_birth) document.getElementById('f-dob').value = p.date_of_birth.split('T')[0];
  document.getElementById('f-ref').value = p.id || '';
  document.getElementById('f-sample-date').value = new Date().toISOString().split('T')[0];
  document.querySelectorAll('input[name=sex]').forEach(function(r) { r.checked = r.value === p.sex; });
  updateLabel();
}

function updateLabel() {
  var fn = document.getElementById('f-forename').value;
  var ln = document.getElementById('f-surname').value;
  var dv = document.getElementById('f-dob').value;
  document.getElementById('lp-name').textContent = [fn,ln].filter(Boolean).join(' ') || '-';
  document.getElementById('lp-dob').textContent = 'DOB: ' + (dv ? new Date(dv).toLocaleDateString('en-GB') : '-');
  document.getElementById('lp-date').textContent = new Date().toLocaleDateString('en-GB');
}

function buildFormHTML() {
  var sel = getSelected();
  var surname = document.getElementById('f-surname').value;
  var forename = document.getElementById('f-forename').value;
  var dob = document.getElementById('f-dob').value;
  var sd = document.getElementById('f-sample-date').value;
  var ref = document.getElementById('f-ref').value;
  var sexEl = document.querySelector('input[name=sex]:checked');
  var sex = sexEl ? sexEl.value : '';
  var additional = document.getElementById('f-additional').value;
  var initials = document.getElementById('c-initials').value;
  var sampleTaker = document.getElementById('f-sample-taker').value;
  var dobStr = dob ? new Date(dob).toLocaleDateString('en-GB') : '';
  var sdStr = sd ? new Date(sd).toLocaleDateString('en-GB') : '';
  function chk(id) { var e = document.getElementById(id); return e && e.checked; }
  var rows = sel.map(function(t) {
    return '<tr><td>'+t.name+'</td><td>'+t.code+'</td><td>'+t.tube+'</td><td style="text-align:center">'+t.qty+'</td></tr>';
  }).join('') || '<tr><td colspan="4" style="color:#888">No tests selected</td></tr>';
  return '<!DOCTYPE html><html><head><meta charset="utf-8"><title>Blood Request</title>' +
    '<style>body{font-family:Arial,sans-serif;margin:24px;font-size:12px;}h2{font-size:13px;border-bottom:1px solid #ccc;padding-bottom:4px;margin:16px 0 8px;}table{width:100%;border-collapse:collapse;}td,th{border:1px solid #ccc;padding:5px 8px;}th{background:#f0f0f0;}.fr{display:grid;grid-template-columns:1fr 1fr 1fr;gap:12px;margin-bottom:10px;}.f{border:1px solid #ccc;border-radius:4px;padding:8px 10px;}.f label{font-size:10px;color:#666;display:block;margin-bottom:2px;}@media print{button{display:none;}}</style>' +
    '</head><body>' +
    '<div style="display:flex;align-items:center;gap:16px;margin-bottom:18px;"><div style="background:#cc0000;padding:8px 16px;border-radius:4px;"><span style="color:white;font-weight:bold;font-size:16px;">Nationwide Pathology</span></div>' +
    '<div><strong>Mannin Doctors Ltd (MND)</strong><br><span style="font-size:11px;color:#666;">Unit 1, Bitteswell Business Park, Lutterworth LE17 4LR | Tel: 01858 571322</span></div></div>' +
    '<div class="fr"><div class="f"><label>Surname</label><strong>'+surname+'</strong></div><div class="f"><label>Date of birth</label><strong>'+dobStr+'</strong></div><div class="f"><label>Sample date</label><strong>'+sdStr+'</strong></div></div>' +
    '<div class="fr"><div class="f"><label>Forename</label><strong>'+forename+'</strong></div><div class="f"><label>Reference number</label><strong>'+ref+'</strong></div><div class="f"><label>Sex</label><strong>'+sex+'</strong></div></div>' +
    '<h2>Tests requested</h2><table><thead><tr><th>Test</th><th>Code</th><th>Tube</th><th>Qty (vials)</th></tr></thead><tbody>'+rows+'</tbody></table>' +
    (additional ? '<p style="margin-top:10px"><strong>Additional:</strong> '+additional+'</p>' : '') +
    '<h2>Clinician section</h2><table><tr>' +
    '<td>Fasting: <strong>'+(chk('c-fasting')?'Yes':'No')+'</strong></td>' +
    '<td>EDTA: <strong>'+(chk('c-edta')?'Yes':'')+'</strong></td>' +
    '<td>SST: <strong>'+(chk('c-sst')?'Yes':'')+'</strong></td>' +
    '<td>Grey: <strong>'+(chk('c-grey')?'Yes':'')+'</strong></td>' +
    '<td>MSU: <strong>'+(chk('c-msu')?'Yes':'')+'</strong></td>' +
    '<td>Initials: <strong>'+initials+'</strong></td></tr></table>' +
    '<p style="margin-top:10px"><strong>Sample taker:</strong> '+sampleTaker+'</p>' +
    '<p style="margin-top:20px;font-size:10px;color:#999">Our terms and conditions apply. V1. Oct 2019</p>' +
    '<br><button onclick="window.print()" style="padding:8px 16px;cursor:pointer;">Print / Save as PDF</button>' +
    '</body></html>';
}

function generatePDF() {
  var win = window.open('','_blank');
  win.document.write(buildFormHTML());
  win.document.close();
  showStatus('form-status','Print window opened.','success');
}

async function saveToClinico() {
  if (!currentPatientId) { showStatus('form-status','No patient selected.','error'); return; }
  showStatus('form-status','Saving to Cliniko patient files...','info');
  try {
    var surname = document.getElementById('f-surname').value;
    var forename = document.getElementById('f-forename').value;
    var sd = document.getElementById('f-sample-date').value;
    var sdStr = sd ? new Date(sd).toLocaleDateString('en-GB').replace(/\\//g,'-') : 'unknown';
    var filename = ('blood-request-'+surname+'-'+forename+'-'+sdStr+'.html').toLowerCase().replace(/\\s+/g,'-');
    var resp = await fetch('/upload', {
      method:'POST',
      headers:{'Content-Type':'application/json'},
      body: JSON.stringify({key:apiKey, patient_id:currentPatientId, filename:filename, content:buildFormHTML(), description:'Blood request - '+forename+' '+surname+' - '+sdStr})
    });
    var data = await resp.json();
    if (data.error) throw new Error(data.error);
    showStatus('form-status','Form saved to patient files in Cliniko.','success');
  } catch(e) { showStatus('form-status','Upload failed: '+e.message,'error'); }
}

async function printDymoLabel() {
  var fn = document.getElementById('f-forename').value;
  var ln = document.getElementById('f-surname').value;
  var name = [fn,ln].filter(Boolean).join(' ');
  var dv = document.getElementById('f-dob').value;
  var dob = dv ? new Date(dv).toLocaleDateString('en-GB') : '';
  var today = new Date().toLocaleDateString('en-GB');
  var ref = document.getElementById('f-ref').value;
  function lineSpan(txt){
    return '<LineTextSpan><TextSpan><Text>'+txt+'</Text>'
      +'<FontInfo><FontName>Helvetica</FontName><FontSize>12.4</FontSize>'
      +'<IsBold>False</IsBold><IsItalic>False</IsItalic><IsUnderline>False</IsUnderline>'
      +'<FontBrush><SolidColorBrush><Color A="1" R="0" G="0" B="0"></Color>'
      +'</SolidColorBrush></FontBrush></FontInfo></TextSpan></LineTextSpan>';
  }
  var lx = '<?xml version="1.0" encoding="utf-8"?>'
    +'<DesktopLabel Version="1"><DYMOLabel Version="4">'
    +'<Description>DYMO Label</Description><Orientation>Landscape</Orientation>'
    +'<LabelName>ReturnAddressInt</LabelName><InitialLength>0</InitialLength>'
    +'<BorderStyle>SolidLine</BorderStyle>'
    +'<DYMORect><DYMOPoint><X>0.09</X><Y>0.056666665</Y></DYMOPoint>'
    +'<Size><Width>1.9766666</Width><Height>0.90333337</Height></Size></DYMORect>'
    +'<BorderColor><SolidColorBrush><Color A="1" R="0" G="0" B="0"></Color></SolidColorBrush></BorderColor>'
    +'<BorderThickness>1</BorderThickness><Show_Border>False</Show_Border>'
    +'<HasFixedLength>False</HasFixedLength><FixedLengthValue>0</FixedLengthValue>'
    +'<DynamicLayoutManager><RotationBehavior>ClearObjects</RotationBehavior><LabelObjects>'
    +'<TextObject><Name>TextObject0</Name>'
    +'<Brushes>'
    +'<BackgroundBrush><SolidColorBrush><Color A="0" R="0" G="0" B="0"></Color></SolidColorBrush></BackgroundBrush>'
    +'<BorderBrush><SolidColorBrush><Color A="1" R="0" G="0" B="0"></Color></SolidColorBrush></BorderBrush>'
    +'<StrokeBrush><SolidColorBrush><Color A="1" R="0" G="0" B="0"></Color></SolidColorBrush></StrokeBrush>'
    +'<FillBrush><SolidColorBrush><Color A="0" R="0" G="0" B="0"></Color></SolidColorBrush></FillBrush>'
    +'</Brushes>'
    +'<Rotation>Rotation0</Rotation><OutlineThickness>1</OutlineThickness>'
    +'<IsOutlined>False</IsOutlined><BorderStyle>SolidLine</BorderStyle>'
    +'<Margin><DYMOThickness Left="0" Top="0" Right="0" Bottom="0" /></Margin>'
    +'<HorizontalAlignment>Center</HorizontalAlignment><VerticalAlignment>Middle</VerticalAlignment>'
    +'<FitMode>AlwaysFit</FitMode><IsVertical>False</IsVertical>'
    +'<FormattedText><FitMode>AlwaysFit</FitMode>'
    +'<HorizontalAlignment>Center</HorizontalAlignment><VerticalAlignment>Middle</VerticalAlignment>'
    +'<IsVertical>False</IsVertical>'
    +lineSpan(name)
    +lineSpan('DOB: '+dob)
    +lineSpan('Ref: '+ref)
    +lineSpan('Date '+today)
    +lineSpan('Mannin Doctors')
    +'</FormattedText>'
    +'<ObjectLayout><DYMOPoint><X>0.1</X><Y>0.06666666</Y></DYMOPoint>'
    +'<Size><Width>1.9666669</Width><Height>0.8822984</Height></Size></ObjectLayout>'
    +'</TextObject></LabelObjects></DynamicLayoutManager></DYMOLabel>'
    +'<LabelApplication>Blank</LabelApplication>'
    +'<DataTable><Columns></Columns><Rows></Rows></DataTable></DesktopLabel>';
  showStatus('form-status','Sending to Dymo...','info');
  try {
    var resp = await fetch('/dymo', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({labelXml:lx})});
    if (resp.ok) showStatus('form-status','Label sent to Dymo LabelWriter 550.','success');
    else { var t = await resp.text(); throw new Error('Dymo error ' + resp.status + ': ' + t.substring(0,120)); }
  } catch(e) { showStatus('form-status','Could not reach Dymo Connect — make sure DYMO Connect for Desktop is running.','error'); }
}

function resetForm() {
  currentPatientId = '';
  hide('panel-form'); show('panel-patient');
  document.getElementById('search-input').value = '';
  document.getElementById('search-results').innerHTML = '';
  hide('search-status');
  Object.values(TESTS).flat().forEach(function(t) {
    var cb = document.getElementById('t-'+t.code); if(cb) cb.checked=false;
    var qw = document.getElementById('qw-'+t.code); if(qw) qw.classList.remove('visible');
    var qi = document.getElementById('qty-'+t.code); if(qi) qi.value=1;
  });
  setStep(2,'active'); setStep(3,'');
  updateLabel();
}

function show(id) { document.getElementById(id).classList.remove('hidden'); }
function hide(id) { document.getElementById(id).classList.add('hidden'); }
function setStep(n,s) { var e=document.getElementById('s'+n); e.className='step'+(s?' '+s:''); }
function showStatus(id,msg,type) {
  var e=document.getElementById(id); if(!e) return;
  e.textContent=msg; e.className='status '+type; e.classList.remove('hidden');
}
buildTests();
</script>
</body>
</html>"""


def auth_header(api_key):
    return 'Basic ' + base64.b64encode(api_key.encode()).decode()


def cliniko_get(url, api_key):
    req = urllib.request.Request(url, headers={
        'Authorization': auth_header(api_key),
        'Accept': 'application/json',
        'User-Agent': 'ManninBloodRequest/1.0 (mannindoctors@mannindoctors.com)'
    })
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read().decode())


def cliniko_post(url, api_key, payload):
    data = json.dumps(payload).encode()
    req = urllib.request.Request(url, data=data, headers={
        'Authorization': auth_header(api_key),
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'User-Agent': 'ManninBloodRequest/1.0 (mannindoctors@mannindoctors.com)'
    }, method='POST')
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read().decode())


class Handler(http.server.BaseHTTPRequestHandler):

    def log_message(self, fmt, *args):
        pass

    def send_json(self, data):
        body = json.dumps(data).encode()
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        p = urllib.parse.urlparse(self.path)
        if p.path == '/search':
            self.handle_search(p.query)
        else:
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(HTML.encode())

    def handle_dymo(self):
        n = int(self.headers.get('Content-Length', 0))
        raw = self.rfile.read(n)
        data = json.loads(raw.decode('utf-8'))
        label_xml = data.get('labelXml', '')
        print("[DYMO XML]", repr(label_xml[:200]))
        body = urllib.parse.urlencode({'printerName':'DYMO LabelWriter 550','labelXml':label_xml,'printParamsXml':''}).encode('utf-8')
        # DYMO Connect on macOS uses HTTPS on 41951
        dymo_urls = [
            'https://localhost:41951/DYMO/DLS/Printing/PrintLabel',
        ]
        # DYMO Connect uses a self-signed certificate — skip verification
        ssl_ctx = ssl.create_default_context()
        ssl_ctx.check_hostname = False
        ssl_ctx.verify_mode = ssl.CERT_NONE
        last_err = None
        for dymo_url in dymo_urls:
            req = urllib.request.Request(
                dymo_url,
                data=body,
                headers={'Content-Type': 'application/x-www-form-urlencoded'},
                method='POST'
            )
            try:
                kwargs = {'timeout': 10}
                if dymo_url.startswith('https'):
                    kwargs['context'] = ssl_ctx
                with urllib.request.urlopen(req, **kwargs) as r:
                    result = r.read()
                print("[DYMO OK via]", dymo_url, result)
                self.send_response(200)
                self.send_header('Content-Type', 'text/plain')
                self.end_headers()
                self.wfile.write(result)
                return
            except Exception as e:
                print("[DYMO try]", dymo_url, str(e))
                last_err = e
        print("[DYMO ERROR]", str(last_err))
        self.send_response(500)
        self.send_header('Content-Type', 'text/plain')
        self.end_headers()
        self.wfile.write(str(last_err).encode())

    def do_POST(self):
        if self.path == '/dymo':
            self.handle_dymo()
        elif self.path == '/upload':
            n = int(self.headers.get('Content-Length', 0))
            body = json.loads(self.rfile.read(n))
            self.handle_upload(body)
        else:
            self.send_response(404); self.end_headers()

    def handle_search(self, qs):
        params = urllib.parse.parse_qs(qs)
        key = params.get('key', [''])[0]
        name = params.get('name', [''])[0]
        dob = params.get('dob', [''])[0]
        if not key:
            self.send_json({'error': 'No API key'}); return
        try:
            if dob:
                url = API_BASE + '/patients?q[]=' + urllib.parse.quote('date_of_birth:=' + dob) + '&per_page=100'
            else:
                url = API_BASE + '/patients?q[]=' + urllib.parse.quote('last_name:~' + name) + '&per_page=100'
            all_patients = []
            while url:
                data = cliniko_get(url, key)
                all_patients.extend(data.get('patients', []))
                url = data.get('links', {}).get('next')
            self.send_json({'patients': all_patients})
        except urllib.error.HTTPError as e:
            self.send_json({'error': 'Cliniko error {}: {}'.format(e.code, e.read().decode()[:200])})
        except Exception as e:
            self.send_json({'error': str(e)})

    def handle_upload(self, body):
        key = body.get('key', '')
        patient_id = body.get('patient_id', '')
        filename = body.get('filename', 'blood-request.html')
        content = body.get('content', '')
        description = body.get('description', 'Blood request form')
        try:
            # Step 1: get presigned S3 post from Cliniko
            presign = cliniko_get(
                API_BASE + '/patients/' + str(patient_id) + '/attachment_presigned_post',
                key
            )
            print('\n[Presign response]', json.dumps(presign, indent=2))

            s3_url = presign.get('url', '')
            fields = presign.get('fields', {})
            if not s3_url:
                raise Exception('No S3 URL in presign response: ' + json.dumps(presign))

            # Step 2: POST file to S3
            boundary = b'ManninBoundary7MA4YWxkTrZu0gW'
            file_bytes = content.encode('utf-8')
            parts = []
            for k, v in fields.items():
                parts.append(b'--' + boundary + b'\r\n' +
                    ('Content-Disposition: form-data; name="' + k + '"\r\n\r\n').encode() +
                    str(v).encode() + b'\r\n')
            parts.append(b'--' + boundary + b'\r\n' +
                ('Content-Disposition: form-data; name="file"; filename="' + filename + '"\r\n').encode() +
                b'Content-Type: text/html\r\n\r\n' + file_bytes + b'\r\n')
            parts.append(b'--' + boundary + b'--\r\n')
            post_body = b''.join(parts)

            s3_req = urllib.request.Request(s3_url, data=post_body, headers={
                'Content-Type': 'multipart/form-data; boundary=' + boundary.decode(),
                'Content-Length': str(len(post_body))
            }, method='POST')
            with urllib.request.urlopen(s3_req, timeout=30) as s3r:
                s3_status = s3r.status
                s3_body = s3r.read().decode('utf-8', errors='ignore')
            print('[S3 status]', s3_status)
            print('[S3 body]', s3_body[:500])

            # Step 3: build upload_url from S3 XML Location element
            key_val = fields.get('key', filename)
            # Extract Key from S3 XML and build upload_url
            key_val = key_val.replace('${filename}', filename)
            # Try each possible upload_url format until one works
            try:
                root2 = ET.fromstring(s3_body)
                xml_key = None
                xml_loc = None
                for el in root2:
                    tag = el.tag.split('}')[-1]
                    if tag == 'Key': xml_key = el.text
                    if tag == 'Location': xml_loc = el.text
            except Exception:
                xml_key = None
                xml_loc = None
            # upload_url = presign url + Key from S3 XML (per Cliniko docs)
            if xml_key:
                upload_url = s3_url.rstrip('/') + '/' + xml_key
            else:
                upload_url = s3_url.rstrip('/') + '/' + key_val.replace('${filename}', filename)
            print('[final upload_url]', upload_url)
            try:
                root = ET.fromstring(s3_body)
                for tag in ['Location', '{http://s3.amazonaws.com/doc/2006-03-01/}Location']:
                    loc = root.find(tag)
                    if loc is not None and loc.text:
                        upload_url = loc.text
                        break
            except Exception as xe:
                print('[XML parse error]', xe)
            # Step 4: register with Cliniko
            payload = {
                'patient_id': int(patient_id),
                'upload_url': urllib.parse.unquote(upload_url),
                'description': description
            }
            print('[Cliniko payload]', json.dumps(payload))
            result = cliniko_post(API_BASE + '/patient_attachments', key, payload)
            print('[Cliniko attachment created successfully] id:', result.get('id',''))
            self.send_json({'success': True})

        except urllib.error.HTTPError as e:
            msg = e.read().decode('utf-8', errors='ignore')[:500]
            print('[Upload HTTPError]', e.code, msg)
            self.send_json({'error': 'Cliniko error {}: {}'.format(e.code, msg)})
        except Exception as e:
            print('[Upload error]', str(e))
            self.send_json({'error': str(e)})


def open_browser():
    import time; time.sleep(1)
    webbrowser.open('http://localhost:{}'.format(PORT))


if __name__ == '__main__':
    try:
        local_ip = socket.gethostbyname(socket.gethostname())
    except Exception:
        local_ip = 'unknown'
    threading.Thread(target=open_browser, daemon=True).start()
    print('\n  Mannin Blood Request Tool')
    print('  Local:   http://localhost:{}'.format(PORT))
    print('  Network: http://{}:{}  <- other devices on WiFi'.format(local_ip, PORT))
    print('  Press Ctrl+C to stop.\n')
    server = http.server.HTTPServer(('0.0.0.0', PORT), Handler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print('\n  Stopped.')
