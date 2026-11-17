# merchandising props (executed inside bl_scene.py namespace)
import random; random.seed(7)
PAL=['#C4B3A3','#6B1E28','#5E5550','#EDE8E0','#B59A7C','#8A7A6E','#D8CBBF']
pm={c:mat('Preke '+c,c,rough=0.92,sheen=0.6,bump=(260,0.25)) for c in PAL}
pm['box_b']=mat('Dezute bordo','#5A1820',rough=0.45,coat=0.2); pm['box_o']=mat('Dezute alyvine','#4C4F33',rough=0.45,coat=0.2)
def rbox(name,cx,cy,z0,w,d,h,m,rotz=0.0,bev=0.012):
    me=bpy.data.meshes.new(name); bmm=bmesh.new(); bmesh.ops.create_cube(bmm,size=1.0)
    for v in bmm.verts: v.co=Vector((v.co.x*w,v.co.y*d,v.co.z*h+h/2))
    bmm.to_mesh(me); bmm.free(); o=bpy.data.objects.new(name,me); sc.collection.objects.link(o)
    o.location=(cx,cy,z0); o.rotation_euler=(0,0,rotz); me.materials.append(m)
    b=o.modifiers.new('bev','BEVEL'); b.width=min(bev,h*0.45); b.segments=3; return o
def stack(cx,cy,z0,n=None,w=0.30,d=0.24,rot=0.0):
    n=n or random.randint(3,6); z=z0; c=random.choice(PAL)
    for k in range(n):
        if random.random()<0.35: c=random.choice(PAL)
        h=random.uniform(0.035,0.05)
        rbox('Megztinis',cx+random.uniform(-.008,.008),cy+random.uniform(-.008,.008),z,w,d,h,pm[c],rot+random.uniform(-.03,.03),bev=0.018); z+=h
def gift(cx,cy,z0,rot=0.0):
    for k,(w,h) in enumerate([(0.24,0.10),(0.18,0.08),(0.13,0.06)]):
        if random.random()<0.8:
            rbox('Dovanu_dezute',cx,cy,z0,w,w*0.8,h,pm[random.choice(['box_b','box_o'])],rot+random.uniform(-.2,.2),bev=0.004); z0+=h
# niche shelves (x0,x1,y0,y1,[z...])
NICH=[(11.56,12.24,7.43,7.92,[1.37,1.90,2.43]),(13.60,14.25,7.43,7.92,[0.96,1.49,2.02,2.55]),(15.73,16.46,7.43,7.92,[1.00,1.53,2.06,2.59])]
for x0,x1,y0,y1,zs in NICH:
    for z in zs:
        r=random.random()
        if r<0.65: stack((x0+x1)/2,(y0+y1)/2+0.02,z)
        else: gift((x0+x1)/2,(y0+y1)/2,z)
for z in [0.98,1.51,2.04,2.57]:
    if random.random()<0.6: stack(17.47,3.79,z,w=0.24,d=0.30,rot=math.pi/2)
    else: gift(17.47,3.79,z)
# display tables: stacks + jewellery trays
for cx,cy in [(15.39,4.82),(13.13,5.90),(11.20,4.70)]:
    stack(cx-0.45,cy+0.05,1.0,n=random.randint(3,5)); stack(cx-0.1,cy-0.05,1.0,n=random.randint(2,4))
    tr=rbox('Padeklas',cx+0.42,cy,1.0,0.30,0.22,0.012,M['marble'],0.2,bev=0.004)
    for k in range(5):
        bpy.ops.mesh.primitive_torus_add(major_radius=random.uniform(0.016,0.028),minor_radius=0.0032,location=(cx+0.32+0.05*k,cy+random.uniform(-.05,.05),1.016),rotation=(math.radians(random.uniform(0,25)),0,random.uniform(0,3)))
        bpy.context.active_object.data.materials.append(M['brass'])
    gift(cx+0.10,cy+0.25,1.0)
