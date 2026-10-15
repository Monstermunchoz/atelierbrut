"""ATELIER BRUT — rendu photoréaliste (Cycles) de la table « W » et de ses déclinaisons.
Usage : python3 table_w.py <variant> <out_dir> [--spin N] [--samples S] [--res W H] [--scene studio|salon]
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
V = {
    "origine":    dict(top="pin", legs="pin", rope="chanvre", pattern="centre", L=.62, W=.62),
    "echec":      dict(top="chene", legs="chene", rope="noir", pattern="centre", chess=True, L=.66, W=.66),
    "brulee":     dict(top="frene", legs="frene", rope="laiton", pattern="centre", L=.62, W=.62),
    "manifeste":  dict(top="noyer", legs="noyer", rope="bordeaux", pattern="centre", text="ce qui tient, tient par le vide", L=.7, W=.62),
    "harpe":      dict(top="chene", legs="chene", rope="mousse", pattern="harpe", L=.62, W=.62),
    "nocturne":   dict(top="frene", legs="frene", rope="laiton", pattern="centre", inlay=True, lamp=True, L=.62, W=.62),
    "console":    dict(top="olivier", legs="olivier", rope="chanvre", pattern="centre", L=1.2, W=.42, two=True),
    "manger":     dict(top="noyer", legs="noyer", rope="noir", pattern="coins", L=1.9, W=.88, two=True, H=.75),
}
V.update({
    "chainette": dict(top="noyer", legs="noyer", rope="noir", pattern="coins", L=1.9, W=.88, two=True, H=.75, potager="chainette"),
    "integre":   dict(top="noyer", legs="noyer", rope="mousse", pattern="coins", L=2.0, W=.92, two=True, H=.75, potager="integre"),
    "cascade":   dict(top="pin", legs="pin", rope="chanvre", pattern="coins", L=.62, W=.62, potager="cascade", notable=True),
})
cfg = V[variant]
L, W = cfg["L"], cfg["W"]; H = cfg.get("H", .74); T = .03
PW, PT = .085, .027

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
sc.view_settings.exposure = -0.15
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
    "noyer":   dict(a=(.2,.11,.06), b=(.13,.07,.035), c=(.28,.17,.1), scale=16, rough=.42, coat=.15),
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
top_m = wood_mat(cfg["top"], 0, "X")
leg_m = wood_mat(cfg["legs"], 1, "X")
rope_m = rope_mat(cfg["rope"])
rope_r = .0012 if cfg["rope"] == "laiton" else .0025

table = []
topZ = H - T
def frame(span, cx, axis="X", lev=False):
    """Cadre W dans un plan vertical. axis X : plan XZ à y=0, centré en x=cx. axis Y : plan YZ à x=cx."""
    objs = []
    def P(u, z): return (cx + u, 0, z) if axis == "X" else (cx, u, z)
    normal = Vector((0, 1, 0)) if axis == "X" else Vector((1, 0, 0))
    run_len = span * 1.15
    baseZ = PT * 1.8
    # patin principal
    r = box("runner", (run_len, PW * .9, PT * .9), loc=P(0, PT * .45), m=leg_m)
    if axis == "Y": r.rotation_euler = (0, 0, math.pi / 2)
    objs.append(r)
    anchors = [P(run_len / 2 - .025, baseZ), P(-(run_len / 2 - .025), baseZ)]
    xo = span * .5 - PW * .35
    # Tenségrité : le triangle bas (Λ) est debout sur le patin, dans le plan du patin, pointe sous le plateau ;
    # le triangle haut (V) est fixé sous le plateau dans le plan PERPENDICULAIRE, pointe au-dessus du patin.
    # Les deux triangles se croisent à 90° (le V passe dans l'ouverture du Λ) ; une corde verticale relie les pointes.
    gapT, gapB = .022, .03
    def Q(u, z): return (cx, u, z) if axis == "X" else (cx + u, 0, z)   # plan perpendiculaire
    normalQ = Vector((1, 0, 0)) if axis == "X" else Vector((0, 1, 0))
    apexB = Vector(P(0, topZ - gapT)); apexT = Vector(Q(0, baseZ + gapB))
    for i, foot in enumerate((P(-xo, baseZ), P(xo, baseZ))):
        o = plank_between("lb%d" % i, Vector(foot), apexB, PW, PT, leg_m, normal); o.location += normal * ((1 if i else -1) * PT * .5); objs.append(o)
    vspan = span * .24
    for i, hang in enumerate((Q(-vspan, topZ), Q(vspan, topZ))):
        o = plank_between("lt%d" % i, Vector(hang), apexT, PW, PT, leg_m, normalQ); o.location += normalQ * ((1 if i else -1) * PT * .5); objs.append(o)
    rc_a = Vector(P(0, topZ - gapT - PW * .5)); rc_b = Vector(Q(0, baseZ + gapB + PW * .5))
    if cfg["pattern"] != "coins":
        objs.append(cyl_between("rope_c", rc_a, rc_b, rope_r * 1.25, rope_m))
        objs.append(torus("eyeB", rc_a, .006, .0016, brass, (math.pi / 2, 0, 0)))
        objs.append(torus("eyeT", rc_b, .006, .0016, brass, (math.pi / 2, 0, 0)))
    if cfg["pattern"] == "harpe":
        n = 9
        for i in range(n):
            t = (i + 1) / (n + 1)
            for sg in (-1, 1):
                u = sg * xo * (1 - t)
                zL = baseZ + (topZ - gapT - baseZ) * t
                A = Vector(P(u, baseZ + PW * .5)); B = Vector(P(u, zL - PW * .35))
                if B.z - A.z > .05: objs.append(cyl_between("harpL", A, B, rope_r * .7, rope_m, 8))
                u2 = sg * vspan * (1 - t)
                zV = topZ - (topZ - baseZ - gapB) * t
                A2 = Vector(Q(u2, topZ - .004)); B2 = Vector(Q(u2, zV + PW * .35))
                if A2.z - B2.z > .05: objs.append(cyl_between("harpV", A2, B2, rope_r * .7, rope_m, 8))
    for a in anchors:
        objs.append(torus("knot", (a[0], a[1], a[2] + .003), rope_r * 1.6, rope_r * .9, rope_m, (math.pi / 2, 0, 0)))
    return objs, anchors, run_len

anchors = []
if not cfg.get("two"):
    objs, anc, run_len = frame(L, 0, "X", cfg["pattern"] == "lev"); table += objs; anchors += anc
    ang = math.radians(90)
    r2 = box("runner2", (run_len, PW * .9, PT * .9), loc=(0, 0, PT * 1.35), rot=(0, 0, ang), m=leg_m); table.append(r2)
    hr = run_len / 2 - .025
    for sg in (1, -1):
        anchors.append((sg * hr * math.cos(ang), sg * hr * math.sin(ang), PT * 1.8))
    # patins laiton
    for a in anchors:
        bpy.ops.mesh.primitive_cylinder_add(radius=.015, depth=.006, vertices=24, location=(a[0], a[1], .003))
        o = bpy.context.active_object; o.data.materials.append(brass); table.append(o)
else:
    for sg in (-1, 1):
        objs, anc, run_len = frame(W, sg * (L / 2 - .2), "Y", False); table += objs; anchors += anc
    s = box("stretcher", (L - .4 - PT, PW * .6, PT * .9), loc=(0, 0, PT * .45), m=leg_m); table.append(s)

# plateau
top = box("top", (L, W, T), loc=(0, 0, topZ + T / 2), m=top_m, bevel=.0035)
table.append(top)
if cfg.get("chess"):
    s = min(L, W) * .78
    hole = box("hole", (s, s, T * .5), loc=(0, 0, topZ + T), bevel=0)
    bo = top.modifiers.new("cut", "BOOLEAN"); bo.object = hole; bo.operation = "DIFFERENCE"
    hole.hide_render = True; hole.hide_viewport = True
    board = box("board", (s - .004, s - .004, .012), loc=(0, 0, topZ + T - .006 + .0005), m=chess_mat(), bevel=.001)
    # UV : projection du dessus
    bpy.context.view_layer.objects.active = board; bpy.ops.object.mode_set(mode="EDIT"); bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.cube_project(cube_size=s - .004, correct_aspect=True); bpy.ops.object.mode_set(mode="OBJECT")
    rim = box("rim", (s + .006, s + .006, .003), loc=(0, 0, topZ + T - .0015), m=brass, bevel=0)
    rim_hole = box("rimhole", (s - .002, s - .002, .01), loc=(0, 0, topZ + T), bevel=0)
    bo2 = rim.modifiers.new("cut", "BOOLEAN"); bo2.object = rim_hole; rim_hole.hide_render = True; rim_hole.hide_viewport = True
    table += [board, rim]
if cfg.get("inlay"):
    inl = box("inlay", (L + .002, W + .002, .004), loc=(0, 0, topZ + T * .5), m=brass, bevel=0)
    ih = box("inlayhole", (L - .012, W - .012, .02), loc=(0, 0, topZ + T * .5), bevel=0)
    b = inl.modifiers.new("cut", "BOOLEAN"); b.object = ih; ih.hide_render = True; ih.hide_viewport = True; table.append(inl)
if cfg.get("lamp"):
    bpy.ops.object.light_add(type="AREA", location=(0, 0, topZ - .01)); la = bpy.context.active_object
    la.data.energy = 18; la.data.color = (1, .78, .55); la.data.size = L * .5; la.rotation_euler = (math.pi, 0, 0); la.data.shape = "SQUARE"
    strip = box("strip", (L * .55, W * .55, .004), loc=(0, 0, topZ - .002), bevel=0)
    em, nt, p = mat("emit"); p.inputs["Emission Color"].default_value = (1, .8, .58, 1); p.inputs["Emission Strength"].default_value = 6
    strip.data.materials.append(em); table.append(strip)
if cfg.get("text"):
    bpy.ops.object.text_add(location=(0, -W / 2 - .0002, topZ + T * .5 - .006))
    tx = bpy.context.active_object; tx.data.body = cfg["text"]; tx.data.size = T * .55; tx.data.align_x = "CENTER"
    tx.data.extrude = .0006
    tx.rotation_euler = (math.pi / 2, 0, 0)
    try:
        f = bpy.data.fonts.load(os.path.expanduser("/usr/share/fonts/truetype/dejavu/DejaVuSerif-Italic.ttf"))
        tx.data.font = f
    except Exception: pass
    tm, nt, p = mat("engrave"); p.inputs["Base Color"].default_value = (.06, .035, .02, 1); p.inputs["Roughness"].default_value = .9
    tx.data.materials.append(tm); table.append(tx)

# haubans : coins du plateau -> ancrages les plus proches
corners = [(L/2-.02, W/2-.02), (-L/2+.02, -W/2+.02), (L/2-.02, -W/2+.02), (-L/2+.02, W/2-.02)]
used = set()
for cxp, cyp in corners:
    best, bd = None, 1e9
    for i, a in enumerate(anchors):
        if i in used: continue
        d = (Vector(a) - Vector((cxp, cyp, topZ))).length
        if d < bd: bd, best = d, i
    used.add(best); a = anchors[best]
    table.append(cyl_between("hauban", (cxp, cyp, topZ - .004), (a[0], a[1], a[2] + .002), rope_r, rope_m))
    table.append(torus("eye", (cxp, cyp, topZ - .005), .006, .0015, brass, (0, 0, 0)))

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
elif cfg.get("potager") == "integre":
    lift = float(opt("--lift", .55))
    slot = (1.0, .3)
    hole = box("slot", (slot[0] + .02, slot[1] + .02, .2), loc=(0, 0, topZ + T / 2), bevel=0)
    bo = top.modifiers.new("slot", "BOOLEAN"); bo.object = hole; bo.operation = "DIFFERENCE"; hole.hide_render = True; hole.hide_viewport = True
    lip = box("lip", (slot[0] + .05, slot[1] + .05, .005), loc=(0, 0, topZ + T + .0025), m=brass, bevel=0)
    liph = box("liph", (slot[0] + .02, slot[1] + .02, .02), loc=(0, 0, topZ + T), bevel=0); b2 = lip.modifiers.new("c", "BOOLEAN"); b2.object = liph; liph.hide_render = True; liph.hide_viewport = True
    z = topZ + T - .2 + .01 + lift * 1.0
    rings = trough((0, 0, z), slot[0] - .01, slot[1] - .01, .2, ["basilic", "menthe", "romarin", "sauge"], 2)
    rail(1.3, ceilZ - .03)
    for rp in rings: chain(rp, (rp[0], rp[1] * .4, ceilZ - .03), brass, .01, .0025)
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
if cfg.get("potager") in ("chainette", "integre"):
    cam_target = (0, 0, .95); cam_h = 1.35; cam_dist = 3.4

# ---------------------------------------------------------------- caméra
bpy.ops.object.camera_add(); cam = bpy.context.active_object; sc.camera = cam
cam.data.lens = 50; cam.data.sensor_width = 36
cam.data.dof.use_dof = True; cam.data.dof.aperture_fstop = 4.0
if cfg.get("two") and not cfg.get("potager"):
    cam_dist *= 1.9 if L > 1.5 else 1.5; cam_h *= 1.15

def place_cam(angle_deg):
    a = math.radians(angle_deg)
    cam.location = (cam_dist * math.sin(a) * -1, -cam_dist * math.cos(a), cam_h)
    d = Vector(cam_target) - cam.location
    cam.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
    cam.data.dof.focus_distance = d.length


if "--norender" in args:
    for o in bpy.data.objects:
        if o.name.startswith(("runner","w0","w3","stretcher")): print("OBJ", o.name, [round(v,3) for v in o.location], [round(math.degrees(v),1) for v in o.rotation_euler], [round(v,3) for v in o.dimensions])
    sys.exit(0)
if SPIN:
    for i in range(START, SPIN):
        place_cam(-28 + i * 360 / SPIN)
        sc.render.filepath = os.path.join(out_dir, "frame-%03d.jpg" % i)
        bpy.ops.render.render(write_still=True)
else:
    place_cam(float(opt("--angle", -28)))
    sc.render.filepath = os.path.join(out_dir, "%s-%s.jpg" % (variant, SCENE))
    bpy.ops.render.render(write_still=True)
print("DONE")
