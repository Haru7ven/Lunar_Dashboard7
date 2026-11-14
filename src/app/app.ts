import { AfterViewInit, Component, ElementRef, ViewChild } from '@angular/core';

declare const Plotly: any;

@Component({
  selector: 'app-root',
  standalone: true,
  templateUrl: './app.html',
  styleUrl: './app.css',
})
export class App implements AfterViewInit {
  @ViewChild('siteSelect') siteSelect!: ElementRef<HTMLSelectElement>;

  private readonly theme = {
    paper_bgcolor: '#1a1a24',
    plot_bgcolor: '#111116',
    font: {
      family: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
      color: '#eee',
      size: 12,
    },
    margin: { l: 55, r: 25, t: 45, b: 45 },
    hovermode: 'x unified',
  };

  ngAfterViewInit(): void {
    if (this.siteSelect) {
      this.loadData(this.siteSelect.nativeElement.value);
    }
  }

  onSiteChange(event: Event): void {
    const target = event.target as HTMLSelectElement;
    this.loadData(target.value);
  }

  private async loadData(jsonFile: string): Promise<void> {
    const corsAlert = document.getElementById('cors-alert') as HTMLElement | null;
    const infoBar = document.getElementById('info-bar') as HTMLElement | null;

    if (!corsAlert || !infoBar) {
      return;
    }

    try {
      corsAlert.style.display = 'none';
      infoBar.innerHTML = `<em>A transferir ${jsonFile}...</em>`;

      const response = await fetch(jsonFile, { cache: 'no-store' });
      if (!response.ok) {
        throw new Error(`HTTP ${response.status} ao carregar ${jsonFile}`);
      }

      const data = await response.json();
      this.renderDashboard(data);
    } catch (err) {
      console.error('Erro ao carregar dados:', err);
      corsAlert.style.display = 'block';
      infoBar.innerHTML = `<span style="color:#ff5252">Erro ao carregar <strong>${jsonFile}</strong>. Verifique o servidor local (python -m http.server 8000).</span>`;
    }
  }

