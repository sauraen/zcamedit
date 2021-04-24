import bpy, mathutils
import random

from .Common import *

def IsActionList(obj):
    if obj is None or obj.type != 'EMPTY': return False
    if not any(obj.name.startswith(s) for s in ['Path.', 'ActionList.']):
        return False
    if obj.parent is None or obj.parent.type != 'EMPTY' \
        or not obj.parent.name.startswith('Cutscene.'):
        return False
    return True
    
def IsActionPoint(obj):
    if obj is None or obj.type != 'EMPTY': return False
    if not any(obj.name.startswith(s) for s in ['Point.', 'Action.']):
        return False
    if not IsActionList(obj.parent): return False
    return True
    
def IsPreview(obj):
    if obj is None or obj.type != 'EMPTY': return False
    if not obj.name.startswith('Preview.'):
        return False
    if obj.parent is None or obj.parent.type != 'EMPTY' \
        or not obj.parent.name.startswith('Cutscene.'):
        return False
    return True

def GetActionListPoints(scene, al_object):
    ret = []
    for o in scene.objects:
        if IsActionPoint(o) and o.parent == al_object:
            ret.append(o)
    ret.sort(key=lambda o: o.zc_apoint.start_frame)
    return ret
    
def GetActionListStartFrame(scene, al_object):
    points = GetActionListPoints(scene, al_object)
    if len(points) < 2: return 1000000
    return points[0].zc_apoint.start_frame
    
def GetActionListsForID(scene, cs_object, actorid):
    ret = []
    for o in scene.objects:
        if IsActionList(o) and o.parent == cs_object and o.zc_alist.actor_id == actorid:
            ret.append(o)
    ret.sort(key=lambda o: GetActionListStartFrame(scene, o))
    return ret
    
def GetActorState(scene, cs_object, actorid, frame):
    actionlists = GetActionListsForID(scene, cs_object, actorid)
    pos = mathutils.Vector((0.0, 0.0, 0.0))
    rot = mathutils.Vector((0.0, 0.0, 0.0))
    for al in actionlists:
        points = GetActionListPoints(scene, al)
        if len(points) < 2: continue
        for i in range(len(points)-1):
            s = points[i].zc_apoint.start_frame
            e = points[i+1].zc_apoint.start_frame
            if e <= s: continue
            if frame <= s: continue
            if frame <= e:
                pos = points[i].location * (e - frame) + points[i+1].location * (frame - s)
                pos /= e - s
                rot = points[i].rotation_euler
                return pos, rot
            elif i == len(points)-2:
                # If went off the end, use last position
                pos = points[i+1].location
                rot = points[i].rotation_euler
    return pos, rot

def AddActionPoint(context, al_object, select):
    points = GetActionListPoints(context.scene, al_object)
    if len(points) == 0:
        num = '000'
        pos = mathutils.Vector((random.random() * 40.0 - 20.0, -10.0, 0.0))
        sf = 0
        action_id = '0x0001'
    else:
        num = '{:03}'.format(GetTrailingNumber(points[-1].name) + 1)
        pos = points[-1].location + mathutils.Vector((0.0, 10.0, 0.0))
        sf = points[-1].zc_apoint.start_frame + 20
        action_id = points[-1].zc_apoint.action_id
    point = CreateObject(context, 'Point.' + num, None, select)
    point.parent = al_object
    point.empty_display_type = 'ARROWS'
    point.location = pos
    point.zc_apoint.start_frame = sf
    point.zc_apoint.action_id = action_id
    return point

def CreateActorAction(context, actorid, cs_object):
    al_object = CreateObject(context, 'ActionList.001', None, True)
    al_object.parent = cs_object
    AddActionPoint(context, al_object, False)
    AddActionPoint(context, al_object, False)

def CreatePreview(context, cs_object, actor_id, select=False):
    for o in context.blend_data.objects:
        if IsPreview(o) and o.parent == cs_object and o.zc_alist.actor_id == actor_id:
            preview = o
            break
    else:
        pname = 'Link' if actor_id < 0 else 'Actor' + str(actor_id)
        preview = CreateObject(context, 'Preview.' + pname + '.001', None, select)
        preview.parent = cs_object
    preview.empty_display_type = 'SINGLE_ARROW'
    preview.empty_display_size = MetersToBlend(context, ActorHeightMeters(context, actor_id))
    preview.zc_alist.actor_id = actor_id
    
