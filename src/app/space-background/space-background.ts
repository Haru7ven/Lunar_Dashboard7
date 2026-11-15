import {
  AfterViewInit,
  Component,
  ElementRef,
  OnDestroy,
  ViewChild
} from '@angular/core';

import * as THREE from 'three';

@Component({
  selector: 'app-space-background',
  standalone: true,
  imports: [],
  templateUrl: './space-background.html',
  styleUrl: './space-background.css'
})
export class SpaceBackground implements AfterViewInit, OnDestroy {

  @ViewChild('spaceContainer')
  spaceContainer!: ElementRef<HTMLDivElement>;

  private scene!: THREE.Scene;
  private camera!: THREE.PerspectiveCamera;
  private renderer!: THREE.WebGLRenderer;
  private animationFrameId = 0;
  private nebulaMaterial!: THREE.ShaderMaterial;
  private starMaterial!: THREE.ShaderMaterial;
  private starfieldMaterial!: THREE.ShaderMaterial;


  ngAfterViewInit(): void {
    this.initializeSpace();
  }

  private initializeSpace(): void {

    const container = this.spaceContainer.nativeElement;

    this.scene = new THREE.Scene();

    this.camera = new THREE.PerspectiveCamera(
      60,
      container.clientWidth / container.clientHeight,
      0.1,
      1000
    );

    this.camera.position.z = 5;

    this.renderer = new THREE.WebGLRenderer({
      alpha: true,
      antialias: true
    });

    this.renderer.setSize(
      container.clientWidth,
      container.clientHeight
    );

    this.renderer.setPixelRatio(
      Math.min(window.devicePixelRatio, 2)
    );

    this.renderer.setClearColor(0x000000, 0);

    container.appendChild(this.renderer.domElement);

    this.createStarfield();

    this.createNebula();
    
    this.animate();
  }

  private createNebula(): void {

  const geometry = new THREE.PlaneGeometry(18, 12);

  this.nebulaMaterial = new THREE.ShaderMaterial({

    transparent: true,
    depthWrite: false,

    uniforms: {
      uTime: { value: 0 }
    },

    vertexShader: `
      varying vec2 vUv;

      void main() {
        vUv = uv;

        gl_Position = projectionMatrix *
          modelViewMatrix *
          vec4(position, 1.0);
      }
    `,

    fragmentShader: `
      uniform float uTime;
      varying vec2 vUv;

      float random(vec2 p) {
        return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453);
      }

      float noise(vec2 p) {
        vec2 i = floor(p);
        vec2 f = fract(p);

        f = f * f * (3.0 - 2.0 * f);

        return mix(
          mix(random(i), random(i + vec2(1.0, 0.0)), f.x),
          mix(random(i + vec2(0.0, 1.0)), random(i + vec2(1.0, 1.0)), f.x),
          f.y
        );
      }

      void main() {

        vec2 uv = vUv;

        float time = uTime * 0.025;

        float n1 = noise(uv * 4.0 + time);
        float n2 = noise(uv * 8.0 - time * 0.7);
        float n3 = noise(uv * 16.0 + time * 0.4);

        float cloud = n1 * 0.55 + n2 * 0.3 + n3 * 0.15;

        vec3 purple = vec3(0.20, 0.06, 0.48);
        vec3 magenta = vec3(0.55, 0.08, 0.38);
        vec3 cyan = vec3(0.03, 0.30, 0.48);

        vec3 color = mix(purple, magenta, smoothstep(0.35, 0.75, cloud));

        color = mix(color, cyan, smoothstep(0.65, 0.95, n2));

        float density = smoothstep(0.38, 0.82, cloud);

        float edge = smoothstep(0.0, 0.25, uv.x) *
                     smoothstep(0.0, 0.25, 1.0 - uv.x) *
                     smoothstep(0.0, 0.25, uv.y) *
                     smoothstep(0.0, 0.25, 1.0 - uv.y);

        float alpha = density * edge * 0.55;

        gl_FragColor = vec4(color, alpha);
  }
    `
  });

  const nebula = new THREE.Mesh(geometry, this.nebulaMaterial);

  nebula.position.z = -8;

  this.scene.add(nebula);
}

  private createStarfield(): void {

  const starCount = 3500;

  const positions = new Float32Array(starCount * 3);
  const colors = new Float32Array(starCount * 3);
  const phases = new Float32Array(starCount);
  const sizes = new Float32Array(starCount);

  const color = new THREE.Color();

  for (let i = 0; i < starCount; i++) {

    const i3 = i * 3;
    phases[i] = Math.random() * Math.PI * 2;
    sizes[i] = 0.7 + Math.random() * 1.5;

    positions[i3] = (Math.random() - 0.5) * 100;
    positions[i3 + 1] = (Math.random() - 0.5) * 60;
    positions[i3 + 2] = (Math.random() - 0.5) * 80;

    const temperature = Math.random();

    if (temperature < 0.65) {
      color.set(0xffffff);
    } else if (temperature < 0.85) {
      color.set(0x9fc5ff);
    } else {
      color.set(0xffd6b0);
    }

    colors[i3] = color.r;
    colors[i3 + 1] = color.g;
    colors[i3 + 2] = color.b;
  }

  const geometry = new THREE.BufferGeometry();

  geometry.setAttribute(
    'position',
    new THREE.BufferAttribute(positions, 3)
  );

  geometry.setAttribute(
    'color',
    new THREE.BufferAttribute(colors, 3)
  );

  geometry.setAttribute(
    'phase',
    new THREE.BufferAttribute(phases, 1)
  );

  geometry.setAttribute(
    'size',
    new THREE.BufferAttribute(sizes, 1)
  );

  const material = new THREE.ShaderMaterial({
  transparent: true,
  depthWrite: false,

  uniforms: {
    uTime: { value: 0 }
  },

  vertexShader: `
    attribute float phase;
    attribute vec3 color;
    attribute float size;

    varying vec3 vColor;
    varying float vTwinkle;

    uniform float uTime;

    void main() {
      vColor = color;

      float twinkle = 0.88 + 0.12 * sin(uTime * 2.0 + phase);
      vTwinkle = twinkle;

      vec4 mvPosition = modelViewMatrix * vec4(position, 1.0);

      gl_PointSize = size * twinkle;

      gl_Position = projectionMatrix * mvPosition;
    }
  `,

  fragmentShader: `
    varying vec3 vColor;
    varying float vTwinkle;

    void main() {
      gl_FragColor = vec4(vColor, vTwinkle);
    }
  `
});

this.starMaterial = material;

  const stars = new THREE.Points(geometry, material);

  this.scene.add(stars);
}

private animate = (): void => {

  this.animationFrameId = requestAnimationFrame(this.animate);

  this.nebulaMaterial.uniforms['uTime'].value += 0.01;

  this.starMaterial.uniforms['uTime'].value += 0.01;

  this.renderer.render(this.scene, this.camera);
};

  ngOnDestroy(): void {
  cancelAnimationFrame(this.animationFrameId);
  this.renderer?.dispose();
}
}