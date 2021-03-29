import bpy
import struct
import shutil
    
'''From https://stackoverflow.com/questions/14431170/get-the-bits-of-a-float-in-python'''
def intBitsAsFloat(i):
    s = struct.pack('>l', i)
    return struct.unpack('>f', s)[0]
def floatBitsAsInt(f):
    s = struct.pack('>f', f)
    return struct.unpack('>l', s)[0]

class CFileIO():
    def __init__(context, scale):
        self.context, self.scale = context, scale
    
    def IsGetCutsceneStart(self, l):
        toks = [t for t in l.strip().split(' ') if t]
        if len(toks) != 4: return None
        if toks[0] not in ['s32', 'CutsceneData']: return None
        if not toks[1].endswith('[]'): return None
        if toks[2] != '=' or toks[3] != '{': return None
        return toks[1][:-2]
        
    def IsCutsceneEnd(self, l):
        return l.strip() == '};'
        
    def IsGetCamListCmd(self, l, isat):
        l = l.strip()
        cmd = 'CS_CAM_FOCUS_POINT_LIST(' if isat else 'CS_CAM_POS_LIST('
        if not l.startswith(cmd): return None
        if not l.endswith('),'): return None
        toks = [t for t in l[len(cmd):-2].split(', ') if t]
        if len(toks) != 2 or not toks[0].isnumeric() or not toks[1].isnumeric(): 
            printf('Syntax error: ' + l)
            return None
        return (int(toks[0]), int(toks[1]))
    
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
        c_x, c_y, c_z = int(toks[4]), int(toks[5]), int(toks[6])
        if any(v < -0x8000 or v >= 0x8000 for v in (c_x, c_y, c_z)):
            print('Position(s) invalid: {}, {}, {}'.format(c_x, c_y, c_z))
            return None
        # OoT: +X right, +Y up, -Z forward
        # Blender: +X right, +Z up, +Y forward
        c_x, c_y, c_z = float(c_x) / self.scale, -float(c_z) / self.scale, float(c_y) / self.scale
        return (c_continue, c_roll, c_frames, c_fov, c_x, c_y, c_z)
    
    def OnCutsceneStart(csname): pass
    def OnCutsceneEnd(): pass
    def OnOtherCommandOutsideCS(l): pass
    def OnOtherCommandInsideCS(l): pass
    def OnStartCamList(poslistinfo, atlistinfo): pass
    def OnEndCamList(): pass
    def OnListCmd(cmdinfo): pass
    
    def TraverseInputFile(filename):
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
                    cmdinfo = self.IsGetCamCmd(l, not listtype, scale)
                    if cmdinfo is not None:
                        raise RuntimeError('Wrong type of camera command in list! ' + l)
                    cmdinfo = self.IsGetCamCmd(l, listtype, scale)
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
                        self.OnStartCamList(poslistinfo, atlistinfo)
                        state = 'InsideList'
                        lastcmd = False
                    else:
                        self.OnOtherCommandInsideCS(l)
                    continue
                raise RuntimeError('Internal state error!')


