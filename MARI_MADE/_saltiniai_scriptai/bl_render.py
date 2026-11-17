import bpy, math, os, sys
from mathutils import Vector
S=os.environ['SCR']; CAMS=os.environ.get('CAMS','C1').split(','); RES=os.environ.get('RES','480x270'); SPP=int(os.environ.get('SPP','24'))
OUT=os.environ.get('OUT',S+'/renders/test'); BLEND=os.environ.get('BLEND',S+'/blend/render_base.blend')
bpy.ops.wm.open_mainfile(filepath=BLEND)
sc=bpy.context.scene; col=sc.collection
def K(t):  # approx blackbody rgb
    return {2700:(1,0.72,0.42),3000:(1,0.77,0.53),3500:(1,0.83,0.64),4000:(1,0.87,0.73)}[t]
def light(name,typ,loc,power,color=3000,size=0.1,spot=None,blend=0.3,target=None,rot=None,shape=None):
    d=bpy.data.lights.new(name,typ); d.energy=power; d.color=K(color)
    if typ=='AREA': d.size=size; d.shape=shape or 'DISK'
    if typ=='SPOT': d.spot_size=math.radians(spot); d.spot_blend=blend; d.shadow_soft_size=size
    if typ=='POINT': d.shadow_soft_size=size
    o=bpy.data.objects.new(name,d); col.objects.link(o); o.location=loc
    if target: o.rotation_euler=(Vector(target)-Vector(loc)).to_track_quat('-Z','Y').to_euler()
    elif rot: o.rotation_euler=rot
    return o
def disk(name,loc,r,mat):
    bpy.ops.mesh.primitive_circle_add(vertices=48,radius=r,fill_type='NGON',location=loc)
    o=bpy.context.active_object; o.name=name; o.data.materials.append(bpy.data.materials[mat]); return o
# world HDRI
w=bpy.data.worlds.new('W'); sc.world=w; w.use_nodes=True; nt=w.node_tree
env=nt.nodes.new('ShaderNodeTexEnvironment'); env.image=bpy.data.images.load(os.environ.get('HDRI',S+'/tex/urban_street_01.hdr'))
mp=nt.nodes.new('ShaderNodeMapping'); tc=nt.nodes.new('ShaderNodeTexCoord'); mp.inputs['Rotation'].default_value=(0,0,math.radians(float(os.environ.get('HROT','200'))))
nt.links.new(tc.outputs['Generated'],mp.inputs[0]); nt.links.new(mp.outputs[0],env.inputs[0])
bg=nt.nodes['Background']; bg.inputs[1].default_value=float(os.environ.get('HSTR','1.6')); nt.links.new(env.outputs[0],bg.inputs[0])
# downlights (from SVIESTUVU PLANAS, transformed to model coords)
DL=[(3.949,4.084),(5.514,6.524),(7.578,4.153),(10.765,6.895),(13.030,4.067),(16.094,6.801)]
for i,(x,y) in enumerate(DL):
    light(f'Downlight_{i}','SPOT',(x,y,5.97),float(os.environ.get('PDL','260')),3500,size=0.06,spot=55,blend=0.45,rot=(0,0,0))
    disk(f'Downlight_lens_{i}',(x,y,5.995),0.075,'LED sviesa')
# track spots over reception
for i,x in enumerate([7.57,8.48,9.37]):
    light(f'Track_{i}','SPOT',(x,7.0,5.85),420,3000,size=0.03,spot=24,blend=0.5,target=(8.73+(x-8.48)*0.3,7.9,1.6 if i!=1 else 1.1))
# pendant lights inside ceiling drums
for n in ['Nuleidimas1_1','Nuleidimas2_1','Neleidimas3_1']:
    o=bpy.data.objects[n]; bb=[o.matrix_world@Vector(c) for c in o.bound_box]
    cx=sum(v.x for v in bb)/8; cy=sum(v.y for v in bb)/8; zb=min(v.z for v in bb)
    light('Drum_'+n,'AREA',(cx,cy,zb-0.01),float(os.environ.get('PDR','450')),3500,size=1.2,rot=(0,0,0))
    d=disk('Drum_diffuser_'+n,(cx,cy,zb-0.004),0.62,'Difuzorius'); 
# soft bounce fill (simulates light reflected from 6m ceiling/walls)
light('Fill','AREA',(10.0,5.2,5.6),float(os.environ.get('PFILL','700')),3500,size=8.0,rot=(0,0,0),shape='RECTANGLE').data.size_y=3.5
if os.environ.get('EXT'):
    for x in [4.0,17.5]: light('Gatves_zibintas','POINT',(x,-3.2,4.6),550,2700,size=0.15)
    light('Vakaro_dangus','AREA',(10,-9,9),700,4000,size=12,target=(10,1.7,3))
# render settings
sc.render.engine='CYCLES'; cy=sc.cycles; cy.device='CPU'; cy.samples=SPP; cy.use_adaptive_sampling=True; cy.adaptive_threshold=0.015
cy.use_denoising=True; cy.denoiser='OPENIMAGEDENOISE'; cy.max_bounces=10; cy.diffuse_bounces=5; cy.glossy_bounces=4; cy.transmission_bounces=8
cy.caustics_reflective=False; cy.caustics_refractive=False; cy.sample_clamp_indirect=8
try:
    sc.view_settings.view_transform='AgX'; sc.view_settings.look='AgX - Medium High Contrast'
except Exception as e: print('look',e)
sc.view_settings.exposure=float(os.environ.get('EXPO','0.0'))
rx,ry=map(int,RES.split('x')); sc.render.resolution_x=rx; sc.render.resolution_y=ry; sc.render.resolution_percentage=100
sc.render.image_settings.file_format='JPEG'; sc.render.image_settings.quality=95
CAMDEF={
 'C1':((4.9,4.4,2.0),(15.5,6.9,1.5),20),
 'C2':((11.4,4.25,1.55),(3.6,6.7,1.3),20),
 'E1':((11.4,-7.2,1.7),(11.4,2.0,1.7),26),
 'E2':((10.06,-1.5,1.75),(10.06,2.0,1.75),28),
 'C3':((8.73,3.9,1.55),(8.73,7.9,1.55),24),
 'C4':((16.6,7.0,1.6),(7.6,2.5,1.6),19),
}
CAMDEF.update(eval(os.environ.get('EXTRA_CAMS','{}')))
os.makedirs(OUT,exist_ok=True)
for cn in CAMS:
    loc,tgt,lens=CAMDEF[cn]
    c=bpy.data.cameras.new(cn); c.lens=lens; c.sensor_width=36; c.clip_start=0.05
    o=bpy.data.objects.new(cn,c); col.objects.link(o); o.location=loc
    d=Vector(tgt)-Vector(loc); yaw=math.atan2(d.y,d.x)-math.pi/2
    o.rotation_euler=(math.radians(90),0,yaw)   # level camera = straight verticals
    c.shift_y=float(os.environ.get('SHIFT_'+cn,'0'))
    sc.camera=o; sc.render.filepath=f'{OUT}/{cn}.jpg'
    bpy.ops.render.render(write_still=True); print('done',cn,flush=True)
if os.environ.get('SAVE'): bpy.ops.wm.save_as_mainfile(filepath=os.environ['SAVE'])
