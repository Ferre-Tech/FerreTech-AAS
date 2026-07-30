# VRC-Arousal-System

Automatic arousal system for VRChat

## Requirements
    VRCFury
    OSCGoesBrr
    An avatar with VRCFury sockets/plugs
    An asset with a radial value to assign to the system

## Before you begin
Ensure you have an OSC Proxy set up through OSCGoesBrr under Home>VRChat>Advanced Settings pointing to localhost:9010 (default)
Avatars without sockets/plugs will get added to the Avatar configs folder, but they will be unable to be configured with the system, and it will not update if sockets and plugs are added.

## Configuration:

### Config Tool
    
The config tool can be ran and supplied with an avatar blueprint ID in order to generate a config in the FerreTech/Avatars folder.
This folder is either located in:
    Windows: %APPDATA%/Roaming/FerreTech
    Mac/Linux: ~/Documents/FerreTech

### Automatic when running Auto-arousal System
    
When running the auto-arousal system you can change avatars to generate a new config file or to update the parameter names on an existing avatar. The output is the same as the config tool.

### Avatar Configuration
You will need to set the parameter name that VRChat uses to the parameters listed in the config file in order for them to update within VRChat with the values sent by this system. If the name does not match it will not do anything in VRChat.

Once set you can configure any of the extra settings to your liking and swap into the avatar to reload any changes you made.

There is presently no way to reload the config without swapping avatars. This includes when launching VRChat. The config will update between instances due to VRChat reloading you avatar.