  private renderDashboard(D: any): void {
    const site = D.site;
    const stats = D.stats;
    const timeSeries = D.time_series || D;

    const infoBar = document.getElementById('info-bar');
    const kpiContainer = document.getElementById('kpi-container');

    if (!infoBar || !kpiContainer) {
      return;
    }

    const t0 = timeSeries.t[0];
    const tEnd = timeSeries.t[timeSeries.t.length - 1];
    const groundAlt = site.ground_alt !== undefined ? site.ground_alt : site.alt - (site.mast || 0);

    infoBar.innerHTML = `
      <span><strong>Local:</strong> Lat ${site.lat.toFixed(2)}&deg; | Lon ${site.lon.toFixed(2)}&deg; E</span>
      <span>&bull;</span>
      <span><strong>Altitude:</strong> ${site.alt.toFixed(0)} m (Solo: ${groundAlt.toFixed(0)} m + Mastro: ${site.mast} m)</span>
      <span>&bull;</span>
      <span><strong>Janela:</strong> ${String(t0).slice(0, 10)} a ${String(tEnd).slice(0, 10)} (${timeSeries.t.length} &eacute;pocas, dt=30min)</span>
    `;

    const kpis = [
      { label: 'Iluminação Solar', value: `${stats.sun_pct.toFixed(1)}%`, cls: '' },
      { label: 'Visibilidade da Terra (DTE)', value: `${stats.earth_pct.toFixed(1)}%`, cls: 'blue' },
      { label: 'Sol + Terra Simultâneos', value: `${stats.both_pct.toFixed(1)}%`, cls: 'green' },
      { label: 'Maior Noite / Sombra', value: `${stats.max_dark_h.toFixed(1)} h`, cls: '' },
      { label: 'Maior Blecaute DTE', value: `${stats.max_noearth_h.toFixed(1)} h`, cls: 'blue' },
    ];

    kpiContainer.innerHTML = kpis
      .map(
        (kpi) => `
          <div class="kpi-card ${kpi.cls}">
            <span class="label">${kpi.label}</span>
            <span class="val">${kpi.value}</span>
          </div>
        `,
      )
      .join('');

    if (D.dem && D.mx && D.my) {
      Plotly.newPlot(
        'plot-map',
        [
          {
            type: 'heatmap',
            x: D.mx,
            y: D.my,
            z: D.dem,
            colorscale: 'Cividis',
            colorbar: { title: 'Elevação (m)', thickness: 14 },
          },
          {
            type: 'scatter',
            x: [site.x],
            y: [site.y],
            mode: 'markers+text',
            name: 'Local de Aterragem',
            text: ['Alvo CLPS'],
            textposition: 'top right',
            marker: { color: '#ff3333', size: 12, symbol: 'cross' },
          },
        ],
        {
          ...this.theme,
          title: 'Topografia Polar Lunar (LOLA 20m/px)',
          xaxis: { title: 'X Estereográfico (km)' },
          yaxis: { title: 'Y Estereográfico (km)', scaleanchor: 'x' },
        },
        { responsive: true },
      );
    }

    const horR = D.hor.map((v: number) => 90.0 - v);
    const sunR = timeSeries.sun_el.map((v: number) => 90.0 - v);
    const earR = timeSeries.ear_el.map((v: number) => 90.0 - v);

    Plotly.newPlot(
      'plot-sky',
      [
        {
          type: 'scatterpolar',
          mode: 'lines',
          r: horR,
          theta: D.az,
          fill: 'toself',
          fillcolor: 'rgba(50, 60, 80, 0.4)',
          line: { color: '#8ab4ff', width: 2 },
          name: 'Perfil do Horizonte (LOLA)',
        },
        {
          type: 'scatterpolar',
          mode: 'markers',
          r: sunR,
          theta: timeSeries.sun_az,
          marker: { color: '#f5b700', size: 4, opacity: 0.8 },
          name: 'Trajetória do Sol',
        },
        {
          type: 'scatterpolar',
          mode: 'markers',
          r: earR,
          theta: timeSeries.ear_az,
          marker: { color: '#4da3ff', size: 5, opacity: 0.9 },
          name: 'Trajetória da Terra',
        },
      ],
      {
        ...this.theme,
        title: 'Projeção Celeste Polar (Centro = Zénite)',
        polar: {
          bgcolor: '#111116',
          angularaxis: { direction: 'clockwise', rotation: 90, color: '#888' },
          radialaxis: {
            range: [0, 95],
            tickvals: [0, 30, 60, 90],
            ticktext: ['90°', '60°', '30°', '0° (Horiz.)'],
            color: '#888',
          },
        },
      },
      { responsive: true },
    );

    Plotly.newPlot(
      'plot-sun',
      [
        {
          x: timeSeries.t,
          y: timeSeries.hz_s,
          mode: 'lines',
          name: 'Sombra (Terreno Oclusor)',
          line: { color: '#666', dash: 'dash', width: 1.5 },
          fill: 'tozeroy',
          fillcolor: 'rgba(35, 35, 45, 0.85)',
        },
        {
          x: timeSeries.t,
          y: timeSeries.sun_el,
          mode: 'lines',
          name: 'Sol Visível (Área Iluminada)',
          line: { color: '#f5b700', width: 2.5 },
          fill: 'tonexty',
          fillcolor: 'rgba(245, 183, 0, 0.35)',
        },
      ],
      {
        ...this.theme,
        title: 'Elevação Solar vs. Horizonte Local',
        yaxis: { title: 'Elevação (°)', zeroline: true, zerolinecolor: '#333' },
        xaxis: { title: 'Data/Hora (UTC)' },
        legend: { orientation: 'h', y: -0.2 },
      },
      { responsive: true },
    );

    Plotly.newPlot(
      'plot-ear',
      [
        {
          x: timeSeries.t,
          y: timeSeries.hz_e,
          mode: 'lines',
          name: 'Sombra (Oclusão Topográfica)',
          line: { color: '#666', dash: 'dash', width: 1.5 },
          fill: 'tozeroy',
          fillcolor: 'rgba(35, 35, 45, 0.85)',
        },
        {
          x: timeSeries.t,
          y: timeSeries.ear_el,
          mode: 'lines',
          name: 'Terra Visível (Linha de Visada DTE)',
          line: { color: '#4da3ff', width: 2.5 },
          fill: 'tonexty',
          fillcolor: 'rgba(77, 163, 255, 0.35)',
        },
      ],
      {
        ...this.theme,
        title: 'Elevação da Terra (DTE) vs. Horizonte Local',
        yaxis: { title: 'Elevação (°)', zeroline: true, zerolinecolor: '#333' },
        xaxis: { title: 'Data/Hora (UTC)' },
        legend: { orientation: 'h', y: -0.2 },
      },
      { responsive: true },
    );

    const zVis = [
      timeSeries.sun_vis,
      timeSeries.ear_vis,
      timeSeries.sun_vis.map((value: number, index: number) => (value && timeSeries.ear_vis[index]) ? 1 : 0),
    ];

    Plotly.newPlot(
      'plot-vis',
      [
        {
          type: 'heatmap',
          x: timeSeries.t,
          y: ['Luz Solar', 'Terra (DTE)', 'Janela Conjunta'],
          z: zVis,
          colorscale: [
            [0, '#1a1a24'],
            [1, '#2ecc71'],
          ],
          showscale: false,
        },
      ],
      {
        ...this.theme,
        title: 'Janelas Operacionais de Missão (Verde = Ativo / Comunicação Estabelecida)',
        yaxis: { automargin: true },
        xaxis: { title: 'Linha Temporal da Missão (Passo 30m)' },
        height: 220,
      },
      { responsive: true },
    );
  }
}
