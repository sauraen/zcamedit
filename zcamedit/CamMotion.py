import bpy
import math, mathutils
from bpy.app.handlers import persistent

def GetCutsceneCameras(scene):
    ret = []
    for o in scene.objects:
        if o.type != 'CAMERA': continue
        if o.parent is None: continue
        if o.parent.type != 'EMPTY': continue
        if not o.parent.name.startswith('Cutscene.'): continue
        ret.append(o)
    return ret


def GetCutsceneCamState(cso, frame):
    '''Returns (pos, rot_quat, fov)'''
    return (mathutils.Vector((0.0, frame * 0.1, 0.0)),
        mathutils.Quaternion(), 45.0)
    

@persistent
def CamMotionFrameHandler(scene):
    cams = GetCutsceneCameras(scene)
    print('Frame Change', scene.frame_current, len(cams), 'eligible cameras')
    for camo in cams:
        cso = camo.parent
        cam = camo.data
        pos, rot_quat, fov = GetCutsceneCamState(cso, scene.frame_current)
        camo.location = pos
        camo.rotation_mode = 'QUATERNION'
        camo.rotation_quaternion = rot_quat
        cam.angle = math.pi * fov / 180.0
        cam.clip_start = 1e-3
        cam.clip_end = 200.0


def CamMotion_register():
    bpy.app.handlers.frame_change_pre.append(CamMotionFrameHandler)

def CamMotion_unregister():
    if CamMotionFrameHandler in bpy.app.handlers.frame_change_pre:
        bpy.app.handlers.frame_change_pre.remove(CamMotionFrameHandler)
