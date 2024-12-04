import pygame
import sys
import math
import random
from Ball.ball import BallGame
from RockPaperScissors.rpsdata import RockPaperScissors
from snake_game.snake import SnakeGame
from utils.sound_manager import SoundManager
import os

class MainMenu:
    def __init__(self):
        pygame.init()
        self.WIDTH = 1280
        self.HEIGHT = 720
        self.screen = pygame.display.set_mode((self.WIDTH, self.HEIGHT), pygame.RESIZABLE)
        pygame.display.set_caption("AI Games for Kids!")
        
        # Colors
        self.PRIMARY = (75, 0, 130)  # Deep Purple
        self.SECONDARY = (255, 140, 0)  # Orange
        self.ACCENT = (0, 255, 255)  # Cyan
        self.WHITE = (255, 255, 255)
        self.BLACK = (0, 0, 0)
        self.GRAY = (128, 128, 128)
        
        # Fonts
        self.title_font = pygame.font.Font(None, 80)
        self.button_font = pygame.font.Font(None, 50)
        self.info_font = pygame.font.Font(None, 36)
        
        # Button properties
        self.button_width = 300
        self.button_height = 80
        self.button_spacing = 40
        self.button_radius = 20
        
        # Game buttons with descriptions and icons
        self.games = [
            {
                'name': 'Snake Game',
                'description': 'Control the snake with your hands! Collect food and grow longer.',
                'color': (50, 168, 82),
                'icon': '🐍'
            },
            {
                'name': 'Ball Game',
                'description': 'Play ping-pong using hand gestures! Test your reflexes.',
                'color': (66, 135, 245),
                'icon': '🏓'
            },
            {
                'name': 'Rock Paper Scissors',
                'description': 'Challenge the AI with hand gestures! Can you win?',
                'color': (245, 66, 66),
                'icon': '✌️'
            }
        ]
        
        # Particle system
        self.particles = []
        self.MAX_PARTICLES = 100
        
        # Background stars
        self.stars = [(random.randint(0, self.WIDTH), random.randint(0, self.HEIGHT)) 
                     for _ in range(100)]
        self.star_speeds = [random.uniform(0.5, 2) for _ in range(100)]
        
        # Sound effects
        self.sound_manager = SoundManager()
        self.hover_sound = None  # Add hover sound file
        self.select_sound = None  # Add select sound file
        
        # Animation variables
        self.title_y = -100
        self.button_x = -self.button_width
        self.animation_speed = 5
        self.hover_scale = 1.0
        self.selected_game = None
        
        # ESC state
        self.esc_pressed = False
        self.esc_press_time = 0
        self.ESC_TIMEOUT = 2000
        
    def draw_title(self):
        title_target_y = 80
        self.title_y += (title_target_y - self.title_y) * 0.1
        
        # Draw main title with gradient and shadow
        title_text = "AI Games for Kids!"
        shadow_offset = 4
        
        # Draw shadow
        shadow_surf = self.title_font.render(title_text, True, (0, 0, 0, 128))
        shadow_rect = shadow_surf.get_rect(center=(self.WIDTH//2 + shadow_offset, 
                                                 self.title_y + shadow_offset))
        self.screen.blit(shadow_surf, shadow_rect)
        
        # Draw main text with gradient
        text_surf = self.title_font.render(title_text, True, self.ACCENT)
        text_rect = text_surf.get_rect(center=(self.WIDTH//2, self.title_y))
        self.screen.blit(text_surf, text_rect)
        
        # Draw subtitle
        subtitle = "Play, Learn, and Have Fun with AI!"
        sub_surf = self.info_font.render(subtitle, True, self.WHITE)
        sub_rect = sub_surf.get_rect(center=(self.WIDTH//2, self.title_y + 60))
        self.screen.blit(sub_surf, sub_rect)
    
    def draw_button(self, rect, text, description, color, icon, hovered=False):
        # Button background with gradient
        if hovered:
            color = tuple(min(c + 30, 255) for c in color)
            pygame.draw.rect(self.screen, color, rect, border_radius=self.button_radius)
            # Add glow effect
            for i in range(3):
                glow_rect = rect.inflate(i*4, i*4)
                pygame.draw.rect(self.screen, (*color, 100-i*30), glow_rect, 
                               border_radius=self.button_radius+i*2, width=2)
        else:
            pygame.draw.rect(self.screen, color, rect, border_radius=self.button_radius)
        
        # Draw icon
        icon_font = pygame.font.Font(None, 60)
        icon_surf = icon_font.render(icon, True, self.WHITE)
        icon_rect = icon_surf.get_rect(midleft=(rect.left + 20, rect.centery))
        self.screen.blit(icon_surf, icon_rect)
        
        # Draw game name
        text_surf = self.button_font.render(text, True, self.WHITE)
        text_rect = text_surf.get_rect(midleft=(icon_rect.right + 20, rect.centery))
        self.screen.blit(text_surf, text_rect)
        
        # Draw description below button when hovered
        if hovered:
            desc_surf = self.info_font.render(description, True, self.WHITE)
            desc_rect = desc_surf.get_rect(midtop=(rect.centerx, rect.bottom + 10))
            self.screen.blit(desc_surf, desc_rect)
    
    def update_stars(self):
        for i in range(len(self.stars)):
            x, y = self.stars[i]
            speed = self.star_speeds[i]
            y = (y + speed) % self.HEIGHT
            self.stars[i] = (x, y)
            
            # Draw star with twinkling effect
            brightness = random.randint(100, 255)
            size = random.randint(1, 3)
            pygame.draw.circle(self.screen, (brightness, brightness, brightness), 
                             (int(x), int(y)), size)
    
    def add_particles(self, pos, color):
        for _ in range(10):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(2, 5)
            self.particles.append({
                'pos': list(pos),
                'vel': [math.cos(angle) * speed, math.sin(angle) * speed],
                'color': color,
                'life': 1.0
            })
    
    def update_particles(self):
        for particle in self.particles[:]:
            particle['pos'][0] += particle['vel'][0]
            particle['pos'][1] += particle['vel'][1]
            particle['life'] -= 0.02
            
            if particle['life'] <= 0:
                self.particles.remove(particle)
            else:
                color = particle['color']
                alpha = int(particle['life'] * 255)
                pygame.draw.circle(self.screen, (*color, alpha), 
                                 (int(particle['pos'][0]), int(particle['pos'][1])), 3)
    
    def run(self):
        clock = pygame.time.Clock()
        running = True
        selected_game = None
        
        while running:
            current_time = pygame.time.get_ticks()
            mouse_pos = pygame.mouse.get_pos()
            
            # Handle events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        if self.esc_pressed:
                            # Second ESC press within timeout - quit game
                            running = False
                        else:
                            # First ESC press - set flag and timer
                            self.esc_pressed = True
                            self.esc_press_time = current_time
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    # Check button clicks
                    for i, game in enumerate(self.games):
                        button_rect = pygame.Rect(
                            self.WIDTH//2 - self.button_width//2,
                            250 + i * (self.button_height + self.button_spacing),
                            self.button_width, self.button_height
                        )
                        if button_rect.collidepoint(mouse_pos):
                            self.add_particles(mouse_pos, game['color'])
                            selected_game = game['name']
                            # Play select sound
                            break
            
            # Reset ESC state if timeout reached
            if self.esc_pressed and current_time - self.esc_press_time > self.ESC_TIMEOUT:
                self.esc_pressed = False
            
            # Clear screen with space background
            self.screen.fill(self.BLACK)
            self.update_stars()
            
            # Draw title
            self.draw_title()
            
            # Draw game buttons
            for i, game in enumerate(self.games):
                button_rect = pygame.Rect(
                    self.WIDTH//2 - self.button_width//2,
                    250 + i * (self.button_height + self.button_spacing),
                    self.button_width, self.button_height
                )
                
                # Check hover
                hovered = button_rect.collidepoint(mouse_pos)
                self.draw_button(button_rect, game['name'], game['description'], 
                               game['color'], game['icon'], hovered)
            
            # Update and draw particles
            self.update_particles()
            
            # Draw ESC message if needed
            if self.esc_pressed:
                msg = "Press ESC again to quit"
                text_surf = self.info_font.render(msg, True, self.WHITE)
                text_rect = text_surf.get_rect(center=(self.WIDTH//2, self.HEIGHT - 50))
                self.screen.blit(text_surf, text_rect)
            
            # Launch selected game
            if selected_game:
                if selected_game == "Snake Game":
                    game = SnakeGame()
                    game.run()
                elif selected_game == "Ball Game":
                    game = BallGame()
                    game.run()
                elif selected_game == "Rock Paper Scissors":
                    game = RockPaperScissors()
                    game.run()
                selected_game = None
                self.esc_pressed = False  # Reset ESC state
            
            pygame.display.flip()
            clock.tick(60)
        
        pygame.quit()

if __name__ == "__main__":
    menu = MainMenu()
    menu.run()
    sys.exit()
