"""ATELIER BRUT — rendus photoréalistes (Blender / Cycles) des tables de tenségrité et des potagers suspendus.
Usage : python3 tensegrite.py <variante> <dossier> [--spin N] [--samples S] [--res W H] [--scene studio|salon] [--angle deg]
"""

import bpy, bmesh, math, sys, os, random
from mathutils import Vector, Matrix

args = sys.argv[1:]
variant = args[0]; out_dir = args[1]
def opt(name, default, n=1):
    if name in args:
        i = args.index(name)
        return args[i + 1] if n == 1 else args[i + 1:i + 1 + n]
    return default
SPIN = int(opt("--spin", 0)); SAMPLES = int(opt("--samples", 96))
RES = [int(x) for x in opt("--res", ["1000", "1250"], 2)]
SCENE = opt("--scene", "studio")
START = int(opt("--start", 0))
os.makedirs(out_dir, exist_ok=True)


# ---------------------------------------------------------------- variantes
# Table de tenségrité (« table en lévitation ») :
#   - plateau bas et plateau haut de même format ;
#   - un triangle (Λ) fixé sur le plateau bas, pointe vers le haut ;
#   - un triangle (V) fixé sous le plateau haut, pointe vers le bas ;
#   - les deux triangles sont dans deux plans parallèles, ils se croisent sans se toucher ;
#   - une corde centrale relie la pointe haute du Λ à la pointe basse du V : elle porte le plateau ;
#   - quatre liens verticaux aux coins (cordes ou chaînettes) empêchent le plateau de basculer.
V = {
    "origine":   dict(L=.50, W=.50, H=.62, wood="pin",     link="chaine",   label="pin, chaînettes laiton"),
    "echec":     dict(L=.60, W=.60, H=.68, wood="chene",   link="noir",     chess=True),
    "brulee":    dict(L=.52, W=.52, H=.62, wood="frene",   link="laiton"),
    "manifeste": dict(L=.62, W=.46, H=.64, wood="noyer",   link="bordeaux", text="ce qui tient, tient par le vide"),
    "lune":      dict(L=.56, W=.56, H=.52, wood="olivier", link="chanvre",  round=True),
    "basse":     dict(L=1.00, W=.56, H=.40, wood="noyer",  link="noir"),
    "console":   dict(L=.96, W=.32, H=.80, wood="chene",   link="chanvre"),
    "nocturne":  dict(L=.52, W=.52, H=.62, wood="frene",   link="laiton",   inlay=True, lamp=True),
    "chainette": dict(L=1.9, W=.88, H=.75, wood="noyer",   link="noir",     potager="chainette"),
    "cascade":   dict(L=.5,  W=.5,  H=.6,  wood="pin",     link="chanvre",  potager="cascade"),
}
cfg = V[variant]
cfg["top"] = cfg["wood"]; cfg["legs"] = cfg["wood"]; cfg["rope"] = cfg["link"] if cfg["link"] != "chaine" else "laiton"
L, W, H = cfg["L"], cfg["W"], cfg["H"]
T = .026 if max(L, W) < .8 else .032

# ---------------------------------------------------------------- scène
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.render.engine = "CYCLES"
sc.cycles.device = "CPU"; sc.cycles.samples = SAMPLES; sc.cycles.use_adaptive_sampling = True
sc.cycles.adaptive_threshold = .05
sc.cycles.use_denoising = True; sc.cycles.denoiser = "OPENIMAGEDENOISE"
sc.cycles.max_bounces = 6; sc.cycles.caustics_reflective = False; sc.cycles.caustics_refractive = False
sc.render.resolution_x, sc.render.resolution_y = RES; sc.render.resolution_percentage = 100
sc.render.image_settings.file_format = "JPEG"; sc.render.image_settings.quality = 90
sc.view_settings.view_transform = "AgX"; sc.view_settings.look = "AgX - Medium High Contrast"
sc.view_settings.exposure = float(opt("--exposure", -0.3))
sc.render.film_transparent = False

def mat(name):
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial"); p = nt.nodes.new("ShaderNodeBsdfPrincipled")
    nt.links.new(p.outputs[0], out.inputs[0])
    return m, nt, p

WOODS = {
    "pin":     dict(a=(.44,.28,.13), b=(.32,.19,.08), c=(.55,.38,.2), scale=22, rough=.48, coat=.1),
    "chene":   dict(a=(.42,.3,.17), b=(.33,.22,.11), c=(.5,.38,.24), scale=14, rough=.5, coat=.08),
    "noyer":   dict(a=(.13,.075,.04), b=(.08,.045,.022), c=(.19,.115,.065), scale=16, rough=.42, coat=.18),
    "olivier": dict(a=(.44,.33,.17), b=(.26,.17,.08), c=(.6,.48,.28), scale=26, rough=.4, coat=.12),
    "frene":   dict(a=(.02,.016,.013), b=(.005,.004,.003), c=(.045,.036,.03), scale=30, rough=.28, coat=.4),
}

