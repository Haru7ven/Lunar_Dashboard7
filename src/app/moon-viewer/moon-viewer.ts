
import {
  Component,
  ElementRef,
  ViewChild,
  AfterViewInit,
  OnDestroy,
  Output,
  EventEmitter
} from '@angular/core';

import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';

export interface LunarSiteSelection {
  latitude: number;
  longitude: number;
  uv: { u: number; v: number } | null;
  surfacePosition: {
    x: number;
    y: number;
    z: number;
  };
}

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

    @Output() siteSelected = new EventEmitter<LunarSiteSelection>();

  private raycaster = new THREE.Raycaster();
  private pointer = new THREE.Vector2();

  private moonModel!: THREE.Group;
  private moonCenterLocal = new THREE.Vector3();
  private moonRadius = 1;

  private siteMarker?: THREE.Mesh;
  private siteInfo!: HTMLDivElement;

  private pointerStart = new THREE.Vector2();

  private onCanvasPointerDown = (event: PointerEvent): void => {
    this.pointerStart.set(event.clientX, event.clientY);
  };

  private onCanvasPointerUp = (event: PointerEvent): void => {
    const movement = Math.hypot(
      event.clientX - this.pointerStart.x,
      event.clientY - this.pointerStart.y
    );

    // Ignore camera drags. Only process actual clicks.
    if (movement > 5 || !this.moonModel) return;

    const rect = this.renderer.domElement.getBoundingClientRect();

    this.pointer.x =
      ((event.clientX - rect.left) / rect.width) * 2 - 1;

    this.pointer.y =
      -((event.clientY - rect.top) / rect.height) * 2 + 1;

    this.raycaster.setFromCamera(this.pointer, this.camera);

    const intersections = this.raycaster.intersectObject(
      this.moonModel,
      true
    );

    if (!intersections.length) return;

    const hit = intersections[0];

    const localPosition = this.moonModel.worldToLocal(
      hit.point.clone()
    );

    const direction = localPosition
      .sub(this.moonCenterLocal)
      .normalize();

    // Initial spherical coordinate conversion.
    const latitude =
      THREE.MathUtils.radToDeg(
        Math.asin(THREE.MathUtils.clamp(direction.y, -1, 1))
      );

    const longitude =
      THREE.MathUtils.radToDeg(
        Math.atan2(direction.z, direction.x)
      );

    this.placeSiteMarker(hit.point, hit.face?.normal, hit.object);

    const selection: LunarSiteSelection = {
      latitude,
      longitude,
      uv: hit.uv
        ? { u: hit.uv.x, v: hit.uv.y }
        : null,
      surfacePosition: {
        x: hit.point.x,
        y: hit.point.y,
        z: hit.point.z
      }
    };

    this.siteInfo.innerHTML = `
      <div style="color:#8bd5ff;font-size:10px;letter-spacing:2px">
        SELECTED LUNAR SITE
      </div>
      <div style="margin-top:8px;font-size:14px">
        LAT: ${latitude.toFixed(3)}°
      </div>
      <div style="font-size:14px">
        LON: ${longitude.toFixed(3)}°
      </div>
      <div style="margin-top:6px;color:#9ba9bd;font-size:10px">
        SURFACE INTERSECTION CONFIRMED
      </div>
    `;

    console.log('NEW LUNAR SITE:', selection);

    this.siteSelected.emit(selection);
  };

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

    this.renderer.setSize(
      container.clientWidth,
      container.clientHeight
    );

    container.appendChild(this.renderer.domElement);

        container.style.position = 'relative';

    this.siteInfo = document.createElement('div');

    Object.assign(this.siteInfo.style, {
      position: 'absolute',
      top: '15px',
      left: '15px',
      padding: '12px 16px',
      background: 'rgba(5, 12, 25, 0.88)',
      border: '1px solid rgba(100, 180, 255, 0.35)',
      borderRadius: '6px',
      color: '#ffffff',
      fontFamily: 'monospace',
      zIndex: '10',
      pointerEvents: 'none',
      minWidth: '190px',
      fontSize: '12px'
    });

    this.siteInfo.textContent = 'SELECT A POINT ON THE MOON';

    container.appendChild(this.siteInfo);

    this.controls = new OrbitControls(
      this.camera,
      this.renderer.domElement
    );

    this.controls.enableDamping = true;
        this.renderer.domElement.style.cursor = 'crosshair';

    this.renderer.domElement.addEventListener(
      'pointerdown',
      this.onCanvasPointerDown
    );

    this.renderer.domElement.addEventListener(
      'pointerup',
      this.onCanvasPointerUp
    );
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

        console.log('GLTF ASSET METADATA:', gltf.asset);
        console.log('MOON SCENE METADATA:', moon.userData);

        moon.updateMatrixWorld(true);

        const box = new THREE.Box3().setFromObject(moon);

        const center = new THREE.Vector3();
        const size = new THREE.Vector3();

        box.getCenter(center);
        box.getSize(size);

        const sphere = new THREE.Sphere();
        box.getBoundingSphere(sphere);

        let meshCount = 0;

        moon.traverse((object) => {
          if (object instanceof THREE.Mesh) {
            meshCount++;

            const geometry = object.geometry;
            const material = object.material as THREE.MeshStandardMaterial;

            geometry.computeBoundingBox();

            console.log('MESH METADATA:', object.userData);
            console.log('--- SURFACE ANALYSIS ---');

            console.log('Position attribute:', geometry.attributes['position']);
            console.log('Normal attribute:', geometry.attributes['normal']);
            console.log('UV attribute:', geometry.attributes['uv']);

            console.log('Local geometry bounds:', geometry.boundingBox);

            console.log('Texture map:', material.map);
            console.log('Normal map:', material.normalMap);
            console.log('Displacement map:', material.displacementMap);

            if (material.map) {
              const image = material.map.image as HTMLImageElement | undefined;

              console.log(
                'Texture dimensions:',
                image?.width,
                image?.height
              );
            }
          }
        });

        console.log('--- MOON MODEL INSPECTION ---');
        console.log('Dimensions:', size);
        console.log('Geometric centre:', center);
        console.log('Bounding sphere radius:', sphere.radius);
        console.log('Number of meshes:', meshCount);
        console.log('Original rotation:', moon.rotation);
        console.log('Original position:', moon.position);

        moon.scale.setScalar(1);
