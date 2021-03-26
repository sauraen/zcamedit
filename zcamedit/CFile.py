import bpy
import struct

'''From https://stackoverflow.com/questions/14431170/get-the-bits-of-a-float-in-python'''
def intBitsAsFloat(i):
    s = struct.pack('>l', i)
    return struct.unpack('>f', s)[0]
def floatBitsAsInt(f):
    s = struct.pack('>f', f)
    return struct.unpack('>l', s)[0]

def IsGetCutsceneStart(l):
    toks = [t for t in l.strip().split(' ') if t]
    if len(toks) != 4: return None
    if toks[0] not in ['s32', 'CutsceneData']: return None
    if not toks[1].endswith('[]'): return None
    if toks[2] != '=' or toks[3] != '{': return None
    return toks[1][:-2]
    
def IsCutsceneEnd(l):
    return l.strip() == '};'
    
def IsGetCamListCmd(l, isat):
    l = l.strip()
    cmd = 'CS_CAM_FOCUS_POINT_LIST(' if isat else 'CS_CAM_POS_LIST('
    if not l.startswith(cmd): return None
    if not l.endswith('),'): return None
    toks = [t for t in l[len(cmd):-2].split(', ') if t]
    if len(toks) != 2 or not toks[0].isnumeric() or not toks[1].isnumeric(): 
        printf('Syntax error: ' + l)
        return None
    return (int(toks[0]), int(toks[1]))
    
def CreateCamListCmd(start, end, tabs, at=False):
    cmd = 'CS_CAM_FOCUS_POINT_LIST(' if at else 'CS_CAM_POS_LIST('
    return ('\t' if tabs else '    ') + cmd + str(start) + ', ' + str(end) + '),'

def IsGetCamCmd(l, isat, scale):
    l = l.strip()
    cmd = 'CS_CAM_FOCUS_POINT(' if isat else 'CS_CAM_POS('
    if not l.startswith(cmd): return None
    if not l.endswith('),'): return None
    toks = [t for t in l[len(cmd):-2].split(', ') if t]
    if len(toks) != 8:
        print('Wrong number of commands: ' + l)
        return None
    if toks[0] in ['0', 'CS_CMD_CONTINUE']:
        c_continue = True
    elif toks[0] in ['-1', 'CS_CMD_STOP']:
        c_continue = False
    else:
        print('Invalid first parameter: ' + l)
        return None
    c_roll = int(toks[1], 0)
    if c_roll >= 0x80 and c_roll <= 0xFF:
        c_roll -= 0x100
    elif not (c_roll >= -0x80 and c_roll <= 0x7F):
        print('Roll out of range: ' + l)
        return None
    c_frames = int(toks[2])
    if not isat and (c_roll != 0 or c_frames != 0):
        print('Roll and frames must be 0 in cam pos command: ' + l)
        return None
    if toks[3].startswith('0x'):
        c_fov = int(toks[3], 16)
        c_fov = intBitsAsFloat(c_fov)
    elif toks[3].endswith('f'):
        c_fov = float(toks[3][:-1])
    else:
        print('Invalid FOV: ' + l)
        return None
    if not (c_fov >= 0.01 and c_fov <= 179.99):
        print('FOV out of range: ' + l)
        return None
    c_x = int(toks[4])
    c_y = int(toks[5])
    c_z = int(toks[6])
    if any(v < -0x8000 or v >= 0x8000 for v in (c_x, c_y, c_z)):
        print('Position(s) invalid: ' + l)
        return None
    c_x = float(c_x) / scale
    c_y = float(c_y) / scale
    c_z = float(c_z) / scale
    return (c_continue, c_roll, c_frames, c_fov, c_x, c_y, c_z)

def CreateCamCmd(c_continue, c_roll, c_frames, c_fov, c_x, c_y, c_z, floats, tabs, cscmd, at=False):
    cmd = 'CS_CAM_FOCUS_POINT(' if at else 'CS_CAM_POS('
    if cscmd:
        c_continue = 'CS_CMD_CONTINUE' if c_continue else 'CS_CMD_STOP'
    else:
        c_continue = '0' if c_continue else '-1'
    cmd = ('\t' if tabs else '    ') * 2 + cmd + c_continue + ', '
    cmd += str(c_roll) + ', '
    cmd += str(c_frames) + ', '
    cmd += (str(c_fov) if floats else hex(floatBitsAsInt(c_fov))) + ', '
    cmd += str(c_x) + ', '
    cmd += str(c_y) + ', '
    cmd += str(c_z) + ', 0),'
    return cmd

def CreateObject(context, name, data, select):
    obj = context.blend_data.objects.new(name=name, object_data=data)
    context.view_layer.active_layer_collection.collection.objects.link(obj)
    if select:
        obj.select_set(True)
        context.view_layer.objects.active = obj
    return obj

