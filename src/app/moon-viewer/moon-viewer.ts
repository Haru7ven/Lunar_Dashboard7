import {
  Component,
  ElementRef,
  ViewChild,
  AfterViewInit,
  OnDestroy
} from '@angular/core';

import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';

@Component({
  selector: 'app-moon-viewer',
  standalone: true,
  templateUrl: './moon-viewer.html',
  styleUrl: './moon-viewer.css'
})
export class MoonViewer implements AfterViewInit, OnDestroy {

  @ViewChild('rendererContainer', { static: true })
  rendererContainer!: ElementRef<HTMLDivElement>;

  private scene!: THREE.Scene;
  private camera!: THREE.PerspectiveCamera;
  private renderer!: THREE.WebGLRenderer;
  private controls!: OrbitControls;
  private animationId = 0;

  ngAfterViewInit(): void {
    this.initializeScene();
    this.loadMoon();
    this.animate();
  }

  private initializeScene(): void {
    const container = this.rendererContainer.nativeElement;

    this.scene = new THREE.Scene();
    this.scene.background = null;

    this.camera = new THREE.PerspectiveCamera(
      45,
      container.clientWidth / container.clientHeight,
      0.1,
      1000
    );

    this.camera.position.set(0, 0, 3.5);

    this.renderer = new THREE.WebGLRenderer({
      antialias: true,
      alpha: true
    });
    
    this.renderer.setClearColor(0x000000, 0);
    this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    this.renderer.setSize(container.clientWidth, container.clientHeight);

    container.appendChild(this.renderer.domElement);

    this.controls = new OrbitControls(
      this.camera,
      this.renderer.domElement
    );

    this.controls.enableDamping = true;
    this.controls.minDistance = 1.5;
    this.controls.maxDistance = 8;

    const sunlight = new THREE.DirectionalLight(0xffffff, 3);
    sunlight.position.set(5, 3, 5);
    this.scene.add(sunlight);

    const ambientLight = new THREE.AmbientLight(0x526080, 0.6);
    this.scene.add(ambientLight);
  }

  private loadMoon(): void {
    const loader = new GLTFLoader();

    loader.load(
      '/models/Moon_NASA_LRO_8k_Topo_Small.glb',

      (gltf) => {
        const moon = gltf.scene;

        moon.scale.setScalar(1);
        this.scene.add(moon);
      },

      (progress) => {
        if (progress.total > 0) {
          const percentage = Math.round(
            (progress.loaded / progress.total) * 100
          );
          console.log(`Loading Moon: ${percentage}%`);
        }
      },

      (error) => {
        console.error('Could not load the NASA Moon model:', error);
      }
    );
  }

  private animate = (): void => {
    this.animationId = requestAnimationFrame(this.animate);

    this.controls.update();
    this.renderer.render(this.scene, this.camera);
  };

  ngOnDestroy(): void {
    cancelAnimationFrame(this.animationId);
    this.controls?.dispose();
    this.renderer?.dispose();
  }
}