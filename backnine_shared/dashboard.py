from __future__ import annotations

import json
import os
from pathlib import Path

from flask import Flask, abort, jsonify, render_template_string

from backnine_shared.clubs import build_runtime_config, list_club_slugs
HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{{ app_title }}</title>
<link href="https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=Fraunces:ital,opsz,wght@0,9..144,300;0,9..144,600;1,9..144,300&display=swap" rel="stylesheet">
<style>
  :root {
    --grass: {{ theme.panel }};
    --fairway: {{ theme.accent }};
    --rough: {{ theme.bg }};
    --flag: {{ theme.accent }};
    --sky: {{ theme.text }};
    --sand: {{ theme.warn }};
    --ink: {{ theme.panel_strong }};
    --mist: rgba(255,255,255,0.08);
    --line: {{ theme.line }};
    --muted: {{ theme.muted }};
    --ok: {{ theme.ok }};
    --warn: {{ theme.warn }};
    --dot: {{ theme.dot }};
  }

  * { box-sizing: border-box; margin: 0; padding: 0; }

  body {
    background:
      radial-gradient(circle at top left, rgba(255,255,255,0.06), transparent 26%),
      linear-gradient(180deg, var(--ink), var(--rough) 42%, #09111f 100%);
    color: var(--sky);
    font-family: 'DM Mono', monospace;
    min-height: 100vh;
    position: relative;
    overflow-x: hidden;
  }

  body::before {
    content: '';
    position: fixed;
    inset: 0;
    background-image:
      repeating-linear-gradient(
        90deg,
        transparent,
        transparent 60px,
        rgba(255,255,255,0.02) 60px,
        rgba(255,255,255,0.02) 61px
      ),
      repeating-linear-gradient(
        180deg,
        transparent,
        transparent 40px,
        rgba(6, 14, 28, 0.2) 40px,
        rgba(6, 14, 28, 0.2) 41px
      );
    pointer-events: none;
    z-index: 0;
  }

  .wrap {
    position: relative;
    z-index: 1;
    max-width: 980px;
    margin: 0 auto;
    padding: 24px 16px 60px;
  }

  header {
    display: flex;
    align-items: flex-end;
    justify-content: space-between;
    gap: 16px;
    margin-bottom: 32px;
    padding-bottom: 16px;
    border-bottom: 1px solid var(--line);
  }

  .logo-block h1 {
    font-family: 'Fraunces', serif;
    font-size: clamp(1.4rem, 5vw, 2.1rem);
    font-weight: 600;
    color: var(--flag);
    letter-spacing: -0.02em;
    line-height: 1;
  }

  .logo-block p {
    font-size: 0.65rem;
    color: var(--muted);
    text-transform: uppercase;
    letter-spacing: 0.12em;
    margin-top: 6px;
  }

  .back-link {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    margin-bottom: 10px;
    color: var(--muted);
    text-decoration: none;
    font-size: 0.68rem;
    letter-spacing: 0.08em;
    text-transform: uppercase;
  }

  .back-link:hover {
    color: var(--flag);
  }

  .status-pill {
    font-size: 0.65rem;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    padding: 5px 12px;
    border-radius: 99px;
    border: 1px solid;
    white-space: nowrap;
  }

  .status-pill.ok { border-color: var(--ok); color: var(--ok); }
  .status-pill.error { border-color: var(--warn); color: var(--warn); }
  .status-pill.starting { border-color: var(--flag); color: var(--flag); }

  .meta-bar {
    display: flex;
    gap: 24px;
    margin-bottom: 24px;
    font-size: 0.7rem;
    color: var(--muted);
    flex-wrap: wrap;
  }

  .meta-bar span strong {
    color: rgba(255,255,255,0.86);
    font-weight: 500;
  }

  .course-card, .slots-card {
    background: var(--mist);
    border: 1px solid var(--line);
    border-radius: 10px;
    padding: 14px 14px 12px;
    margin-bottom: 24px;
  }

  .course-title {
    font-size: 0.68rem;
    text-transform: uppercase;
    letter-spacing: 0.12em;
    color: var(--muted);
    margin-bottom: 10px;
  }

  .course-controls {
    display: grid;
    grid-template-columns: 1fr auto;
    gap: 10px 14px;
    margin-bottom: 12px;
  }

  .course-control label {
    display: block;
    font-size: 0.6rem;
    text-transform: uppercase;
    letter-spacing: 0.09em;
    color: var(--muted);
    margin-bottom: 4px;
  }

  .course-control .value {
    font-size: 0.8rem;
    color: var(--flag);
    margin-left: 8px;
  }

  .course-time-slider {
    width: 100%;
    accent-color: var(--flag);
  }

  .pace-select {
    width: 132px;
    background: rgba(0,0,0,0.2);
    color: var(--sky);
    border: 1px solid rgba(255,255,255,0.15);
    border-radius: 5px;
    padding: 8px;
    font-family: 'DM Mono', monospace;
    font-size: 0.75rem;
  }

  .course-scale {
    display: flex;
    justify-content: space-between;
    color: rgba(255,255,255,0.42);
    font-size: 0.62rem;
    margin-bottom: 4px;
  }

  .course-track {
    position: relative;
    min-height: 520px;
    margin: 10px 0 8px;
  }

  .hole-units {
    display: flex;
    flex-direction: column;
    gap: 14px;
  }

  .hole-row {
    display: flex;
    gap: 10px;
  }

  .hole-row.reverse {
    flex-direction: row-reverse;
  }

  .hole-unit {
    position: relative;
    padding: 12px 10px 4px;
    min-height: 54px;
  }

  .hole-label {
    position: absolute;
    top: 0;
    left: 50%;
    transform: translateX(-50%);
    font-size: 0.54rem;
    color: rgba(255,255,255,0.6);
    letter-spacing: 0.04em;
    line-height: 1;
    pointer-events: none;
  }

  .hole-lane {
    position: relative;
    height: 30px;
    background: linear-gradient(180deg, #1f5b2a, #194922);
    border: 1px solid rgba(0,0,0,0.25);
    overflow: visible;
  }

  .hole-well {
    display: none;
  }

  .hole-finish {
    position: absolute;
    top: 50%;
    width: 30px;
    height: 30px;
    margin-left: -15px;
    margin-top: -15px;
    border-radius: 50%;
    background: #8fe6ad;
    opacity: 0.95;
    z-index: 1;
  }

  .hole-start {
    position: absolute;
    top: 50%;
    width: 20px;
    height: 20px;
    margin-left: -10px;
    margin-top: -10px;
    border-radius: 3px;
    background: #8fe6ad;
    border: none;
    box-shadow: none;
    z-index: 1;
  }

  .hole-group-dot {
    position: absolute;
    top: 50%;
    width: 14px;
    height: 14px;
    background: var(--dot);
    border: 2px solid rgba(9, 17, 31, 0.75);
    border-radius: 50%;
    transform: translate(-50%, -50%);
    box-shadow: 0 0 0 2px rgba(243, 212, 59, 0.14);
    z-index: 3;
    cursor: pointer;
    pointer-events: auto;
  }

  .hole-group-dot.active {
    box-shadow: 0 0 0 3px rgba(255,255,255,0.26), 0 0 0 6px rgba(243, 212, 59, 0.16);
    transform: translate(-50%, -50%) scale(1.08);
  }

  .legend {
    display: flex;
    gap: 14px;
    flex-wrap: wrap;
    margin-top: 10px;
    color: var(--muted);
    font-size: 0.68rem;
  }

  .legend-item {
    display: flex;
    gap: 6px;
    align-items: center;
  }

  .legend-dot {
    width: 10px;
    height: 10px;
    border-radius: 50%;
  }

  .legend-dot.unavailable { background: var(--dot); }
  .legend-dot.available { background: var(--dot); }
  .legend-dot.unknown { background: var(--dot); }

  .slots-header {
    display: flex;
    justify-content: space-between;
    align-items: baseline;
    gap: 12px;
    margin-bottom: 12px;
  }

  .slots-header .count {
    color: var(--muted);
    font-size: 0.7rem;
  }

  .slot-list {
    display: grid;
    gap: 8px;
    max-height: 420px;
    overflow: auto;
    padding-right: 2px;
    position: relative;
    z-index: 2;
  }

  .slot-row {
    display: grid;
    grid-template-columns: 72px 110px 1fr;
    gap: 10px;
    align-items: start;
    padding: 10px 12px;
    background: rgba(0,0,0,0.14);
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 8px;
    cursor: pointer;
    width: 100%;
    text-align: left;
    color: inherit;
    background-clip: padding-box;
    pointer-events: auto;
    border: 1px solid rgba(255,255,255,0.06);
  }

  .slot-radio {
    position: absolute;
    opacity: 0;
    pointer-events: none;
  }

  .slot-row.active {
    border-color: rgba(255,255,255,0.58);
    background: rgba(255,255,255,0.12);
    box-shadow: 0 0 0 2px rgba(255,255,255,0.18);
  }

  .slot-row:hover {
    border-color: rgba(255,255,255,0.24);
  }

  .slot-time {
    color: var(--flag);
    font-size: 0.8rem;
  }

  .slot-state {
    color: var(--muted);
    font-size: 0.68rem;
    text-transform: uppercase;
    letter-spacing: 0.08em;
  }

  .slot-players {
    color: rgba(255,255,255,0.88);
    font-size: 0.76rem;
    line-height: 1.45;
    word-break: break-word;
  }

  .slot-players.empty {
    color: var(--muted);
  }

  .slot-raw {
    margin-top: 4px;
    color: rgba(255,255,255,0.42);
    font-size: 0.62rem;
    white-space: pre-wrap;
  }

  .empty-state {
    color: var(--muted);
    font-size: 0.74rem;
    padding: 8px 0;
  }

  .details-card {
    background: var(--mist);
    border: 1px solid var(--line);
    border-radius: 10px;
    padding: 14px;
    margin-bottom: 24px;
  }

  .details-toggle {
    cursor: pointer;
    list-style: none;
    padding: 14px;
    color: var(--flag);
    font-size: 0.72rem;
    text-transform: uppercase;
    letter-spacing: 0.1em;
  }

  .details-toggle::-webkit-details-marker {
    display: none;
  }

  .details-body {
    border-top: 1px solid var(--line);
    padding: 14px;
  }

  .detail-grid {
    display: grid;
    grid-template-columns: 120px 1fr;
    gap: 8px 14px;
    font-size: 0.74rem;
  }

  .detail-label {
    color: var(--muted);
    text-transform: uppercase;
    letter-spacing: 0.08em;
  }

  .detail-value {
    color: rgba(255,255,255,0.9);
    white-space: pre-wrap;
    word-break: break-word;
  }

  .detail-raw {
    margin-top: 14px;
    padding: 12px;
    background: rgba(0,0,0,0.16);
    border-radius: 8px;
    border: 1px solid rgba(255,255,255,0.06);
    font-size: 0.68rem;
    color: rgba(255,255,255,0.78);
    white-space: pre-wrap;
    word-break: break-word;
  }

  @media (max-width: 760px) {
    header {
      flex-direction: column;
      align-items: flex-start;
    }

    .wrap {
      padding: 18px 10px 42px;
    }

    .course-card, .slots-card, .details-card {
      padding-left: 10px;
      padding-right: 10px;
    }

    .course-controls {
      grid-template-columns: 1fr;
    }

    .slot-row {
      grid-template-columns: 1fr;
    }

    .hole-row {
      flex-wrap: nowrap;
      gap: 4px;
    }

    .hole-unit {
      min-width: 0;
      padding: 12px 4px 4px;
    }
  }

  @media (max-aspect-ratio: 4/5) {
    .wrap {
      padding-left: 8px;
      padding-right: 8px;
    }

    .course-card, .slots-card, .details-card {
      padding-left: 8px;
      padding-right: 8px;
    }

    .hole-units {
      gap: 10px;
    }

    .hole-row {
      gap: 2px;
    }

    .hole-unit {
      padding: 12px 2px 4px;
    }
  }
</style>
</head>
<body>
<div class="wrap">
  <header>
    <div class="logo-block">
      <a href="/" class="back-link">← Back to Home</a>
      <h1>⛳ {{ club_name }}</h1>
      <p>Tee Sheet Monitor</p>
    </div>
    <div id="status-pill" class="status-pill starting">Loading…</div>
  </header>

  <div class="meta-bar">
    <span>Last scrape <strong id="last-scrape">-</strong></span>
    <span>History <strong id="history-count">0 snapshots</strong></span>
    <span>Refresh in <strong id="refresh-countdown">{{ interval }}s</strong></span>
    <span>Latest tee sheet <strong id="snapshot-url">-</strong></span>
  </div>

  <section class="course-card">
    <div class="course-title">Course Projection</div>
    <div class="course-controls">
      <div class="course-control">
        <label for="course-time-slider">Projected Course Time <span class="value" id="course-time-label">--:--</span></label>
        <div class="course-scale"><span id="course-min">--:--</span><span id="course-max">--:--</span></div>
        <input id="course-time-slider" class="course-time-slider" type="range" min="0" max="0" value="0" step="1">
      </div>
      <div class="course-control">
        <label for="pace-select">Projected Round Duration</label>
        <select id="pace-select" class="pace-select">
          <option value="200">3h 20m</option>
          <option value="210">3h 30m</option>
          <option value="220">3h 40m</option>
          <option value="230">3h 50m</option>
          <option value="240" selected>4h 00m</option>
          <option value="250">4h 10m</option>
          <option value="260">4h 20m</option>
          <option value="270">4h 30m</option>
          <option value="280">4h 40m</option>
        </select>
      </div>
    </div>

    <div class="course-track">
      <div class="hole-units" id="hole-units"></div>
    </div>

    <div class="legend">
      <span class="legend-item"><span class="legend-dot unavailable"></span> projected group</span>
    </div>
  </section>

  <section class="details-card" id="group-details">
    <div class="course-title">Group Details</div>
    <div class="details-body" style="border-top:none; padding:0;">
      <div class="detail-grid">
        <div class="detail-label">Start Time</div>
        <div class="detail-value" id="detail-time">Select a group below.</div>
        <div class="detail-label">Players</div>
        <div class="detail-value" id="detail-players">-</div>
        <div class="detail-label">Slate</div>
        <div class="detail-value" id="detail-state">-</div>
        <div class="detail-label">Availability</div>
        <div class="detail-value" id="detail-availability">-</div>
      </div>
    </div>
  </section>

  <details class="slots-card">
    <summary class="details-toggle">Snapshot Slots</summary>
    <div class="details-body">
      <div class="slots-header">
        <div class="course-title">Snapshot Slots</div>
        <div class="count" id="slot-count">0 slots</div>
      </div>
      <div class="slot-list" id="slot-list"></div>
    </div>
  </details>
</div>

<script>
const holePars = {{ hole_pars_json|safe }};
const apiPath = {{ api_path_json|safe }};
const autoRefreshSecs = {{ interval }};
const holeWells = holePars.map((par) => Math.max(1, par - 1));
const totalCourseWells = holeWells.reduce((sum, value) => sum + value, 0);
let countdown = autoRefreshSecs;
let currentData = { snapshots: [], last_scrape: null, status: 'starting' };
let currentSnapshot = null;
let selectedSlotIndex = -1;

function fmtDate(value) {
  if (!value) return '-';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString();
}

function parseTimeToMinutes(timeStr) {
  if (!timeStr || !/^\\d{2}:\\d{2}$/.test(timeStr)) return null;
  const [h, m] = timeStr.split(':').map(Number);
  return (h * 60) + m;
}

function fmtMinutes(minutes) {
  if (minutes == null) return '--:--';
  const h = Math.floor(minutes / 60);
  const m = minutes % 60;
  return `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}`;
}

function slotState(slot) {
  return slot.booking_state || slot.available || 'unknown';
}

function normalisePlayers(slot) {
  if (slot.players && String(slot.players).trim()) return String(slot.players).trim();
  if (slot.raw_fallback) return 'Fallback parse only';
  if (slot.raw && !slot.time) return slot.raw;
  return '';
}

function latestSnapshot(data) {
  return data.snapshots && data.snapshots.length ? data.snapshots[data.snapshots.length - 1] : null;
}

function getCourseTimeBounds(snapshot) {
  const times = (snapshot?.slots || [])
    .map((slot) => parseTimeToMinutes(slot.time))
    .filter((value) => value != null);
  if (!times.length) return { min: 420, max: 1020 };
  return { min: Math.min(...times), max: Math.max(...times) + 180 };
}

function buildHoleUnits() {
  const root = document.getElementById('hole-units');
  const holes = holePars.map((par, idx) => ({ hole: idx + 1, par, wells: holeWells[idx] }));
  const rows = [];
  for (let index = 0; index < holes.length; index += 3) {
    rows.push(holes.slice(index, index + 3));
  }

  function rowHtml(holesInRow, reverse) {
    const items = holesInRow.map(({ hole, wells }) => `
      <div class="hole-unit" data-hole="${hole}" data-wells="${wells}" data-reverse="${reverse ? '1' : '0'}" style="flex:${wells} 1 0;">
        <div class="hole-label">Hole ${hole}</div>
        <div class="hole-lane" style="border-radius:${reverse ? '15px 10px 10px 15px' : '10px 15px 15px 10px'};">
          ${Array.from({ length: wells }, (_, idx) => `<span class="hole-well" style="left:${wellPosition(wells, idx, reverse)}"></span>`).join('')}
          <span class="hole-start" style="left:${wellPosition(wells, 0, reverse)}"></span>
          <span class="hole-finish" style="left:${wellPosition(wells, wells - 1, reverse)}"></span>
        </div>
      </div>
    `).join('');
    return `<div class="hole-row${reverse ? ' reverse' : ''}">${items}</div>`;
  }

  root.innerHTML = rows.map((row, idx) => rowHtml(row, idx % 2 === 1)).join('');
}

function wellPosition(wellCount, index, reverse = false) {
  const radiusPx = 15;
  if (wellCount <= 1) return 'calc(50%)';
  const t = index / (wellCount - 1);
  const percent = reverse ? (1 - t) * 100 : t * 100;
  const pixelOffset = reverse ? ((2 * radiusPx * t) - radiusPx) : (radiusPx - (2 * radiusPx * t));
  return `calc(${percent}% + ${pixelOffset}px)`;
}

function locateGroup(slot, courseMinutes, paceMinutes) {
  const start = parseTimeToMinutes(slot.time);
  if (start == null) return null;
  const elapsed = courseMinutes - start;
  if (elapsed < 0) return null;
  const totalWellSteps = Math.floor(elapsed / paceMinutes);
  let cursor = 0;
  for (let idx = 0; idx < holeWells.length; idx += 1) {
    const holeWellCount = holeWells[idx];
    if (totalWellSteps < cursor + holeWellCount) {
      return { hole: idx + 1, wellIndex: Math.max(0, totalWellSteps - cursor) };
    }
    cursor += holeWellCount;
  }
  return { hole: holeWells.length, wellIndex: holeWells[holeWells.length - 1] - 1 };
}

function renderProjection(snapshot) {
  const slider = document.getElementById('course-time-slider');
  const roundMinutes = Number(document.getElementById('pace-select').value);
  const pace = roundMinutes / totalCourseWells;
  const courseMinutes = Number(slider.value);
  document.getElementById('course-time-label').textContent = fmtMinutes(courseMinutes);

  document.querySelectorAll('.hole-group-dot').forEach((node) => node.remove());
  if (!snapshot) return;

  snapshot.slots.forEach((slot, index) => {
    const position = locateGroup(slot, courseMinutes, pace);
    if (!position) return;
    const unit = document.querySelector(`.hole-unit[data-hole="${position.hole}"] .hole-lane`);
    if (!unit) return;

    const dot = document.createElement('span');
    dot.className = `hole-group-dot${index === selectedSlotIndex ? ' active' : ''}`;
    const holeUnit = document.querySelector(`.hole-unit[data-hole="${position.hole}"]`);
    const isReverse = holeUnit?.dataset.reverse === '1';
    dot.style.left = wellPosition(holeWells[position.hole - 1], position.wellIndex, isReverse);
    dot.title = `${slot.time || '--:--'} · ${normalisePlayers(slot) || slotState(slot)}`;
    dot.dataset.slotIndex = String(index);
    dot.setAttribute('role', 'button');
    dot.setAttribute('tabindex', '0');
    unit.appendChild(dot);
  });
}

function renderSlots(snapshot) {
  const root = document.getElementById('slot-list');
  if (!snapshot || !snapshot.slots || !snapshot.slots.length) {
    root.innerHTML = '<div class="empty-state">No slot data available yet.</div>';
    document.getElementById('slot-count').textContent = '0 slots';
    selectedSlotIndex = -1;
    renderSelectedSlot(null);
    return;
  }

  if (selectedSlotIndex >= snapshot.slots.length || selectedSlotIndex === -1) {
    selectedSlotIndex = 0;
  }

  document.getElementById('slot-count').textContent = `${snapshot.slot_count} slots`;
  root.innerHTML = snapshot.slots.map((slot, idx) => {
    const players = normalisePlayers(slot);
    return `
      <label class="slot-row${idx === selectedSlotIndex ? ' active' : ''}" data-slot-index="${idx}">
        <input class="slot-radio" type="radio" name="slot-picker" value="${idx}" ${idx === selectedSlotIndex ? 'checked' : ''}>
        <div class="slot-time">${slot.time || '--:--'}</div>
        <div class="slot-state">${slotState(slot)}</div>
        <div class="slot-players${players ? '' : ' empty'}">
          ${players || 'No player detail'}
          ${slot.raw && players && players !== slot.raw ? `<div class="slot-raw">${slot.raw.slice(0, 160)}</div>` : ''}
        </div>
      </label>
    `;
  }).join('');

  if (!root.dataset.bound) {
    root.addEventListener('change', (event) => {
      const radio = event.target.closest('.slot-radio');
      if (!radio) return;
      const index = Number(radio.value);
      if (Number.isNaN(index)) return;
      selectSlot(index);
    });
    root.dataset.bound = '1';
  }
}

function updateActiveSlot() {
  document.querySelectorAll('.slot-row').forEach((node) => {
    node.classList.toggle('active', Number(node.dataset.slotIndex) === selectedSlotIndex);
  });
}

function selectSlot(index) {
  selectedSlotIndex = index;
  updateActiveSlot();
  document.querySelectorAll('.slot-radio').forEach((radio) => {
    radio.checked = Number(radio.value) === selectedSlotIndex;
  });
  renderSelectedSlot(currentSnapshot?.slots?.[selectedSlotIndex] || null);
}

window.selectSlot = selectSlot;

document.addEventListener('click', (event) => {
  const dot = event.target.closest('.hole-group-dot');
  if (!dot) return;
  const index = Number(dot.dataset.slotIndex);
  if (Number.isNaN(index)) return;
  selectSlot(index);
});

document.addEventListener('keydown', (event) => {
  const dot = event.target.closest('.hole-group-dot');
  if (!dot) return;
  if (event.key !== 'Enter' && event.key !== ' ') return;
  event.preventDefault();
  const index = Number(dot.dataset.slotIndex);
  if (Number.isNaN(index)) return;
  selectSlot(index);
});

function renderSelectedSlot(slot) {
  document.getElementById('detail-time').textContent = slot?.time || 'Select a group below.';
  document.getElementById('detail-players').textContent = normalisePlayers(slot || {}) || '-';
  document.getElementById('detail-state').textContent = slot ? slotState(slot) : '-';
  document.getElementById('detail-availability').textContent = slot?.available || '-';
}

function applySnapshot(snapshot) {
  currentSnapshot = snapshot;
  renderSlots(snapshot);
  renderProjection(snapshot);
  document.getElementById('snapshot-url').textContent = snapshot?.url || '-';
  updateActiveSlot();
  renderSelectedSlot(snapshot?.slots?.[selectedSlotIndex] || null);
}

function setupSlider(snapshot) {
  const bounds = getCourseTimeBounds(snapshot);
  const slider = document.getElementById('course-time-slider');
  slider.min = String(bounds.min);
  slider.max = String(bounds.max);
  if (!slider.dataset.initialised) {
    const now = new Date();
    const nowMinutes = now.getHours() * 60 + now.getMinutes();
    slider.value = String(Math.max(bounds.min, Math.min(bounds.max, nowMinutes)));
    slider.dataset.initialised = 'true';
  } else {
    slider.value = String(Math.max(bounds.min, Math.min(bounds.max, Number(slider.value))));
  }
  document.getElementById('course-min').textContent = fmtMinutes(bounds.min);
  document.getElementById('course-max').textContent = fmtMinutes(bounds.max);
  document.getElementById('course-time-label').textContent = fmtMinutes(Number(slider.value));
}

async function loadData() {
  const response = await fetch(apiPath, { cache: 'no-store' });
  const data = await response.json();
  currentData = data;
  const snapshot = latestSnapshot(data);
  const status = data.status || 'starting';
  const pill = document.getElementById('status-pill');
  pill.textContent = status;
  pill.className = 'status-pill ' + (status === 'ok' ? 'ok' : (status.startsWith('error') || status.includes('failed') || status === 'timeout' ? 'error' : 'starting'));
  document.getElementById('last-scrape').textContent = fmtDate(data.last_scrape);
  document.getElementById('history-count').textContent = `${(data.snapshots || []).length} snapshot${(data.snapshots || []).length === 1 ? '' : 's'}`;
  setupSlider(snapshot);
  applySnapshot(snapshot);
}

document.getElementById('course-time-slider').addEventListener('input', () => renderProjection(currentSnapshot));
document.getElementById('pace-select').addEventListener('change', () => renderProjection(currentSnapshot));

setInterval(() => {
  countdown -= 1;
  if (countdown <= 0) {
    countdown = autoRefreshSecs;
    loadData();
  }
  document.getElementById('refresh-countdown').textContent = `${countdown}s`;
}, 1000);

buildHoleUnits();
loadData();
</script>
</body>
</html>
"""


LANDING_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Back Nine</title>
<link href="https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=Fraunces:opsz,wght@9..144,400;9..144,600&display=swap" rel="stylesheet">
<style>
  body {
    margin: 0;
    font-family: 'DM Mono', monospace;
    background: linear-gradient(180deg, #081220, #122038 55%, #0e1727);
    color: #e8f0ff;
    min-height: 100vh;
  }
  .wrap {
    max-width: 960px;
    margin: 0 auto;
    padding: 32px 16px 48px;
  }
  h1 {
    margin: 0 0 10px;
    font-family: 'Fraunces', serif;
    font-size: clamp(2rem, 6vw, 4rem);
  }
  .subtle {
    color: rgba(232, 240, 255, 0.64);
    line-height: 1.6;
    max-width: 54rem;
  }
  .clubs {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
    gap: 16px;
    margin-top: 28px;
  }
  a.card {
    display: block;
    padding: 18px;
    border-radius: 18px;
    color: inherit;
    text-decoration: none;
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(255,255,255,0.08);
  }
  a.card:hover { border-color: rgba(191, 231, 255, 0.38); }
  .slug { margin-top: 8px; color: rgba(191, 231, 255, 0.7); font-size: 0.85rem; }
</style>
</head>
<body>
  <div class="wrap">
    <h1>Back Nine</h1>
    <div class="subtle">One app, many clubs. Choose a club dashboard below.</div>
    <div class="clubs">
      {% for club in clubs %}
        <a class="card" href="/{{ club.slug }}/">
          <div>{{ club.name }}</div>
          <div class="slug">/{{ club.slug }}/</div>
        </a>
      {% endfor %}
    </div>
  </div>
</body>
</html>
"""


def load_data(data_file: str) -> dict:
    if os.path.exists(data_file):
        with open(data_file) as f:
            return json.load(f)
    return {"snapshots": [], "last_scrape": None, "status": "starting"}


def create_app(config) -> Flask:
    app = Flask(__name__)

    @app.route("/")
    def index():
        return render_template_string(
            HTML,
            app_title=config.APP_TITLE,
            club_name=config.CLUB_NAME,
            interval=config.SCRAPE_INTERVAL,
            hole_pars_json=json.dumps(config.HOLE_PARS),
            api_path_json=json.dumps("/api/data"),
            theme=config.THEME,
        )

    @app.route("/api/data")
    def api_data():
        return jsonify(load_data(config.DATA_FILE))

    return app


def create_multi_club_app(root_dir: str) -> Flask:
    app = Flask(__name__)

    def club_config(slug: str):
        try:
            return type("Config", (), build_runtime_config(slug, Path(root_dir) / "data" / slug))
        except KeyError:
            abort(404)

    @app.route("/")
    def landing():
        clubs = [
            {"slug": slug, "name": build_runtime_config(slug, Path(root_dir) / "data" / slug)["CLUB_NAME"]}
            for slug in list_club_slugs()
        ]
        return render_template_string(LANDING_HTML, clubs=clubs)

    @app.route("/<slug>/")
    def club_page(slug: str):
        config = club_config(slug)
        return render_template_string(
            HTML,
            app_title=config.APP_TITLE,
            club_name=config.CLUB_NAME,
            interval=config.SCRAPE_INTERVAL,
            hole_pars_json=json.dumps(config.HOLE_PARS),
            api_path_json=json.dumps(f"/{slug}/api/data"),
            theme=config.THEME,
        )

    @app.route("/<slug>/api/data")
    def club_api_data(slug: str):
        config = club_config(slug)
        return jsonify(load_data(config.DATA_FILE))

    return app
