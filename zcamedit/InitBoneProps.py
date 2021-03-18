import bpy

def CheckGetEditBones(context):
    '''Check if we are editing an armature in the appropriate hierarchy.'''
    if len(context.selected_objects) != 1:
        self.report({'WARNING'}, 'Must have only one object selected')
        return None
    obj = context.selected_objects[0]
    if obj.type != 'ARMATURE' or obj.mode != 'EDIT':
        self.report({'WARNING'}, 'Must be in Edit Mode for an armature')
        return None
    if obj.parent is None or obj.parent.type != 'EMPTY':
        self.report({'WARNING'}, 'Armature must be child of empty object (Cutscene)')
        return None
    if not obj.parent.name.startswith('Cutscene.'):
        self.report({'WARNING'}, 'Empty parent must be named "Cutscene.<YourCutsceneName>"')
        return None
    arm = obj.data
    if len(arm.edit_bones) == 0:
        self.report({'WARNING'}, 'Armature must contain some bones')
        return None
    return arm.edit_bones

class ZCAMEDIT_OT_init_bone_props(bpy.types.Operator):
    '''Click here after any time you add bones.'''
    bl_idname = 'zcamedit.init_bone_props'
    bl_label = 'Init Bone Props'
        
    def execute(self, context):
        edit_bones = CheckGetEditBones(context)
        if edit_bones is None:
            return {'CANCELLED'}
        for eb in edit_bones:
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
        edit_bones = CheckGetEditBones(context)
        if edit_bones is None:
            return {'CANCELLED'}
        for eb in edit_bones:
            eb.roll = 0.0
        return {'FINISHED'}
        

class ZCAMEDIT_PT_init_bone_props_panel(bpy.types.Panel):
    bl_label = 'zcamedit Bone Init'
    bl_idname = 'ZCAMEDIT_PT_init_bone_props_panel'
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = 'bone'
    
    def draw(self, context):
        layout = self.layout
        row = layout.row()
        row.operator('zcamedit.init_bone_props')
        row = layout.row()
        row.operator('zcamedit.reset_bone_rolls')

def InitBoneProps_register():
    bpy.utils.register_class(ZCAMEDIT_OT_init_bone_props)
    bpy.utils.register_class(ZCAMEDIT_OT_reset_bone_rolls)
    bpy.utils.register_class(ZCAMEDIT_PT_init_bone_props_panel)
    
def InitBoneProps_unregister():
    bpy.utils.unregister_class(ZCAMEDIT_PT_init_bone_props_panel)
    bpy.utils.unregister_class(ZCAMEDIT_OT_reset_bone_rolls)
    bpy.utils.unregister_class(ZCAMEDIT_OT_init_bone_props)
    
