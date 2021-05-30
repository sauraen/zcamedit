zcamedit - Zelda 64 (OoT/MM) cutscene camera editor Blender plugin

Copyright (C) 2021 Sauraen

GPL V3 licensed, see LICENSE.txt

zcamedit can import, edit, and export *positional* cutscene commands from scenes
in Zelda 64 (OoT and MM, only OoT has been tested). This means
- camera motion (all types)
- Link actions
- NPC actions

zcamedit does not support non-positional cutscene commands, such as text boxes,
music commands, etc. For these, install [fast64](https://bitbucket.org/kurethedead/fast64/src/master/).
Please be sure to update your fast64 installation regularly, as several members
of the community are contributing bugfixes and new features.

zcamedit imports from and exports to C files. For export, it writes into an
existing C file, overwriting only the camera / action commands within the
cutscene data in those scenes. This means you can edit cutscenes in the base
game, as well as create new cutscenes in existing scenes in the base game.
If working on a new map in fast64, there are two export steps: saving the scene
as C with fast64 (including the non-positional cutscene commands), and then
exporting into that same C file with zcamedit.

## Installation

This is a Blender plugin for 2.80+. Copy the zcamedit directory to your Blender
plugins directory, then start Blender, go to Preferences > Addons, and search
for and enable zcamedit.

## Importing

File > Import > z64 cutscene C source. Choose a scene C file and you'll get all
the cutscenes in that file. This is a good way to get started with zcamedit, to
see how cutscenes are organized.

## Exporting

These settings must match your build toolchain, whether you are using decomp
or z64ovl.
- Use Floats: whether to write camera FoV values as float or as int-encoded
float.
- Use Tabs: whether to use tabs or 4 spaces for indentation in the C file.
- Use CS_CMD defines: Use `CS_CMD_CONTINUE` / `CS_CMD_STOP` or 0 / -1 for
camera key frames.

## Setting up a Cutscene

If you're creating a new scene for a romhack:

1. Create an empty called Cutscene.YourCutsceneNameHere, parented to your Scene
empty object. If you're using fast64, the cutscene name (determine by fast64's
export process) will be something like YourSceneName_scene_header00_cutscene.
If you want to find out what this is specifically, just export the scene with
fast64 and then look in the C code. Note that you can have as many cutscenes as
you want per scene.

2. The controls for most things are in the Object Properties pane (orange
square). Select the cutscene empty and click Init Cutscene Empty. This will set
up a camera and previewers for all your actions, and some other scene
properties. You can click this later too, it doesn't erase anything.

3. Click "Create camera shot", "Create Link action list", or "Create actor (NPC)
action list".

### Camera Shots

