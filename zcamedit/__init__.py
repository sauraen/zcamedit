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
from .InitBoneProps import InitBoneProps_register, InitBoneProps_unregister
from .CamMotion import CamMotion_register, CamMotion_unregister

def register():
    InitBoneProps_register()
    CamMotion_register()

def unregister():
    CamMotion_unregister()
    InitBoneProps_unregister()

if __name__ == '__main__':
    register()
