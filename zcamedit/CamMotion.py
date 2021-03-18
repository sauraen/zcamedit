import bpy
from bpy.app.handlers import persistent

def GetCutsceneCamera(scene):
    for o in scene.objects:
        if o.type == 'CAMERA' and o.name == 'CutsceneCam':
            return o
    return None

@persistent
def CamMotionFrameHandler(scene):
    print('Frame Change', scene.frame_current)
    camo = GetCutsceneCamera(scene)
    if camo is None:
        return
    cam = camo.data
    

def CamMotion_register():
    bpy.app.handlers.frame_change_pre.append(CamMotionFrameHandler)

def CamMotion_unregister():
    if CamMotionFrameHandler in bpy.app.handlers.frame_change_pre:
        bpy.app.handlers.frame_change_pre.remove(CamMotionFrameHandler)
