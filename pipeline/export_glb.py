"""Write models/veltrix-services.glb from service_geometry.py (no Blender needed).

Usage:  python3 export_glb.py [out_path]
"""
import json, struct, sys, os
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from service_geometry import SERVICES, MATERIALS

out = sys.argv[1] if len(sys.argv) > 1 else "veltrix-services.glb"

blob = bytearray()
gltf = {"asset": {"version": "2.0", "generator": "VELTRIX service_geometry.py"},
        "scene": 0, "scenes": [{"nodes": []}], "nodes": [], "meshes": [],
        "materials": [], "accessors": [], "bufferViews": [], "buffers": []}

mat_index = {}
for name, (rgba, metal, rough) in MATERIALS.items():
    m = {"name": name, "pbrMetallicRoughness": {"baseColorFactor": list(rgba),
         "metallicFactor": metal, "roughnessFactor": rough}}
    if rgba[3] < 1: m["alphaMode"] = "BLEND"
    if name == "glow": m["emissiveFactor"] = [1.0, 0.85, 0.6]
    mat_index[name] = len(gltf["materials"]); gltf["materials"].append(m)


def add(arr, target, comp, typ, minmax=False):
    while len(blob) % 4: blob.append(0)
    off = len(blob); data = arr.tobytes(); blob.extend(data)
    gltf["bufferViews"].append({"buffer": 0, "byteOffset": off, "byteLength": len(data), "target": target})
    acc = {"bufferView": len(gltf["bufferViews"]) - 1, "componentType": comp,
           "count": int(arr.shape[0]), "type": typ}
    if minmax:
        acc["min"] = arr.min(axis=0).tolist(); acc["max"] = arr.max(axis=0).tolist()
    gltf["accessors"].append(acc)
    return len(gltf["accessors"]) - 1


for i, (name, build) in enumerate(SERVICES):
    prims = []
    for mat, p, n, u, idx in build():
        prims.append({"attributes": {
            "POSITION": add(p.astype(np.float32), 34962, 5126, "VEC3", True),
            "NORMAL": add(n.astype(np.float32), 34962, 5126, "VEC3"),
            "TEXCOORD_0": add(u.astype(np.float32), 34962, 5126, "VEC2")},
            "indices": add(idx.astype(np.uint32), 34963, 5125, "SCALAR"),
            "material": mat_index[mat]})
    gltf["meshes"].append({"name": name, "primitives": prims})
    gltf["nodes"].append({"name": name, "mesh": i})
    gltf["scenes"][0]["nodes"].append(i)

while len(blob) % 4: blob.append(0)
gltf["buffers"].append({"byteLength": len(blob)})
js = json.dumps(gltf, separators=(",", ":")).encode()
while len(js) % 4: js += b" "
total = 12 + 8 + len(js) + 8 + len(blob)
with open(out, "wb") as f:
    f.write(struct.pack("<III", 0x46546C67, 2, total))
    f.write(struct.pack("<II", len(js), 0x4E4F534A)); f.write(js)
    f.write(struct.pack("<II", len(blob), 0x004E4942)); f.write(blob)
print(f"wrote {out}  {total/1024:.0f} KB  objects={len(SERVICES)}")