def wood_mat(kind, seed=0, along="X"):
    w = WOODS[kind]
    m, nt, p = mat("wood_" + kind + str(seed))
    tc = nt.nodes.new("ShaderNodeTexCoord"); mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Location"].default_value = (seed * 1.37, seed * .71, 0)
    # veinage : étirer fortement selon la longueur
    mp.inputs["Scale"].default_value = (1, 9, 9) if along == "X" else (9, 1, 9)
    nt.links.new(tc.outputs["Object"], mp.inputs["Vector"])
    noise = nt.nodes.new("ShaderNodeTexNoise"); noise.inputs["Scale"].default_value = w["scale"] * .35
    noise.inputs["Detail"].default_value = 8; noise.inputs["Roughness"].default_value = .62
    nt.links.new(mp.outputs[0], noise.inputs["Vector"])
    wave = nt.nodes.new("ShaderNodeTexWave"); wave.wave_type = "BANDS"; wave.bands_direction = "Y"
    wave.inputs["Scale"].default_value = w["scale"] * .14; wave.inputs["Distortion"].default_value = 9
    wave.inputs["Detail"].default_value = 8; wave.inputs["Detail Scale"].default_value = 2.2; wave.inputs["Detail Roughness"].default_value = .7
    nt.links.new(mp.outputs[0], wave.inputs["Vector"])
    # pores fins
    pores = nt.nodes.new("ShaderNodeTexNoise"); pores.inputs["Scale"].default_value = 420
    pores.inputs["Detail"].default_value = 2; nt.links.new(tc.outputs["Object"], pores.inputs["Vector"])
    mixn = nt.nodes.new("ShaderNodeMix"); mixn.data_type = "FLOAT"; mixn.inputs["Factor"].default_value = .45
    nt.links.new(wave.outputs["Fac"], mixn.inputs[2]); nt.links.new(pores.outputs["Fac"], mixn.inputs[3])
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = .25; ramp.color_ramp.elements[0].color = (*w["b"], 1)
    e = ramp.color_ramp.elements.new(.6); e.color = (*w["a"], 1)
    ramp.color_ramp.elements[-1].position = .95; ramp.color_ramp.elements[-1].color = (*w["c"], 1)
    nt.links.new(mixn.outputs[0], ramp.inputs[0])
    # variation de teinte à grande échelle (aubier / duramen)
    big = nt.nodes.new("ShaderNodeTexNoise"); big.inputs["Scale"].default_value = .9; big.inputs["Detail"].default_value = 3
    nt.links.new(tc.outputs["Object"], big.inputs["Vector"])
    bramp = nt.nodes.new("ShaderNodeValToRGB"); bramp.color_ramp.elements[0].color = (.72,.66,.6,1); bramp.color_ramp.elements[1].color = (1.08,1.04,1,1)
    nt.links.new(big.outputs["Fac"], bramp.inputs[0])
    mcol = nt.nodes.new("ShaderNodeMix"); mcol.data_type = "RGBA"; mcol.blend_type = "MULTIPLY"; mcol.inputs["Factor"].default_value = 1
    nt.links.new(ramp.outputs["Color"], mcol.inputs[6]); nt.links.new(bramp.outputs["Color"], mcol.inputs[7])
    nt.links.new(mcol.outputs[2], p.inputs["Base Color"])
    rr = nt.nodes.new("ShaderNodeMath"); rr.operation = "MULTIPLY_ADD"
    rr.inputs[1].default_value = .25; rr.inputs[2].default_value = w["rough"]
    nt.links.new(wave.outputs["Fac"], rr.inputs[0]); nt.links.new(rr.outputs[0], p.inputs["Roughness"])
    bump = nt.nodes.new("ShaderNodeBump"); bump.inputs["Strength"].default_value = .18; bump.inputs["Distance"].default_value = .002
    nt.links.new(mixn.outputs[0], bump.inputs["Height"]); nt.links.new(bump.outputs[0], p.inputs["Normal"])
    p.inputs["Coat Weight"].default_value = w["coat"]; p.inputs["Coat Roughness"].default_value = .25
    p.inputs["Sheen Weight"].default_value = .08
    if kind == "frene":
        # craquelures du bois brûlé
        vor = nt.nodes.new("ShaderNodeTexVoronoi"); vor.inputs["Scale"].default_value = 60; vor.feature = "DISTANCE_TO_EDGE"
        nt.links.new(mp.outputs[0], vor.inputs["Vector"])
        cr = nt.nodes.new("ShaderNodeMath"); cr.operation = "LESS_THAN"; cr.inputs[1].default_value = .035
        nt.links.new(vor.outputs["Distance"], cr.inputs[0])
        b2 = nt.nodes.new("ShaderNodeBump"); b2.inputs["Strength"].default_value = .6; b2.inputs["Distance"].default_value = .004; b2.invert = True
        nt.links.new(cr.outputs[0], b2.inputs["Height"]); nt.links.new(bump.outputs[0], b2.inputs["Normal"]); nt.links.new(b2.outputs[0], p.inputs["Normal"])
    return m

def metal_mat(kind="laiton"):
    m, nt, p = mat("metal_" + kind)
    col = {"laiton": (.78,.58,.3), "acier": (.1,.1,.1), "cuivre": (.6,.3,.2)}[kind]
    p.inputs["Base Color"].default_value = (*col, 1); p.inputs["Metallic"].default_value = 1
    p.inputs["Roughness"].default_value = .28 if kind == "laiton" else .4
    noise = nt.nodes.new("ShaderNodeTexNoise"); noise.inputs["Scale"].default_value = 300
    rr = nt.nodes.new("ShaderNodeMath"); rr.operation = "MULTIPLY_ADD"; rr.inputs[1].default_value = .15; rr.inputs[2].default_value = .22
    nt.links.new(noise.outputs["Fac"], rr.inputs[0]); nt.links.new(rr.outputs[0], p.inputs["Roughness"])
    p.inputs["Anisotropic"].default_value = .5
    return m

ROPES = {"chanvre": (.72,.6,.38), "noir": (.03,.025,.02), "bordeaux": (.3,.06,.06), "mousse": (.27,.33,.18), "laiton": None}
def rope_mat(kind):
    if kind == "laiton":
        m = metal_mat("laiton"); m.name = "rope_laiton"; return m
    m, nt, p = mat("rope_" + kind)
    p.inputs["Base Color"].default_value = (*ROPES[kind], 1); p.inputs["Roughness"].default_value = .92
    p.inputs["Sheen Weight"].default_value = .4
    tc = nt.nodes.new("ShaderNodeTexCoord")
    wave = nt.nodes.new("ShaderNodeTexWave"); wave.inputs["Scale"].default_value = 900; wave.wave_type = "BANDS"; wave.bands_direction = "DIAGONAL"
    nt.links.new(tc.outputs["Object"], wave.inputs["Vector"])
    bump = nt.nodes.new("ShaderNodeBump"); bump.inputs["Strength"].default_value = .5; bump.inputs["Distance"].default_value = .0008
    nt.links.new(wave.outputs["Fac"], bump.inputs["Height"]); nt.links.new(bump.outputs[0], p.inputs["Normal"])
    return m

