import bpy
import struct
import os, shutil

from .CamMotion import GetCamCommands, GetCamBones

def GetCamBonesChecked(cmd):
    bones = GetCamBones(cmd)
    if bones is None:
        raise RuntimeError('Error in bone properties')
    if len(bones) < 4:
        raise RuntimeError('Only {} bones in {}.{}'.format(len(bones), cs_object.name, l.name))
    return bones
    
'''From https://stackoverflow.com/questions/14431170/get-the-bits-of-a-float-in-python'''
def intBitsAsFloat(i):
    s = struct.pack('>l', i)
    return struct.unpack('>f', s)[0]
def floatBitsAsInt(f):
    s = struct.pack('>f', f)
    return struct.unpack('>l', s)[0]

class CFileIO():
    def __init__(self, context, scale):
        self.context, self.scale = context, scale
    
    def IsGetCutsceneStart(self, l):
        toks = [t for t in l.strip().split(' ') if t]
        if len(toks) != 4: return None
        if toks[0] not in ['s32', 'CutsceneData']: return None
        if not toks[1].endswith('[]'): return None
        if toks[2] != '=' or toks[3] != '{': return None
        return toks[1][:-2]
        
    def IsCutsceneEnd(self, l):
        return l.strip() == 'CS_END(),'
        
    def IsGetCamListCmd(self, l, isat):
        l = l.strip()
        cmd = 'CS_CAM_FOCUS_POINT_LIST(' if isat else 'CS_CAM_POS_LIST('
        if not l.startswith(cmd): return None
        if not l.endswith('),'): return None
        toks = [t for t in l[len(cmd):-2].split(', ') if t]
        if len(toks) != 2 or not toks[0].isnumeric() or not toks[1].isnumeric(): 
            printf('Syntax error: ' + l)
            return None
        start_frame = int(toks[0])
        end_frame = int(toks[1])
        if end_frame < start_frame + 2:
            printf('Cam cmd has nonstandard start/end frames: {}, {}'.format(start_frame, end_frame))
            return None
        return (start_frame, end_frame)
    
    def IsGetCamCmd(self, l, isat):
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
        if not isat and c_frames != 0:
            print('Frames must be 0 in cam pos command: ' + l)
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
        c_x, c_y, c_z = int(toks[4]), int(toks[5]), int(toks[6])
        if any(v < -0x8000 or v >= 0x8000 for v in (c_x, c_y, c_z)):
            print('Position(s) invalid: {}, {}, {}'.format(c_x, c_y, c_z))
            return None
        # OoT: +X right, +Y up, -Z forward
        # Blender: +X right, +Z up, +Y forward
        c_x, c_y, c_z = float(c_x) / self.scale, -float(c_z) / self.scale, float(c_y) / self.scale
        return (c_continue, c_roll, c_frames, c_fov, c_x, c_y, c_z)
    
    def OnCutsceneStart(self, csname): pass
    def OnCutsceneEnd(self): pass
    def OnOtherCommandOutsideCS(self, l): pass
    def OnOtherCommandInsideCS(self, l): pass
    def OnStartCamList(self, poslistinfo, atlistinfo): pass
    def OnEndCamList(self): pass
    def OnListCmd(self, cmdinfo): pass
    
    def TraverseInputFile(self, filename):
        state = 'OutsideCS'
        with open(filename, 'r') as infile:
            for l in infile:
                if state == 'OutsideCS':
                    csname = self.IsGetCutsceneStart(l)
                    if csname is not None:
                        print('Found cutscene ' + csname)
                        state = 'InsideCS'
                        self.OnCutsceneStart(csname)
                    else:
                        self.OnOtherCommandOutsideCS(l)
                    continue
                if state == 'InsideList':
                    cmdinfo = self.IsGetCamCmd(l, not self.listtype)
                    if cmdinfo is not None:
                        raise RuntimeError('Wrong type of camera command in list! ' + l)
                    cmdinfo = self.IsGetCamCmd(l, self.listtype)
                    if cmdinfo is not None:
                        if lastcmd:
                            raise RuntimeError('More camera commands after last cmd! ' + l)
                        lastcmd = not cmdinfo[0]
                        self.OnListCmd(cmdinfo)
                        continue
                    # It's some other kind of command, so end of cam list
                    if not lastcmd:
                        raise RuntimeError('List terminated without stop marker! ' + l)
                    self.OnEndCamList()
                    state = 'InsideCS'
                if state == 'InsideCS':
                    if self.IsCutsceneEnd(l):
                        self.OnCutsceneEnd()
                        state = 'OutsideCS'
                        continue
                    poslistinfo = self.IsGetCamListCmd(l, False)
                    atlistinfo = self.IsGetCamListCmd(l, True)
                    if poslistinfo is not None or atlistinfo is not None:
                        self.listtype = (atlistinfo is not None)
                        self.OnStartCamList(poslistinfo, atlistinfo)
                        state = 'InsideList'
                        lastcmd = False
                    else:
                        self.OnOtherCommandInsideCS(l)
                    continue
                raise RuntimeError('Internal state error!')


