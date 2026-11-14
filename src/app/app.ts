import { Component, signal } from '@angular/core';
import { RouterOutlet } from '@angular/router';
import { MoonViewer } from './moon-viewer/moon-viewer';


@Component({
  imports: [RouterOutlet, MoonViewer],
  selector: 'app-root',
  styleUrl: './app.css',
  templateUrl: './app.html',
})
export class App {
  protected readonly title = signal('lunar-dashboard');
}
