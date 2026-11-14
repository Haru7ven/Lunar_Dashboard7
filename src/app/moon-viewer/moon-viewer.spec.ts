import { ComponentFixture, TestBed } from '@angular/core/testing';
import { MoonViewer } from './moon-viewer';

describe('MoonViewer', () => {
  let component: MoonViewer;
  let fixture: ComponentFixture<MoonViewer>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [MoonViewer],
    }).compileComponents();

    fixture = TestBed.createComponent(MoonViewer);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