class CFileImport(CFileIO):
    def __init__(self, context, scale):
        super().__init__(context, scale)
    
    def CreateObject(self, name, data, select):
        obj = self.context.blend_data.objects.new(name=name, object_data=data)
        self.context.view_layer.active_layer_collection.collection.objects.link(obj)
        if select:
            obj.select_set(True)
            self.context.view_layer.objects.active = obj
        return obj

    def CSToBlender(self, csname, poslists, atlists):
        # Create empty cutscene object
        cs_object = self.CreateObject('Cutscene.' + csname, None, False)
        # Add or move camera
        camo = None
        nocam = True
        for o in self.context.blend_data.objects:
            if o.type != 'CAMERA': continue
            nocam = False
            if o.parent is not None: continue
            camo = o
            break
        if nocam:
            cam = self.context.blend_data.cameras.new('Camera')
            camo = self.CreateObject('Camera', cam, False)
            print('Created new camera')
        if camo is not None:
            camo.parent = cs_object
            camo.data.display_size = (0.15 / 56.0) * self.scale 
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
            name = 'Shot{:02}'.format(shotnum+1)
            arm = self.context.blend_data.armatures.new(name)
            arm.display_type = 'STICK'
            arm.show_names = True
            armo = self.CreateObject(name, arm, True)
            armo.parent = cs_object
            armo['start_frame'] = start_frame
            armo['rel_link'] = False #TODO
            bpy.ops.object.mode_set(mode='EDIT')
            fake_total_frames = 0
            for i in range(len(pl[2])):
                pos = pl[2][i]
                at = al[2][i]
                bone = arm.edit_bones.new('K{:02}'.format(i+1))
                bone.head = [pos[4], pos[5], pos[6]]
                bone.tail = [at[4], at[5], at[6]]
                bone['frames'] = at[2]
                bone['fov'] = at[3]
                bone['camroll'] = at[1]
                fake_total_frames += at[2]
            bpy.ops.object.mode_set(mode='OBJECT')
            self.context.scene.frame_start = min(self.context.scene.frame_start, start_frame)
            self.context.scene.frame_end = max(self.context.scene.frame_end, start_frame + fake_total_frames)
        return True

    
    def OnCutsceneStart(self, csname):
        self.csname = csname
        self.poslists = []
        self.atlists = []
        
    def OnCutsceneEnd(self):
        if len(self.poslists) != len(self.atlists):
            raise RuntimeError('Found ' + str(len(self.poslists)) + ' pos lists but '
                + str(len(self.atlists)) + ' at lists!')
        if not self.CSToBlender(self.csname, self.poslists, self.atlists):
            raise RuntimeError('CSToBlender failed')
        
    def OnStartCamList(self, poslistinfo, atlistinfo):
        self.listdata = []
        self.listinfo = atlistinfo if self.listtype else poslistinfo
        if self.listtype:
            # Make sure there's already a cam pos list with this start frame
            for ls in self.poslists:
                if ls[0] == atlistinfo[0]:
                    self.corresponding_poslist = ls[2]
                    break
            else:
                raise RuntimeError('Started at list for start frame ' + str(atlistinfo[0])
                    + ', but there\'s no pos list with this start frame!')
        
    def OnEndCamList(self):
        if len(self.listdata) < 4:
            raise RuntimeError('Only {} key points in camera command!'.format(len(self.listdata)))
        if len(self.listdata) > 4:
            # Extra dummy point at end if there's 5 or more points--remove
            # at import and re-add at export
            del self.listdata[-1]
        if not self.listtype:
            self.poslists.append((self.listinfo[0], self.listinfo[1], self.listdata))
        else:
            if len(self.listdata) != len(self.corresponding_poslist):
                raise RuntimeError('At list contains ' + str(len(self.listdata)) 
                    + ' commands, but corresponding pos list contains ' 
                    + str(len(self.corresponding_poslist)) + ' commands!')
            self.atlists.append((self.listinfo[0], self.listinfo[1], self.listdata))
    
    def OnListCmd(self, cmdinfo):
        self.listdata.append(cmdinfo)
    
    def ImportCFile(self, filename):
        if self.context.view_layer.objects.active is not None: 
            bpy.ops.object.mode_set(mode='OBJECT')
        self.context.scene.frame_start = 1
        self.context.scene.frame_end = 3
        self.context.scene.render.fps = 20
        self.context.scene.render.resolution_x = 320
        self.context.scene.render.resolution_y = 240
        try:
            self.TraverseInputFile(filename)
        except Exception as e:
            return str(e)
        self.context.scene.frame_set(self.context.scene.frame_start)
        return None


