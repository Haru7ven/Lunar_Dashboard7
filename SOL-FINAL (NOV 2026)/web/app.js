/**
 * SOL - CLPS Lunar Planner
 * Frontend Application: Plotly Interactive Dashboard
 * NASA Space Apps Challenge 2026
 */

// Plotly Dark Theme Default Configuration
const THEME = {
  paper_bgcolor: '#1a1a24',
  plot_bgcolor: '#111116',
  font: {
    family: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
    color: '#eee',
    size: 12
  },
  margin: { l: 55, r: 25, t: 45, b: 45 },
  hovermode: 'x unified'
};

const siteSelect = document.getElementById('site-select');
const infoBar = document.getElementById('info-bar');
const kpiContainer = document.getElementById('kpi-container');
const corsAlert = document.getElementById('cors-alert');

async function loadData(jsonFile) {
  try {
    corsAlert.style.display = 'none';
    infoBar.innerHTML = `<em>A transferir ${jsonFile}...</em>`;

    const response = await fetch(jsonFile);
    if (!response.ok) {
      throw new Error(`HTTP ${response.status} ao carregar ${jsonFile}`);
    }

    const D = await response.json();
    renderDashboard(D);
  } catch (err) {
    console.error('Erro ao carregar dados:', err);
    corsAlert.style.display = 'block';
    infoBar.innerHTML = `<span style="color:#ff5252">Erro ao carregar <strong>${jsonFile}</strong>. Verifique o servidor local (python -m http.server 8000).</span>`;
  }
}

