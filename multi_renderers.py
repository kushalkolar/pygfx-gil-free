# works but requires small tweaks to pygfx renderer so that the renders are flushed with alpha blending
# run with PYTHON_GIL=0

from concurrent.futures import ThreadPoolExecutor, wait

import numpy as np
import pygfx as gfx
from pygfx.renderers.wgpu import select_adapter
import wgpu
from rendercanvas.auto import RenderCanvas, loop


select_adapter(wgpu.gpu.enumerate_adapters_sync()[1])

canvas = RenderCanvas(
    size=(2000, 2000),
    title="$fps",
    update_mode="continuous",
    max_fps=999.0,
    vsync=False,
)


renderers = list()
datas = list()
textures = list()
scenes = list()
cameras = list()

w, h = 2000, 2000

rects = list()
for row in range(4):
    for col in range(4):
        rects.append((col * w / 4, row * h / 4, w / 4, h / 4))

rngs = [np.random.default_rng(seed=i) for i in range(16)]

for i in range(16):
    renderers.append(gfx.renderers.WgpuRenderer(canvas))

    data = np.zeros((512, 512), dtype=np.uint8)
    data[:] = 255
    datas.append(data)

    tex = gfx.Texture(data, dim=2)
    textures.append(tex)

    scene = gfx.Scene()
    scene.add(
        gfx.Image(
            gfx.Geometry(grid=tex),
            gfx.ImageBasicMaterial(clim=(0, 255)),
        )
    )
    scenes.append(scene)

    cam = gfx.OrthographicCamera(512, 512)
    cam.show_object(scene)
    cameras.append(cam)


pool = ThreadPoolExecutor(max_workers=16)


def update_and_render(i):
    """Worker thread: update data, then render to internal texture (no flush)."""
    datas[i][:] = rngs[i].integers(0, 256, size=(512, 512), dtype=np.uint8)
    textures[i].update_range((0, 0, 0), textures[i].size)
    renderers[i].render(scenes[i], cameras[i], rect=rects[i], flush=False, clear=True)


def animate():
    futures = [pool.submit(update_and_render, i) for i in range(16)]
    wait(futures)

    for r in renderers:
        r.flush(blend=True)


canvas.request_draw(animate)
loop.run()