def ImportCFile(context, filename, scale):
    im = CFileImport(context, scale)
    return im.ImportCFile(filename)


class CFileExport(CFileIO):
    def __init__(self, context, scale, use_floats, use_tabs, use_cscmd):
        super().__init__(context, scale)
        self.use_floats, self.use_tabs, self.use_cscmd = use_floats, use_tabs, use_cscmd
        self.tabstr = ('\t' if self.use_tabs else '    ')
        self.cs_object = None
        self.GetAllCutsceneObjects()
    
    def CreateCutsceneStartCmd(self, csname):
        return ('CutsceneData ' if self.use_cscmd else 's32 ') + csname + '[] = {\n'
    
    def CreateCutsceneEndCmd(self):
        return self.tabstr + 'CS_END(),\n'
    
    def CreateCamListCmd(self, start, end, at=False):
        cmd = 'CS_CAM_FOCUS_POINT_LIST(' if at else 'CS_CAM_POS_LIST('
        return self.tabstr + cmd + str(start) + ', ' + str(end) + '),\n'

    def CreateCamCmd(self, c_continue, c_roll, c_frames, c_fov, c_x, c_y, c_z, at=False):
        cmd = 'CS_CAM_FOCUS_POINT(' if at else 'CS_CAM_POS('
        if self.use_cscmd:
            c_continue = 'CS_CMD_CONTINUE' if c_continue else 'CS_CMD_STOP'
        else:
            c_continue = '0' if c_continue else '-1'
        cmd = self.tabstr * 2 + cmd + c_continue + ', '
        cmd += str(c_roll) + ', '
        cmd += str(c_frames) + ', '
        cmd += (str(c_fov) + 'f' if self.use_floats else hex(floatBitsAsInt(c_fov))) + ', '
        c_x, c_y, c_z = int(round(c_x * self.scale)), int(round(c_z * self.scale)), int(round(-c_y * self.scale))
        if any(v < -0x8000 or v >= 0x8000 for v in (c_x, c_y, c_z)):
            print('Position(s) too large, out of range: {}, {}, {}'.format(c_x, c_y, c_z))
            return None
        cmd += str(c_x) + ', '
        cmd += str(c_y) + ', '
        cmd += str(c_z) + ', 0),\n'
        return cmd

    def GetAllCutsceneObjects(self):
        self.cs_objects = []
        for o in self.context.blend_data.objects:
            if o.type != 'EMPTY': continue
            if not o.name.startswith('Cutscene.'): continue
            self.cs_objects.append(o)
            
    def GetFakeCutsceneLength(self, bones):
        return max(2, sum(b['frames'] for b in bones))
    
    def OnCutsceneStart(self, csname):
        self.wrote_cam_list = False
        for o in self.cs_objects:
            if o.name == 'Cutscene.' + csname:
                self.cs_object = o
                self.cs_objects.remove(o)
                print('Replacing camera commands in cutscene ' + csname)
                break
        else:
            self.cs_object = None
            print('Scene does not contain cutscene ' + csname + ' in file, skipping')
        self.outfile.write(self.CreateCutsceneStartCmd(csname))
        
    def OnCutsceneEnd(self):
        if self.cs_object is not None and not self.wrote_cam_list:
            print('Warning, cutscene did not contain any camera commands, adding at end')
            self.WriteCutscene(self.cs_object)
        self.cs_object = None
        self.outfile.write(self.CreateCutsceneEndCmd())
    
    def OnOtherCommandOutsideCS(self, l):
        self.outfile.write(l)
    
    def OnOtherCommandInsideCS(self, l):
        self.outfile.write(l)
    
    def OnStartCamList(self, poslistinfo, atlistinfo):
        if self.cs_object is not None and not self.wrote_cam_list:
            self.WriteCutscene(self.cs_object)
            self.wrote_cam_list = True
    
    def WriteCutscene(self, cs_object):
        cmdlists = GetCamCommands(self.context.scene, cs_object)
        if len(cmdlists) == 0:
            raise RuntimeError('No camera command lists in cutscene ' + cs_object.name)
        def WriteLists(at):
            for l in cmdlists:
                bones = GetCamBonesChecked(l)
                self.outfile.write(self.CreateCamListCmd(l['start_frame'], 
                    l['start_frame'] + self.GetFakeCutsceneLength(bones), at))
                for i, b in enumerate(bones):
                    c_roll = b['camroll'] if at else 0
                    c_frames = b['frames'] if at else 0
                    c_fov = b['fov']
                    c_pos = b.tail if at else b.head
                    c_x, c_y, c_z = c_pos.x, c_pos.y, c_pos.z
                    self.outfile.write(self.CreateCamCmd(
                        True, c_roll, c_frames, c_fov, c_x, c_y, c_z, at))
                # Extra dummy point
                self.outfile.write(self.CreateCamCmd(False, 0, 0, 0.0, 0.0, 0.0, 0.0, at))
        WriteLists(False)
        WriteLists(True)
        
    def ExportCFile(self, filename):
        if os.path.isfile(filename):
            tmpfile = filename + '.tmp'
            try:
                shutil.copyfile(filename, tmpfile)
            except OSError as err:
                print('Could not make backup file')
                return False
        else:
            tmpfile = None
        ret = None
        try:
            with open(filename, 'w') as self.outfile:
                if tmpfile is not None:
                    self.TraverseInputFile(tmpfile)
                for o in self.cs_objects:
                    print(o.name + ' not found in C file, appending to end. This may require manual editing afterwards.')
                    cmdlists = GetCamCommands(self.context.scene, o)
                    overall_start_frame = 1000000
                    overall_end_frame = -1
                    for c in cmdlists:
                        overall_start_frame = min(overall_start_frame, c['start_frame'])
                        bones = GetCamBonesChecked(c)
                        end_frame = c['start_frame'] + self.GetFakeCutsceneLength(bones)
                        overall_end_frame = max(overall_end_frame, end_frame)
                    self.outfile.write('\n// clang-format off\n')
                    self.outfile.write(self.CreateCutsceneStartCmd(o.name[9:]))
                    self.outfile.write(self.tabstr + 'CS_BEGIN_CUTSCENE(' 
                        + str(overall_start_frame) + ', ' + str(overall_end_frame) + '),\n')
                    self.WriteCutscene(o)
                    self.outfile.write(self.CreateCutsceneEndCmd())
                    self.outfile.write('};\n// clang-format on\n')
        except Exception as e:
            print(str(e))
            if tmpfile is not None:
                print('Aborting, restoring original file')
                shutil.copyfile(tmpfile, filename)
            ret = str(e)
        if tmpfile is not None:
            os.remove(tmpfile)
        return ret

def ExportCFile(context, filename, scale, use_floats, use_tabs, use_cscmd):
    ex = CFileExport(context, scale, use_floats, use_tabs, use_cscmd)
    return ex.ExportCFile(filename)
