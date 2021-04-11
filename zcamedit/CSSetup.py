import bpy

from .Common import *

def CheckGetCSObj(op, context):
    '''Check if we are editing a cutscene.'''
    if len(context.selected_objects) != 1:
        op.report({'WARNING'}, 'Must have only one object selected')
        return None
    cso = context.selected_objects[0]
    if cso.type != 'EMPTY':
        op.report({'WARNING'}, 'Must have an empty object selected')
        return None
    if not cso.name.startswith('Cutscene.'):
        op.report({'WARNING'}, 'Cutscene empty object must be named "Cutscene.<YourCutsceneName>"')
        return None
    return cso


class ZCAMEDIT_OT_init_cs(bpy.types.Operator):
    '''Click here after adding an empty Cutscene.YourCutsceneName'''
    bl_idname = 'zcamedit.init_cs'
    bl_label = 'Init Cutscene Empty'
    
    def execute(self, context):
        cso = CheckGetCSObj(self, context)
        if cso is None:
            return {'CANCELLED'}
        InitCS(context, cso)
        return {'FINISHED'}


class ZCAMEDIT_PT_init_cs_panel(bpy.types.Panel):
    bl_label = 'zcamedit Cutscene Controls'
    bl_idname = 'ZCAMEDIT_PT_init_cs_panel'
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = 'object'
    
    def draw(self, context):
        layout = self.layout
        layout.row().prop(context.scene, 'ootBlenderScale')
        layout.row().prop(context.scene, 'zcamedit_previewlinkage')
        layout.row().operator('zcamedit.init_cs')

def CSSetup_register():
    bpy.utils.register_class(ZCAMEDIT_OT_init_cs)
    bpy.utils.register_class(ZCAMEDIT_PT_init_cs_panel)
    if not hasattr(bpy.types.Scene, 'ootBlenderScale'):
        bpy.types.Scene.ootBlenderScale = FloatProperty(
            name='Scale',
            description='All stair steps in game are 10 units high. Assuming Hylian ' + \
                'carpenters follow US building codes, that\'s about 17 cm or a scale of about ' + \
                '56 if your scene is in meters.',
            soft_min=1.0, soft_max=1000.0,
            default=56.0
        )
    bpy.types.Scene.zcamedit_previewlinkage = EnumProperty(
        items=[
            ('link_adult', 'Adult', 'Adult Link (170 cm)', 0),
            ('link_child', 'Child', 'Child Link (130 cm)', 1)],
        name='Link age for preview',
        description='For setting Link\'s height for preview', 
        default='link_adult'
    )
    
def CSSetup_unregister():
    del bpy.types.Scene.zcamedit_previewlinkage
    bpy.utils.unregister_class(ZCAMEDIT_PT_init_cs_panel)
    bpy.utils.unregister_class(ZCAMEDIT_OT_init_cs)
    
