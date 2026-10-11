/**
 * NFL Predictive & Value System - Frontend Application Logic
 * Consume report_data.json y renderiza los 6 bloques estadísticos obligatorios (A, B, C, D, E, F),
 * ventanas Temporada/L8/L5/L3, decisiones categóricas, valor esperado y metadatos de auditoría.
 */

let currentFilter = 'ALL';
let fullReport = null;
let secondsRemaining = 120;

function startAutoRefreshTimer() {
  setInterval(() => {
    secondsRemaining--;
    const badge = document.getElementById('auto-refresh-timer');
    if (badge) {
      const mins = String(Math.floor(secondsRemaining / 60)).padStart(2, '0');
      const secs = String(secondsRemaining % 60).padStart(2, '0');
      badge.textContent = `${mins}:${secs}`;
    }
    if (secondsRemaining <= 0) {
      secondsRemaining = 120;
      console.log("Recargando datos automáticamente (cada 2 min)...");
      location.reload();
    }
  }, 1000);
}

async function loadReportData() {
  if (window.WEEKLY_REPORT && window.WEEKLY_REPORT.games && window.WEEKLY_REPORT.games.length > 0) {
    fullReport = window.WEEKLY_REPORT;
    renderDashboard(fullReport);
    return;
  }
  try {
    const res = await fetch('report_data.json?v=' + Date.now());
    if (!res.ok) throw new Error("No se pudo cargar el reporte semanal.");
    fullReport = await res.json();
    renderDashboard(fullReport);
  } catch (err) {
    console.error("Error al cargar datos:", err);
    if (window.WEEKLY_REPORT) {
      renderDashboard(window.WEEKLY_REPORT);
    }
  }
}

function renderDashboard(data) {
  // 1. KPIs
  const summary = data.summary || {};
  document.getElementById('kpi-candidatas').textContent = summary.CANDIDATA || 0;
  document.getElementById('kpi-esperar').textContent = summary.ESPERAR || 0;
  document.getElementById('kpi-dejar-pasar').textContent = summary.DEJAR_PASAR || 0;
  document.getElementById('kpi-pendiente').textContent = summary.PENDIENTE || 0;

  if (data.generated_at) {
    const d = new Date(data.generated_at);
    document.getElementById('last-updated-text').textContent = 'Auditado: ' + d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  }

  // 2. Render Cards
  const container = document.getElementById('matchups-container');
  container.innerHTML = '';

  const games = data.games || [];
  const filtered = games.filter(g => {
    if (currentFilter === 'ALL') return true;
    return g.global_decision === currentFilter;
  });

  if (filtered.length === 0) {
    container.innerHTML = `
      <div class="bg-gray-900 border border-gray-800 p-8 rounded-xl text-center text-gray-500">
        No hay partidos con el filtro seleccionado: <b>${currentFilter}</b>
      </div>
    `;
    return;
  }

  filtered.forEach(game => {
    container.appendChild(createGameCard(game));
  });
}