def chess_mat():
    m, nt, p = mat("chess")
    tc = nt.nodes.new("ShaderNodeTexCoord"); ch = nt.nodes.new("ShaderNodeTexChecker")
    ch.inputs["Scale"].default_value = 8
    ch.inputs["Color1"].default_value = (.82,.72,.52,1); ch.inputs["Color2"].default_value = (.02,.05,.035,1)
    nt.links.new(tc.outputs["UV"], ch.inputs["Vector"])
    noise = nt.nodes.new("ShaderNodeTexNoise"); noise.inputs["Scale"].default_value = 40; noise.inputs["Detail"].default_value = 6
    nt.links.new(tc.outputs["Object"], noise.inputs["Vector"])
    mixc = nt.nodes.new("ShaderNodeMix"); mixc.data_type = "RGBA"; mixc.blend_type = "MULTIPLY"; mixc.inputs["Factor"].default_value = .25
    nt.links.new(ch.outputs["Color"], mixc.inputs[6]); nt.links.new(noise.outputs["Color"], mixc.inputs[7])
    nt.links.new(mixc.outputs[2], p.inputs["Base Color"])
    p.inputs["Roughness"].default_value = .12; p.inputs["Coat Weight"].default_value = 1; p.inputs["Coat Roughness"].default_value = .08
    bump = nt.nodes.new("ShaderNodeBump"); bump.inputs["Strength"].default_value = .25; bump.inputs["Distance"].default_value = .0015
    nt.links.new(noise.outputs["Fac"], bump.inputs["Height"]); nt.links.new(bump.outputs[0], p.inputs["Normal"])
    return m

# ---------------------------------------------------------------- géométrie
def box(name, size, loc=(0,0,0), rot=(0,0,0), m=None, bevel=.003):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    o = bpy.context.active_object; o.name = name; o.scale = size; o.rotation_euler = rot
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if bevel:
        b = o.modifiers.new("bevel", "BEVEL"); b.width = bevel; b.segments = 3
    if m: o.data.materials.append(m)
    return o

def plank_between(name, a, b, w, t, m, normal=Vector((0,1,0))):
    a, b = Vector(a), Vector(b); d = b - a; ln = d.length; d.normalize()
    y = normal.cross(d); y.normalize()
    o = box(name, (ln, w, t), m=m)
    M = Matrix((tuple(d), tuple(y), tuple(normal))).transposed().to_4x4()
    o.matrix_world = Matrix.Translation((a + b) / 2) @ M
    return o

def cyl_between(name, a, b, r, m, verts=12):
    a, b = Vector(a), Vector(b); d = b - a; ln = d.length
    bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=ln, vertices=verts, location=(a + b) / 2)
    o = bpy.context.active_object; o.name = name
    o.rotation_euler = d.to_track_quat("Z", "Y").to_euler()
    o.data.materials.append(m); bpy.ops.object.shade_smooth()
    return o

def torus(name, loc, R, r, m, rot=(0,0,0)):
    bpy.ops.mesh.primitive_torus_add(major_radius=R, minor_radius=r, location=loc, rotation=rot, major_segments=24, minor_segments=10)
    o = bpy.context.active_object; o.name = name; o.data.materials.append(m); bpy.ops.object.shade_smooth(); return o

# Blender : Z vers le haut. Plan du W = plan XZ (y = 0).
brass = metal_mat("laiton")
table = []
# ---------------------------------------------------------------- décor + lumière
def floor_mat():
    m, nt, p = mat("floor")
    tc = nt.nodes.new("ShaderNodeTexCoord")
    n1 = nt.nodes.new("ShaderNodeTexNoise"); n1.inputs["Scale"].default_value = 2.5; n1.inputs["Detail"].default_value = 9; n1.inputs["Roughness"].default_value = .7
    nt.links.new(tc.outputs["Object"], n1.inputs["Vector"])
    ramp = nt.nodes.new("ShaderNodeValToRGB"); ramp.color_ramp.elements[0].color = (.12, .11, .10, 1); ramp.color_ramp.elements[1].color = (.24, .22, .20, 1)
    nt.links.new(n1.outputs["Fac"], ramp.inputs[0]); nt.links.new(ramp.outputs["Color"], p.inputs["Base Color"])
    rr = nt.nodes.new("ShaderNodeMath"); rr.operation = "MULTIPLY_ADD"; rr.inputs[1].default_value = .3; rr.inputs[2].default_value = .25
    nt.links.new(n1.outputs["Fac"], rr.inputs[0]); nt.links.new(rr.outputs[0], p.inputs["Roughness"])
    bump = nt.nodes.new("ShaderNodeBump"); bump.inputs["Strength"].default_value = .08; nt.links.new(n1.outputs["Fac"], bump.inputs["Height"]); nt.links.new(bump.outputs[0], p.inputs["Normal"])
    return m