class CFileImport(CFileIO):
    def __init__(context, scale):
        super().__init__(context, scale)
    
    def CreateObject(name, data, select):
        obj = self.context.blend_data.objects.new(name=name, object_data=data)
        self.context.view_layer.active_layer_collection.collection.objects.link(obj)
        if select:
            obj.select_set(True)
            self.context.view_layer.objects.active = obj
        return obj

    def CSToBlender(csname, poslists, atlists):
        # Create empty cutscene object
        cs_object = CreateObject('Cutscene.' + csname, None, False)
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
            camo = CreateObject('Camera', cam, False)
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
            end_frame = al[1] if al[1] >= start_frame + 2 else pl[1]
            self.context.scene.frame_start = min(self.context.scene.frame_start, start_frame)
            self.context.scene.frame_end = max(self.context.scene.frame_end, end_frame)
            name = 'Shot{:02}'.format(shotnum+1)
            arm = self.context.blend_data.armatures.new(name)
            arm.display_type = 'STICK'
            arm.show_names = True
            armo = CreateObject(name, arm, True)
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

    
    def OnCutsceneStart(csname):
        self.csname = csname
        self.poslists = []
        self.atlists = []
        
    def OnCutsceneEnd():
        if len(self.poslists) != len(self.atlists):
            raise RuntimeError('Found ' + str(len(self.poslists)) + ' pos lists but '
                + str(len(self.atlists)) + ' at lists!')
        if not CSToBlender(self.csname, self.poslists, self.atlists):
            raise RuntimeError('CSToBlender failed')
        
    def OnStartCamList(poslistinfo, atlistinfo):
        self.listdata = []
        self.listtype = (atlistinfo is not None)
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
        
    def OnEndCamList():
        if not self.listtype:
            self.poslists.append((self.listinfo[0], self.listinfo[1], self.listdata))
        else:
            if len(self.listdata) != len(self.corresponding_poslist):
                raise RuntimeError('At list contains ' + str(len(self.listdata)) 
                    + ' commands, but corresponding pos list contains ' 
                    + str(len(self.corresponding_poslist)) + ' commands!')
            self.atlists.append((self.listinfo[0], self.listinfo[1], self.listdata))
    
    def OnListCmd(cmdinfo):
        self.listdata.append(cmdinfo)
    
    def ImportCFile(filename):
        if context.view_layer.objects.active is not None: 
            bpy.ops.object.mode_set(mode='OBJECT')
        context.scene.frame_start = 1
        context.scene.frame_end = 3
        context.scene.render.fps = 20
        context.scene.render.resolution_x = 320
        context.scene.render.resolution_y = 240
        try:
            self.TraverseInputFile(filename)
        except Exception as e:
            print(str(e))
            return False
        context.scene.frame_set(context.scene.frame_start)
        return True


def ImportCFile(context, filename, scale):
    im = CFileImport(context, scale)
    return im.ImportCFile(filename)


class CFileExport(CFileIO):
    def __init__(context, scale, use_floats, use_tabs, use_cscmd):
        super().__init__(context, scale)
        self.use_floats, self.use_tabs, self.use_cscmd = use_floats, use_tabs, use_cscmd
    
    def CreateCamListCmd(self, start, end, at=False):
        cmd = 'CS_CAM_FOCUS_POINT_LIST(' if at else 'CS_CAM_POS_LIST('
        return ('\t' if self.use_tabs else '    ') + cmd + str(start) + ', ' + str(end) + '),'

    def CreateCamCmd(self, c_continue, c_roll, c_frames, c_fov, c_x, c_y, c_z, at=False):
        cmd = 'CS_CAM_FOCUS_POINT(' if at else 'CS_CAM_POS('
        if self.use_cscmd:
            c_continue = 'CS_CMD_CONTINUE' if c_continue else 'CS_CMD_STOP'
        else:
            c_continue = '0' if c_continue else '-1'
        cmd = ('\t' if self.use_tabs else '    ') * 2 + cmd + c_continue + ', '
        cmd += str(c_roll) + ', '
        cmd += str(c_frames) + ', '
        cmd += (str(c_fov) if self.use_floats else hex(floatBitsAsInt(c_fov))) + ', '
        c_x, c_y, c_z = int(c_x * self.scale), int(c_z * self.scale), int(-c_y * self.scale)
        if any(v < -0x8000 or v >= 0x8000 for v in (c_x, c_y, c_z)):
            print('Position(s) too large, out of range: {}, {}, {}'.format(c_x, c_y, c_z))
            return None
        cmd += str(c_x) + ', '
        cmd += str(c_y) + ', '
        cmd += str(c_z) + ', 0),'
        return cmd

    
    def OnCutsceneStart(csname): pass #TODO
    def OnCutsceneEnd(): pass #TODO
    
    def OnOtherCommandOutsideCS(l):
        self.outfile.write(l + '\n')
    
    def OnOtherCommandInsideCS(l):
        self.outfile.write(l + '\n')
    
    def OnStartCamList(poslistinfo, atlistinfo): pass #TODO
    
    def ExportCFile(filename):
        tmpfile = filename + '.tmp'
        try:
            shutil.copyfile(filename, tmpfile)
        except OSError as err:
            print('Could not make backup file')
            return False
        ret = True
        try:
            with open(filename, 'w') as self.outfile:
                self.TraverseInputFile(tmpfile)
        except Exception as e:
            print(str(e) + '\nAborting, restoring original file')
            shutil.copyfile(tmpfile, filename)
            ret = False
        os.remove(tmpfile)
        return ret

def ExportCFile(context, filename, scale, use_floats, use_tabs, use_cscmd):
    ex = CFileExport(context, scale, use_floats, use_tabs, use_cscmd)
    return ex.ExportCFile(filename)
