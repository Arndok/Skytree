"""
A Singleton class to organize and manage resources.

Variables used from config: IMG_PATH, FONT_SIZE, FONT_PATH, SOUND_PATH, FILE_PATH
"""

import pygame
from skytree.singleton import Singleton
from skytree import config

class ResourceManager(metaclass=Singleton):
    """
    A class to organize all resource management for the game. It is a Singleton.
    
    Public methods:
    get_image(img): Try to fetch an image from the dict; try to load it if absent.
    get_font(font, size): Try to fetch a font from the dict; try to load it if absent.
    get_sound(sound): Try to fetch a sound from the dict; try to load it if absent.
    get_file(file): Try to fetch a file from the dict; tries to load it if absent.
    unload_image(img): If the given image is in the dict, delete it.
    unload_font(font, size): If the given font is in the dict, delete it.
    unload_sound(sound): If the given sound is in the dict, delete it.
    unload_file(file): If the given file is in the dict, delete it.
    unload_all_images(): Clear the images dict.
    unload_all_fonts(): Clear the fonts dict.
    unload_all_sounds(): Clear the sounds dict.
    unload_all_files(): Clear the files dict.
    unload_all(): Clear all dicts.
    """
    
    def __init__(self):
        """Define a dictionary for each kind of resource."""
        self._images = {}
        """A dictionary that maps image file names to image objects."""
        self._fonts = {}
        """A dictionary that maps font file names and sizes to font objects."""
        self._files = {}
        """A dictionary that maps file names to file objects."""
        self._sounds = {}
        """A dictionary that maps sound file names to sound objects."""

    def _load_image(self, img):
        """
        Load an image file as a Pygame Surface with transparency into the img dictionary and return it.
        
        In case of error, Pygame will handle it.
        """
        self._images[img] = pygame.image.load(config.IMG_PATH + img).convert_alpha()
        return self._images[img]
        
    def _load_font(self, font, size=None):
        """
        Load a font as a font object into the font dictionary and return it.
        
        Different sizes generate different font objects.
        If left as None, use framework's font size default.
        In case of error, Pygame will handle it.
        """
        if not size:
            size = config.FONT_SIZE
        flabel = font+"_"+str(size)
        self._fonts[flabel] = pygame.font.Font(config.FONT_PATH + font, size)
        return self._fonts[flabel]
        
    def _load_sound(self, sound):
        """
        Load a sound as a Sound object into the sound dictionary.
        
        In case of error, Pygame will handle it.
        """
        self._sounds[sound] = pygame.mixer.Sound(config.SOUND_PATH + sound)
        return self._sounds[sound]

    def _load_file(self, file):
        """
        Load a file as a list of lines into the file dictionary.
        
        Raise FileNotFoundError if the file is --well, not found.
        """
        try:
            with open(config.FILE_PATH + file, "r") as f:
                self._files[file] = [line for line in f]
        except FileNotFoundError as err:
            print("Couldn't load file '{f}' --".format(f=file), err)
            raise
        return self._files[file]
            
    def get_image(self, img):
        """Try to fetch an image from the dict; try to load it if absent."""
        if img in self._images:
            return self._images[img]
        else:
            return self._load_image(img)
    
    def get_font(self, font, size=None):
        """
        Try to fetch a font from the dict; try to load it if absent.
        
        Different sizes generate different font objects.
        If left as None, use framework's font size default.
        """
        if not size:
            size = config.FONT_SIZE
        flabel = font+"_"+str(size)
        if flabel in self._fonts:
            return self._fonts[flabel]
        else:
            return self._load_font(font, size)

    def get_sound(self, sound):
        """Try to fetch a sound from the dict; try to load it if absent."""
        if sound in self._sounds:
            return self._sounds[sound]
        else:
            return self._load_sound(sound)

    def get_file(self, file):
        """Try to fetch a file from the dict; try to load it if absent."""
        if file in self._files:
            return self._files[file]
        else:
            return self._load_file(file)
    
    def unload_image(self, img):
        """If the given image is in the dict, delete it."""
        if img in self._images:
            del self._images[img]

    def unload_font(self, font, size=None):
        """
        If the given font is in the dict, delete it.
        
        Leaving size as None will use the framework's default font size.
        Using the keyword "all" will delete every font object built from the given font.
        """
        if size == "all":
            fonts = []
            name_length = len(font)
            for flabel in self._fonts:
                if flabel[:name_length] == font:
                    fonts.append(flabel)
            for flabel in fonts:
                del self._fonts[flabel]
        else:
            if not size:
                size = config.FONT_SIZE
            flabel = font+"_"+str(size)
            if flabel in self._fonts:
                del self._fonts[flabel]

    def unload_sound(self, sound):
        """If the given sound is in the dict, delete it."""
        if sound in self._sounds:
            del self._sounds[sound]

    def unload_file(file):
        """If the given file is in the dict, delete it."""
        if file in self._files:
            del self._files[file]
    
    def unload_all_images(self):
        """Clear the images dict."""
        self._images.clear()
        
    def unload_all_fonts(self):
        """Clear the fonts dict."""
        self._fonts.clear()
    
    def unload_all_sounds(self):
        """Clear the sounds dict."""
        self._sounds.clear()

    def unload_all_files(self):
        """Clear the files dict."""
        self._files.clear()
        
    def unload_all(self):
        """Dump it all like the pigs are coming."""
        for dict in (self._images, self._fonts, self._sounds, self._files):
            dict.clear()