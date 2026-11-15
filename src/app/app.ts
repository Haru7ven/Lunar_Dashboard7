
import { Component, signal, OnInit } from '@angular/core';
import { RouterOutlet } from '@angular/router';
import { MoonViewer, type LunarSiteSelection } from './moon-viewer/moon-viewer';
import { SpaceBackground } from './space-background/space-background';

@Component({
  imports: [RouterOutlet, MoonViewer, SpaceBackground],
  selector: 'app-root',
  styleUrl: './app.css',
  templateUrl: './app.html',
})
export class App implements OnInit {
  protected readonly title = signal('lunar-dashboard');

  protected selectedDataset = signal('data_A.json');
  protected dataset = signal<any>(null);
  protected loading = signal(true);
  protected loadError = signal('');
  protected selectedPoint = signal<LunarSiteSelection | null>(null);

  ngOnInit(): void {
    this.loadDataset(this.selectedDataset());
  }

  async loadDataset(filename: string): Promise<void> {
    this.loading.set(true);
    this.loadError.set('');

    try {
      const response = await fetch(`/data/${filename}`);

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${filename}`);
      }

      const data = await response.json();

      this.dataset.set(data);
      this.selectedDataset.set(filename);

      console.log('LUNAROPS DATA LOADED:', filename, data);
      console.log('Available keys:', Object.keys(data));
      console.log('Site:', data.site);
      console.log('Statistics:', data.stats);
    } catch (error) {
      console.error('Dataset loading failed:', error);
      this.loadError.set('Unable to load dataset. Check the file location.');
    } finally {
      this.loading.set(false);
    }
  }

  onSiteChange(event: Event): void {
    const filename = (event.target as HTMLSelectElement).value;
    this.loadDataset(filename);
  }

  onSiteSelected(selection: LunarSiteSelection): void {
    this.selectedPoint.set(selection);
    console.log('DASHBOARD LOCATION UPDATED:', selection);
  }
}
