import bpy
from bpy_extras.io_utils import ImportHelper, ExportHelper
from bpy.props import StringProperty, BoolProperty

class ZCAMEDIT_OT_import_c(bpy.types.Operator, ImportHelper):
    '''Import cutscene camera data from a Zelda 64 scene C source file.'''
    bl_idname = 'zcamedit.import_c'
    bl_label = 'Import From C'
    
    filename_ext = '.c'
    filter_glob: StringProperty(default='*.c', options={'HIDDEN'}, maxlen=4096)
    
    def execute(self, context):
        #return CImport(context, self.filepath)
        return {'FINISHED'} #TODO

class ZCAMEDIT_OT_export_c(bpy.types.Operator, ExportHelper):
    '''Export cutscene camera into a Zelda 64 scene C source file.'''
    bl_idname = 'zcamedit.export_c'
    bl_label = 'Export Into C'
    
    filename_ext = '.c'
    filter_glob: StringProperty(default='*.c', options={'HIDDEN'}, maxlen=4096)
    
    use_floats: BoolProperty(
        name='Use Floats',
        description='Write FOV value as floating point (e.g. 45.0f). If False, write as integer (e.g. 0x42340000)',
        default=False
    )
    use_tabs: BoolProperty(
        name='Use Tabs',
        description='Indent commands with tabs rather than 4 spaces. For decomp toolchain compatibility',
        default=True
    )
    
    def execute(self, context):
        #return CExport(context, self.filepath, use_floats, use_tabs)
        return {'FINISHED'} #TODO

def menu_func_import(self, context):
    self.layout.operator(ZCAMEDIT_OT_import_c.bl_idname, text='Z64 cutscene C source (.c)')

def menu_func_export(self, context):
    self.layout.operator(ZCAMEDIT_OT_export_c.bl_idname, text='Z64 cutscene C source (.c)')

def ImportExportControls_register():
    bpy.utils.register_class(ZCAMEDIT_OT_import_c)
    bpy.utils.register_class(ZCAMEDIT_OT_export_c)
    bpy.types.TOPBAR_MT_file_import.append(menu_func_import)
    bpy.types.TOPBAR_MT_file_export.append(menu_func_export)

def ImportExportControls_unregister():
    bpy.types.TOPBAR_MT_file_export.remove(menu_func_export)
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)
    bpy.utils.unregister_class(ZCAMEDIT_OT_export_c)
    bpy.utils.unregister_class(ZCAMEDIT_OT_import_c)