function createGameCard(g) {
  const card = document.createElement('div');
  card.className = "bg-gray-900 border border-gray-800 rounded-2xl p-6 shadow-xl space-y-6";

  // Badge y colores de decisión
  let badgeClass = "bg-gray-800 text-gray-300 border-gray-700";
  let decText = g.global_decision;
  if (decText === "APUESTA CANDIDATA") {
    badgeClass = "bg-emerald-950 text-emerald-300 border-emerald-600 animate-pulse";
  } else if (decText === "ESPERAR") {
    badgeClass = "bg-amber-950 text-amber-300 border-amber-600";
  } else if (decText === "PENDIENTE") {
    badgeClass = "bg-rose-950 text-rose-300 border-rose-600";
  }

  // Si el partido está PENDIENTE por datos incompletos
  if (g.global_decision === "PENDIENTE") {
    card.innerHTML = `
      <div class="flex flex-wrap items-center justify-between gap-3 border-b border-gray-800 pb-4">
        <div>
          <span class="text-xs font-mono text-gray-400">ID: ${g.game_id}</span>
          <h2 class="text-xl font-black text-white mt-1">${g.away_team} @ ${g.home_team}</h2>
        </div>
        <span class="px-3 py-1.5 rounded-full text-xs font-black uppercase tracking-wider border ${badgeClass}">
          🚨 PENDIENTE (DATOS INCOMPLETOS)
        </span>
      </div>
      <div class="bg-rose-950/40 border border-rose-900/60 p-4 rounded-xl text-xs space-y-2">
        <div class="font-bold text-rose-300 flex items-center gap-2">
          <span>⛔ Regla de Integridad Estricta: Cero Imputación Artificial</span>
        </div>
        <p class="text-gray-300">${g.reason}</p>
        <ul class="list-disc list-inside text-rose-400 font-mono text-[11px] space-y-1">
          ${(g.pending_issues || []).map(err => `<li>${err}</li>`).join('')}
        </ul>
      </div>
    `;
    return card;
  }

  // Partido con datos completos: renderizar los 6 bloques
  const homeSide = (g.sides_analysis || []).find(s => s.side === 'HOME') || {};
  const awaySide = (g.sides_analysis || []).find(s => s.side === 'AWAY') || {};

  const bA = g.block_a_efficiency || {};
  const bB = g.block_b_qb || {};
  const bC = g.block_c_matchup || {};
  const bD = g.block_d_injuries || {};
  const bE = g.block_e_context || {};
  const bF = g.block_f_market || {};
  const w = g.rolling_windows || {};

  card.innerHTML = `
    <!-- Card Header -->
    <div class="flex flex-wrap items-center justify-between gap-3 border-b border-gray-800 pb-4">
      <div>
        <div class="flex items-center gap-2">
          <span class="text-xs font-mono text-gray-400">${g.game_id}</span>
          <span class="text-[10px] bg-cyan-950 text-cyan-400 border border-cyan-800 px-2 py-0.5 rounded">Snapshot Inmutable Guardado</span>
        </div>
        <h2 class="text-2xl font-black text-white mt-1">${g.away_team} @ ${g.home_team}</h2>
        <div class="text-xs text-gray-400 flex items-center gap-3 mt-1">
          <span>🏟️ ${bE.details ? bE.details.stadium : 'Estadio NFL'}</span>
          <span>🌡️ ${bE.details ? bE.details.temp_f + '°F' : '65°F'}</span>
          <span>💨 ${bE.details ? bE.details.wind_mph + ' mph' : '5 mph'}</span>
          <span>${bE.is_divisional ? '⚔️ Divisional' : 'Normal'}</span>
        </div>
      </div>
      <div class="text-right">
        <span class="px-3 py-1.5 rounded-full text-xs font-black uppercase tracking-wider border ${badgeClass}">
          ${g.global_decision}
        </span>
        <div class="text-xs font-mono text-cyan-400 mt-2 font-bold">
          Proyección: ${g.projected_score}
        </div>
        <div class="text-[11px] text-gray-400">
          Spread Justo: ${g.fair_spread} | Total Justo: ${g.fair_total}
        </div>
      </div>
    </div>

    <!-- Valor Esperado (+EV) & Mercado (Bloque F) -->
    <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
      <!-- Home Side -->
      <div class="bg-gray-850 p-4 rounded-xl border ${homeSide.decision === 'APUESTA CANDIDATA' ? 'border-emerald-600 bg-emerald-950/20' : 'border-gray-800'}">
        <div class="flex justify-between items-center mb-2">
          <span class="font-bold text-sm text-white">${g.home_team} (LOCAL)</span>
          <span class="text-[10px] px-2 py-0.5 rounded font-bold uppercase ${homeSide.decision === 'APUESTA CANDIDATA' ? 'bg-emerald-500 text-black' : (homeSide.decision === 'ESPERAR' ? 'bg-amber-500 text-black' : 'bg-gray-800 text-gray-400')}">${homeSide.decision}</span>
        </div>
        <div class="grid grid-cols-4 gap-2 text-center text-xs mb-2">
          <div class="bg-gray-900 p-2 rounded">
            <div class="text-gray-400 text-[10px]">Prob Modelo</div>
            <div class="font-bold text-cyan-400 font-mono text-sm">${homeSide.estimated_prob_pct}%</div>
          </div>
          <div class="bg-gray-900 p-2 rounded">
            <div class="text-gray-400 text-[10px]">Cuota Justa</div>
            <div class="font-bold text-white font-mono text-sm">${homeSide.fair_odds}</div>
          </div>
          <div class="bg-gray-900 p-2 rounded">
            <div class="text-gray-400 text-[10px]">Mejor Cuota</div>
            <div class="font-bold text-emerald-400 font-mono text-sm">${homeSide.market_odds}</div>
          </div>
          <div class="bg-gray-900 p-2 rounded">
            <div class="text-gray-400 text-[10px]">Valor (+EV)</div>
            <div class="font-bold ${homeSide.expected_value_ev_pct >= 3.5 ? 'text-emerald-400' : 'text-gray-400'} font-mono text-sm">${homeSide.expected_value_ev_pct > 0 ? '+' : ''}${homeSide.expected_value_ev_pct}%</div>
          </div>
        </div>
        <p class="text-[11px] text-gray-400 italic">${homeSide.decision_reason}</p>
      </div>

      <!-- Away Side -->
      <div class="bg-gray-850 p-4 rounded-xl border ${awaySide.decision === 'APUESTA CANDIDATA' ? 'border-emerald-600 bg-emerald-950/20' : 'border-gray-800'}">
        <div class="flex justify-between items-center mb-2">
          <span class="font-bold text-sm text-white">${g.away_team} (VISITANTE)</span>
          <span class="text-[10px] px-2 py-0.5 rounded font-bold uppercase ${awaySide.decision === 'APUESTA CANDIDATA' ? 'bg-emerald-500 text-black' : (awaySide.decision === 'ESPERAR' ? 'bg-amber-500 text-black' : 'bg-gray-800 text-gray-400')}">${awaySide.decision}</span>
        </div>
        <div class="grid grid-cols-4 gap-2 text-center text-xs mb-2">
          <div class="bg-gray-900 p-2 rounded">
            <div class="text-gray-400 text-[10px]">Prob Modelo</div>
            <div class="font-bold text-cyan-400 font-mono text-sm">${awaySide.estimated_prob_pct}%</div>
          </div>
          <div class="bg-gray-900 p-2 rounded">
            <div class="text-gray-400 text-[10px]">Cuota Justa</div>
            <div class="font-bold text-white font-mono text-sm">${awaySide.fair_odds}</div>
          </div>
          <div class="bg-gray-900 p-2 rounded">
            <div class="text-gray-400 text-[10px]">Mejor Cuota</div>
            <div class="font-bold text-emerald-400 font-mono text-sm">${awaySide.market_odds}</div>
          </div>
          <div class="bg-gray-900 p-2 rounded">
            <div class="text-gray-400 text-[10px]">Valor (+EV)</div>
            <div class="font-bold ${awaySide.expected_value_ev_pct >= 3.5 ? 'text-emerald-400' : 'text-gray-400'} font-mono text-sm">${awaySide.expected_value_ev_pct > 0 ? '+' : ''}${awaySide.expected_value_ev_pct}%</div>
          </div>
        </div>
        <p class="text-[11px] text-gray-400 italic">${awaySide.decision_reason}</p>
      </div>
    </div>

    <!-- Desglose de los 6 Bloques Estadísticos (Acordeón o Tablas) -->
    <div class="border-t border-gray-800 pt-4">
      <div class="text-xs font-bold uppercase tracking-wider text-cyan-400 mb-3 flex items-center justify-between">
        <span>📋 Desglose Técnico Completo de los 6 Bloques & Ventanas Rodantes</span>
        <span class="text-gray-500 font-normal">Temporada &bull; L8 &bull; L5 &bull; L3</span>
      </div>

      <div class="grid grid-cols-1 md:grid-cols-3 gap-3 text-xs">
        
        <!-- Bloque A: Eficiencia de Equipos -->
        <div class="bg-gray-850 p-3 rounded-xl border border-gray-800 space-y-1.5">
          <div class="font-bold text-gray-200 border-b border-gray-700/60 pb-1">Bloque A: Eficiencia de Equipos</div>
          <div class="flex justify-between text-[11px] text-gray-400">
            <span>EPA/play Ofensivo:</span>
            <span class="font-mono text-white">${bA.home ? bA.home.off_epa_play : '-'} (H) vs ${bA.away ? bA.away.off_epa_play : '-'} (A)</span>
          </div>
          <div class="flex justify-between text-[11px] text-gray-400">
            <span>Success Rate Ofensivo:</span>
            <span class="font-mono text-white">${bA.home ? bA.home.off_success_rate + '%' : '-'} vs ${bA.away ? bA.away.off_success_rate + '%' : '-'}</span>
          </div>
          <div class="flex justify-between text-[11px] text-gray-400">
            <span>EPA Pase / Carrera:</span>
            <span class="font-mono text-white">${bA.home ? bA.home.off_pass_epa + ' / ' + bA.home.off_rush_epa : '-'}</span>
          </div>
          <div class="flex justify-between text-[11px] text-gray-400">
            <span>Presión Def / Sacks Perm:</span>
            <span class="font-mono text-white">${bA.home ? bA.home.def_pressure_rate + '% / ' + bA.home.sacks_allowed_pg : '-'}</span>
          </div>
          <div class="flex justify-between text-[11px] text-gray-400">
            <span>Red Zone TD% / Balones:</span>
            <span class="font-mono text-white">${bA.home ? bA.home.red_zone_pct + '% / ' + bA.home.turnover_diff : '-'}</span>
          </div>
        </div>

        <!-- Bloque B: Quarterback Titular & Suplente -->
        <div class="bg-gray-850 p-3 rounded-xl border border-gray-800 space-y-1.5">
          <div class="font-bold text-gray-200 border-b border-gray-700/60 pb-1">Bloque B: Quarterbacks</div>
          <div class="text-[11px]">
            <span class="text-gray-400">Home QB:</span> <b class="text-white">${bB.home ? bB.home.qb_name : '-'}</b>
            <div class="text-gray-500 font-mono text-[10px]">EPA: ${bB.home ? bB.home.metrics.epa_dropback : '-'} | CPOE: ${bB.home ? bB.home.metrics.cpoe + '%' : '-'} | Rtg: ${bB.home ? bB.home.metrics.passer_rating : '-'}</div>
            <div class="text-gray-400 text-[10px] italic">${bB.home ? bB.home.status_note : ''}</div>
          </div>
          <div class="text-[11px] pt-1 border-t border-gray-800">
            <span class="text-gray-400">Away QB:</span> <b class="text-white">${bB.away ? bB.away.qb_name : '-'}</b>
            <div class="text-gray-500 font-mono text-[10px]">EPA: ${bB.away ? bB.away.metrics.epa_dropback : '-'} | CPOE: ${bB.away ? bB.away.metrics.cpoe + '%' : '-'} | Rtg: ${bB.away ? bB.away.metrics.passer_rating : '-'}</div>
            <div class="text-gray-400 text-[10px] italic">${bB.away ? bB.away.status_note : ''}</div>
          </div>
        </div>

        <!-- Bloque C & D: Matchup, Trincheras & Lesiones -->
        <div class="bg-gray-850 p-3 rounded-xl border border-gray-800 space-y-1.5">
          <div class="font-bold text-gray-200 border-b border-gray-700/60 pb-1">Bloques C & D: Colisión & Lesiones</div>
          <div class="flex justify-between text-[11px] text-gray-400">
            <span>Fuerza Choque (H/A):</span>
            <span class="font-mono text-cyan-300 font-bold">${bC.home_off_vs_away_def ? bC.home_off_vs_away_def.composite_offensive_strength : '-'} pts vs ${bC.away_off_vs_home_def ? bC.away_off_vs_home_def.composite_offensive_strength : '-'} pts</span>
          </div>
          <div class="flex justify-between text-[11px] text-gray-400">
            <span>Protección OL vs Presión DL:</span>
            <span class="font-mono text-white">${bC.home_off_vs_away_def ? bC.home_off_vs_away_def.trench_protection_score : '-'} / 100</span>
          </div>
          <div class="text-[11px] pt-1 border-t border-gray-800">
            <div class="text-gray-400">Reporte Lesiones Oficial:</div>
            <div class="text-[10px] text-amber-300">H: OL: ${bD.home ? bD.home.ol_health.ol_status : '-'} | QB: ${bD.home ? bD.home.qb_health.status : '-'}</div>
            <div class="text-[10px] text-amber-300">A: OL: ${bD.away ? bD.away.ol_health.ol_status : '-'} | QB: ${bD.away ? bD.away.qb_health.status : '-'}</div>
          </div>
        </div>

      </div>
    </div>
  `;

  return card;
}

function filterDecisions(filter) {
  currentFilter = filter;
  document.querySelectorAll('.btn-filter').forEach(b => {
    b.className = 'btn-filter px-3 py-1 text-xs rounded-lg bg-gray-800 text-gray-400 hover:bg-gray-700';
  });
  event.target.className = 'btn-filter px-3 py-1 text-xs rounded-lg bg-cyan-500 text-black font-bold';
  if (fullReport) renderDashboard(fullReport);
}

async function triggerPipelineRun() {
  const btn = document.getElementById('btn-sync-pipeline');
  btn.disabled = true;
  btn.innerHTML = `<span>⏳</span> Ejecutando...`;
  try {
    const res = await fetch('/api/run_pipeline', { method: 'POST' });
    const json = await res.json();
    await loadReportData();
  } catch (e) {
    console.error(e);
    await loadReportData();
  } finally {
    btn.disabled = false;
    btn.innerHTML = `<span>🔄</span> Re-ejecutar Pipeline`;
  }
}

document.addEventListener('DOMContentLoaded', () => {
  loadReportData();
  startAutoRefreshTimer();
});