def plaster_mat(col):
    m, nt, p = mat("plaster")
    tc = nt.nodes.new("ShaderNodeTexCoord"); n1 = nt.nodes.new("ShaderNodeTexNoise"); n1.inputs["Scale"].default_value = 6; n1.inputs["Detail"].default_value = 10
    nt.links.new(tc.outputs["Object"], n1.inputs["Vector"])
    ramp = nt.nodes.new("ShaderNodeValToRGB"); ramp.color_ramp.elements[0].color = (*[c * .8 for c in col], 1); ramp.color_ramp.elements[1].color = (*col, 1)
    nt.links.new(n1.outputs["Fac"], ramp.inputs[0]); nt.links.new(ramp.outputs["Color"], p.inputs["Base Color"]); p.inputs["Roughness"].default_value = .9
    bump = nt.nodes.new("ShaderNodeBump"); bump.inputs["Strength"].default_value = .12; nt.links.new(n1.outputs["Fac"], bump.inputs["Height"]); nt.links.new(bump.outputs[0], p.inputs["Normal"])
    return m

def parquet_mat():
    m = wood_mat("noyer", 3, "X"); m.name = "parquet"
    nt = m.node_tree
    # lames : brick texture pour décaler les veines et assombrir les joints
    tc = [n for n in nt.nodes if n.type == "TEX_COORD"][0]
    brick = nt.nodes.new("ShaderNodeTexBrick"); brick.inputs["Scale"].default_value = 1; brick.inputs["Mortar Size"].default_value = .004
    brick.inputs["Color1"].default_value = (1,1,1,1); brick.inputs["Color2"].default_value = (.9,.9,.9,1); brick.inputs["Mortar"].default_value = (.15,.1,.07,1)
    brick.inputs["Brick Width"].default_value = 1.4; brick.inputs["Row Height"].default_value = .14; brick.offset = .5
    nt.links.new(tc.outputs["Object"], brick.inputs["Vector"])
    p = [n for n in nt.nodes if n.type == "BSDF_PRINCIPLED"][0]
    src = p.inputs["Base Color"].links[0].from_socket
    mx = nt.nodes.new("ShaderNodeMix"); mx.data_type = "RGBA"; mx.blend_type = "MULTIPLY"; mx.inputs["Factor"].default_value = 1
    nt.links.new(src, mx.inputs[6]); nt.links.new(brick.outputs["Color"], mx.inputs[7]); nt.links.new(mx.outputs[2], p.inputs["Base Color"])
    p.inputs["Coat Weight"].default_value = .35; p.inputs["Coat Roughness"].default_value = .18
    return m

world = bpy.data.worlds.new("w"); sc.world = world; world.use_nodes = True
wn = world.node_tree; bg = wn.nodes["Background"]

if SCENE == "studio":
    bpy.ops.mesh.primitive_plane_add(size=16, location=(0, 0, 0)); fl = bpy.context.active_object; fl.data.materials.append(floor_mat())
    # cyclo : mur courbe au fond
    bpy.ops.mesh.primitive_plane_add(size=16, location=(0, 3.5, 4), rotation=(math.pi / 2, 0, 0)); wl = bpy.context.active_object
    wl.data.materials.append(plaster_mat((.26, .235, .21)))
    bg.inputs["Color"].default_value = (.2, .18, .16, 1); bg.inputs["Strength"].default_value = .45
    def area(name, loc, size, energy, color=(1, .95, .88), look=(0, 0, .5), shape="RECTANGLE", size_y=None):
        bpy.ops.object.light_add(type="AREA", location=loc); l = bpy.context.active_object; l.name = name
        l.data.energy = energy; l.data.color = color; l.data.size = size; l.data.shape = shape
        if size_y: l.data.size_y = size_y
        d = Vector(look) - Vector(loc); l.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
        return l
    area("key", (-2.2, -2.4, 3.0), 2.6, 480, (1, .93, .84), size_y=2.0)
    area("fill", (3.0, -2.5, 1.6), 3.0, 120, (.86, .9, 1), size_y=2.4)
    area("rim", (1.8, 2.6, 2.4), 1.2, 420, (1, .85, .6), size_y=.4)
    cam_dist, cam_h, cam_target = 2.35, 1.05, (0, 0, .42)
