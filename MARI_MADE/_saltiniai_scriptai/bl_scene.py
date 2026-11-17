import bpy, bmesh, math, os, sys
from mathutils import Vector
S=os.environ['SCR']; TEX=S+'/tex/'
bpy.ops.wm.open_mainfile(filepath=S+'/blend/scene.blend')
sc=bpy.context.scene; OB=bpy.data.objects
def srgb(h):
    h=h.lstrip('#'); c=[int(h[i:i+2],16)/255 for i in (0,2,4)]
    return tuple(((x+0.055)/1.055)**2.4 if x>0.04045 else x/12.92 for x in c)+(1,)
# ---------- material factory ----------
def mat(name,color='#ffffff',rough=0.5,metal=0.0,tex=None,scale=1.0,tint=True,nstr=0.5,coat=0.0,trans=0.0,ior=1.45,sheen=0.0,emit=None,estr=0.0,alpha=1.0,rot=0.0,bump=None):
    m=bpy.data.materials.get(name) or bpy.data.materials.new(name); m.use_nodes=True; m.use_fake_user=True
    nt=m.node_tree; nt.nodes.clear()
    out=nt.nodes.new('ShaderNodeOutputMaterial'); b=nt.nodes.new('ShaderNodeBsdfPrincipled')
    nt.links.new(b.outputs[0],out.inputs[0])
    b.inputs['Base Color'].default_value=srgb(color); b.inputs['Roughness'].default_value=rough; b.inputs['Metallic'].default_value=metal
    b.inputs['Coat Weight'].default_value=coat; b.inputs['Transmission Weight'].default_value=trans; b.inputs['IOR'].default_value=ior
    b.inputs['Sheen Weight'].default_value=sheen; b.inputs['Alpha'].default_value=alpha
    if emit: b.inputs['Emission Color'].default_value=srgb(emit); b.inputs['Emission Strength'].default_value=estr
    if tex:
        tc=nt.nodes.new('ShaderNodeTexCoord'); mp=nt.nodes.new('ShaderNodeMapping')
        mp.inputs['Scale'].default_value=(scale,scale,scale); mp.inputs['Rotation'].default_value=(0,0,rot)
        nt.links.new(tc.outputs['Object'],mp.inputs[0])
        def img(kind,noncolor):
            p=TEX+f'{tex}_{kind}.jpg'
            if not os.path.exists(p): return None
            n=nt.nodes.new('ShaderNodeTexImage'); n.image=bpy.data.images.load(p,check_existing=True)
            n.projection='BOX'; n.projection_blend=0.2
            if noncolor: n.image.colorspace_settings.name='Non-Color'
            nt.links.new(mp.outputs[0],n.inputs[0]); return n
        d=img('diff',False)
        if d:
            if tint:
                mx=nt.nodes.new('ShaderNodeMix'); mx.data_type='RGBA'; mx.blend_type='MULTIPLY'; mx.inputs['Factor'].default_value=1.0
                # desaturate texture then multiply with color
                hs=nt.nodes.new('ShaderNodeHueSaturation'); hs.inputs['Saturation'].default_value=0.0
                nt.links.new(d.outputs[0],hs.inputs['Color'])
                br=nt.nodes.new('ShaderNodeBrightContrast'); br.inputs['Bright'].default_value=0.35; br.inputs['Contrast'].default_value=-0.5
                nt.links.new(hs.outputs[0],br.inputs['Color'])
                nt.links.new(br.outputs[0],mx.inputs[6]); mx.inputs[7].default_value=srgb(color)
                nt.links.new(mx.outputs[2],b.inputs['Base Color'])
            else:
                hs=nt.nodes.new('ShaderNodeHueSaturation'); hs.inputs['Saturation'].default_value=SAT.get(name,1.0); hs.inputs['Value'].default_value=VAL.get(name,1.0)
                nt.links.new(d.outputs[0],hs.inputs['Color']); nt.links.new(hs.outputs[0],b.inputs['Base Color'])
        r=img('rough',True)
        if r:
            mr=nt.nodes.new('ShaderNodeMapRange'); mr.inputs['To Min'].default_value=max(0,rough-0.15); mr.inputs['To Max'].default_value=min(1,rough+0.15)
            nt.links.new(r.outputs[0],mr.inputs[0]); nt.links.new(mr.outputs[0],b.inputs['Roughness'])
        n=img('nor',True)
        if n:
            nm=nt.nodes.new('ShaderNodeNormalMap'); nm.inputs['Strength'].default_value=nstr
            nt.links.new(n.outputs[0],nm.inputs['Color']); nt.links.new(nm.outputs[0],b.inputs['Normal'])
    if bump:
        tc=nt.nodes.new('ShaderNodeTexCoord'); nz=nt.nodes.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value=bump[0]; nz.inputs['Detail'].default_value=8
        nt.links.new(tc.outputs['Object'],nz.inputs['Vector'])
        bp=nt.nodes.new('ShaderNodeBump'); bp.inputs['Strength'].default_value=bump[1]; bp.inputs['Distance'].default_value=0.002
        nt.links.new(nz.outputs[0],bp.inputs['Height']); nt.links.new(bp.outputs[0],b.inputs['Normal'])
    return m
