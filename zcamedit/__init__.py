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
from .ArmControls import ArmControls_register, ArmControls_unregister
from .CamMotion import CamMotion_register, CamMotion_unregister

def register():
    ArmControls_register()
    CamMotion_register()

def unregister():
    CamMotion_unregister()
    ArmControls_unregister()

if __name__ == '__main__':
    register()
