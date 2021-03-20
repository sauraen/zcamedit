zcamedit - Zelda 64 (OoT/MM) cutscene camera editor Blender plugin

Copyright (C) 2021 Sauraen

GPL V3 licensed, see LICENSE.txt

This is a Blender plugin for 2.80+. Copy the zcamedit directory to your Blender plugins directory, then start Blender, go to Preferences > Addons, and search for and enable zcamedit.

Your scene should be set to 20 FPS. The structure should look like this,
where "-->" means child object.

Empty object, named "Cutscene.YourCutsceneNameHere"
        This represents a cutscene. Its name in C is YourCutsceneNameHere.
        There can be as many of these as you want per blend scene / file.
--> Camera. 
        Name can be anything, but each cutscene object should only have one
        camera as a child of it. This camera will get animated based on the
        cutscene. This is not exported, you can use one camera and just switch
        which cutscene it's in to preview different cutscenes.
--> Armature. Represents one camera command (contiguous camera shot).
        These will be sorted and processed in name order, so recommend naming
        them something like Shot01, Shot02, etc. or something else with a
        sortable name order. This is important because it's possible for a
        cutscene to have two commands starting on the same frame, and the
        first one in the cutscene binary data will get used, so we have to be
        able to control their order.
    Custom property: start_frame
    Custom property: end_frame
        Click "Init Armature & Bone Props" in the "zcamedit Armature Controls"
        panel within the armature properties window to create and initialize
        these. This will only create them if they don't exist, so clicking it
        again won't overwrite your frame settings if you've already set them.
        end_frame is almost useless, it does not end or stop the camera command
        (running out of key points, or another camera command starting, is what
        does). It's only checked when the camera command starts. In a normal
        cutscene where time starts from 0 and advances one frame at a time, as 
        long as end_frame >= start_frame + 2, the command will work the same.
    Bones. Represent camera key points.
        The head of each bone represents a camera position and the tail
        represents a camera focus point. The order of the bones as determined
        by their names represents the order of the key points, so they should
        be named something like K01, K02, or anything else with sortable names.
        The bone roll is used for the camera roll. Press Alt+R to reset the roll
        for an individual bone or click the "Reset All Bone Rolls" button (also
        in the "zcamedit Armature Controls" panel in armature properties) after
        editing bones. Note that any operation of moving the head or tail of a
        bone will change its roll, so you have to reset them frequently if you
        don't want roll in game. Also note that the B-Bone draw style does NOT
        display zero roll as the top and bottom surfaces of the bone being "not
        tilted", at least not if the position and focus point don't have the
        same Z value. Basically just ignore how the bone is drawn and set the
        roll manually if you want it to not be zero.
        Bone custom property: frames
        Bone custom property: fov
        "frames" means roughly how many frames the camera should spend near
        this key point, though this is weird with the spline interpolation
        algorithm. This weirdness is exactly why the camera previewer exists.
        If the previewer is not behaving as you expect, it's probably working
        correctly! Please check in game!
        "fov" means the camera FOV in degrees. 45 and 60 are some common values.
        The "Init Armature & Bone Props" button mentioned above will also add
        these custom properties to all bones. It won't mess with existing values
        so you should click it any time you add bones.
--> Another armature if you want another camera command.
--> Etc.