moon.visible = true;

this.inspectModelCoordinates('TOPOGRAPHIC MOON', moon);
this.inspectCardinalAxes('TOPOGRAPHIC MOON', moon);

this.scene.add(moon);

moon.updateMatrixWorld(true);

this.moonModel = moon;

this.moonCenterLocal.copy(
  moon.worldToLocal(center.clone())
);

this.moonRadius = sphere.radius;

console.log('CLICKABLE MOON INITIALIZED');
console.log('Local centre:', this.moonCenterLocal);
console.log('Reference radius:', this.moonRadius);

        // this.loadGeographicGrid(moon);
      },

      (progress) => {
        if (progress.total > 0) {
          const percentage = Math.round(
            (progress.loaded / progress.total) * 100
          );

          console.log(`Loading Moon: ${percentage}%`);
        }
      },

      (error: unknown) => {
        console.error('Could not load the NASA Moon model:', error);
      }
    );
  }

  private loadGeographicGrid(moon: THREE.Group): void {
    const gridLoader = new GLTFLoader();

    gridLoader.load(
      '/models/Moon_NASA_LRO_15k_Grid_Small.glb',

      (gridGltf) => {
        const gridMoon = gridGltf.scene;

        gridMoon.updateMatrixWorld(true);

        const gridBox = new THREE.Box3().setFromObject(gridMoon);

        const gridCenter = new THREE.Vector3();
        const gridSize = new THREE.Vector3();

        gridBox.getCenter(gridCenter);
        gridBox.getSize(gridSize);

        console.log('--- NASA GRID MODEL ---');
        console.log('Asset metadata:', gridGltf.asset);
        console.log('GRID MODEL POSITION:', gridMoon.position);
        console.log('GRID MODEL ROTATION:', gridMoon.rotation);
        console.log('GRID MODEL SCALE:', gridMoon.scale);
        console.log('GRID MODEL CENTER:', gridCenter);
        console.log('GRID MODEL DIMENSIONS:', gridSize);

        gridMoon.traverse((object) => {
          if (object instanceof THREE.Mesh) {
            const material = object.material as THREE.MeshStandardMaterial;

            const image = material.map?.image as HTMLImageElement | undefined;

            console.log('Grid mesh:', object.name);
            console.log('Grid material:', material);

            console.log(
              'GRID TEXTURE DIMENSIONS:',
              image?.width,
              image?.height
            );
          }
        });

        // Display both models for geographic alignment inspection
        moon.visible = true;
        gridMoon.visible = true;

        // Slightly enlarge the grid to reduce z-fighting
        gridMoon.scale.setScalar(1.002);
        this.inspectModelCoordinates('GEOGRAPHIC GRID', gridMoon);
        this.scene.add(gridMoon);

        console.log('Both lunar models loaded successfully.');
      },

      undefined,

      (error: unknown) => {
        console.error('Could not load NASA grid model:', error);
      }
    );
   }
  