else:  # salon
    bpy.ops.mesh.primitive_plane_add(size=16, location=(0, 0, 0)); fl = bpy.context.active_object; fl.data.materials.append(parquet_mat())
    bpy.ops.mesh.primitive_plane_add(size=16, location=(0, 3.0, 4), rotation=(math.pi / 2, 0, 0)); wl = bpy.context.active_object
    wl.data.materials.append(plaster_mat((.62, .57, .5)))
    bpy.ops.mesh.primitive_plane_add(size=16, location=(-4.2, 0, 4), rotation=(math.pi / 2, 0, math.pi / 2)); wl2 = bpy.context.active_object
    wl2.data.materials.append(plaster_mat((.55, .5, .44)))
    # baie vitrée : trou dans le mur gauche + lumière
    win = box("winhole", (.1, 2.6, 2.6), loc=(-4.2, -.3, 1.6), bevel=0); b = wl2.modifiers.new("cut", "BOOLEAN"); b.object = win; win.hide_render = True; win.hide_viewport = True
    for yy in (-1.55, -.3, .95):
        box("winbar", (.04, .05, 2.6), loc=(-4.2, yy, 1.6), m=metal_mat("acier"), bevel=0)
    box("winbarh", (.04, 2.6, .05), loc=(-4.2, -.3, .3), m=metal_mat("acier"), bevel=0)
    bg.inputs["Color"].default_value = (.75, .8, .9, 1); bg.inputs["Strength"].default_value = .8
    bpy.ops.object.light_add(type="SUN"); sun = bpy.context.active_object; sun.data.energy = 2.0; sun.data.angle = math.radians(1.5); sun.data.color = (1, .95, .85)
    sun.rotation_euler = (math.radians(58), 0, math.radians(-118))
    bpy.ops.object.light_add(type="AREA", location=(-3.9, -.3, 1.7)); l = bpy.context.active_object; l.data.energy = 260; l.data.size = 2.4; l.data.size_y = 2.4; l.data.shape = "RECTANGLE"
    l.rotation_euler = (0, math.radians(90), 0); l.data.color = (.9, .93, 1)
    # tapis, canapé, plante
    rug = box("rug", (2.6, 1.9, .012), loc=(.1, .2, .006), bevel=0)
    rm, nt, p = mat("rug"); p.inputs["Base Color"].default_value = (.045, .05, .04, 1); p.inputs["Roughness"].default_value = 1; p.inputs["Sheen Weight"].default_value = 0
    rug.data.materials.append(rm)
    sm, nt, p = mat("sofa"); p.inputs["Base Color"].default_value = (.3, .25, .2, 1); p.inputs["Roughness"].default_value = 1; p.inputs["Sheen Weight"].default_value = .6
    box("seat", (2.2, .9, .42), loc=(.9, 2.3, .21), m=sm, bevel=.03); box("back", (2.2, .22, .5), loc=(.9, 2.64, .66), m=sm, bevel=.03)
    box("armL", (.2, .9, .3), loc=(-.1, 2.3, .57), m=sm, bevel=.03); box("armR", (.2, .9, .3), loc=(1.9, 2.3, .57), m=sm, bevel=.03)
    # coussins
    box("cush1", (.5, .5, .14), loc=(.3, 2.45, .52), m=plaster_mat((.55,.5,.42)), bevel=.04); box("cush2", (.5, .5, .14), loc=(1.4, 2.45, .52), m=plaster_mat((.28,.3,.26)), bevel=.04)
    # olivier en pot : tronc + branches + centaines de petites feuilles
    pm, nt, p = mat("pot"); p.inputs["Base Color"].default_value = (.22, .17, .13, 1); p.inputs["Roughness"].default_value = .8
    bpy.ops.mesh.primitive_cylinder_add(radius=.21, depth=.46, location=(-2.4, 2.2, .23)); pot = bpy.context.active_object; pot.data.materials.append(pm)
    tm, nt, p = mat("trunk"); p.inputs["Base Color"].default_value = (.2, .16, .12, 1); p.inputs["Roughness"].default_value = .95
    bpy.ops.mesh.primitive_cylinder_add(radius=.03, depth=1.0, location=(-2.4, 2.2, .9)); tr = bpy.context.active_object; tr.data.materials.append(tm)
    lm, nt, p = mat("leaf"); p.inputs["Base Color"].default_value = (.11, .19, .07, 1); p.inputs["Roughness"].default_value = .55; p.inputs["Subsurface Weight"].default_value = .12
    random.seed(4)
    bpy.ops.mesh.primitive_ico_sphere_add(radius=.042, subdivisions=1); leaf = bpy.context.active_object; leaf.scale = (1, .32, .1); leaf.data.materials.append(lm)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    leaves = []
    for i in range(14):
        # branche
        a = random.uniform(0, 6.28); z0 = random.uniform(1.1, 1.75); ln = random.uniform(.35, .7)
        bx, by = math.cos(a), math.sin(a)
        br = cyl_between("branch", (-2.4, 2.2, z0), (-2.4 + bx * ln, 2.2 + by * ln, z0 + random.uniform(.05, .3)), .01, tm, 8)
        for j in range(70):
            t = random.uniform(.2, 1)
            lx, ly, lz = -2.4 + bx * ln * t + random.uniform(-.12, .12), 2.2 + by * ln * t + random.uniform(-.12, .12), z0 + t * .2 + random.uniform(-.14, .14)
            lf = leaf.copy(); lf.data = leaf.data; lf.location = (lx, ly, lz); lf.rotation_euler = (random.uniform(0, 3.1), random.uniform(0, 3.1), random.uniform(0, 3.1))
            bpy.context.collection.objects.link(lf)
    leaf.hide_render = True; leaf.hide_viewport = True
    cam_dist, cam_h, cam_target = 2.6, 1.0, (0, 0, .4)


# ---------------------------------------------------------------- potagers suspendus
def chain(a, b, m, R=.011, r=.0028):
    a, b = Vector(a), Vector(b); d = b - a; ln = d.length; d.normalize()
    step = R * 2.0; n = max(2, int(ln / step))
    bpy.ops.mesh.primitive_torus_add(major_radius=R, minor_radius=r, major_segments=20, minor_segments=8); link = bpy.context.active_object
    link.scale = (1, 1.45, 1); bpy.ops.object.transform_apply(location=False, rotation=False, scale=True); link.data.materials.append(m)
    q = d.to_track_quat("Y", "Z")
    objs = []
    for i in range(n):
        o = link.copy() if i else link; o.data = link.data
        if i: bpy.context.collection.objects.link(o)
        o.location = a + d * ((i + .5) * step)
        rot = Matrix.Rotation(math.pi / 2 * (i % 2), 4, "Y")
        o.matrix_world = Matrix.Translation(o.location) @ q.to_matrix().to_4x4() @ rot
        objs.append(o)
    return objs

def soil_mat():
    m, nt, p = mat("soil"); p.inputs["Base Color"].default_value = (.06, .04, .025, 1); p.inputs["Roughness"].default_value = 1
    tc = nt.nodes.new("ShaderNodeTexCoord"); n1 = nt.nodes.new("ShaderNodeTexNoise"); n1.inputs["Scale"].default_value = 300; n1.inputs["Detail"].default_value = 4
    nt.links.new(tc.outputs["Object"], n1.inputs["Vector"])
    bump = nt.nodes.new("ShaderNodeBump"); bump.inputs["Strength"].default_value = .6; bump.inputs["Distance"].default_value = .003
    nt.links.new(n1.outputs["Fac"], bump.inputs["Height"]); nt.links.new(bump.outputs[0], p.inputs["Normal"])
    return m