SAT={'Parketas eglute':0.6,'Azuolas sviesus':0.7}; VAL={'Parketas eglute':1.12,'Azuolas sviesus':1.1}
# palette (MARI MADE: nude, latte, burgundy, warm grey, white, gold)
M={}
M['parquet']=mat('Parketas eglute',tex='herringbone_parquet',tint=False,scale=0.42,rough=0.38,nstr=0.6,coat=0.15)
M['plaster']=mat('Tinkas siltai baltas','#EFEBE6',rough=0.85,tex='painted_plaster_wall',scale=0.6,nstr=0.25)
M['ceiling']=mat('Lubos RAL1013','#E3DACA',rough=0.9,bump=(40,0.05))
M['burgundy']=mat('Bordo dekoratyvinis tinkas','#5E1A22',rough=0.8,tex='plastered_wall_04',scale=0.5,nstr=0.45)
M['latte']=mat('Latte matinis lakas','#CDBEB0',rough=0.42,coat=0.1)
M['nude']=mat('Nude mikrocementas','#D8CBBF',rough=0.7,tex='concrete_floor_02',scale=0.8,nstr=0.15)
M['oak']=mat('Azuolas sviesus',tex='oak_veneer_01',tint=False,scale=1.2,rough=0.45,nstr=0.3,coat=0.1)
M['marble']=mat('Travertino tono marmuras','#E8DCCB',tex='marble_01',scale=0.8,rough=0.25,nstr=0.2,coat=0.3)
M['brass']=mat('Zalvaris sukeltas','#C9A063',rough=0.28,metal=1.0)
M['black']=mat('Juodas metalas','#1C1A19',rough=0.35,metal=0.9)
M['boucle']=mat('Bukle audinys kreminis','#E9E0D2',rough=0.95,tex='fabric_pattern_07',scale=6,nstr=0.9,sheen=0.6)
M['rug']=mat('Vilnonis kilimas','#DCD2C3',rough=1.0,tex='fabric_pattern_07',scale=3,nstr=1.0,sheen=0.5)
M['mirror']=mat('Veidrodis','#FFFFFF',rough=0.02,metal=1.0)
M['glass']=mat('Stiklas','#FFFFFF',rough=0.0,trans=1.0,ior=1.5)
M['frame']=mat('Lango remas bronza','#3A322B',rough=0.4,metal=0.8)
M['stone']=mat('Fasado akmuo smelio','#CDBFA6',rough=0.85,tex='granite_tile',scale=0.35,nstr=0.4)
M['cloth_nude']=mat('Audinys nude','#C4B3A3',rough=0.9,sheen=0.5,bump=(300,0.15))
M['cloth_burg']=mat('Audinys bordo','#6B1E28',rough=0.85,sheen=0.5,bump=(300,0.15))
M['cloth_grey']=mat('Audinys pilkas','#5E5550',rough=0.9,sheen=0.5,bump=(300,0.15))
M['cloth_white']=mat('Audinys baltas','#EDE8E0',rough=0.9,sheen=0.5,bump=(300,0.15))
M['leaf']=mat('Alyvmedzio lapai','#55603F',rough=0.55,sheen=0.2)
M['bark']=mat('Kamienas','#5A4A3A',rough=0.9,bump=(60,0.4))
M['pot']=mat('Vazonas keramika','#BFAF9C',rough=0.6,tex='concrete_floor_02',scale=2,nstr=0.3)
M['soil']=mat('Zeme','#3A2E25',rough=1.0,bump=(200,0.5))
M['stem']=mat('Gelems stiebai','#4F5E35',rough=0.6)
M['diff']=mat('Difuzorius','#FFF4E8',emit='#FFE6CC',estr=3.0,rough=0.5)
M['led']=mat('LED sviesa','#FFE3C2',emit='#FFD9B0',estr=25.0,rough=0.5)
def setmat(obj,mapping,default=None):
    me=obj.data
    for i,m in enumerate(me.materials):
        n=m.name if m else ''
        key=next((v for k,v in mapping.items() if n.startswith(k)),default)
        if key: me.materials[i]=M[key]