# reception: gift boxes + tablet
gift(7.95,6.85,1.141)
# ---- more shelf fill (right-back corner boards, small shelf) ----
for z in [0.60,1.13,1.66,2.19]:
    if random.random()<0.7: stack(17.47,6.95,z,w=0.26,d=0.32,rot=math.pi/2)
    else: gift(17.47,6.95,z)
gift(17.45,5.6,0.929); stack(17.45,4.9,0.929,n=3,w=0.24,d=0.30,rot=math.pi/2)
# ================= VITRINA (window display concept) =================
WX=[(6.665,7.857),(9.465,10.654),(12.263,13.465),(15.128,16.303)]
M['velvet_b']=mat('Bordo aksomas','#5A1720',rough=0.9,sheen=1.0,bump=(400,0.1))
M['velvet_n']=mat('Nude aksomas','#CDB6A2',rough=0.9,sheen=1.0,bump=(400,0.1))
M['halo']=mat('LED aureole','#FFE2BF',emit='#FFD7A8',estr=18.0)
M['vinyl']=mat('Aukso pleve','#C9A063',rough=0.35,metal=1.0)
M['trav']=mat('Travertinas','#DCCDB8',tex='marble_01',scale=1.5,rough=0.5,nstr=0.6)
def arch_panel(name,cx,y,w,z0,h,thick,m):
    import bmesh as _b
    r=w/2; pts=[(-r,0),(r,0)]
    for k in range(0,33): a=math.pi*k/32; pts.append((r*math.cos(a), h-r+r*math.sin(a)))
    pts=[pts[0],pts[1]]+pts[2:]
    me=bpy.data.meshes.new(name); bmm=_b.new()
    vs=[bmm.verts.new((cx+x,y,z0+z)) for x,z in pts]
    f=bmm.faces.new(vs); _b.ops.extrude_face_region(bmm,geom=[f])
    for v in bmm.verts:
        if abs(v.co.y-y)<1e-9 and v not in vs: pass
    bmm.verts.ensure_lookup_table()
    for v in bmm.verts[len(vs):]: v.co.y=y+thick
    _b.ops.recalc_face_normals(bmm,faces=bmm.faces); bmm.to_mesh(me); bmm.free()
    o=bpy.data.objects.new(name,me); sc.collection.objects.link(o); me.materials.append(m); return o
def arch_halo(name,cx,y,w,z0,h,m):
    r=w/2; pts=[(-r,0)]+[(-r*math.cos(math.pi*k/40), h-r+r*math.sin(math.pi*k/40)) for k in range(41)]+[(r,0)]
    cu=bpy.data.curves.new(name,'CURVE'); cu.dimensions='3D'; cu.bevel_depth=0.008
    sp=cu.splines.new('POLY'); sp.points.add(len(pts)-1)
    for p,(x,z) in zip(sp.points,pts): p.co=(cx+x,y,z0+z,1)
    o=bpy.data.objects.new(name,cu); sc.collection.objects.link(o); cu.materials.append(m); return o
def cyl(name,cx,cy,z0,r,h,m):
    bpy.ops.mesh.primitive_cylinder_add(vertices=64,radius=r,depth=h,location=(cx,cy,z0+h/2))
    o=bpy.context.active_object; o.name=name; o.data.materials.append(m)
    b=o.modifiers.new('bev','BEVEL'); b.width=0.006; b.segments=3; return o