_leafprotos = {}
def leaf_proto(kind):
    if kind in _leafprotos: return _leafprotos[kind]
    cols = {"basilic": (.14,.3,.09), "menthe": (.1,.26,.11), "romarin": (.2,.27,.17), "sauge": (.36,.44,.33), "fraise": (.12,.26,.08)}
    lm, nt, p = mat("leaf_" + kind); p.inputs["Base Color"].default_value = (*cols[kind], 1); p.inputs["Roughness"].default_value = .5
    p.inputs["Subsurface Weight"].default_value = .25; p.inputs["Subsurface Radius"].default_value = (.02, .05, .01)
    if kind == "romarin":
        bpy.ops.mesh.primitive_cylinder_add(radius=.0014, depth=.04, vertices=6); o = bpy.context.active_object
    else:
        sz = {"basilic": .05, "menthe": .036, "sauge": .048, "fraise": .042}[kind]
        bpy.ops.mesh.primitive_ico_sphere_add(radius=sz, subdivisions=2); o = bpy.context.active_object
        o.scale = (1, .62, .07); bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        # légère courbure
        sd = o.modifiers.new("disp", "SIMPLE_DEFORM"); sd.deform_method = "BEND"; sd.angle = math.radians(40)
    o.data.materials.append(lm); bpy.ops.object.shade_smooth()
    o.hide_render = True; o.hide_viewport = True
    _leafprotos[kind] = o; return o

def plant(kind, loc, seed):
    random.seed(seed)
    proto = leaf_proto(kind)
    sm, nt, p = mat("stem"); p.inputs["Base Color"].default_value = (.18, .28, .1, 1); p.inputs["Roughness"].default_value = .8
    h = {"basilic": .28, "menthe": .32, "romarin": .38, "sauge": .26, "fraise": .16}[kind]
    stems = 13 if kind != "romarin" else 16
    for s_ in range(stems):
        a = random.uniform(0, 6.28); tilt = random.uniform(0, .5); hh = h * random.uniform(.6, 1.1)
        top = (loc[0] + math.cos(a) * math.sin(tilt) * hh, loc[1] + math.sin(a) * math.sin(tilt) * hh, loc[2] + math.cos(tilt) * hh)
        cyl_between("stem", loc, top, .0022, sm, 6)
        nl = 30 if kind == "romarin" else random.randint(7, 11)
        for i in range(nl):
            t = random.uniform(.3, 1.0)
            pos = Vector(loc).lerp(Vector(top), t)
            o = proto.copy(); o.data = proto.data; bpy.context.collection.objects.link(o)
            o.hide_render = False; o.hide_viewport = False
            o.location = pos + Vector((random.uniform(-.01, .01), random.uniform(-.01, .01), 0))
            o.rotation_euler = (random.uniform(-.5, -1.3) if kind != "romarin" else random.uniform(0, 3.1), random.uniform(0, .6), random.uniform(0, 6.28))
            o.scale = (1, 1, 1) if kind != "romarin" else (1, 1, 1)
        if kind == "fraise" and random.random() > .5:
            fm, nt2, p2 = mat("fruit"); p2.inputs["Base Color"].default_value = (.5, .04, .04, 1); p2.inputs["Roughness"].default_value = .35; p2.inputs["Coat Weight"].default_value = .5
            bpy.ops.mesh.primitive_ico_sphere_add(radius=.011, subdivisions=2, location=(top[0] + random.uniform(-.03, .03), top[1] + random.uniform(-.03, .03), top[2] - .04)); f = bpy.context.active_object; f.data.materials.append(fm); bpy.ops.object.shade_smooth()

def trough(center, ln, w, h, plants, seed):
    cx, cy, cz = center
    wm = wood_mat(cfg["top"], 7 + seed, "X"); t = .018
    box("tr_f", (ln, t, h), loc=(cx, cy - w / 2 + t / 2, cz + h / 2), m=wm, bevel=.002)
    box("tr_b", (ln, t, h), loc=(cx, cy + w / 2 - t / 2, cz + h / 2), m=wm, bevel=.002)
    box("tr_l", (t, w, h), loc=(cx - ln / 2 + t / 2, cy, cz + h / 2), m=wm, bevel=.002)
    box("tr_r", (t, w, h), loc=(cx + ln / 2 - t / 2, cy, cz + h / 2), m=wm, bevel=.002)
    box("tr_bot", (ln, w, t), loc=(cx, cy, cz + t / 2), m=wm, bevel=.002)
    for x in (cx - ln / 2 + .07, cx + ln / 2 - .07):
        box("band", (.03, w + .006, h * .92), loc=(x, cy, cz + h / 2), m=brass, bevel=.001)
    box("soil", (ln - 2 * t - .002, w - 2 * t - .002, .012), loc=(cx, cy, cz + h - .035), m=soil_mat(), bevel=0)
    rings = []
    for sx in (-1, 1):
        for sy in (-1, 1):
            rp = (cx + sx * (ln / 2 - .07), cy + sy * (w / 2 - .01), cz + h + .012)
            torus("ring", rp, .014, .0035, brass, (math.pi / 2, 0, 0)); rings.append(rp)
    n = len(plants)
    for i, k in enumerate(plants):
        plant(k, (cx - ln / 2 + .12 + (i + .5) * (ln - .24) / n, cy, cz + h - .03), seed * 10 + i)
    return rings

ceilZ = 2.45
def rail(ln, z, y=0, x=0):
    bpy.ops.mesh.primitive_cylinder_add(radius=.012, depth=ln, vertices=24, location=(x, y, z), rotation=(0, math.pi / 2, 0)); r = bpy.context.active_object; r.data.materials.append(brass)
    for sg in (-1, 1):
        bpy.ops.mesh.primitive_cylinder_add(radius=.02, depth=.03, vertices=24, location=(x + sg * (ln / 2 - .05), y, z + .02)); c = bpy.context.active_object; c.data.materials.append(brass)

