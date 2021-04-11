import bpy

def CheckGetArmO(op, context):
    '''Check if we are editing an armature in the appropriate hierarchy.'''
    armo = context.view_layer.objects.active
    if armo is None or armo.type != 'ARMATURE' or armo.mode != 'EDIT':
        if op: op.report({'WARNING'}, 'Must be in Edit Mode for an armature')
        return None
    if armo.parent is None or armo.parent.type != 'EMPTY':
        if op: op.report({'WARNING'}, 'Armature must be child of empty object (Cutscene)')
        return None
    if not armo.parent.name.startswith('Cutscene.'):
        if op: op.report({'WARNING'}, 'Empty parent must be named "Cutscene.<YourCutsceneName>"')
        return None
    arm = armo.data
    if len(arm.edit_bones) == 0:
        if op: op.report({'WARNING'}, 'Armature must contain some bones')
        return None
    return armo

class ZCAMEDIT_OT_init_arm_props(bpy.types.Operator):
    '''Click here after any time you add bones.'''
    bl_idname = 'zcamedit.init_arm_props'
    bl_label = 'Init Armature & Bone Props'
        
    def execute(self, context):
        armo = CheckGetArmO(self, context)
        if armo is None:
            return {'CANCELLED'}
        arm_props = {'start_frame': 10, 'rel_link': False}
        bone_props = {'frames': 20, 'fov': 60.0, 'camroll': 0}
        for p in arm_props:
            if p not in armo:
                armo[p] = arm_props[p]
        for eb in armo.data.edit_bones:
            for p in bone_props:
                if p not in eb:
                    eb[p] = bone_props[p]
        return {'FINISHED'}


class ZCAMEDIT_PT_arm_panel(bpy.types.Panel):
    bl_label = 'zcamedit Armature Controls'
    bl_idname = 'ZCAMEDIT_PT_arm_panel'
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = 'data'
    
    def draw(self, context):
        layout = self.layout
        if not CheckGetArmO(None, context):
            layout.label(text='Go into Edit Mode for an armature')
            layout.label(text='Must be parented to cutscene object')
        else:
            layout.operator('zcamedit.init_arm_props')

def ArmControls_register():
    bpy.utils.register_class(ZCAMEDIT_OT_init_arm_props)
    bpy.utils.register_class(ZCAMEDIT_PT_arm_panel)
    
def ArmControls_unregister():
    bpy.utils.unregister_class(ZCAMEDIT_PT_arm_panel)
    bpy.utils.unregister_class(ZCAMEDIT_OT_init_arm_props)
    
