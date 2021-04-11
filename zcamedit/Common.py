import struct
import random

import bpy, mathutils
from bpy.props import FloatProperty, EnumProperty

def MetersToBlend(context, v):
    return v * 56.0 / context.scene.ootBlenderScale

'''From https://stackoverflow.com/questions/14431170/get-the-bits-of-a-float-in-python'''
def intBitsAsFloat(i):
    s = struct.pack('>l', i)
    return struct.unpack('>f', s)[0]
def floatBitsAsInt(f):
    s = struct.pack('>f', f)
    return struct.unpack('>l', s)[0]

def GetCamCommands(scene, cso):
    ret = []
    for o in scene.objects:
        if o.type != 'ARMATURE': continue
        if o.parent is None: continue
        if o.parent != cso: continue
        if any(p not in o for p in ['start_frame', 'rel_link']):
            print('Armature ' + o.name + ' missing custom parameters')
            continue
        ret.append(o)
    ret.sort(key=lambda o: o.name)
    return ret
    
def GetCamBones(cmd):
    bones = [b for b in (cmd.data.edit_bones if cmd.mode == 'EDIT' else cmd.data.bones)]
    for b in bones:
        if 'frames' not in b or 'fov' not in b or 'camroll' not in b:
            print('Bone ' + b.name + ' missing custom parameters')
            return None
        if b.parent is not None:
            print('Camera armature bones are not allowed to have parent bones')
            return None
    bones.sort(key=lambda b: b.name)
    return bones

def GetCamBonesChecked(cmd):
    bones = GetCamBones(cmd)
    if bones is None:
        raise RuntimeError('Error in bone properties')
    if len(bones) < 4:
        raise RuntimeError('Only {} bones in {}'.format(len(bones), cmd.name))
    return bones
    
def GetFakeCamCmdLength(armo):
    bones = GetCamBonesChecked(armo)
    return max(2, sum(b['frames'] for b in bones))
    
def GetCSStartFakeEnd(context, cs_object):
    cmdlists = GetCamCommands(context.scene, cs_object)
    cs_startf = 1000000
    cs_endf = -1
    for c in cmdlists:
        cs_startf = min(cs_startf, c['start_frame'])
        end_frame = c['start_frame'] + GetFakeCamCmdLength(c) + 1
        cs_endf = max(cs_endf, end_frame)
    return cs_startf, cs_endf
    
def GetNameActorID(name):
    name = name.split('.')[0]
    if name == 'Link' or name == 'Player':
        return -1
    elif name.startswith('NPC'):
        name = name[3:]
    elif name.startswith('Actor'):
        name = name[5:]
    else:
        return None
    if not name.isnumeric(): return None
    try:
        return int(name)
    except ValueError:
        return None
    
def GetActionListPoints(scene, al_object):
    ret = []
    for o in scene.objects:
        if o.parent != al_object or o.type != 'EMPTY': continue
        if 'start_frame' not in o: continue
        ret.append(o)
    ret.sort(key=lambda o: o['start_frame'])
    return ret
    
def GetActionListStartFrame(scene, al_object):
    points = GetActionListPoints(scene, al_object)
    if len(points) < 2: return 1000000
    return points[0]['start_frame']
    
def GetActionListsForID(scene, cs_object, actorid):
    ret = []
    for o in scene.objects:
        if o.parent != cs_object or o.type != 'EMPTY': continue
        if o.name.startswith('Path.'):
            name = o.name[5:]
        elif o.name.startswith('ActionList.'):
            name = o.name[11:]
        else:
            continue
        if GetNameActorID(name) != actorid: continue
        ret.append(o)
    ret.sort(key=lambda o: GetActionListStartFrame(scene, o))
    return ret
    
def GetObjectUniqueName(context, basename):
    num = 1
    while True:
        name = basename + '.{:02}'.format(num)
        for o in context.scene.objects:
            if o.name == name:
                break
        else:
            return name
        num += 1
    
def CreateObject(context, name, data, select):
    obj = context.blend_data.objects.new(name=name, object_data=data)
    context.view_layer.active_layer_collection.collection.objects.link(obj)
    if select:
        obj.select_set(True)
        context.view_layer.objects.active = obj
    return obj

def InitCS(context, cs_object):
    # Add or move camera
    camo = None
    nocam = True
    for o in context.blend_data.objects:
        if o.type != 'CAMERA': continue
        nocam = False
        if o.parent is not None and o.parent != cs_object: continue
        camo = o
        break
    if nocam:
        cam = context.blend_data.cameras.new('Camera')
        camo = CreateObject(context, 'Camera', cam, False)
        print('Created new camera')
    if camo is not None:
        camo.parent = cs_object
        camo.data.display_size = MetersToBlend(context, 0.25)
        camo.data.passepartout_alpha = 0.95
        camo.data.clip_start = 1e-3
        camo.data.clip_end = 200.0
    # Link preview
    for o in context.blend_data.objects:
        if o.type != 'EMPTY': continue
        if o.parent != cs_object: continue
        if o.name != 'Preview.Link': continue
        link_preview = o
        break
    else:
        link_preview = CreateObject(context, 'Preview.Link', None, False)
        link_preview.parent = cs_object
    link_age = context.scene.zcamedit_previewlinkage
    link_height = MetersToBlend(context, 1.7 if link_age == 'link_adult' else 1.3)
    link_preview.empty_display_type = 'SINGLE_ARROW'
    link_preview.empty_display_size = link_height
    # Other setup
    cs_startf, cs_endf = GetCSStartFakeEnd(context, cs_object)
    context.scene.frame_start = min(cs_startf, context.scene.frame_start)
    context.scene.frame_end = max(cs_endf, context.scene.frame_end)
    context.scene.render.fps = 20
    context.scene.render.resolution_x = 320
    context.scene.render.resolution_y = 240

def CreateActorAction(context, basename, cs_object):
    al_object = CreateObject(context, GetObjectUniqueName(context, basename), None, True)
    al_object.parent = cs_object
    x = random.random() * 40.0 - 20.0
    point1 = CreateObject(context, 'Point01', None, False)
    point1.parent = al_object
    point1.empty_display_type = 'ARROWS'
    point1.location = mathutils.Vector((x, -10.0, 0.0))
    point1['start_frame'] = 0
    point2 = CreateObject(context, 'Point02', None, False)
    point2.parent = al_object
    point2.empty_display_type = 'ARROWS'
    point2.location = mathutils.Vector((x, 10.0, 0.0))
    point2['start_frame'] = 40
