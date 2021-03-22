
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
    
def IsGetCamListCmd(l, at=False):
    l = l.strip()
    cmd = 'CS_CAM_FOCUS_POINT_LIST(' if at else 'CS_CAM_POS_LIST('
    if not l.startswith(cmd): return None
    if not l.endswith('),'): return None
    toks = [t for t in l[len(start):-2].split(', ') if t]
    if len(toks) != 2 or not toks[0].isnumeric() or not toks[1].isnumeric(): 
        printf('Syntax error: ' + l)
        return None
    return (int(toks[0]), int(toks[1]))
    
def CreateCamListCmd(start, end, tabs, at=False):
    cmd = 'CS_CAM_FOCUS_POINT_LIST(' if at else 'CS_CAM_POS_LIST('
    return ('\t' if tabs else '    ') + cmd + str(start) + ', ' + str(end) + '),'

def IsGetCamCmd(l, at=False):
    l = l.strip()
    cmd = 'CS_CAM_FOCUS_POINT(' if at else 'CS_CAM_POS('
    if not l.startswith(cmd): return None
    if not l.endswith('),'): return None
    toks = [t for t in l[len(start):-2].split(', ') if t]
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
    if not at and (c_roll != 0 or c_frames != 0):
        print('Roll and frames must be 0 in cam pos command: ' + l)
        return None
    if toks[3].startswith('0x'):
        c_fov = int(toks[3], 16)
        c_fov = intBitsAsFloat(c_fov)
    elif toks[3].endswith('f'):
        c_fov = float(toks[3])
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
