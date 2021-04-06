zcamedit - Zelda 64 (OoT/MM) cutscene camera editor Blender plugin

Copyright (C) 2021 Sauraen

GPL V3 licensed, see LICENSE.txt

## Installation

This is a Blender plugin for 2.80+. Copy the zcamedit directory to your Blender
plugins directory, then start Blender, go to Preferences > Addons, and search
for and enable zcamedit.

## Important things to know

Your scene should be set to 20 FPS and 320x240 render. If you import, this will
be set up automatically.

If the preview camera moves to the origin aiming downwards, this means
"undefined camera position", which can be caused by three things.
1. It's a frame before the first command starts. In this case, the camera
position will not be set by the cutscene at all, and therefore it will be
whatever it last was in the game, so the previewer has no way of knowing what
this value is.
2. There are less than 4 points in a camera command, or there are 4 points but
the command ran out (see below). The camera position is undefined in these
cases (will be some garbage data on the stack). Or, other undefined situations
like key point eye and at positions are on top of each other (zero length bone),
etc.
3. There is some mistake in the scene structure / setup, e.g. missing custom
properties from a bone / armature. Error messages for this are printed in the
system terminal, but to avoid spamming you with GUI error messages every frame
in scenes you're not using this plugin in, there are no GUI error messages for
these kinds of issues.

## How the in-game cutscene camera system works

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


## Scene structure

The structure should look like this:

#### Empty object, named "Cutscene.YourCutsceneNameHere". Represents a cutscene.
* Camera. Gets animated for preview. Not exported.
* Armature. Represents one camera command (contiguous camera shot).
    * Bone. Represents a camera key point.
    * Bone.
    * Etc.
* Another armature if you want another camera command.
* Etc.
#### Another cutscene.
#### Etc.

## Cutscene empty object

This represents a cutscene. Its name in Blender must start with "Cutscene.",
e.g. "Cutscene.YourCutsceneNameHere", in which case its name in C will be
YourCutsceneNameHere. There can be as many of these as you want per blend scene
/ file.

## Preview camera

Name can be anything, but each cutscene object should only have one camera as a
child of it. This camera will get animated based on the cutscene. This is not
exported.

You can use one camera and just switch which cutscene it's parented to to
preview different cutscenes.

## Armature / camera command

These will be sorted and processed in name order, so recommend naming them
something like Shot01, Shot02, etc. or something else with a sortable name
order. This is important because it's possible for a cutscene to have two
commands starting on the same frame, and the first one in the cutscene binary
data will get used by the game engine, so we have to be able to control their
order.        

Each armature must have the custom properties described below. Click
"Init Armature & Bone Props" in the "zcamedit Armature Controls" panel within
the armature properties window to create and initialize these. This will only
create them if they don't exist, so clicking it again won't overwrite your
settings if you've already set them.

#### start_frame

The camera action actually starts on frame start_frame+1.

#### end_frame

There is also an end_frame parameter in the cutscene data, however it is almost
useless. It does not end or stop the camera command--running out of key points,
or another camera command starting, is what does. It's only checked when the
camera command starts. In a normal cutscene where time starts from 0 and
advances one frame at a time, as long as end_frame >= start_frame + 2, the
command will work the same.

So, this plugin just sets it to a "reasonable value" (the sum of the `frames`
values of all the key points, though this is not the number of frames the
camera command actually lasts for! This was chosen because it seems like what
the original developers' tool did) on export, and just asserted for validity on
import.

So this is not actually a custom property in the armature--you can ignore it.

#### rel_link

rel_link is a boolean for whether the camera command is normal (False)
(0x01 and 0x02) or relative to Link (True) (0x05 and 0x06).

## Bone

The head of each bone represents a camera position and the tail
represents a camera focus point. The order of the bones as determined
by their names represents the order of the key points, so they should
be named something like K01, K02, or anything else with sortable names.

Each bone must have the following custom properties. The "Init Armature & Bone 
Props" button mentioned above will also add these custom properties to all 
bones. It won't mess with existing values so you should click it any time you
add bones.

#### frames

Roughly how many frames the camera should spend near this key point, see above.

#### fov

Camera FOV in degrees. 45.0 and 60.0 are some common values.

#### camroll

The roll (rotation around its axis) of the camera. For technical reasons, bone
roll is not used as camera roll. (Also bone roll changes whenever you edit the
bone anyway, so it'd be kinda a pain.) Positive values turn the image clockwise
(turn the camera body counterclockwise).
