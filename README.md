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
1. It's the first frame (or a frame before the first command starts). In these
cases, the camera position will not be set by the cutscene at all, and therefore
it will be whatever it last was in the game, so the previewer has no way of
knowing what this value is.
2. There is some mistake in the scene structure / setup, e.g. missing custom
properties from a bone / armature. Error messages for this are printed in the
system terminal, but to avoid spamming you with GUI error messages every frame
in scenes you're not using this plugin in, there are no GUI error messages for
these kinds of issues.
3. Undefined situations in the actual data, e.g. if a key point eye and at
positions are on top of each other (zero length bone), if key point frame counts
are negative, etc.

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

There is a bug (in the actual game) where when incrementing to the next set
of key points, the key point which is checked for whether it's the last point
or not is the last point of the new set, not the last point of the old set.
This means that you always need an additional extra point at the end, except for
the case of exactly four points. This is in addition to the extra point at the
end (and the one at the beginning) which are used for the spline interpolation
to set how the camera behaves at the start or the end. No data whatsoever is
read from this second extra point (except for the flag that it's the last point,
which is set up automatically on export). So you can make this the same as the
first extra point at the end, or put it wherever else, or set its parameters to
any values.

So in summary:
* Command has 0 points: Will fail to export, but probably crash in game
* Command has 1/2/3 points: Command will immediately end; the position and look
will be uninitialized values, whatever was last on the stack (may cause a 
floating-point exception)
* Command has 4 points: Works normally
* Command has 5 points: Works exactly the same as 4 points; fifth point ignored
* Command has 6 points: Works exactly the same as 5 points: sixth point ignored
* Etc.

#### Frames interpolation

The number of frames actually spent between key points is interpolated in
reciprocals *and* in a varying way between the key points. This makes predicting
the number of frames actually spent extremely difficult unless the `frames`
values are the same. You can think of it as it will spend *about* `frames`
frames around each key point.




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

Each armature must have the following custom properties. Click "Init Armature & 
Bone Props" in the "zcamedit Armature Controls" panel within the armature 
properties window to create and initialize these. This will only create them if
they don't exist, so clicking it again won't overwrite your frame settings if
you've already set them.

#### start_frame

The camera action actually starts on frame startFrame+1, but it doesn't
update until the second frame it's run (the first frame is init). So,
e.g. if startFrame = 10, the first frame where the camera has moved will
be frame 12, and on frame 11 it will be in the exact same position as
it was in on frame 10 due to whatever previous commands.

#### end_frame

end_frame is almost useless, it does not end or stop the camera command
(running out of key points, or another camera command starting, is what
does). It's only checked when the camera command starts. In a normal
cutscene where time starts from 0 and advances one frame at a time, as 
long as end_frame >= start_frame + 2, the command will work the same.

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
roll is not used as camera roll. (Also it changes whenever you edit the bone
anyway, so it'd be kinda a pain.) Positive values turn the image clockwise
(turn the camera body counterclockwise).
