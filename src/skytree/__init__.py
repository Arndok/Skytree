"""
Skytree - A 2D game framework for Python

Version: 0.1.1

This project is licensed under the Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License. 
You may share and adapt the material for non-commercial purposes, as long as you provide appropriate attribution and share any adaptations under the same license.

For more details, see: https://creativecommons.org/licenses/by-nc-sa/4.0/

Copyright (c) Pablo Reyes de Rojas 2024

###

The broad object structure is a tree graph, with nodes inheriting from component.Component.
  Components can be owned by another component and can own their own components.
  Basic functionalities are propagated through components (see component documentation).
The root of the tree is a singleton game.Game object.
Resources are managed through a singleton resource_manager.ResourceManager object.
There's heavy use of multiple inheritance for constructing objects; most importantly Sprites (see sprites documentation).
The framework features some funcionalities for working with tiled spaces (see layer, tile_objects, sprites and board documentation).

General usage goes like this:
- Import config and set variables as needed (at the very least variables needed to instantiate Game).
- Instantiate Game and set event controllers (these can also be set right before running the game).
- Import every other necessary part of the framework.
- Set game variables and objects.
- Define game entities, layers, boards and stages.
- Run the game.

Modules:
config: a repository of variables to be used as definitions for other classes.
helpers: a repository of helper functions.
tools: a repository of file manipulation functions.
singleton: a singleton metaclass, used by game.Game and resource_manager.ResourceManager.
component: the base class for the nodes of the game tree --the core of the framework.
updateable: a Component direct subclass that can keep track of time and do some work on each frame.
positional: a Component direct subclass that can have a presence in a 2d space.
collidable: Hitbox classes and a Positional subclass that uses them to test collisions.
resource_manager: a singleton class to organize all resource management for the game.
drawable: a Positional subclass that can have a visible appearance.
tileset: a Drawable subclass with a tiled canvas and ability to select which of those tiles is drawn on any given moment.
timers: Updateable subclasses that can keep track of time; includes countdowns that can trigger an action when reaching zero, with two subclass variants.
animated: Drawable subclasses that use a tileset to support frame-by-frame animation.
key_commands: an event controller for key pressed and releases and a Component direct subclass that can process commands coming from it.
user_interface: UI objects and states.
game: a singleton class to initialize the game and run the main loop (the root of the game tree), and a base class for the game states.
stage: an object to help organize groups of interconnected game spaces.
boards: enclosed game spaces.
layers: visible layers on a game space.
tile_objects: objects associated with tiles on a grid (tightly connected to layers.TiledLayer).
sprites: a collection of classes used to build game entities, mostly through multiple inheritance.
examples: a runnable demo!
"""

__author__ = "Pablo Reyes de Rojas"
__version__ = "0.1.1"
__all__ = [
    "config",
    "component",
    "updateable",
    "positional",
    "collidable",
    "resource_manager",
    "drawable",
    "tileset",
    "timers",
    "animated",
    "key_commands",
    "user_interface",
    "game",
    "stage",
    "boards",
    "layers",
    "tile_objects",
    "sprites",
    "examples"
    ]