# ---------- shell: open windows, facade stone ----------
sh=OB['a1_erdve1']; bm=bmesh.new(); bm.from_mesh(sh.data); bm.faces.ensure_lookup_table()
kill=[]; wins=[]
for f in bm.faces:
    c=f.calc_center_median(); zs=[v.co.z for v in f.verts]; ys=[v.co.y for v in f.verts]
    if abs(f.normal.y)>0.9 and min(ys)>1.93 and max(ys)<2.14 and min(zs)>0.85 and max(zs)-min(zs)>4:
        kill.append(f); wins.append((min(v.co.x for v in f.verts),max(v.co.x for v in f.verts)))
bmesh.ops.delete(bm,geom=kill,context='FACES')
# material slots: add stone
sh.data.materials.append(M['stone']); stone_i=len(sh.data.materials)-1
for f in bm.faces:
    c=f.calc_center_median()
    if c.y<1.80 or (c.y<1.99 and abs(f.normal.y)<0.3 and c.z>0.85): f.material_index=stone_i
bm.to_mesh(sh.data); bm.free()
setmat(sh,{'Sree_Dress_1':'parquet','Sree_Complexion_3':'plaster','Sree_Complexion_2':'oak','Sree_Laptop_1':'plaster','FrontColor':'plaster','Fasado':'stone'})
wx=[]
for a,b in sorted(wins):
    if b-a<0.5: continue
    if wx and a<wx[-1][1]-0.05: wx[-1]=(min(wx[-1][0],a),max(wx[-1][1],b))
    else: wx.append((a,b))
print('windows',wx)
# glass + frames
def box(name,x0,x1,y0,y1,z0,z1,m):
    me=bpy.data.meshes.new(name); bmm=bmesh.new()
    bmesh.ops.create_cube(bmm,size=1.0); 
    for v in bmm.verts: v.co=Vector(((x0+x1)/2+v.co.x*(x1-x0),(y0+y1)/2+v.co.y*(y1-y0),(z0+z1)/2+v.co.z*(z1-z0)))
    bmm.to_mesh(me); bmm.free(); o=bpy.data.objects.new(name,me); sc.collection.objects.link(o); me.materials.append(M[m]); return o
WIN=[(a,b,0.9,6.0,2.05) for a,b in wx]+[(3.56,5.31,0.45,6.0,1.80)]
for i,(a,b,z0,z1,y) in enumerate(WIN):
    box(f'Stiklas_{i}',a+0.03,b-0.03,y-0.006,y+0.006,z0+0.03,z1-0.03,'glass')
    t=0.05
    box(f'Remas_{i}_k',a,a+t,y-0.03,y+0.03,z0,z1,'frame'); box(f'Remas_{i}_d',b-t,b,y-0.03,y+0.03,z0,z1,'frame')
    box(f'Remas_{i}_a',a,b,y-0.03,y+0.03,z0,z0+t,'frame'); box(f'Remas_{i}_v',a,b,y-0.03,y+0.03,z1-t,z1,'frame')
    box(f'Remas_{i}_s',a,b,y-0.03,y+0.03,3.6,3.65,'frame')
