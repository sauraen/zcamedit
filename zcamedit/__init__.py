bl_info = {
    'name': 'zcamedit',
    'author': 'Sauraen',
    'version': (0, 1),
    'blender': (2, 80, 0),
    'description': 'Zelda 64 Cutscene Camera Editor',
    'warning': '',
    'doc_url': 'https://github.com/sauraen/zcamedit',
    'category': 'N64'
}

import bpy
from .CSControls import CSControls_register, CSControls_unregister
from .CamControls import CamControls_register, CamControls_unregister
from .ActionControls import ActionControls_register, ActionControls_unregister
from .Preview import Preview_register, Preview_unregister
from .ImportExportControls import ImportExportControls_register, ImportExportControls_unregister

def register():
    CSControls_register()
    CamControls_register()
    ActionControls_register()
    ImportExportControls_register()
    Preview_register()

def unregister():
    Preview_unregister()
    ImportExportControls_unregister()
    ActionControls_unregister()
    CamControls_unregister()
    CSControls_unregister()

if __name__ == '__main__':
    register()