function renderDashboard(D) {
  const site = D.site;
  const S = D.stats;
  // Compatibilidade com estrutura aninhada (time_series) ou direta
  const ts = D.time_series || D;

  // 1. Barra de Informacoes
  const t0 = ts.t[0];
  const tEnd = ts.t[ts.t.length - 1];
  const groundAlt = site.ground_alt !== undefined ? site.ground_alt : (site.alt - (site.mast || 0));
  
  infoBar.innerHTML = `
    <span><strong>Local:</strong> Lat ${site.lat.toFixed(2)}&deg; | Lon ${site.lon.toFixed(2)}&deg; E</span>
    <span>&bull;</span>
    <span><strong>Altitude:</strong> ${site.alt.toFixed(0)} m (Solo: ${groundAlt.toFixed(0)} m + Mastro: ${site.mast} m)</span>
    <span>&bull;</span>
    <span><strong>Janela:</strong> ${t0.slice(0, 10)} a ${tEnd.slice(0, 10)} (${ts.t.length} &eacute;pocas, dt=30min)</span>
  `;

  // 2. Cartoes KPI
  const kpis = [
    { label: 'Iluminação Solar', val: `${S.sun_pct.toFixed(1)}%`, cls: '' },
    { label: 'Visibilidade da Terra (DTE)', val: `${S.earth_pct.toFixed(1)}%`, cls: 'blue' },
    { label: 'Sol + Terra Simultâneos', val: `${S.both_pct.toFixed(1)}%`, cls: 'green' },
    { label: 'Maior Noite / Sombra', val: `${S.max_dark_h.toFixed(1)} h`, cls: '' },
    { label: 'Maior Blecaute DTE', val: `${S.max_noearth_h.toFixed(1)} h`, cls: 'blue' }
  ];

  kpiContainer.innerHTML = kpis.map(k => `
    <div class="kpi-card ${k.cls}">
      <span class="label">${k.label}</span>
      <span class="val">${k.val}</span>
    </div>
  `).join('');

  // 3. Mapa de Calor (DEM LOLA)
  if (D.dem && D.mx && D.my) {
    Plotly.newPlot('plot-map', [
      {
        type: 'heatmap',
        x: D.mx,
        y: D.my,
        z: D.dem,
        colorscale: 'Cividis',
        colorbar: { title: 'Elevação (m)', thickness: 14 }
      },
      {
        type: 'scatter',
        x: [site.x],
        y: [site.y],
        mode: 'markers+text',
        name: 'Local de Aterragem',
        text: ['Alvo CLPS'],
        textposition: 'top right',
        marker: { color: '#ff3333', size: 12, symbol: 'cross' }
      }
    ], {
      ...THEME,
      title: 'Topografia Polar Lunar (LOLA 20m/px)',
      xaxis: { title: 'X Estereográfico (km)' },
      yaxis: { title: 'Y Estereográfico (km)', scaleanchor: 'x' }
    }, { responsive: true });
  }

  // 4. Sky Plot (Projecao Polar do Ceu Local)
  const horR = D.hor.map(v => 90.0 - v);
  const sunR = ts.sun_el.map(v => 90.0 - v);
  const earR = ts.ear_el.map(v => 90.0 - v);

  Plotly.newPlot('plot-sky', [
    {
      type: 'scatterpolar',
      mode: 'lines',
      r: horR,
      theta: D.az,
      fill: 'toself',
      fillcolor: 'rgba(50, 60, 80, 0.4)',
      line: { color: '#8ab4ff', width: 2 },
      name: 'Perfil do Horizonte (LOLA)'
    },
    {
      type: 'scatterpolar',
      mode: 'markers',
      r: sunR,
      theta: ts.sun_az,
      marker: { color: '#f5b700', size: 4, opacity: 0.8 },
      name: 'Trajetória do Sol'
    },
    {
      type: 'scatterpolar',
      mode: 'markers',
      r: earR,
      theta: ts.ear_az,
      marker: { color: '#4da3ff', size: 5, opacity: 0.9 },
      name: 'Trajetória da Terra'
    }
  ], {
    ...THEME,
    title: 'Projeção Celeste Polar (Centro = Zénite)',
    polar: {
      bgcolor: '#111116',
      angularaxis: { direction: 'clockwise', rotation: 90, color: '#888' },
      radialaxis: {
        range: [0, 95],
        tickvals: [0, 30, 60, 90],
        ticktext: ['90°', '60°', '30°', '0° (Horiz.)'],
        color: '#888'
      }
    }
  }, { responsive: true });

  // 5. Grafico de Elevacao do Sol (com preenchimento tozeroy / tonexty conforme especificado)
  // Requisito: "preencher a área acima do horizonte de amarelo ('Sol Visível') e a área abaixo de cinza escuro ('Sombra')"
  Plotly.newPlot('plot-sun', [
    {
      x: ts.t,
      y: ts.hz_s,
      mode: 'lines',
      name: 'Sombra (Terreno Oclusor)',
      line: { color: '#666', dash: 'dash', width: 1.5 },
      fill: 'tozeroy',
      fillcolor: 'rgba(35, 35, 45, 0.85)'
    },
    {
      x: ts.t,
      y: ts.sun_el,
      mode: 'lines',
      name: 'Sol Visível (Área Iluminada)',
      line: { color: '#f5b700', width: 2.5 },
      fill: 'tonexty',
      fillcolor: 'rgba(245, 183, 0, 0.35)'
    }
  ], {
    ...THEME,
    title: 'Elevação Solar vs. Horizonte Local',
    yaxis: { title: 'Elevação (°)', zeroline: true, zerolinecolor: '#333' },
    xaxis: { title: 'Data/Hora (UTC)' },
    legend: { orientation: 'h', y: -0.2 }
  }, { responsive: true });

  // 6. Grafico de Elevacao da Terra (DTE)
  Plotly.newPlot('plot-ear', [
    {
      x: ts.t,
      y: ts.hz_e,
      mode: 'lines',
      name: 'Sombra (Oclusão Topográfica)',
      line: { color: '#666', dash: 'dash', width: 1.5 },
      fill: 'tozeroy',
      fillcolor: 'rgba(35, 35, 45, 0.85)'
    },
    {
      x: ts.t,
      y: ts.ear_el,
      mode: 'lines',
      name: 'Terra Visível (Linha de Visada DTE)',
      line: { color: '#4da3ff', width: 2.5 },
      fill: 'tonexty',
      fillcolor: 'rgba(77, 163, 255, 0.35)'
    }
  ], {
    ...THEME,
    title: 'Elevação da Terra (DTE) vs. Horizonte Local',
    yaxis: { title: 'Elevação (°)', zeroline: true, zerolinecolor: '#333' },
    xaxis: { title: 'Data/Hora (UTC)' },
    legend: { orientation: 'h', y: -0.2 }
  }, { responsive: true });

  // 7. Faixa de Visibilidade Contínua (Timeline Heatmap)
  const zVis = [
    ts.sun_vis,
    ts.ear_vis,
    ts.sun_vis.map((v, i) => (v && ts.ear_vis[i]) ? 1 : 0)
  ];

  Plotly.newPlot('plot-vis', [
    {
      type: 'heatmap',
      x: ts.t,
      y: ['Luz Solar', 'Terra (DTE)', 'Janela Conjunta'],
      z: zVis,
      colorscale: [
        [0, '#1a1a24'],
        [1, '#2ecc71']
      ],
      showscale: false
    }
  ], {
    ...THEME,
    title: 'Janelas Operacionais de Missão (Verde = Ativo / Comunicação Estabelecida)',
    yaxis: { automargin: true },
    xaxis: { title: 'Linha Temporal da Missão (Passo 30m)' },
    height: 220
  }, { responsive: true });
}

// Event Listeners
siteSelect.addEventListener('change', (e) => {
  loadData(e.target.value);
});

// Carregamento inicial do Site A
window.addEventListener('DOMContentLoaded', () => {
  loadData(siteSelect.value);
});