private inspectCardinalAxes(
  label: string,
  model: THREE.Group
): void {

  console.log(`===== ${label}: CARDINAL AXES =====`);

  const directions = [
    { name: '+X', vector: new THREE.Vector3(1, 0, 0) },
    { name: '-X', vector: new THREE.Vector3(-1, 0, 0) },
    { name: '+Y', vector: new THREE.Vector3(0, 1, 0) },
    { name: '-Y', vector: new THREE.Vector3(0, -1, 0) },
    { name: '+Z', vector: new THREE.Vector3(0, 0, 1) },
    { name: '-Z', vector: new THREE.Vector3(0, 0, -1) }
  ];

  model.updateMatrixWorld(true);

  model.traverse((object) => {

    if (!(object instanceof THREE.Mesh)) return;

    const positions = object.geometry.getAttribute('position') as THREE.BufferAttribute;

    const matrix = object.matrixWorld;

    for (const direction of directions) {

      let bestDot = -Infinity;
      let bestIndex = -1;

      for (let i = 0; i < positions.count; i++) {

        const point = new THREE.Vector3(
          positions.getX(i),
          positions.getY(i),
          positions.getZ(i)
        ).applyMatrix4(matrix).normalize();

        const dot = point.dot(direction.vector);

        if (dot > bestDot) {
          bestDot = dot;
          bestIndex = i;
        }
      }

      console.log(direction.name, {
        vertexIndex: bestIndex,
        alignment: bestDot
      });
    }
  });
}
  private inspectModelCoordinates(
    label: string,
    model: THREE.Group
  ): void {

    console.log(`===== ${label}: COORDINATE INSPECTION =====`);

    model.updateMatrixWorld(true);

    model.traverse((object) => {
      if (!(object instanceof THREE.Mesh)) {
        return;
      }

      const geometry = object.geometry;
      const positions = geometry.attributes['position'] as THREE.BufferAttribute;
      const uvs = geometry.attributes['uv'] as THREE.BufferAttribute;

      if (!positions || !uvs) {
        console.warn('Missing position or UV attributes:', object.name);
        return;
      }

      let minU = Infinity;
      let maxU = -Infinity;
      let minV = Infinity;
      let maxV = -Infinity;

      for (let i = 0; i < uvs.count; i++) {
        const u = uvs.getX(i);
        const v = uvs.getY(i);

        minU = Math.min(minU, u);
        maxU = Math.max(maxU, u);
        minV = Math.min(minV, v);
        maxV = Math.max(maxV, v);
      }

      console.log('Mesh:', object.name);
      console.log('Vertex count:', positions.count);
      console.log('UV count:', uvs.count);
      console.log('UV range:', { minU, maxU, minV, maxV });

      const targets = [
        { name: 'U=0.00, V=0.50', u: 0.00, v: 0.50 },
        { name: 'U=0.25, V=0.50', u: 0.25, v: 0.50 },
        { name: 'U=0.50, V=0.50', u: 0.50, v: 0.50 },
        { name: 'U=0.75, V=0.50', u: 0.75, v: 0.50 },
        { name: 'U=1.00, V=0.50', u: 1.00, v: 0.50 },
        { name: 'U=0.50, V=0.00', u: 0.50, v: 0.00 },
        { name: 'U=0.50, V=1.00', u: 0.50, v: 1.00 }
      ];

      for (const target of targets) {
        let bestIndex = -1;
        let bestDistance = Infinity;

        for (let i = 0; i < uvs.count; i++) {
          const du = uvs.getX(i) - target.u;
          const dv = uvs.getY(i) - target.v;
          const distance = du * du + dv * dv;

          if (distance < bestDistance) {
            bestDistance = distance;
            bestIndex = i;
          }
        }

        const localPosition = new THREE.Vector3(
          positions.getX(bestIndex),
          positions.getY(bestIndex),
          positions.getZ(bestIndex)
        );

        const worldPosition = localPosition.clone()
          .applyMatrix4(object.matrixWorld);

        console.log(target.name, {
          vertexIndex: bestIndex,
          actualUV: {
            u: uvs.getX(bestIndex),
            v: uvs.getY(bestIndex)
          },
          localPosition,
          worldPosition
        });
      }
    });
  }

    private placeSiteMarker(
    point: THREE.Vector3,
    faceNormal?: THREE.Vector3,
    hitObject?: THREE.Object3D
  ): void {

    if (this.siteMarker) {
      this.scene.remove(this.siteMarker);

      this.siteMarker.geometry.dispose();

      (this.siteMarker.material as THREE.Material).dispose();
    }

    const markerGeometry = new THREE.SphereGeometry(
      this.moonRadius * 0.012,
      20,
      20
    );

    const markerMaterial = new THREE.MeshBasicMaterial({
      color: 0xffa629,
      depthTest: true,
      depthWrite: false
    });

    this.siteMarker = new THREE.Mesh(
      markerGeometry,
      markerMaterial
    );

    const normal = faceNormal && hitObject
      ? faceNormal.clone().applyMatrix3(
          new THREE.Matrix3().getNormalMatrix(
            hitObject.matrixWorld
          )
        ).normalize()
      : point.clone().sub(this.moonCenterLocal).normalize();

    this.siteMarker.position.copy(
      point.clone().addScaledVector(
        normal,
        this.moonRadius * 0.004
      )
    );

    this.siteMarker.renderOrder = 10;

    this.scene.add(this.siteMarker);
  }

  private animate = (): void => {
    this.animationId = requestAnimationFrame(this.animate);

    this.controls.update();
    this.renderer.render(this.scene, this.camera);
  };

  ngOnDestroy(): void {
    cancelAnimationFrame(this.animationId);

        this.renderer?.domElement.removeEventListener(
      'pointerdown',
      this.onCanvasPointerDown
    );

    this.renderer?.domElement.removeEventListener(
      'pointerup',
      this.onCanvasPointerUp
    );

    this.siteMarker?.geometry.dispose();

    if (this.siteMarker) {
      (this.siteMarker.material as THREE.Material).dispose();
      this.scene.remove(this.siteMarker);
    }

    this.siteInfo?.remove();

    this.controls?.dispose();
    this.renderer?.dispose();

    this.renderer?.domElement.remove();
  }
}