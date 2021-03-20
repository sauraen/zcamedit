import bpy

def CheckGetArmO(op, context):
    '''Check if we are editing an armature in the appropriate hierarchy.'''
    if len(context.selected_objects) != 1:
        op.report({'WARNING'}, 'Must have only one object selected')
        return None
    armo = context.selected_objects[0]
    if armo.type != 'ARMATURE' or armo.mode != 'EDIT':
        op.report({'WARNING'}, 'Must be in Edit Mode for an armature')
        return None
    if armo.parent is None or armo.parent.type != 'EMPTY':
        op.report({'WARNING'}, 'Armature must be child of empty object (Cutscene)')
        return None
    if not armo.parent.name.startswith('Cutscene.'):
        op.report({'WARNING'}, 'Empty parent must be named "Cutscene.<YourCutsceneName>"')
        return None
    arm = armo.data
    if len(arm.edit_bones) == 0:
        op.report({'WARNING'}, 'Armature must contain some bones')
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
        if 'start_frame' not in armo:
            armo['start_frame'] = 10
        if 'end_frame' not in armo:
            armo['end_frame'] = 100
        for eb in armo.data.edit_bones:
            if 'frames' not in eb:
                eb['frames'] = 20
            if 'fov' not in eb:
                eb['fov'] = 60
        return {'FINISHED'}
        
class ZCAMEDIT_OT_reset_bone_rolls(bpy.types.Operator):
    '''Click to reset all bones' roll (Z rotation) to zero.'''
    bl_idname = 'zcamedit.reset_bone_rolls'
    bl_label = 'Reset All Bone Rolls'
    
    def execute(self, context):
        arm = CheckGetArmO(self, context)
        if armo is None:
            return {'CANCELLED'}
        for eb in armo.data.edit_bones:
            eb.roll = 0.0
        return {'FINISHED'}
        

class ZCAMEDIT_PT_arm_panel(bpy.types.Panel):
    bl_label = 'zcamedit Armature Controls'
    bl_idname = 'ZCAMEDIT_PT_arm_panel'
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = 'armature'
    
    def draw(self, context):
        layout = self.layout
        row = layout.row()
        row.operator('zcamedit.init_arm_props')
        row = layout.row()
        row.operator('zcamedit.reset_bone_rolls')

def ArmControls_register():
    bpy.utils.register_class(ZCAMEDIT_OT_init_arm_props)
    bpy.utils.register_class(ZCAMEDIT_OT_reset_bone_rolls)
    bpy.utils.register_class(ZCAMEDIT_PT_arm_panel)
    
def ArmControls_unregister():
    bpy.utils.unregister_class(ZCAMEDIT_PT_arm_panel)
    bpy.utils.unregister_class(ZCAMEDIT_OT_reset_bone_rolls)
    bpy.utils.unregister_class(ZCAMEDIT_OT_init_arm_props)
    