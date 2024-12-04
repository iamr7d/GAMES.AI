import pygame
import os

class SoundManager:
    def __init__(self):
        pygame.mixer.init()
        self.sounds = {}
        self.music_volume = 0.5
        self.sound_volume = 0.7
        self.music_playing = False
        
        # Create default sounds dictionary with None values
        self.default_sounds = {
            'menu_music': None,
            'menu_select': None,
            'menu_hover': None,
            'game_music': None,
            'game_over': None,
            'collision': None,
            'score': None,
            'special': None
        }
        
        self.sounds = self.default_sounds.copy()
    
    def load_sound(self, name, path):
        """Load a sound effect"""
        try:
            if os.path.exists(path):
                self.sounds[name] = pygame.mixer.Sound(path)
                self.sounds[name].set_volume(self.sound_volume)
                return True
        except:
            print(f"Could not load sound: {path}")
        return False
    
    def load_music(self, path):
        """Load background music"""
        try:
            if os.path.exists(path):
                pygame.mixer.music.load(path)
                pygame.mixer.music.set_volume(self.music_volume)
                return True
        except:
            print(f"Could not load music: {path}")
        return False
    
    def play_sound(self, name):
        """Play a sound effect"""
        if name in self.sounds and self.sounds[name]:
            self.sounds[name].play()
    
    def play_music(self, loop=True):
        """Start playing the loaded music"""
        try:
            pygame.mixer.music.play(-1 if loop else 0)
            self.music_playing = True
        except:
            print("Could not play music")
    
    def stop_music(self):
        """Stop the currently playing music"""
        try:
            pygame.mixer.music.stop()
            self.music_playing = False
        except:
            print("Could not stop music")
    
    def pause_music(self):
        """Pause the currently playing music"""
        try:
            pygame.mixer.music.pause()
            self.music_playing = False
        except:
            print("Could not pause music")
    
    def unpause_music(self):
        """Unpause the music"""
        try:
            pygame.mixer.music.unpause()
            self.music_playing = True
        except:
            print("Could not unpause music")
    
    def set_music_volume(self, volume):
        """Set music volume (0.0 to 1.0)"""
        self.music_volume = max(0.0, min(1.0, volume))
        pygame.mixer.music.set_volume(self.music_volume)
    
    def set_sound_volume(self, volume):
        """Set sound effects volume (0.0 to 1.0)"""
        self.sound_volume = max(0.0, min(1.0, volume))
        for sound in self.sounds.values():
            if sound:
                sound.set_volume(self.sound_volume)
    
    def toggle_music(self):
        """Toggle music on/off"""
        if self.music_playing:
            self.pause_music()
        else:
            self.unpause_music()