def CSToBlender(context, csname, poslists, atlists):
    # Create empty cutscene object
    cs_object = CreateObject(context, 'Cutscene.' + csname, None, False)
    # Add or move camera
    camo = None
    nocam = True
    for o in context.blend_data.objects:
        if o.type != 'CAMERA': continue
        nocam = False
        if o.parent is not None: continue
        camo = o
        break
    if nocam:
        cam = context.blend_data.cameras.new('Camera')
        camo = CreateObject(context, 'Camera', cam, False)
        print('Created new camera')
    if camo is not None:
        camo.parent = cs_object
    # Main import
    for shotnum, pl in enumerate(poslists):
        # Get corresponding atlist
        al = None
        for a in atlists:
            if a[0] == pl[0]:
                al = a
                break
        if al is None or len(pl[2]) != len(al[2]):
            print('Internal error!')
            return False
        start_frame = pl[0]
        end_frame = al[1] if al[1] >= start_frame + 2 else pl[1]
        context.scene.frame_start = min(context.scene.frame_start, start_frame)
        context.scene.frame_end = max(context.scene.frame_end, end_frame)
        name = 'Shot{:02}'.format(shotnum+1)
        arm = context.blend_data.armatures.new(name)
        arm.display_type = 'STICK'
        arm.show_names = True
        armo = CreateObject(context, name, arm, True)
        armo.parent = cs_object
        armo['start_frame'] = start_frame
        armo['end_frame'] = end_frame
        armo['rel_link'] = False #TODO
        bpy.ops.object.mode_set(mode='EDIT')
        for i in range(len(pl[2])):
            pos = pl[2][i]
            at = al[2][i]
            bone = arm.edit_bones.new('K{:02}'.format(i+1))
            bone.head = [pos[4], pos[5], pos[6]]
            bone.tail = [at[4], at[5], at[6]]
            bone['frames'] = at[2]
            bone['fov'] = at[3]
            bone['camroll'] = at[1]
        bpy.ops.object.mode_set(mode='OBJECT')
    return True

def ImportCFile(context, filename, scale):
    if context.view_layer.objects.active is not None: 
        bpy.ops.object.mode_set(mode='OBJECT')
    context.scene.frame_start = 1
    context.scene.frame_end = 3
    state = 'OutsideCS'
    with open(filename, 'r') as file:
        for l in file:
            if state == 'OutsideCS':
                csname = IsGetCutsceneStart(l)
                if csname is not None:
                    print('Found cutscene ' + csname)
                    state = 'InsideCS'
                    poslists = []
                    atlists = []
                continue
            if state == 'InsideList':
                cmdinfo = IsGetCamCmd(l, not listtype, scale)
                if cmdinfo is not None:
                    print('Wrong type of camera command in list! ' + l)
                    return False
                cmdinfo = IsGetCamCmd(l, listtype, scale)
                if cmdinfo is not None:
                    if lastcmd:
                        print('More camera commands after last cmd! ' + l)
                        return False
                    listdata.append(cmdinfo)
                    lastcmd = not cmdinfo[0]
                    continue
                # It's some other kind of command, so end of cam list
                if not lastcmd:
                    print('List terminated without stop marker! ' + l)
                    return False
                if not listtype:
                    poslists.append((poslistinfo[0], poslistinfo[1], listdata))
                else:
                    if len(listdata) != len(corresponding_poslist):
                        print('At list contains ' + str(len(listdata)) 
                            + ' commands, but corresponding pos list contains ' 
                            + str(len(corresponding_poslist)) + ' commands!')
                        return False
                    atlists.append((atlistinfo[0], atlistinfo[1], listdata))
                state = 'InsideCS'
            if state == 'InsideCS':
                if IsCutsceneEnd(l):
                    if len(poslists) != len(atlists):
                        print('Found ' + str(len(poslists)) + ' pos lists but '
                            + str(len(atlists)) + ' at lists!')
                        return False
                    if not CSToBlender(context, csname, poslists, atlists):
                        return False
                    state = 'OutsideCS'
                    continue
                poslistinfo = IsGetCamListCmd(l, False)
                atlistinfo = IsGetCamListCmd(l, True)
                if poslistinfo is not None or atlistinfo is not None:
                    listdata = []
                    listtype = (atlistinfo is not None)
                    state = 'InsideList'
                    lastcmd = False
                    if listtype:
                        # Make sure there's already a cam pos list with this start frame
                        for ls in poslists:
                            if ls[0] == atlistinfo[0]:
                                corresponding_poslist = ls[2]
                                break
                        else:
                            print('Started at list for start frame ' + str(atlistinfo[0])
                                + ', but there\'s no pos list with this start frame!')
                            return False
                continue
            print('Internal error!')
            return False
    context.scene.frame_set(context.scene.frame_start)
    return True

def ExportCFile(context, filename, scale, use_floats, use_tabs, use_cscmd):
    pass #TODO
    return False
