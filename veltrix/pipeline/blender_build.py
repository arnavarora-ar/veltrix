"""Build the six VELTRIX service objects in Blender, then export GLB.

Run headless:
    blender -b -P blender_build.py -- ../models/veltrix-services.glb
or open Blender > Scripting > open this file > Run Script.

It clears the scene, creates one object per service from service_geometry.py
(same names + material names the website expects), adds smooth shading and a
Bevel/Weighted-Normal pass for nicer highlights, and exports glTF Binary.
Refine the objects by hand afterwards if you like — just keep object names
(brand_identity, social_media, …) and material names (accent, chrome, glass,
glow) unchanged, then re-export to the same path.
"""
import os, sys
import bpy

HERE = os.path.dirname(os.path.abspath(__file__)) if "__file__" in dir() else bpy.path.abspath("//")
sys.path.insert(0, HERE)
from service_geometry import SERVICES, MATERIALS  # noqa: E402  (needs numpy; bundled with Blender)

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
OUT = os.path.abspath(argv[0]) if argv else os.path.join(HERE, "..", "models", "veltrix-services.glb")

bpy.ops.wm.read_factory_settings(use_empty=True)


def material(name):
    if name in bpy.data.materials:
        return bpy.data.materials[name]
    rgba, metal, rough = MATERIALS[name]
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = m.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = rgba
    bsdf.inputs["Metallic"].default_value = metal
    bsdf.inputs["Roughness"].default_value = rough
    if rgba[3] < 1:
        bsdf.inputs["Alpha"].default_value = rgba[3]
        m.blend_method = "BLEND"
    if name == "glow":
        bsdf.inputs["Emission Color"].default_value = (1.0, 0.85, 0.6, 1.0)
        bsdf.inputs["Emission Strength"].default_value = 1.0
    return m


for col_idx, (name, build) in enumerate(SERVICES):
    verts, faces, uvs, mat_ids, mats = [], [], [], [], []
    for mat_name, p, n, u, idx in build():
        if mat_name not in mats:
            mats.append(mat_name)
        base = len(verts)
        verts += [tuple(v) for v in p]
        tri = idx.reshape(-1, 3)
        for t in tri:
            faces.append(tuple(int(k) + base for k in t))
            uvs.append([tuple(u[int(k)]) for k in t])
            mat_ids.append(mats.index(mat_name))

    # glTF is Y-up; Blender is Z-up. Convert (x, y, z) -> (x, -z, y).
    verts = [(x, -z, y) for x, y, z in verts]
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    uv = me.uv_layers.new(name="UVMap")
    for poly, tri_uv in zip(me.polygons, uvs):
        poly.material_index = mat_ids[poly.index]
        for li, (uu, vv) in zip(poly.loop_indices, tri_uv):
            uv.data[li].uv = (uu, 1 - vv)
    for m in mats:
        me.materials.append(material(m))
    me.validate(); me.update()
    bpy.ops.object.select_all(action="DESELECT") if bpy.context.object else None
    ob = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(ob)
    bpy.context.view_layer.objects.active = ob
    ob.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.remove_doubles(threshold=1e-5)
    bpy.ops.object.mode_set(mode="OBJECT")
    bpy.ops.object.shade_auto_smooth(angle=0.6) if hasattr(bpy.ops.object, "shade_auto_smooth") else bpy.ops.object.shade_smooth()
    ob.modifiers.new("WeightedNormal", "WEIGHTED_NORMAL")
    ob.location.x = col_idx * 2.0  # spread out for editing; the site positions them itself
    ob.select_set(False)

# Positions are reset on export so each object sits at its own origin.
for ob in bpy.data.objects:
    ob.location = (0, 0, 0)

os.makedirs(os.path.dirname(OUT), exist_ok=True)
bpy.ops.export_scene.gltf(filepath=OUT, export_format="GLB", export_apply=True,
                          export_yup=True, export_materials="EXPORT")
print("Exported", OUT)