if cfg.get("potager") == "chainette":
    lift = float(opt("--lift", .35))
    z = .98 + lift * .95
    rings = trough((0, 0, z), 1.1, .24, .2, ["basilic", "menthe", "romarin", "sauge", "fraise"], 1)
    rail(1.4, ceilZ - .03)
    for rp in rings: chain(rp, (rp[0], rp[1] * .35, ceilZ - .03), brass)
elif cfg.get("potager") == "cascade":
    for o in table: o.hide_render = True; o.hide_viewport = True
    tiers = [(1.2, 1.95, 0, ["romarin", "sauge", "romarin", "sauge"]), (.95, 1.5, .12, ["basilic", "menthe", "basilic"]), (.7, 1.05, .24, ["fraise", "fraise", "menthe"])]
    rail(1.6, ceilZ - .03)
    prev = None
    for i, (ln, z, y, pl) in enumerate(tiers):
        rings = trough((0, y, z), ln, .22, .18, pl, 3 + i)
        for k, rp in enumerate(rings):
            if prev is None: to = (rp[0], 0, ceilZ - .03)
            else:
                up = prev[k]; to = (math.copysign(min(abs(rp[0]), abs(up[0])), rp[0]), up[1], up[2] - .012 - .18 - .012 + .18)  # sous le bac du dessus
                to = (to[0], up[1], tiers[i - 1][1] - .004)
            chain(rp, to, brass, .01, .0025)
        prev = rings
    cam_target = (0, .1, 1.45); cam_h = 1.5; cam_dist = 2.9
if cfg.get("potager") == "chainette":
    cam_target = (0, 0, .95); cam_h = 1.35; cam_dist = 3.4

# ---------------------------------------------------------------- table de tenségrité
brass = metal_mat("laiton")
wood = cfg["wood"]
top_m = wood_mat(wood, 0, "X")
base_m = wood_mat(wood, 2, "X")
leg_m = wood_mat(wood, 1, "X")
rope_m = rope_mat(cfg["rope"])
rope_r = .0014 if cfg["link"] == "laiton" else .0026
table = []

def plate(name, z0, m):
    """Plateau d'épaisseur T, face inférieure à z0."""
    if cfg.get("round"):
        bpy.ops.mesh.primitive_cylinder_add(radius=L / 2, depth=T, vertices=96, location=(0, 0, z0 + T / 2))
        o = bpy.context.active_object; o.name = name
        b = o.modifiers.new("bevel", "BEVEL"); b.width = .003; b.segments = 3; b.limit_method = "ANGLE"
        o.data.materials.append(m)
        return o
    return box(name, (L, W, T), loc=(0, 0, z0 + T / 2), m=m, bevel=.003)

