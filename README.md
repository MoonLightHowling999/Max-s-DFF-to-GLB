# Max's .DFF to .GLB

batch converts SA .dff models to .glb for use in godot. uses blender + dragonff under the hood so textures, normals, origins and 2dfx lights all come out correct.

---

## what you need
- python 3.10+
- blender 4.x or 5.x
- [DragonFF](https://github.com/Parik27/DragonFF) (the folder, not installed in blender)

---

## setup

put these three files in the same folder:

```
dff_to_glb.py
blender_worker.py
converter.cfg
```

edit `converter.cfg`:

```ini
[paths]
source_folder      = C:/SA/models
destination_folder = C:/SA/models/glb
blender_exe        = C:/Program Files/Blender Foundation/Blender 5.1/blender.exe
dragonff_path      = C:/tools/DragonFF-master
```

if you drop the DragonFF-master folder next to the script you can skip `dragonff_path`, it'll find it automatically.

---

## usage

```
python dff_to_glb.py                   # convert everything
python dff_to_glb.py --workers 8       # more parallel blender instances
python dff_to_glb.py --debug infernus.dff   # test one file, full blender output
python dff_to_glb.py --init-config     # writes a blank converter.cfg
```

already converted files are skipped. delete the output folder (or specific .glb files) to redo them.

---

## output

- one .glb per .dff, same name, subfolder structure preserved
- textures embedded in the glb (no separate pngs)
- 2dfx point lights exported as real omnilight3d nodes via KHR_lights_punctual
- origins match SA pivot points so IPL placement works as-is

---

## lights (ModelLightController.gd)

streetlamps, neons, etc. come through as actual godot lights. attach `ModelLightController.gd` to the root node of any imported model and you get a single intensity slider in the inspector that controls all of them.

```gdscript
# dim all lights on a model
$streetlamp.set_intensity(0.4)

# turn them off
$streetlamp.set_intensity(0.0)

# night mode — only shows lights flagged AT_NIGHT in SA
$streetlamp.night_mode = true
```

---

## building an exe

```
pip install pyinstaller
pyinstaller --onefile --console --name dff_to_glb dff_to_glb.py
```

copy `blender_worker.py` and `converter.cfg` next to the exe in `dist/`. blender and dragonff still need to be on the machine, they're not bundled.

---

## known issues

- ped skins with bone weights import fine but won't animate in godot without a separate skeleton setup and they also have broken UVs
- some LOD models (prefixed `_lod_`) have no geometry, just an empty frame — they export as empty glbs, that's correct
- if a model fails check the full error with `--debug modelname.dff`
