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

def GetCamCommands(scene, cso):
    ret = []
    for o in scene.objects:
        if o.type != 'ARMATURE': continue
        if o.parent is None: continue
        if o.parent != cso: continue
        if 'start_frame' not in o or 'end_frame' not in o:
            print('Armature ' + o.name + ' missing custom parameters')
            continue
        ret.append(o)
    ret.sort(key=lambda o: o.name)
    return ret

def UndefinedCamPos():
    return (mathutils.Vector((0.0, 0.0, 0.0)),
        mathutils.Quaternion(), 45.0)

def Z64SplineInterpolate(bones, frame):
    # TODO replace this with the real algorithm
    if len(bones) == 0:
        return UndefinedCamPos()
    f = 0
    last_bone = None
    next_bone = bones[0]
    for b in bones[1:]:
        last_bone = next_bone
        next_bone = b
        frames = last_bone['frames']
        if frame >= f and frame < f + frames:
            fade = float(frame - f) / frames
            break
        f += frames
    else:
        last_bone = bones[-1]
        fade = 0.0
    if last_bone is None or next_bone is None:
        print('Internal error in spline algorithm')
        return UndefinedCamPos()
    last_eye, next_eye = last_bone.head, next_bone.head
    last_at, next_at = last_bone.tail, next_bone.tail #"At" == "look at"
    last_roll, next_roll = last_bone['camroll'], next_bone['camroll']
    last_fov, next_fov = last_bone['fov'], next_bone['fov']
    eye = last_eye * (1.0 - fade) + next_eye * fade
    at = last_at * (1.0 - fade) + next_at * fade
    roll = last_roll * (1.0 - fade) + next_roll * fade
    fov = last_fov * (1.0 - fade) + next_fov * fade
    return (eye, at, roll, fov)

def GetCmdCamState(cmd, frame):
    frame -= cmd['start_frame'] + 1
    if frame <= 0:
        print('Warning, camera command evaluated for frame ' + str(frame))
        return UndefinedCamPos()
    bones = [b for b in (cmd.data.edit_bones if cmd.mode == 'EDIT' else cmd.data.bones)]
    for b in bones:
        if 'frames' not in b or 'fov' not in b or 'camroll' not in b:
            print('Bone ' + b.name + ' missing custom parameters')
            return UndefinedCamPos()
        if b.parent is not None:
            print('Camera armature bones are not allowed to have parent bones')
            return UndefinedCamPos()
    bones.sort(key=lambda b: b.name)
    eye, at, roll, fov = Z64SplineInterpolate(bones, frame)
    lookvec = at - eye
    if lookvec.length < 1e-6:
        return UndefinedCamPos()
    lookvec.normalize()
    ux = mathutils.Vector((1.0, 0.0, 0.0))
    uy = mathutils.Vector((0.0, 1.0, 0.0))
    uz = mathutils.Vector((0.0, 0.0, 1.0))
    qroll  = mathutils.Quaternion(uz, roll * math.pi / 128.0)
    qpitch = mathutils.Quaternion(-ux, math.pi + math.acos(lookvec.dot(uz)))
    qyaw   = mathutils.Quaternion(-uz, math.atan2(lookvec.dot(ux), lookvec.dot(uy)))
    return (eye, qyaw @ qpitch @ qroll, fov)
    

def GetCutsceneCamState(scene, cso, frame):
    '''Returns (pos, rot_quat, fov)'''
    cmds = GetCamCommands(scene, cso)
    if len(cmds) == 0:
        return UndefinedCamPos()
    cur_cmd, last_cmd = None, None
    cur_cmd_start_frame = -1
    for c in cmds:
        if c['start_frame'] >= frame: continue
        if c['end_frame'] < c['start_frame'] + 2: continue
        if c['start_frame'] > cur_cmd_start_frame:
            last_cmd = cur_cmd
            cur_cmd = c
            cur_cmd_start_frame = c['start_frame']
    if cur_cmd is None:
        return UndefinedCamPos()
    # The first frame of any camera command doesn't update the camera position
    # and look at all. So, we have to use the same result as the previous
    # camera command's result from one frame ago.
    if frame == cur_cmd['start_frame'] + 1:
        if last_cmd is None:
            return UndefinedCamPos()
        return GetCmdCamState(last_cmd, frame - 1)
    return GetCmdCamState(cur_cmd, frame)
    

@persistent
def CamMotionFrameHandler(scene):
    cams = GetCutsceneCameras(scene)
    for camo in cams:
        cso = camo.parent
        cam = camo.data
        pos, rot_quat, fov = GetCutsceneCamState(scene, cso, scene.frame_current)
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