# ---------- other objects ----------
setmat(OB['Lubos1'],{'':'ceiling'})
for n in ['Nuleidimas1_1','Nuleidimas2_1','Neleidimas3_1']: setmat(OB[n],{'':'ceiling'})
setmat(OB['G_1_variantas_sienele1'],{'':'burgundy'})
setmat(OB['G_1variantas_lentyna1'],{'Sree__Pearls_2':'latte','Sree_Complexion_2':'oak','Sree_Dress_3':'oak'})
setmat(OB['Lentyna_maza'],{'':'oak'})
setmat(OB['Recepcijos_baldas1'],{'':'latte'}); setmat(OB['Recepcijos_lameles'],{'':'oak'}); setmat(OB['Recepcijos_stalvir_is1'],{'':'marble'})
for n in ['Staliukas1_1','Staliukas2_1','Staliukas3_1']: setmat(OB[n],{'Sree__Pearls_2':'marble','Sree_Complexion_2':'marble','Sree_Complexion_3':'nude','FrontColor':'nude'})
cl=['cloth_nude','cloth_burg','cloth_grey']
for i,n in enumerate(['Componente1','Componente2','Componente3']):
    setmat(OB[n],{'_LC_Clothing_Rack_Material4':'oak','_LC_Clothing_Rack_Material2':'brass','_LC_Clothing_Rack_Material3':cl[i%3],'_LC_Clothing_Rack_Material1':cl[(i+1)%3],'_LC_Clothing_Rack_Material':'cloth_white','Sree_Watch_2':'brass','Sree_Complexion_3':'oak'})
for n in ['Armchair__4_1','Armchair__4_2']: setmat(OB[n],{'linho':'boucle','FrontColor':'oak'})
for n in ['table_basse1','table_basse2']: setmat(OB[n],{'Material1':'marble','M_0136':'black','Material3_1':'marble'})
setmat(OB['Serengueti_Rose_white_120x160_1'],{'':'rug'})
setmat(OB['G_82716_Mirror_Curve_Round_Copper_100cm1'],{'M_1_brushed':'brass','M_0136':'black','M_82717':'mirror'})
setmat(OB['Olive_Tree____Plant1'],{'Material9':'leaf','Material1':'leaf','Material8':'leaf','_8':'leaf','_101':'leaf','soil':'soil','_86':'pot','_1':'pot','_3_1':'pot'},default='bark')
setmat(OB['ARRANJO_VASOS_05_1'],{'Material_2':'glass','Material_3':'glass','Material_13':'glass'},default='stem')
# ---------- logo MARI MADE (replaces 'MARY MADE') ----------
OB['MARY_MADE_1_1'].hide_render=True; OB['MARY_MADE_1_1'].hide_viewport=True
fnt=bpy.data.fonts.load('/usr/share/fonts/truetype/dejavu/DejaVuSans-ExtraLight.ttf') if os.path.exists('/usr/share/fonts/truetype/dejavu/DejaVuSans-ExtraLight.ttf') else bpy.data.fonts.load('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf')
def txt(s,size,z,space):
    cu=bpy.data.curves.new('logo','FONT'); cu.body=s; cu.font=fnt; cu.size=size; cu.align_x='CENTER'; cu.align_y='CENTER'; cu.extrude=0.006; cu.space_character=space
    o=bpy.data.objects.new('Logo_'+s,cu); sc.collection.objects.link(o)
    o.location=(8.73,7.915,z); o.rotation_euler=(math.radians(90),0,0); cu.materials.append(M['brass']); return o
txt('MARI',0.36,1.98,1.45); txt('MADE',0.10,1.70,1.6)
exec(open(S+'/scripts/bl_props.py').read())
bpy.ops.wm.save_as_mainfile(filepath=S+'/blend/render_base.blend')
print('OK scene')
