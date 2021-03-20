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

def GetCamCommands(cso):
    ret = []
    for o in scene.objects:
        if o.type != 'ARMATURE': continue
        if o.parent is None: continue
        if o.parent != cso: continue
        if 'start_frame' not in o or 'end_frame' not in o: continue
        ret.append(o)
    ret.sort(key=lambda o: o.name)
    return ret

def GetCutsceneCamState(cso, frame):
    '''Returns (pos, rot_quat, fov)'''
    cmds = GetCamCommands(cso)
    if len(cmds) == 0:
        return (None, None, None)
    cur_cmd = None
    cur_cmd_start_frame = -1
    for c in cmds:
        if c['start_frame'] >= frame: continue
        if c['end_frame'] < c['start_frame'] + 2: continue
        if c['start_frame'] > cur_cmd_start_frame:
            cur_cmd = c
            cur_cmd_start_frame = c['start_frame']
    if cur_cmd is None:
        return (None, None, None)
    # TODO first frame of new cmd does not update camera pos at all
    

@persistent
def CamMotionFrameHandler(scene):
    cams = GetCutsceneCameras(scene)
    print('Frame Change', scene.frame_current, len(cams), 'eligible cameras')
    for camo in cams:
        cso = camo.parent
        cam = camo.data
        pos, rot_quat, fov = GetCutsceneCamState(cso, scene.frame_current)
        if pos is None: continue
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
