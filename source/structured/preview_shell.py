import bpy, math, pathlib
from mathutils import Vector
root=pathlib.Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(root/'cloud_coat.blend'))
s=bpy.context.scene
s.render.engine='BLENDER_WORKBENCH'
s.display.shading.light='STUDIO'
s.display.shading.color_type='SINGLE'
s.display.shading.single_color=(.22,.24,.30)
s.display.shading.show_cavity=True
s.display.shading.cavity_type='BOTH'
s.display.shading.curvature_ridge_factor=1.65
s.display.shading.curvature_valley_factor=1.4
s.render.resolution_x=520;s.render.resolution_y=580;s.render.resolution_percentage=100
c=bpy.data.cameras.new('Survey'); o=bpy.data.objects.new('Survey',c);s.collection.objects.link(o);s.camera=o;c.type='ORTHO';c.ortho_scale=2.15
for n,p in [('front',(0,-5,.16)),('three-quarter',(2,-4,.68)),('side',(5,0,.16)),('back',(0,5,.16))]:
 o.location=p;o.rotation_euler=(Vector((0,0,.13))-o.location).to_track_quat('-Z','Y').to_euler()
 s.render.filepath=str(root/f'shell-{n}.png')
 bpy.ops.render.render(write_still=True)
