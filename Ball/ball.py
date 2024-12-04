import pygame
import cv2
import mediapipe as mp
import numpy as np
import random
import math
from utils.sound_manager import SoundManager

class BallGame:
    def __init__(self):
        pygame.init()
        self.WIDTH = 1280
        self.HEIGHT = 720
        self.screen = pygame.display.set_mode((self.WIDTH, self.HEIGHT), pygame.RESIZABLE)
        pygame.display.set_caption("AI Ping Pong")
        
        # Colors
        self.WHITE = (255, 255, 255)
        self.BLACK = (0, 0, 0)
        self.BLUE = (30, 144, 255)
        self.RED = (255, 50, 50)
        self.GREEN = (50, 205, 50)
        self.YELLOW = (255, 215, 0)
        self.PURPLE = (147, 0, 211)
        self.GRAY = (128, 128, 128)
        
        # Fonts
        self.title_font = pygame.font.Font(None, 74)
        self.font = pygame.font.Font(None, 48)
        self.small_font = pygame.font.Font(None, 36)
        
        # Game objects
        self.paddle_width = 20
        self.paddle_height = 100
        self.ball_size = 20
        self.paddle_speed = 10
        self.ball_speed = 7
        
        # Particle system
        self.particles = []
        self.MAX_PARTICLES = 100
        
        # Sound manager
        self.sound_manager = SoundManager()
        
        # Hand tracking
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            min_detection_confidence=0.7,
            min_tracking_confidence=0.7)
        self.cap = cv2.VideoCapture(0)
        
        # Game states
        self.paused = False
        self.game_over = False
        self.show_tutorial = True
        self.hand_control = False
        
        # Initialize game state
        self.reset_game()
    
    def reset_game(self):
        self.paddle1_pos = [50, self.HEIGHT//2 - self.paddle_height//2]
        self.paddle2_pos = [self.WIDTH - 70, self.HEIGHT//2 - self.paddle_height//2]
        self.ball_pos = [self.WIDTH//2, self.HEIGHT//2]
        self.ball_dir = [random.choice([-1, 1]) * self.ball_speed, random.uniform(-1, 1) * self.ball_speed]
        self.score1 = 0
        self.score2 = 0
        self.game_over = False
        self.winner = None
        self.particles.clear()
    
    def add_particles(self, pos, color, count=10):
        for _ in range(count):
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
    
    def draw_ui_overlay(self):
        # Draw top UI bar
        overlay = pygame.Surface((self.WIDTH, 80), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))
        
        # Draw scores with glow
        score_text = f"{self.score1} - {self.score2}"
        shadow_surf = self.font.render(score_text, True, (0, 0, 0))
        text_surf = self.font.render(score_text, True, self.WHITE)
        
        # Add glow effect
        glow_surf = pygame.Surface(text_surf.get_size(), pygame.SRCALPHA)
        glow_surf.blit(text_surf, (0, 0))
        for i in range(3):
            pygame.draw.rect(glow_surf, (*self.BLUE, 50-i*15), 
                           glow_surf.get_rect().inflate(i*2, i*2), 1)
        
        score_x = self.WIDTH//2
        self.screen.blit(shadow_surf, (score_x - text_surf.get_width()//2 + 2, 22))
        self.screen.blit(glow_surf, (score_x - text_surf.get_width()//2, 20))
        self.screen.blit(text_surf, (score_x - text_surf.get_width()//2, 20))
        
        # Draw game controls with icons
        controls = [
            ("⌨️ Arrows", "Move"),
            ("🤚 H", "Hand Control: " + ("ON" if self.hand_control else "OFF")),
            ("⏸️ P", "Pause"),
            ("🏠 ESC", "Menu")
        ]
        
        x = 20
        for icon_text, control_text in controls:
            icon_surf = self.small_font.render(icon_text, True, self.WHITE)
            control_surf = self.small_font.render(control_text, True, self.GRAY)
            
            self.screen.blit(icon_surf, (x, 25))
            self.screen.blit(control_surf, (x + icon_surf.get_width() + 5, 25))
            x += icon_surf.get_width() + control_surf.get_width() + 30
    
    def draw_pause_menu(self):
        # Draw semi-transparent overlay
        overlay = pygame.Surface((self.WIDTH, self.HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))
        
        # Draw pause menu title
        title_text = "Game Paused"
        title_surf = self.font.render(title_text, True, self.WHITE)
        title_rect = title_surf.get_rect(center=(self.WIDTH//2, self.HEIGHT//2 - 60))
        
        # Add glow effect to title
        for i in range(3):
            glow_surf = self.font.render(title_text, True, (*self.BLUE, 100-i*30))
            glow_rect = glow_surf.get_rect(center=(self.WIDTH//2, self.HEIGHT//2 - 60))
            self.screen.blit(glow_surf, glow_rect.inflate(i*4, i*4))
        
        self.screen.blit(title_surf, title_rect)
        
        # Draw menu options
        options = [
            ("▶️ Press SPACE to Resume", self.WHITE),
            ("🔄 Press R to Restart", self.WHITE),
            ("🏠 Press ESC for Menu", self.YELLOW)
        ]
        
        for i, (text, color) in enumerate(options):
            text_surf = self.small_font.render(text, True, color)
            text_rect = text_surf.get_rect(center=(self.WIDTH//2, self.HEIGHT//2 + i*40))
            self.screen.blit(text_surf, text_rect)
    
    def draw_game_over(self):
        # Draw semi-transparent overlay
        overlay = pygame.Surface((self.WIDTH, self.HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))
        
        # Draw winner announcement with animation
        winner_text = f"Player {self.winner} Wins!"
        title_surf = self.font.render(winner_text, True, self.GREEN)
        title_rect = title_surf.get_rect(center=(self.WIDTH//2, self.HEIGHT//2 - 60))
        
        # Add pulsing glow effect
        pulse = math.sin(pygame.time.get_ticks() * 0.005) * 0.5 + 0.5
        for i in range(3):
            glow_surf = self.font.render(winner_text, True, (*self.GREEN, int(100*pulse-i*30)))
            glow_rect = glow_surf.get_rect(center=(self.WIDTH//2, self.HEIGHT//2 - 60))
            self.screen.blit(glow_surf, glow_rect.inflate(i*4, i*4))
        
        self.screen.blit(title_surf, title_rect)
        
        # Draw final score
        score_text = f"Final Score: {self.score1} - {self.score2}"
        score_surf = self.small_font.render(score_text, True, self.WHITE)
        score_rect = score_surf.get_rect(center=(self.WIDTH//2, self.HEIGHT//2))
        self.screen.blit(score_surf, score_rect)
        
        # Draw options
        options = [
            ("🔄 Press SPACE to Play Again", self.WHITE),
            ("🏠 Press ESC for Menu", self.YELLOW)
        ]
        
        for i, (text, color) in enumerate(options):
            text_surf = self.small_font.render(text, True, color)
            text_rect = text_surf.get_rect(center=(self.WIDTH//2, self.HEIGHT//2 + 60 + i*40))
            self.screen.blit(text_surf, text_rect)
    
    def draw_tutorial(self):
        # Draw semi-transparent overlay
        overlay = pygame.Surface((self.WIDTH, self.HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))
        
        # Draw tutorial title
        title_text = "Welcome to AI Ping Pong!"
        title_surf = self.font.render(title_text, True, self.BLUE)
        title_rect = title_surf.get_rect(center=(self.WIDTH//2, self.HEIGHT//3))
        
        # Add glow to title
        for i in range(3):
            glow_surf = self.font.render(title_text, True, (*self.BLUE, 100-i*30))
            glow_rect = glow_surf.get_rect(center=(self.WIDTH//2, self.HEIGHT//3))
            self.screen.blit(glow_surf, glow_rect.inflate(i*4, i*4))
        
        self.screen.blit(title_surf, title_rect)
        
        # Draw instructions
        instructions = [
            "🎮 Use UP/DOWN arrows to move your paddle",
            "🤚 Press H to toggle hand control mode",
            "🎯 First to 5 points wins!",
            "",
            "▶️ Press SPACE to start"
        ]
        
        y = self.HEIGHT//2
        for text in instructions:
            text_surf = self.small_font.render(text, True, self.WHITE)
            text_rect = text_surf.get_rect(center=(self.WIDTH//2, y))
            self.screen.blit(text_surf, text_rect)
            y += 40
    
    def draw_game_state(self):
        # Draw game field
        self.screen.fill(self.BLACK)
        
        # Draw center line
        for y in range(0, self.HEIGHT, 40):
            pygame.draw.rect(self.screen, self.GRAY, 
                           (self.WIDTH//2 - 2, y, 4, 20))
        
        # Draw paddles with glow effect
        for paddle_pos in [self.paddle1_pos, self.paddle2_pos]:
            # Glow
            for i in range(3):
                glow_rect = pygame.Rect(paddle_pos[0]-i*2, paddle_pos[1]-i*2,
                                      self.paddle_width+i*4, self.paddle_height+i*4)
                pygame.draw.rect(self.screen, (*self.BLUE, 50-i*15), glow_rect, border_radius=5)
            
            # Main paddle
            paddle_rect = pygame.Rect(paddle_pos[0], paddle_pos[1],
                                    self.paddle_width, self.paddle_height)
            pygame.draw.rect(self.screen, self.WHITE, paddle_rect, border_radius=5)
        
        # Draw ball with glow
        for i in range(3):
            glow_size = self.ball_size + i*4
            pygame.draw.circle(self.screen, (*self.YELLOW, 50-i*15),
                             (int(self.ball_pos[0]), int(self.ball_pos[1])), glow_size)
        
        pygame.draw.circle(self.screen, self.WHITE,
                         (int(self.ball_pos[0]), int(self.ball_pos[1])), self.ball_size)
    
    def update_game_state(self):
        if not self.paused and not self.game_over and not self.show_tutorial:
            self.ball_pos[0] += self.ball_dir[0]
            self.ball_pos[1] += self.ball_dir[1]
            
            # Collision with top and bottom
            if self.ball_pos[1] < self.ball_size or self.ball_pos[1] > self.HEIGHT - self.ball_size:
                self.ball_dir[1] *= -1
            
            # Collision with paddles
            if (self.ball_pos[0] < self.paddle1_pos[0] + self.paddle_width and
                self.ball_pos[1] > self.paddle1_pos[1] and
                self.ball_pos[1] < self.paddle1_pos[1] + self.paddle_height):
                self.ball_dir[0] *= -1
            elif (self.ball_pos[0] > self.paddle2_pos[0] - self.ball_size and
                  self.ball_pos[1] > self.paddle2_pos[1] and
                  self.ball_pos[1] < self.paddle2_pos[1] + self.paddle_height):
                self.ball_dir[0] *= -1
            
            # Collision with left and right
            if self.ball_pos[0] < self.ball_size:
                self.score2 += 1
                self.reset_game()
            elif self.ball_pos[0] > self.WIDTH - self.ball_size:
                self.score1 += 1
                self.reset_game()
            
            # Update paddles
            keys = pygame.key.get_pressed()
            if keys[pygame.K_w]:
                self.paddle1_pos[1] -= self.paddle_speed
            if keys[pygame.K_s]:
                self.paddle1_pos[1] += self.paddle_speed
            if keys[pygame.K_UP]:
                self.paddle2_pos[1] -= self.paddle_speed
            if keys[pygame.K_DOWN]:
                self.paddle2_pos[1] += self.paddle_speed
            
            # Ensure paddles don't go off screen
            self.paddle1_pos[1] = max(0, min(self.HEIGHT - self.paddle_height, self.paddle1_pos[1]))
            self.paddle2_pos[1] = max(0, min(self.HEIGHT - self.paddle_height, self.paddle2_pos[1]))
    
    def process_hand_tracking(self):
        ret, frame = self.cap.read()
        if not ret:
            return
        
        frame = cv2.flip(frame, 1)
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.hands.process(rgb_frame)
        
        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                # Use index finger tip for paddle control
                x = hand_landmarks.landmark[8].x
                self.paddle1_pos[1] = int(x * self.HEIGHT) - self.paddle_height//2
                self.paddle1_pos[1] = max(0, min(self.HEIGHT - self.paddle_height, self.paddle1_pos[1]))
    
    def run(self):
        clock = pygame.time.Clock()
        running = True
        return_to_menu = True
        
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                    return_to_menu = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    elif event.key == pygame.K_SPACE:
                        if self.show_tutorial:
                            self.show_tutorial = False
                        elif self.game_over:
                            self.reset_game()
                        else:
                            self.paused = not self.paused
                    elif event.key == pygame.K_h:
                        self.hand_control = not self.hand_control
            
            # Process hand tracking
            if self.hand_control:
                self.process_hand_tracking()
            
            # Update game state
            self.update_game_state()
            
            # Draw everything
            self.draw_game_state()
            self.draw_ui_overlay()
            self.update_particles()
            
            if self.show_tutorial:
                self.draw_tutorial()
            elif self.game_over:
                self.draw_game_over()
            elif self.paused:
                self.draw_pause_menu()
            
            pygame.display.flip()
            clock.tick(60)
        
        self.cap.release()
        self.hands.close()
        pygame.quit()
        return return_to_menu

if __name__ == "__main__":
    game = BallGame()
    game.run()