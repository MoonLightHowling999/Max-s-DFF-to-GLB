# attach to the root node of any imported SA model
# finds all omnilight3d children and lets you control them with one slider
# works in editor too (@tool)

@tool
extends Node3D

@export_range(0.0, 2.0, 0.01) var intensity: float = 1.0 :
	set(v):
		intensity = v
		_apply()

@export var night_mode: bool = false :
	set(v):
		night_mode = v
		_apply()

var _lights := []

func _ready():
	_scan()
	_apply()

func set_intensity(v: float):
	intensity = v

func get_light_count() -> int:
	return _lights.size()

func _scan():
	_lights.clear()
	for node in _all_children(self):
		if not node is OmniLight3D:
			continue
		var base = node.light_energy
		if node.has_meta("sa_energy_base"):
			base = float(node.get_meta("sa_energy_base"))
		_lights.append({
			"node": node,
			"base": base,
			"at_night": node.get_meta("sa_at_night") if node.has_meta("sa_at_night") else false,
			"at_day":   node.get_meta("sa_at_day")   if node.has_meta("sa_at_day")   else true,
		})
	print("%s: %d light(s)" % [name, _lights.size()])

func _apply():
	for e in _lights:
		var l: OmniLight3D = e.node
		if not is_instance_valid(l):
			continue
		if night_mode and e.at_day and not e.at_night:
			l.visible = false
			continue
		l.light_energy = e.base * intensity
		l.visible = intensity > 0.0

func _all_children(node: Node) -> Array:
	var out := []
	for c in node.get_children():
		out.append(c)
		out.append_array(_all_children(c))
	return out
