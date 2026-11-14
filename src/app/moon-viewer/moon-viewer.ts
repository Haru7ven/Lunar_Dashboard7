import {
  Component,
  ElementRef,
  ViewChild,
  AfterViewInit,
  OnDestroy,
  ChangeDetectorRef,
} from '@angular/core';

import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';

@Component({
  selector: 'app-moon-viewer',
  standalone: true,
  templateUrl: './moon-viewer.html',
  styleUrl: './moon-viewer.css',
})
export class MoonViewer implements AfterViewInit, OnDestroy {
  @ViewChild('rendererContainer', { static: true })
  rendererContainer!: ElementRef<HTMLDivElement>;

  private scene!: THREE.Scene;
  private camera!: THREE.PerspectiveCamera;
  private renderer!: THREE.WebGLRenderer;
  private controls!: OrbitControls;
  private animationId = 0;
  private moonModel: THREE.Object3D | null = null;

  constructor(private readonly cdr: ChangeDetectorRef) {}

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
      container.clientWidth > 0 ? container.clientWidth / container.clientHeight : 1,
      0.1,
      1000,
    );

    this.camera.position.set(0, 0, 3.5);

    this.renderer = new THREE.WebGLRenderer({
      antialias: true,
      alpha: true,
      powerPreference: 'high-performance',
    });

    this.renderer.setClearColor(0x000000, 0);
    this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    this.renderer.setSize(container.clientWidth || 800, container.clientHeight || 450);

    container.appendChild(this.renderer.domElement);

    this.controls = new OrbitControls(this.camera, this.renderer.domElement);
    this.controls.enableDamping = true;
    this.controls.enablePan = false;
    this.controls.minDistance = 1.5;
    this.controls.maxDistance = 8;
    this.controls.rotateSpeed = 0.7;

    const sunlight = new THREE.DirectionalLight(0xffffff, 3);
    sunlight.position.set(5, 3, 5);
    this.scene.add(sunlight);

    const ambientLight = new THREE.AmbientLight(0x526080, 0.6);
    this.scene.add(ambientLight);

    const resizeObserver = new ResizeObserver(() => {
      const { clientWidth, clientHeight } = container;
      if (!clientWidth || !clientHeight) {
        return;
      }

      this.camera.aspect = clientWidth / clientHeight;
      this.camera.updateProjectionMatrix();
      this.renderer.setSize(clientWidth, clientHeight);
    });

    resizeObserver.observe(container);
    (this as any).resizeObserver = resizeObserver;
  }

  private loadMoon(): void {
    const loader = new GLTFLoader();

    loader.load(
      '/models/Moon_NASA_LRO_8k_Topo_Small.glb',
      (gltf) => {
        this.moonModel = gltf.scene;

        if (this.moonModel) {
          this.moonModel.scale.setScalar(1);
          this.scene.add(this.moonModel);
        }

        this.cdr.detectChanges();
      },
      (progress) => {
        if (progress.total > 0) {
          const percentage = Math.round((progress.loaded / progress.total) * 100);
          console.log(`Loading Moon: ${percentage}%`);
        }
      },
      (error) => {
        console.error('Could not load the NASA Moon model:', error);
      },
    );
  }

  private animate = (): void => {
    this.animationId = requestAnimationFrame(this.animate);

    if (this.moonModel) {
      this.moonModel.rotation.y += 0.0035;
    }

    this.controls.update();
    this.renderer.render(this.scene, this.camera);
  };

  ngOnDestroy(): void {
    cancelAnimationFrame(this.animationId);
    this.controls?.dispose();
    this.renderer?.dispose();

    const container = this.rendererContainer?.nativeElement;
    if (container && container.contains(this.renderer?.domElement)) {
      container.removeChild(this.renderer.domElement);
    }

    (this as any).resizeObserver?.disconnect?.();
  }
}