if not cfg.get("potager"):
    big = max(L, W) >= .8
    PW = .058 if big else .046          # largeur visible des tasseaux
    PT = .022                           # épaisseur des tasseaux
    s = PT * .95                        # décalage des deux plans (le Λ derrière, le V devant)
    h = H - 2 * T                       # hauteur libre entre plateaux
    zA = T + .80 * h                    # pointe haute du Λ
    zV = T + .20 * h                    # pointe basse du V
    xa = .36 * L                        # pieds du Λ sur le plateau bas
    xv = .21 * L                        # départs du V sous le plateau haut

    base = plate("base", 0, base_m); table.append(base)
    top = plate("top", H - T, top_m); table.append(top)

    # coupe nette des tasseaux contre les plateaux (comme une coupe d'onglet réelle)
    clip = box("clip", (L * 3, W * 3, h), loc=(0, 0, T + h / 2), bevel=0)
    clip.hide_render = True; clip.hide_viewport = True
    def leg(name, a, b):
        a, b = Vector(a), Vector(b); d = (a - b).normalized()
        o = plank_between(name, a + d * PW, b, PW, PT, leg_m, Vector((0, 1, 0)))
        bo = o.modifiers.new("clip", "BOOLEAN"); bo.object = clip; bo.operation = "INTERSECT"
        table.append(o); return o
    # Λ (sur le plateau bas)
    leg("lambda_g", (-xa, s, T), (0, s, zA))
    leg("lambda_d", (xa, s, T), (0, s, zA))
    # V (sous le plateau haut)
    leg("v_g", (-xv, -s, H - T), (0, -s, zV))
    leg("v_d", (xv, -s, H - T), (0, -s, zV))
    # crochets d'about : petits blocs qui ramènent le point d'attache au centre
    hookA = box("crochet_haut", (PW * .9, s + PT * .8, PW * .55), loc=(0, (s - PT * .3) / 2, zA - PW * .75), m=leg_m, bevel=.002)
    hookV = box("crochet_bas", (PW * .9, s + PT * .8, PW * .55), loc=(0, -(s - PT * .3) / 2, zV + PW * .75), m=leg_m, bevel=.002)
    table += [hookA, hookV]
    ea = (0, 0, zA - PW * 1.03 - .004); ev = (0, 0, zV + PW * 1.03 + .004)
    table.append(torus("piton_haut", ea, .006, .0016, brass, (math.pi / 2, 0, 0)))
    table.append(torus("piton_bas", ev, .006, .0016, brass, (math.pi / 2, 0, 0)))
    # corde centrale : porte tout le plateau
    if cfg["link"] == "chaine":
        table += chain((0, 0, ea[2] - .006), (0, 0, ev[2] + .006), brass, .0055, .0014)
    else:
        table.append(cyl_between("corde_centrale", (0, 0, ea[2] - .005), (0, 0, ev[2] + .005), rope_r * 1.15, rope_m))

    # liens verticaux aux coins
    if cfg.get("round"):
        r = L / 2 - .032
        corners = [(r * math.cos(a), r * math.sin(a)) for a in (math.radians(45), math.radians(135), math.radians(225), math.radians(315))]
    else:
        corners = [(sx * (L / 2 - .03), sy * (W / 2 - .03)) for sx in (-1, 1) for sy in (-1, 1)]
    for (cx_, cy_) in corners:
        t1 = (cx_, cy_, H - T - .007); t0 = (cx_, cy_, T + .007)
        table.append(torus("piton", t1, .005, .0014, brass, (math.pi / 2, 0, 0)))
        table.append(torus("piton", t0, .005, .0014, brass, (math.pi / 2, 0, 0)))
        if cfg["link"] == "chaine":
            table += chain((cx_, cy_, t1[2] - .005), (cx_, cy_, t0[2] + .005), brass, .0055, .0014)
        else:
            table.append(cyl_between("lien", (cx_, cy_, t1[2] - .005), (cx_, cy_, t0[2] + .005), rope_r, rope_m))

    # finitions
    if cfg.get("chess"):
        sq = min(L, W) * .74
        hole = box("hole", (sq, sq, T * .5), loc=(0, 0, H), bevel=0)
        bo = top.modifiers.new("cut", "BOOLEAN"); bo.object = hole; bo.operation = "DIFFERENCE"; hole.hide_render = True; hole.hide_viewport = True
        board = box("board", (sq - .003, sq - .003, .01), loc=(0, 0, H - .005 + .0004), m=chess_mat(), bevel=.0008)
        bpy.context.view_layer.objects.active = board; bpy.ops.object.mode_set(mode="EDIT"); bpy.ops.mesh.select_all(action="SELECT")
        bpy.ops.uv.cube_project(cube_size=sq - .003, correct_aspect=True); bpy.ops.object.mode_set(mode="OBJECT")
        rim = box("rim", (sq + .006, sq + .006, .002), loc=(0, 0, H - .001), m=brass, bevel=0)
        rh = box("rimhole", (sq - .002, sq - .002, .01), loc=(0, 0, H), bevel=0)
        b2 = rim.modifiers.new("cut", "BOOLEAN"); b2.object = rh; rh.hide_render = True; rh.hide_viewport = True
        table += [board, rim]
    if cfg.get("inlay"):
        inl = box("filet", (L + .0016, W + .0016, .004), loc=(0, 0, H - T / 2), m=brass, bevel=0)
        ih = box("filethole", (L - .01, W - .01, .02), loc=(0, 0, H - T / 2), bevel=0)
        b3 = inl.modifiers.new("cut", "BOOLEAN"); b3.object = ih; ih.hide_render = True; ih.hide_viewport = True
        table.append(inl)
    if cfg.get("lamp"):
        bpy.ops.object.light_add(type="AREA", location=(0, 0, H - T - .004)); la = bpy.context.active_object
        la.data.energy = 6; la.data.color = (1, .76, .5); la.data.size = L * .5; la.rotation_euler = (math.pi, 0, 0)
    if cfg.get("text"):
        bpy.ops.object.text_add(location=(0, -W / 2 - .0004, H - T / 2 - T * .17))
        tx = bpy.context.active_object; tx.data.body = cfg["text"]; tx.data.size = T * .42; tx.data.align_x = "CENTER"
        tx.data.extrude = .0003; tx.rotation_euler = (math.pi / 2, 0, 0)
        try: tx.data.font = bpy.data.fonts.load("/usr/share/fonts/truetype/dejavu/DejaVuSerif-Italic.ttf")
        except Exception: pass
        tx.data.materials.append(brass); table.append(tx)

elif cfg["potager"] == "chainette":
    # table à manger simple sous le potager
    tm = wood_mat("noyer", 4, "X")
    box("plateau", (L, W, .04), loc=(0, 0, H - .02), m=tm, bevel=.004)
    for sx in (-1, 1):
        for sy in (-1, 1):
            box("pied", (.06, .06, H - .04), loc=(sx * (L / 2 - .1), sy * (W / 2 - .08), (H - .04) / 2), m=tm, bevel=.003)


# ---------------------------------------------------------------- caméra
bpy.ops.object.camera_add(); cam = bpy.context.active_object; sc.camera = cam
cam.data.lens = 50; cam.data.sensor_width = 36; cam.data.sensor_fit = "AUTO"
cam.data.dof.use_dof = True; cam.data.dof.aperture_fstop = 5.6
cam.data.shift_x = float(opt("--shift", 0))
if not cfg.get("potager"):
    aspect = RES[0] / RES[1]
    half = math.atan(18 / 50)
    if aspect >= 1: hf, vf = half, math.atan(math.tan(half) / aspect)
    else: vf, hf = half, math.atan(math.tan(half) * aspect)
    wneed = max(L, W) * (1.85 if SCENE == "studio" else 2.3)
    hneed = H * (1.8 if SCENE == "studio" else 2.2)
    cam_dist = max(wneed / (2 * math.tan(hf)), hneed / (2 * math.tan(vf)))
    cam_h = H * .55 + cam_dist * .26
    cam_target = (0, 0, H * .46)

def place_cam(angle_deg):
    a = math.radians(angle_deg)
    cam.location = (cam_dist * math.sin(a) * -1, -cam_dist * math.cos(a), cam_h)
    d = Vector(cam_target) - cam.location
    cam.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
    cam.data.dof.focus_distance = d.length

if "--norender" in args:
    print("OBJECTS", len(bpy.data.objects)); sys.exit(0)
if SPIN:
    for i in range(START, SPIN):
        place_cam(-24 + i * 360 / SPIN)
        sc.render.filepath = os.path.join(out_dir, "frame-%03d.jpg" % i)
        bpy.ops.render.render(write_still=True)
else:
    place_cam(float(opt("--angle", -24)))
    sc.render.filepath = os.path.join(out_dir, "%s-%s.jpg" % (variant, SCENE))
    bpy.ops.render.render(write_still=True)
print("DONE")
