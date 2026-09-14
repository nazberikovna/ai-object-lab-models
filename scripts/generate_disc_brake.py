#!/usr/bin/env python3
"""Generate an original browser-ready educational disc-brake GLB.

The geometry is intentionally generic: it explains the main assemblies of a
ventilated automotive disc brake without representing a particular make or
engineering specification.
"""

from __future__ import annotations

import math
from pathlib import Path

import numpy as np
import trimesh


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "models" / "brake" / "disc-brake-educational.glb"


COLORS = {
    "rotor": (126, 132, 138, 255),
    "rotor_edge": (76, 81, 86, 255),
    "hub": (58, 62, 66, 255),
    "caliper": (148, 28, 33, 255),
    "caliper_dark": (88, 18, 22, 255),
    "pad": (47, 49, 51, 255),
    "pad_back": (166, 115, 45, 255),
    "bolt": (174, 178, 181, 255),
    "rubber": (26, 28, 30, 255),
}


def color(mesh: trimesh.Trimesh, rgba: tuple[int, int, int, int]) -> trimesh.Trimesh:
    mesh.visual = trimesh.visual.ColorVisuals(mesh=mesh, face_colors=rgba)
    return mesh


def annulus(outer: float, inner: float, height: float, sections: int = 160) -> trimesh.Trimesh:
    """Closed annular cylinder centered on the Z axis."""
    vertices: list[list[float]] = []
    faces: list[list[int]] = []
    for z in (-height / 2, height / 2):
        for radius in (outer, inner):
            for i in range(sections):
                a = 2 * math.pi * i / sections
                vertices.append([radius * math.cos(a), radius * math.sin(a), z])

    def idx(layer: int, radius_idx: int, i: int) -> int:
        return (layer * 2 + radius_idx) * sections + (i % sections)

    for i in range(sections):
        j = (i + 1) % sections
        # front and back ring faces
        faces += [
            [idx(1, 0, i), idx(1, 0, j), idx(1, 1, j)],
            [idx(1, 0, i), idx(1, 1, j), idx(1, 1, i)],
            [idx(0, 0, i), idx(0, 1, j), idx(0, 0, j)],
            [idx(0, 0, i), idx(0, 1, i), idx(0, 1, j)],
            # outer and inner cylindrical walls
            [idx(0, 0, i), idx(0, 0, j), idx(1, 0, j)],
            [idx(0, 0, i), idx(1, 0, j), idx(1, 0, i)],
            [idx(0, 1, i), idx(1, 1, j), idx(0, 1, j)],
            [idx(0, 1, i), idx(1, 1, i), idx(1, 1, j)],
        ]
    return trimesh.Trimesh(np.asarray(vertices), np.asarray(faces), process=True)


def box(extents, position, rgba, transform=None):
    mesh = trimesh.creation.box(extents=extents, transform=transform)
    mesh.apply_translation(position)
    return color(mesh, rgba)


def cylinder(radius, height, position, rgba, sections=64):
    mesh = trimesh.creation.cylinder(radius=radius, height=height, sections=sections)
    mesh.apply_translation(position)
    return color(mesh, rgba)


def add(scene: trimesh.Scene, name: str, mesh: trimesh.Trimesh) -> None:
    scene.add_geometry(mesh, node_name=name, geom_name=name)


