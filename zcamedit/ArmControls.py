import bpy
from bpy.props import FloatProperty, IntProperty, EnumProperty

class ZCAMEDIT_PT_arm_panel(bpy.types.Panel):
    bl_label = 'zcamedit Cutscene Camera Controls'
    bl_idname = 'ZCAMEDIT_PT_arm_panel'
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = 'object'
    bl_options = {'HIDE_HEADER'}
    
    def draw(self, context):
        obj = context.view_layer.objects.active
        if obj is None or obj.type != 'ARMATURE': return
        box = self.layout.box()
        box.label(text = 'zcamedit Cutscene Camera Controls')
        box.prop(obj, 'start_frame')
        box.prop(obj, 'cam_mode', expand = True)
        abone = obj.data.bones.active
        if abone is not None and obj.mode == 'EDIT':
            box.label(text = 'Bone / Key point:')
            r = box.row()
            r.prop(abone, 'frames')
            r.prop(abone, 'fov')
            r.prop(abone, 'camroll')

def ArmControls_register():
    bpy.utils.register_class(ZCAMEDIT_PT_arm_panel)
    bpy.types.Bone.frames = bpy.props.IntProperty(
        name='Frames', description='Key point frames value',
        default=20, min=0)
    bpy.types.Bone.fov = bpy.props.FloatProperty(
        name='FoV', description='Field of view (degrees)',
        default=60.0, min=0.01, max=179.99)
    bpy.types.Bone.camroll = bpy.props.IntProperty(
        name='Roll', description='Camera roll (degrees), positive turns image clockwise',
        default=0, min=-0x80, max=0x7F)
    bpy.types.Armature.start_frame = bpy.props.IntProperty(
        name='Start Frame', description='Shot start frame',
        default=0, min=0)
    bpy.types.Armature.cam_mode = bpy.props.EnumProperty(items = [
        ('normal', 'Normal', 'Normal (0x1 / 0x2)'),
        ('rel_link', 'Rel. Link', 'Relative to Link (0x5 / 0x6)'),
        ('0708', '0x7/0x8', 'Not Yet Understood Mode (0x7 / 0x8)')],
        name='Mode', description='Camera command mode', default='normal')
    
    
def ArmControls_unregister():
    del bpy.types.Armature.cam_mode
    del bpy.types.Armature.start_frame
    del bpy.types.Bone.camroll
    del bpy.types.Bone.fov
    del bpy.types.Bone.frames
    bpy.utils.unregister_class(ZCAMEDIT_PT_arm_panel)
    