for i,(x0,x1) in enumerate(WX):
    cx=(x0+x1)/2; w=x1-x0-0.26; zs=0.9
    m=M['velvet_b'] if i%2==0 else M['velvet_n']
    arch_panel(f'Vitrina_arka_{i}',cx,2.56,w,zs,2.75,0.04,m)
    arch_halo(f'Vitrina_aureole_{i}',cx,2.55,w+0.04,zs,2.77,M['halo'])
    # plinths
    hs=[(0.65,0.20,-0.22),(0.40,0.24,0.18),(0.22,0.17,-0.02)]
    for k,(h,r,dx) in enumerate(hs): cyl(f'Vitrina_podiumas_{i}_{k}',cx+dx,2.38+0.04*k,zs,r,h,M['trav'])
    stack(cx-0.22,2.38,zs+0.65,n=4,w=0.28,d=0.22)
    gift(cx+0.18,2.42,zs+0.40)
    if i%2==1:
        # giant gold hoop earring, suspended
        bpy.ops.mesh.primitive_torus_add(major_radius=0.36,minor_radius=0.032,major_segments=96,minor_segments=24,location=(cx,2.30,zs+2.25),rotation=(math.radians(90),0,0))
        hp=bpy.context.active_object; hp.name=f'Vitrina_auskaras_{i}'; hp.data.materials.append(M['brass'])
        cyl(f'Vitrina_lynas_{i}',cx,2.30,zs+2.61,0.0015,2.45,M['black'])
    else:
        # small gold hoops on top plinth + vinyl wordmark on glass
        for k in range(3):
            bpy.ops.mesh.primitive_torus_add(major_radius=0.05+0.015*k,minor_radius=0.006,location=(cx-0.02+0.04*k,2.40,zs+0.22+0.05+0.03*k),rotation=(math.radians(80),0,0))
            bpy.context.active_object.data.materials.append(M['brass'])
    for t,sz,zz,sp in [('MARI',0.16,2.15,1.5),('MADE',0.045,2.03,1.6)]:
        cu=bpy.data.curves.new('vinyl','FONT'); cu.body=t; cu.font=fnt; cu.size=sz; cu.align_x='CENTER'; cu.align_y='CENTER'; cu.extrude=0.0004; cu.space_character=sp
        o=bpy.data.objects.new('Vitrina_pleve_'+t,cu); sc.collection.objects.link(o); o.location=(cx,2.041,zz); o.rotation_euler=(math.radians(90),0,0); cu.materials.append(M['vinyl'])
# ================= EXTERIOR: rusticated facade, sidewalk, street =================
fac=mat('Fasadas rustikuotas','#CEC6B6',rough=0.85,tex='plastered_wall_04',scale=0.4,nstr=0.3)
nt=fac.node_tree; bsdf=[n for n in nt.nodes if n.type=='BSDF_PRINCIPLED'][0]
tc=nt.nodes.new('ShaderNodeTexCoord'); wv=nt.nodes.new('ShaderNodeTexWave'); wv.wave_type='BANDS'; wv.bands_direction='Z'; wv.wave_profile='SAW'
wv.inputs['Scale'].default_value=0.38; wv.inputs['Distortion'].default_value=0.0
nt.links.new(tc.outputs['Object'],wv.inputs['Vector'])
cr=nt.nodes.new('ShaderNodeValToRGB'); cr.color_ramp.elements[0].position=0.0; cr.color_ramp.elements[1].position=0.06
nt.links.new(wv.outputs['Fac'],cr.inputs[0])
bp=nt.nodes.new('ShaderNodeBump'); bp.inputs['Strength'].default_value=0.8; bp.inputs['Distance'].default_value=0.01
nt.links.new(cr.outputs[0],bp.inputs['Height'])
nm=[l for l in nt.links if l.to_socket==bsdf.inputs['Normal']]
if nm: nt.links.new(nm[0].from_socket,bp.inputs['Normal'])
nt.links.new(bp.outputs[0],bsdf.inputs['Normal'])
M['stone'].node_tree.nodes.clear()
sh.data.materials[stone_i]=fac
sw=mat('Saligatvis granitas','#9C978F',tex='granite_tile',tint=False,scale=0.5,rough=0.6,nstr=0.5)
road=mat('Asfaltas','#2E2D2C',rough=0.9,bump=(80,0.3))
rbox('Saligatvis',10,-2.5,0.15,40,8.6,0.15,sw,bev=0.0)
rbox('Gatve',10,-11,0.0,40,8.4,0.12,road,bev=0.0)
rbox('Fasadas_virs',9.9,1.6,6.0,16.4,0.5,2.4,fac,bev=0.0)
rbox('Karnizas',9.9,1.45,6.0,16.4,0.3,0.18,fac,bev=0.02)
for x in [1.0,18.8]: rbox('Fasadas_sonas',x,1.6,0.3,1.8,0.5,8.1,fac,bev=0.0)