def build() -> trimesh.Scene:
    scene = trimesh.Scene()

    # Ventilated rotor: two friction rings and visible radial vanes.
    front = color(annulus(2.15, 1.02, 0.13), COLORS["rotor"])
    front.apply_translation([0, 0, 0.22])
    add(scene, "rotor_front_friction_ring", front)

    rear = color(annulus(2.15, 1.02, 0.13), COLORS["rotor"])
    rear.apply_translation([0, 0, -0.22])
    add(scene, "rotor_rear_friction_ring", rear)

    for i in range(28):
        angle = 2 * math.pi * i / 28
        vane = trimesh.creation.box(extents=[0.72, 0.075, 0.28])
        vane.apply_translation([1.48, 0, 0])
        vane.apply_transform(trimesh.transformations.rotation_matrix(angle, [0, 0, 1]))
        color(vane, COLORS["rotor_edge"])
        add(scene, f"vent_vane_{i:02d}", vane)

    # Bell/hub, studs and dark recesses that read as lug holes.
    add(scene, "hub_bell", color(annulus(1.10, 0.34, 0.64), COLORS["hub"]))
    add(scene, "axle_opening", cylinder(0.33, 0.67, [0, 0, 0], COLORS["rubber"]))
    for i in range(5):
        a = 2 * math.pi * i / 5 + math.pi / 2
        x, y = 0.71 * math.cos(a), 0.71 * math.sin(a)
        add(scene, f"wheel_stud_{i+1}", cylinder(0.09, 0.88, [x, y, 0], COLORS["bolt"], 32))
        add(scene, f"lug_recess_{i+1}", cylinder(0.16, 0.66, [x, y, 0], COLORS["rubber"], 32))

    # Caliper body constructed from overlapping rounded-looking capsules and boxes.
    caliper_parts = []
    capsule = trimesh.creation.capsule(radius=0.48, height=1.38, count=[24, 24])
    capsule.apply_transform(trimesh.transformations.rotation_matrix(math.pi / 2, [1, 0, 0]))
    capsule.apply_translation([-1.65, 0, 0])
    caliper_parts.append(capsule)
    bridge = box([0.82, 1.82, 0.76], [-1.47, 0, 0], COLORS["caliper"])
    caliper_parts.append(bridge)
    outer_lobe = trimesh.creation.capsule(radius=0.31, height=1.20, count=[20, 20])
    outer_lobe.apply_transform(trimesh.transformations.rotation_matrix(math.pi / 2, [1, 0, 0]))
    outer_lobe.apply_translation([-1.18, 0, 0.42])
    caliper_parts.append(outer_lobe)
    caliper = trimesh.util.concatenate(caliper_parts)
    color(caliper, COLORS["caliper"])
    add(scene, "caliper_body", caliper)

    # Pad backing plates and friction material on either side of the rotor.
    for side, z in (("outer", 0.43), ("inner", -0.43)):
        add(scene, f"{side}_pad_backing", box([0.46, 1.33, 0.10], [-1.44, 0, z], COLORS["pad_back"]))
        add(scene, f"{side}_friction_pad", box([0.39, 1.18, 0.12], [-1.30, 0, z - math.copysign(0.10, z)], COLORS["pad"]))

    # Guide pins, piston caps and hose stub.
    for y in (-0.61, 0.61):
        pin = trimesh.creation.cylinder(radius=0.095, height=0.96, sections=32)
        pin.apply_transform(trimesh.transformations.rotation_matrix(math.pi / 2, [0, 1, 0]))
        pin.apply_translation([-1.53, y, 0])
        color(pin, COLORS["bolt"])
        add(scene, f"guide_pin_{'top' if y > 0 else 'bottom'}", pin)

    for y in (-0.36, 0.36):
        piston = trimesh.creation.cylinder(radius=0.25, height=0.15, sections=48)
        piston.apply_translation([-1.14, y, -0.48])
        color(piston, COLORS["caliper_dark"])
        add(scene, f"hydraulic_piston_{'top' if y > 0 else 'bottom'}", piston)

    hose = trimesh.creation.cylinder(radius=0.075, height=0.72, sections=24)
    hose.apply_transform(trimesh.transformations.rotation_matrix(math.pi / 2, [1, 0, 0]))
    hose.apply_translation([-1.74, 1.13, -0.20])
    color(hose, COLORS["rubber"])
    add(scene, "brake_hose_connection", hose)

    # Small face details improve scale without pretending to exact engineering data.
    for ring_r, count, phase in ((1.88, 18, 0.0), (1.58, 14, 0.12)):
        for i in range(count):
            a = 2 * math.pi * i / count + phase
            x, y = ring_r * math.cos(a), ring_r * math.sin(a)
            marker = cylinder(0.045, 0.012, [x, y, 0.292], COLORS["rotor_edge"], 16)
            add(scene, f"surface_mark_{ring_r}_{i:02d}", marker)

    return scene


def main() -> None:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    scene = build()
    scene.export(OUTPUT)
    print(f"Wrote {OUTPUT} ({OUTPUT.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()
