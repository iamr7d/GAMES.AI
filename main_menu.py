import pygame
import sys
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
        self.init_display()
        
        # Initialize fonts
        self.title_font = pygame.font.Font(None, 74)
        self.font = pygame.font.Font(None, 48)
        self.small_font = pygame.font.Font(None, 36)
        
        # Colors
        self.WHITE = (255, 255, 255)
        self.BLACK = (0, 0, 0)
        self.GRAY = (128, 128, 128)
        self.PURPLE = (147, 0, 211)
        self.YELLOW = (255, 255, 0)
        
        # Game state
        self.running = True
        self.should_quit = False
        
        # ESC handling
        self.esc_pressed = False
        self.esc_press_time = 0
        self.ESC_TIMEOUT = 2000
        
        # Initialize buttons
        self.init_buttons()
    
    def init_display(self):
        """Initialize or reinitialize the display"""
        self.screen = pygame.display.set_mode((self.WIDTH, self.HEIGHT))
        pygame.display.set_caption("AI Mini Games")
    
    def init_buttons(self):
        """Initialize menu buttons"""
        button_width = 300
        button_height = 60
        button_y_start = 250
        button_spacing = 100
        
        self.buttons = []
        games = ["Snake Game", "Ball Game", "Rock Paper Scissors"]
        
        for i, game in enumerate(games):
            button_y = button_y_start + (i * button_spacing)
            button_rect = pygame.Rect(
                self.WIDTH//2 - button_width//2,
                button_y,
                button_width,
                button_height
            )
            self.buttons.append({
                'rect': button_rect,
                'text': game,
                'hover': False,
                'y_offset': 0
            })
    
    def handle_events(self):
        current_time = pygame.time.get_ticks()
        
        # Reset ESC state if timeout reached
        if self.esc_pressed and current_time - self.esc_press_time > self.ESC_TIMEOUT:
            self.esc_pressed = False
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                self.should_quit = True
                return
            
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if self.esc_pressed:
                        self.running = False
                        self.should_quit = True
                        return
                    else:
                        self.esc_pressed = True
                        self.esc_press_time = current_time
            
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left click
                    for button in self.buttons:
                        if button['rect'].collidepoint(event.pos):
                            game_name = button['text']
                            
                            # Create game instance
                            game = None
                            if game_name == "Snake Game":
                                game = SnakeGame()
                            elif game_name == "Ball Game":
                                game = BallGame()
                            elif game_name == "Rock Paper Scissors":
                                game = RockPaperScissors()
                            
                            if game:
                                # Run the game
                                return_to_menu = game.run()
                                
                                if not return_to_menu:
                                    self.running = False
                                    self.should_quit = True
                                    return
                                
                                # Reinitialize display and reset state
                                self.init_display()
                                self.esc_pressed = False
    
    def draw(self):
        try:
            self.screen.fill(self.BLACK)
            
            # Draw title
            title_text = "AI Mini Games"
            title_surf = self.title_font.render(title_text, True, self.PURPLE)
            title_rect = title_surf.get_rect(center=(self.WIDTH//2, 120))
            
            # Add glow to title
            for i in range(3):
                glow_surf = pygame.Surface(title_surf.get_size(), pygame.SRCALPHA)
                glow_surf.blit(title_surf, (0, 0))
                size_mult = 1 + (i * 0.1)
                scaled_size = (int(glow_surf.get_width() * size_mult), 
                             int(glow_surf.get_height() * size_mult))
                glow_surf = pygame.transform.smoothscale(glow_surf, scaled_size)
                glow_surf.set_alpha(100 - i * 30)
                glow_rect = glow_surf.get_rect(center=title_rect.center)
                self.screen.blit(glow_surf, glow_rect)
            
            self.screen.blit(title_surf, title_rect)
            
            # Draw buttons
            mouse_pos = pygame.mouse.get_pos()
            for button in self.buttons:
                # Update hover state
                button['hover'] = button['rect'].collidepoint(mouse_pos)
                
                # Animate hover effect
                if button['hover']:
                    button['y_offset'] = min(button['y_offset'] + 0.5, 5)
                else:
                    button['y_offset'] = max(button['y_offset'] - 0.5, 0)
                
                # Draw button
                button_color = self.PURPLE if button['hover'] else self.GRAY
                button_y = button['rect'].y - button['y_offset']
                
                # Draw button glow
                for i in range(3):
                    glow_rect = pygame.Rect(
                        button['rect'].x - i*2,
                        button_y - i*2,
                        button['rect'].width + i*4,
                        button['rect'].height + i*4
                    )
                    pygame.draw.rect(self.screen, (*button_color, 50-i*15), 
                                   glow_rect, border_radius=10)
                
                # Draw main button
                pygame.draw.rect(self.screen, button_color,
                               (button['rect'].x, button_y,
                                button['rect'].width, button['rect'].height),
                               border_radius=10)
                
                # Draw button text
                text_surf = self.font.render(button['text'], True, self.WHITE)
                text_rect = text_surf.get_rect(
                    center=(button['rect'].centerx,
                           button_y + button['rect'].height//2)
                )
                self.screen.blit(text_surf, text_rect)
            
            # Draw ESC message if needed
            if self.esc_pressed:
                msg = "Press ESC again to quit"
                text_surf = self.small_font.render(msg, True, self.WHITE)
                text_rect = text_surf.get_rect(center=(self.WIDTH//2, self.HEIGHT - 50))
                self.screen.blit(text_surf, text_rect)
            
            pygame.display.flip()
        except pygame.error:
            # Handle display surface errors by attempting to reinitialize
            self.init_display()
    
    def run(self):
        clock = pygame.time.Clock()
        
        while self.running:
            self.handle_events()
            if self.running:  # Check again in case handle_events changed it
                self.draw()
            clock.tick(60)
        
        if self.should_quit:
            pygame.quit()

if __name__ == "__main__":
    menu = MainMenu()
    menu.run()
