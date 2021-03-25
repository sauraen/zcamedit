zcamedit - Zelda 64 (OoT/MM) cutscene camera editor Blender plugin

Copyright (C) 2021 Sauraen

GPL V3 licensed, see LICENSE.txt

## Installation

This is a Blender plugin for 2.80+. Copy the zcamedit directory to your Blender
plugins directory, then start Blender, go to Preferences > Addons, and search
for and enable zcamedit.

## Important things to know

Your scene should be set to 20 FPS.

If the preview camera moves to the origin aiming downwards, this means
"undefined camera position", which can be caused by two things.
1. There is some mistake in the scene structure / setup, e.g. missing custom
properties from a bone / armature. Error messages for this are printed in the
system terminal, but to avoid spamming you with GUI error messages every frame
in scenes you're not using this plugin in, there are no GUI error messages for
these kinds of issues.
2. The camera position is actually undefined. For example, on the first frame
(frame 1, if startFrame of the first command is 0), the camera position will
not be set by the cutscene at all, and therefore it will be whatever it last
was in the game, so the previewer has no way of knowing what this value is.
Other examples of actually undefined camera positions would be: if a key point
eye and at positions are on top of each other (zero length bone), if key point
frame counts are negative, etc.


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

Roughly how many frames the camera should spend near this key point, though this
is weird with the spline interpolation algorithm. This weirdness is exactly why
the camera previewer exists. If the previewer is not behaving as you expect,
it's probably working correctly!

#### fov

Camera FOV in degrees. 45.0 and 60.0 are some common values.

#### camroll

The roll (rotation around its axis) of the camera. For technical reasons, bone
roll is not used as camera roll. (Also it changes whenever you edit the bone
anyway, so it'd be kinda a pain.) Positive values turn the image clockwise
(turn the camera body counterclockwise).
