# VELTRIX Creative Co. — 3D services site

```
index.html                      the site (Three.js r160 + GSAP 3.12 from CDN)
models/veltrix-services.glb     the six service objects (binary glTF)
models/veltrix-services.glb.txt same GLB as base64, used only if a host refuses .glb
pipeline/service_geometry.py    shared geometry for all six objects
pipeline/blender_build.py       builds the objects in Blender and exports the GLB
pipeline/export_glb.py          writes the GLB without Blender (pure Python + numpy)
```

## Run locally
GLTFLoader needs a web server (not file://):  `python3 -m http.server` then open http://localhost:8000

## Blender workflow
1. `blender -b -P pipeline/blender_build.py -- models/veltrix-services.glb`
   (or open the script in Blender's Scripting tab and press Run Script)
2. Refine the objects by hand: bevels, subdivision, sculpting, anything you like.
3. Keep the **object names** (`brand_identity`, `social_media`, `content_copy`,
   `web_design`, `performance_ads`, `strategy`) and **material names**
   (`accent`, `chrome`, `glass`, `glow`). The site finds objects and re-skins
   materials by name, and tints `accent` with each service's colour.
4. File > Export > glTF 2.0 (.glb) to `models/veltrix-services.glb`. Each object
   should sit at the origin, about 2 m tall, on y = 0.
5. If you deploy to a host that serves .glb (Vercel, Netlify, Cloudflare Pages
   all do), delete the `.txt` copy. Otherwise regenerate it:
   `base64 -w0 models/veltrix-services.glb > models/veltrix-services.glb.txt`

## Editing services
Edit the `SERVICES` array near the top of the first `<script>` in index.html:
name, accent colour, tagline, description and deliverables.

## Contact form
It isn't connected to a backend yet. On submit it builds a summary the visitor
can copy. Wire `form` submit to Formspree, Resend, a Supabase function, etc.
