import bpy
import random

from .Common import *

def CheckGetCSObj(op, context):
    '''Check if we are editing a cutscene.'''
    cs_object = context.view_layer.objects.active
    if cs_object is None or cs_object.type != 'EMPTY':
        if op: op.report({'WARNING'}, 'Must have an empty object active (selected)')
        return None
    if not cs_object.name.startswith('Cutscene.'):
        if op: op.report({'WARNING'}, 'Cutscene empty object must be named "Cutscene.<YourCutsceneName>"')
        return None
    return cs_object
    
def CheckGetActionList(op, context):
    '''Check if we are editing an action list or a action point.'''
    al_object = context.view_layer.objects.active
    if al_object is None or al_object.type != 'EMPTY':
        if op: op.report({'WARNING'}, 'Must have an empty object active (selected)')
        return None
    if al_object.parent is not None and 'start_frame' in al_object and 'action_id' in al_object:
        # We have one of the points selected, not the list
        al_object = al_object.parent
    if not any(al_object.name.startswith(s) for s in ['Path.', 'ActionList.']):
        if op: op.report({'WARNING'}, 'Action list name must start with Path. or ActionList.')
        return None
    if al_object.parent is None or al_object.parent.type != 'EMPTY' or not al_object.parent.name.startswith('Cutscene.'):
        if op: op.report({'WARNING'}, 'Action list must be child of cutscene')
        return None
    return al_object

class ZCAMEDIT_OT_init_cs(bpy.types.Operator):
    '''Click here after adding an empty Cutscene.YourCutsceneName'''
    bl_idname = 'zcamedit.init_cs'
    bl_label = 'Init Cutscene Empty'
    
    def execute(self, context):
        cs_object = CheckGetCSObj(self, context)
        if cs_object is None:
            return {'CANCELLED'}
        InitCS(context, cs_object)
        return {'FINISHED'}

class ZCAMEDIT_OT_create_link_action(bpy.types.Operator):
    '''Create a cutscene action list for Link'''
    bl_idname = 'zcamedit.create_link_action'
    bl_label = 'Create Link action list'
    
    def execute(self, context):
        cs_object = CheckGetCSObj(self, context)
        if cs_object is None:
            return {'CANCELLED'}
        CreateActorAction(context, 'ActionList.Link', cs_object)
        return {'FINISHED'}
        
class ZCAMEDIT_OT_create_actor_action(bpy.types.Operator):
    '''Create a cutscene action list for an actor (NPC)'''
    bl_idname = 'zcamedit.create_actor_action'
    bl_label = 'Create actor (NPC) action list'
    
    def execute(self, context):
        cs_object = CheckGetCSObj(self, context)
        if cs_object is None:
            return {'CANCELLED'}
        actorid = random.randint(1, 100)
        CreateActorAction(context, 'ActionList.Actor' + str(actorid), cs_object)
        for o in context.blend_data.objects:
            if o.type != 'EMPTY': continue
            if o.parent != cs_object: continue
            if o.name != 'Preview.Actor' + str(actorid): continue
            break
        else:
            actor_preview = CreateObject(context, 'Preview.Actor' + str(actorid), None, False)
            actor_preview.parent = cs_object
            actor_preview.empty_display_type = 'SINGLE_ARROW'
            actor_preview.empty_display_size = MetersToBlend(context, 1.5)
        return {'FINISHED'}

class ZCAMEDIT_OT_add_action_point(bpy.types.Operator):
    '''Add a point to a Link or actor action list'''
    bl_idname = 'zcamedit.add_action_point'
    bl_label = 'Add point to current action'

    def execute(self, context):
        al_object = CheckGetActionList(self, context)
        if al_object is None:
            return {'CANCELLED'}
        AddActionPoint(context, al_object)
        return {'FINISHED'}

class ZCAMEDIT_PT_cs_controls_panel(bpy.types.Panel):
    bl_label = 'zcamedit Cutscene Controls'
    bl_idname = 'ZCAMEDIT_PT_cs_controls_panel'
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = 'object'
    
    def draw(self, context):
        layout = self.layout
        if CheckGetCSObj(None, context):
            layout.prop(context.scene, 'ootBlenderScale')
            layout.prop(context.scene, 'zcamedit_previewlinkage')
            layout.operator('zcamedit.init_cs')
            layout.operator('zcamedit.create_link_action')
            layout.operator('zcamedit.create_actor_action')
        elif CheckGetActionList(None, context):
            layout.operator('zcamedit.add_action_point')
        else:
            layout.label(text='Make active (select) a cutscene object')
            layout.label(text='(Empty object named "Cutscene.XXXXX")')

def CSControls_register():
    bpy.utils.register_class(ZCAMEDIT_OT_init_cs)
    bpy.utils.register_class(ZCAMEDIT_OT_create_link_action)
    bpy.utils.register_class(ZCAMEDIT_OT_create_actor_action)
    bpy.utils.register_class(ZCAMEDIT_OT_add_action_point)
    bpy.utils.register_class(ZCAMEDIT_PT_cs_controls_panel)
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
    
def CSControls_unregister():
    del bpy.types.Scene.zcamedit_previewlinkage
    bpy.utils.unregister_class(ZCAMEDIT_PT_cs_controls_panel)
    bpy.utils.unregister_class(ZCAMEDIT_OT_add_action_point)
    bpy.utils.unregister_class(ZCAMEDIT_OT_create_actor_action)
    bpy.utils.unregister_class(ZCAMEDIT_OT_create_link_action)
    bpy.utils.unregister_class(ZCAMEDIT_OT_init_cs)
    