A shot is a continuous camera motion, represented by an armature, where the head
of each bone is the camera position and the tail is the look-at (called "at")
position for a key point. Due to the game's spline algorithm for camera motion,
you always need one more key point at each end, to define how the camera is
moving when it approaches the last normal point. So, the minimum number of bones
in the armature is 4, if you want the camera to move between the positions
indicated by bones 2 to 3. (More info below if you're curious on the details.)

When the shot / armature is selected, in the Object Properties pane there are
controls for the start frame of that shot and whether it's normal, relative to
Link, or 0x7 / 0x8 (unknown mode). When a particular key point / bone is
selected, you have controls for the number of frames, FoV, and roll of the
camera at that position.

At export, camera shots are sorted by name, so you should name them with
something they will be in the correct order with at export (e.g. Shot01, Shot02,
etc.) Also, the bones / key frames are also sorted by name, so their names must
be in the order you want the motion to have. These should both be previewed
correctly (i.e. if it looks right in Blender, it should work right in game)--
if there's any issues, let me know.

When you add a new bone, e.g. by duplicating the last bone in the sequence, you
must switch out of edit mode and back in for the previewer to properly handle
that new bone. This only needs to be done after adding bones; you can preview
while editing bones normally. This is due to how Blender represents bones
differently in edit vs. object mode, and can't be fixed easily in the plugin.

### Previewing Camera Motion

When you import or click Init Cutscene Empty, a camera is created or moved to
be a child of the cutscene. This camera previews the camera motion in game,
using the exact same algorithm (see below for the nasty details). Create a new
3D view and in that view, select the camera and click View > Cameras > Active
Camera. Then, you will get a preview of the real camera motion based on the
Blender timeline time (i.e. play, pause, adjust the frame on the timeline).

If the preview camera moves to the origin aiming downwards, this means
"undefined camera position", which can be caused by three things.
1. It's a frame before the first command starts. In this case, the camera
position will not be set by the cutscene at all, and therefore it will be
whatever it last was in the game, so the previewer has no way of knowing what
this value is.
2. There are less than 4 points in a camera command. The camera position is
undefined in this case (will be some garbage data on the stack). Or, other
undefined situations like key point eye and at positions are on top of each
other (zero length bone), etc.
3. There is some mistake in the scene structure / setup, e.g. missing custom
properties from a bone / armature. Error messages for this are printed in the
system terminal, but to avoid spamming you with GUI error messages every frame
in scenes you're not using this plugin in, there are no GUI error messages for
these kinds of issues.

### Link / Actor (NPC) Actions

The actor ID for an actor/NPC action is not the normal actor number. Look in
z_demo.c for the complete list. These numbers select which of 10 slots the
action values get written into. (Link has his own slot.) Then, each actor reads
from whatever slot it wants to, and changes its own behavior based on the value.

Each action is from a point to the next point. So, the minimum number of points
is 2, and you always need an extra point at the end. The Action ID values are
specific to each actor. In addition to start frame and action ID, each action
point has a position and rotation, which you can edit directly in the Blender
scene.

### Previewing Link / Actor (NPC) Actions

Click "Create preview object for action" to add a previewer object. This is an
empty object which will get animated when you play the Blender scene. It merely
moves between key frames with the starting rotation.

## Details

You don't have to read this stuff if you just want to use the plugin.

### How the in-game cutscene camera system works

The camera system in game is weird--this is partly why this previewer exists. 
If the previewer is not behaving as you expect, it's probably working correctly!
(Of course if the behavior differs between Blender and in-game, please report a
bug.)

First of all, the system is based on four-point spline interpolation. This
means, in the simplest case you have four values A-B-C-D, and the output changes
from B to C over the duration, except with the initial trajectory based on A-B
and with the final trajectory based on C-D so you get a nice curve. This is used
separately to interpolate eye (camera position) and at (target look-at position)
as well as camera roll and FOV. If you have more values (with the caveats
below), the system will move through all the values except the start and end
values. So basically you need an extra camera point at the beginning and at the
end to set how the camera is starting and stopping.

Now, the game's version of this is weird for two reasons.

#### Continue flag checking bug

If you don't care about the coding and just want to make cutscenes, you don't
have to worry about this, the plugin takes care of it at import/export. Just
make sure every cutscene command has at least 4 key points (bones).

There is a bug (in the actual game) where when incrementing to the next set
of key points, the key point which is checked for whether it's the last point
or not is the last point of the new set, not the last point of the old set.
This means that you always need an additional extra point at the end (except for
the case of exactly four points, see below). This is in addition to the extra
point at the end (and the one at the beginning) which are used for the spline
interpolation to set how the camera behaves at the start or the end. No data
whatsoever is read from this second extra point (except for the flag that it's
the last point, which is set up automatically on export).

For the case of 4 points, the camera motion from B to C works correctly, but
when it gets to C, it reads the continue flag out of bounds (which will be an
unspecified value). In most cases that byte won't be 0xFF, which means that on
the following frame it will take the case for 1/2/3 points, and not initialize
the camera position values at all, potentially leading to garbage values being
used for them.

So in summary:
* Command has 0 points: Will fail to export, but probably crash in game
* Command has 1/2/3 points: Command will immediately end; the position and look
will be uninitialized values, whatever was last on the stack (may cause a 
floating-point exception)
* Command has 4 points: Works, but don't let the cutscene get to the end of
this command
* Command has 5 points: Works as if it had 4 points
* Command has 6 points: Works as if it had 5 points
* Etc.

This plugin will automatically add this second extra point at the end on export,
and also automatically remove the extra point at the end on import unless the
command has only four points.

#### Frames interpolation

The number of frames actually spent between key points is interpolated in
reciprocals *and* in a varying way between the key points. This makes predicting
the number of frames actually spent extremely difficult unless the `frames`
values are the same. In fact it's so difficult that this plugin actually just
simulates the cutscene frame-by-frame up to the current frame every time the
Blender frame changes, because solving for the position at some future time
without actually stepping through all the frames up to there is too hard.
(It's a discretized differential equation--if time was continuous, i.e. the
frame rate was infinite, it could be solved with calculus, but since it moves
in discrete steps at the frames, even the calculus solution would be only
approximate. On top of that, when it changes from going between B-C and going
between C-D, the initial position near C depends on what happened at B, and so
on.)

You can think of it as it will spend *about* `frames` frames around each key
point. So, if the camera moves from point B to C but B has a larger `frames`
value than C, the camera will move more slowly near B and more quickly near C.
Also, a value of 0 means infinity, not zero--if C has `frames=0`, the camera
will approach C but never reach it.

Only the `frames` values of points B and C affect the result when the camera is
between B and C. So, the `frames` values of the one extra points at the
beginning and the end (in this case A and D) can be arbitrary.

The actual algorithm is:
* Compute the increment in `t` value (percentage of the way from point B to C)
  at point B by 1 / `B.frames`, or 0 if `B.frames` is 0
* Compute the increment in `t` value at point C by 1 / `C.frames` or 0.
* Linearly interpolate between these based on the current `t` value.
* Add this increment to `t`.

So you can think of it like, if `B.frames` is 10 and `C.frames` is 30, the
camera moves 1/10th of the way from B to C per frame when it's at B, and 1/30th
of the way from B to C per frame when it's nearly at C. But, when it's halfway
between B and C, it doesn't move 1/20th of the way per frame, it moves
(1/10)/2 + (1/30)/2 = 1/15th of the way. And on top of that, it will cross that
positional halfway point less than half the total number of frames it actually
takes to get from B to C.

#### end_frame

There is also an end_frame parameter in the cutscene data, however it is almost
useless, so it is not included as a custom property in the armature. The 
end_frame parameter does not end or stop the camera command--running out of
key points, or another camera command starting, is what does. It's only checked
when the camera command starts. In a normal cutscene where time starts from 0
and advances one frame at a time, as long as end_frame >= start_frame + 2, the
command will work the same.

So, this plugin just sets it to a "reasonable value" on export, and just
asserted for validity on import. It seems the original developers'
tool used the sum of all the points--including the second extra point--as the
end_frame parameter for CS_CAM_FOCUS_POINT_LIST, and used the sum of all the
points without the second extra point, plus 1, for the CS_CAM_POS_LIST. (Oh
yeah, did I mention they're different?) So the plugin replicates this behavior.
