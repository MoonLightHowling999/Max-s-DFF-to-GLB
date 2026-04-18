# runs inside blender --background, called by dff_to_glb.py
# env vars: DFF_INPUT, DFF_OUTPUT, DFF_ADDON

import os, sys, traceback, importlib, shutil, tempfile

def load_dragonff(path):
    import bpy
    path = os.path.abspath(path)
    name = os.path.basename(path)
    safe = name.replace("-", "_")
    if safe != name:
        tmp = tempfile.mkdtemp(prefix="dff_")
        shutil.copytree(path, os.path.join(tmp, safe))
        sys.path.insert(0, tmp)
    else:
        sys.path.insert(0, os.path.dirname(path))
    mod = importlib.import_module(safe)
    mod.register()

def setup_lights():
    import bpy
    n = 0
    for obj in bpy.data.objects:
        if obj.type != 'LIGHT' or obj.data.type != 'POINT':
            continue
        light = obj.data
        try:
            r = float(light.ext_2dfx.point_light_range)
        except:
            r = 10.0
        base = max(1.0, (r ** 2) / 10.0)
        light.energy = base
        light.use_shadow = True
        obj["sa_2dfx_light"]  = True
        obj["sa_energy_base"] = base
        obj["sa_range"]       = r
        n += 1
    return n

def main():
    dff_in  = os.environ.get("DFF_INPUT",  "")
    dff_out = os.environ.get("DFF_OUTPUT", "")
    addon   = os.environ.get("DFF_ADDON",  "")

    if not all([dff_in, dff_out, addon]):
        print("missing env vars", file=sys.stderr)
        sys.exit(1)

    try:
        import bpy
        ver = bpy.app.version

        load_dragonff(addon)

        bpy.ops.object.select_all(action='SELECT')
        bpy.ops.object.delete()

        bpy.ops.import_scene.dff(
            filepath=dff_in,
            txd_pack=True,
            txd_apply_to_objects=True,
            connect_bones=False,
        )

        if not bpy.context.scene.objects:
            raise RuntimeError("scene is empty after import")

        n = setup_lights()
        if n: print(f"lights: {n}")

        bpy.ops.object.select_all(action='SELECT')
        bpy.ops.object.make_single_user(object=True, obdata=True, material=False, animation=False)
        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

        os.makedirs(os.path.dirname(dff_out), exist_ok=True)

        kw = dict(
            filepath=dff_out,
            export_format='GLB',
            use_selection=False,
            export_apply=True,
            export_yup=True,
            export_extras=True,
            export_lights=True,
        )
        if ver[0] >= 4:
            kw["export_image_format"] = 'AUTO'
            kw["export_materials"]    = 'EXPORT'
        else:
            kw["export_textures"]  = True
            kw["export_materials"] = 'EXPORT'

        bpy.ops.export_scene.gltf(**kw)

        if not os.path.exists(dff_out):
            raise RuntimeError("glb not written")

        print(f"ok: {os.path.basename(dff_out)} ({os.path.getsize(dff_out):,}b)")
        sys.exit(0)

    except:
        print(f"failed: {dff_in}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)

main()