import pygame
import cv2
import mediapipe as mp
import numpy as np
from utils.sound_manager import SoundManager
import math
import random

class RockPaperScissors:
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
        self.RED = (255, 50, 50)
        self.GREEN = (50, 255, 50)
        self.BLUE = (50, 50, 255)
        self.PURPLE = (147, 0, 211)
        self.GRAY = (128, 128, 128)
        self.YELLOW = (255, 255, 0)
        
        # Game state
        self.running = True
        self.paused = False
        self.player_score = 0
        self.ai_score = 0
        self.player_choice = None
        self.ai_choice = None
        self.round_result = None
        self.frame = None
        self.particles = []
        self.move_history = []
        self.pattern_weights = {"rock": 0.33, "paper": 0.33, "scissors": 0.33}
        
        # Initialize MediaPipe
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=1,
            min_detection_confidence=0.7,
            min_tracking_confidence=0.7
        )
        
        # Initialize camera
        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            print("Error: Could not open camera")
            self.running = False
        
        # Load sound manager
        self.sound_manager = SoundManager()
    
    def init_display(self):
        """Initialize or reinitialize the display"""
        self.screen = pygame.display.set_mode((self.WIDTH, self.HEIGHT))
        pygame.display.set_caption("Rock Paper Scissors")
    
    def cleanup(self):
        """Clean up resources"""
        if self.cap is not None:
            self.cap.release()
        if self.hands is not None:
            self.hands.close()
        cv2.destroyAllWindows()
    
    def create_particles(self, x, y, color):
        for _ in range(10):
            particle = {
                "x": x,
                "y": y,
                "dx": np.random.uniform(-5, 5),
                "dy": np.random.uniform(-5, 5),
                "lifetime": 30,
                "color": color,
                "size": np.random.uniform(2, 6)
            }
            self.particles.append(particle)

    def update_particles(self):
        for particle in self.particles[:]:
            particle["x"] += particle["dx"]
            particle["y"] += particle["dy"]
            particle["lifetime"] -= 1
            if particle["lifetime"] <= 0:
                self.particles.remove(particle)

    def draw_particles(self):
        for particle in self.particles:
            alpha = min(255, particle["lifetime"] * 8)
            color = (*particle["color"][:3], alpha)
            surf = pygame.Surface((particle["size"], particle["size"]), pygame.SRCALPHA)
            pygame.draw.circle(surf, color, (particle["size"]/2, particle["size"]/2), particle["size"]/2)
            self.screen.blit(surf, (particle["x"], particle["y"]))

    def draw_tutorial(self):
        # Draw semi-transparent overlay
        overlay = pygame.Surface((self.WIDTH, self.HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))
        
        # Draw tutorial title
        title_text = "Rock Paper Scissors with AI!"
        title_surf = self.font.render(title_text, True, self.PURPLE)
        title_rect = title_surf.get_rect(center=(self.WIDTH//2, self.HEIGHT//3))
        
        # Add glow to title
        for i in range(3):
            glow_surf = self.font.render(title_text, True, (*self.PURPLE, 100-i*30))
            glow_rect = glow_surf.get_rect(center=(self.WIDTH//2, self.HEIGHT//3))
            self.screen.blit(glow_surf, glow_rect.inflate(i*4, i*4))
        
        self.screen.blit(title_surf, title_rect)
        
        # Draw instructions
        instructions = [
            "✊ Show Rock: Make a fist",
            "✋ Show Paper: Open palm",
            "✌️ Show Scissors: Peace sign",
            "",
            "🤖 The AI learns from your moves!",
            "",
            "▶️ Show your hand to start"
        ]
        
        y = self.HEIGHT//2
        for text in instructions:
            text_surf = self.small_font.render(text, True, self.WHITE)
            text_rect = text_surf.get_rect(center=(self.WIDTH//2, y))
            self.screen.blit(text_surf, text_rect)
            y += 40

    def draw_ui_overlay(self):
        # Draw top UI bar
        overlay = pygame.Surface((self.WIDTH, 80), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))
        
        # Draw scores with glow
        score_text = f"You: {self.player_score}  AI: {self.ai_score}"
        shadow_surf = self.font.render(score_text, True, (0, 0, 0))
        text_surf = self.font.render(score_text, True, self.WHITE)
        
        # Add glow effect
        glow_surf = pygame.Surface(text_surf.get_size(), pygame.SRCALPHA)
        glow_surf.blit(text_surf, (0, 0))
        for i in range(3):
            pygame.draw.rect(glow_surf, (*self.PURPLE, 50-i*15), 
                           glow_surf.get_rect().inflate(i*2, i*2), 1)
        
        self.screen.blit(shadow_surf, (22, 22))
        self.screen.blit(glow_surf, (20, 20))
        self.screen.blit(text_surf, (20, 20))
        
        # Draw game controls with icons
        controls = [
            ("🤚 Show your hand", "to play"),
            ("🔄 R", "Reset Score"),
            ("⏸️ P", "Pause"),
            ("🏠 ESC", "Menu")
        ]
        
        x = 300
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
            glow_surf = self.font.render(title_text, True, (*self.PURPLE, 100-i*30))
            glow_rect = glow_surf.get_rect(center=(self.WIDTH//2, self.HEIGHT//2 - 60))
            self.screen.blit(glow_surf, glow_rect.inflate(i*4, i*4))
        
        self.screen.blit(title_surf, title_rect)
        
        # Draw menu options
        options = [
            ("▶️ Press SPACE to Resume", self.WHITE),
            ("🔄 Press R to Reset Score", self.WHITE),
            ("🏠 Press ESC for Menu", self.YELLOW)
        ]
        
        for i, (text, color) in enumerate(options):
            text_surf = self.small_font.render(text, True, color)
            text_rect = text_surf.get_rect(center=(self.WIDTH//2, self.HEIGHT//2 + i*40))
            self.screen.blit(text_surf, text_rect)

    def draw_game_state(self):
        self.screen.fill(self.BLACK)
        
        # Draw player and AI choices
        player_text = f"Your Choice: {self.player_choice if self.player_choice else '?'}"
        ai_text = f"AI Choice: {self.ai_choice if self.ai_choice else '?'}"
        
        # Draw player choice
        player_surf = self.font.render(player_text, True, self.WHITE)
        player_rect = player_surf.get_rect(center=(self.WIDTH//4, self.HEIGHT//2))
        self.screen.blit(player_surf, player_rect)
        
        # Draw VS text with glow
        vs_text = "VS"
        vs_surf = self.title_font.render(vs_text, True, self.PURPLE)
        vs_rect = vs_surf.get_rect(center=(self.WIDTH//2, self.HEIGHT//2))
        
        # Add pulsing glow to VS
        pulse = math.sin(pygame.time.get_ticks() * 0.003) * 0.5 + 0.5
        for i in range(3):
            glow_surf = self.title_font.render(vs_text, True, (*self.PURPLE, int(100*pulse-i*30)))
            glow_rect = glow_surf.get_rect(center=(self.WIDTH//2, self.HEIGHT//2))
            self.screen.blit(glow_surf, glow_rect.inflate(i*4, i*4))
        
        self.screen.blit(vs_surf, vs_rect)
        
        # Draw AI choice
        ai_surf = self.font.render(ai_text, True, self.WHITE)
        ai_rect = ai_surf.get_rect(center=(3*self.WIDTH//4, self.HEIGHT//2))
        self.screen.blit(ai_surf, ai_rect)
        
        # Draw hand gesture preview if available
        if self.frame is not None:
            # Convert frame to pygame surface
            frame = cv2.cvtColor(self.frame, cv2.COLOR_BGR2RGB)
            frame = np.rot90(frame)
            frame = pygame.surfarray.make_surface(frame)
            # Scale and position the preview
            preview_size = (320, 240)
            frame = pygame.transform.scale(frame, preview_size)
            self.screen.blit(frame, (self.WIDTH//2 - preview_size[0]//2, 
                                   self.HEIGHT - preview_size[1] - 20))

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

    def detect_gesture(self, hand_landmarks):
        # Implement gesture detection logic here
        # This is a simplified version - you should implement proper gesture recognition
        thumb_tip = hand_landmarks.landmark[4]
        index_tip = hand_landmarks.landmark[8]
        middle_tip = hand_landmarks.landmark[12]
        
        if abs(thumb_tip.y - index_tip.y) < 0.1:
            return "paper"
        elif thumb_tip.y < index_tip.y:
            return "rock"
        else:
            return "scissors"

    def get_ai_choice(self):
        if len(self.move_history) < 3:
            return np.random.choice(["rock", "paper", "scissors"])
        
        # Analyze patterns in move history
        last_moves = self.move_history[-3:]
        pattern = "".join(last_moves)
        
        # Predict next move based on pattern weights
        predicted_move = max(self.pattern_weights, key=self.pattern_weights.get)
        
        # Choose counter move
        counter_moves = {
            "rock": "paper",
            "paper": "scissors",
            "scissors": "rock"
        }
        return counter_moves[predicted_move]

    def update_ai(self, player_move):
        if len(self.move_history) >= 3:
            pattern = "".join(self.move_history[-3:])
            self.pattern_weights[player_move] += 1
        self.move_history.append(player_move)

    def determine_winner(self, player_choice, ai_choice):
        if player_choice == ai_choice:
            return "Tie!"
        
        winning_moves = {
            "rock": "scissors",
            "paper": "rock",
            "scissors": "paper"
        }
        
        if winning_moves[player_choice] == ai_choice:
            self.player_score += 1
            return "You Win!"
        else:
            self.ai_score += 1
            return "AI Wins!"

    def process_frame(self):
        rgb_frame = cv2.cvtColor(self.frame, cv2.COLOR_BGR2RGB)
        results = self.hands.process(rgb_frame)
        
        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                return self.detect_gesture(hand_landmarks)
        return None

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                return False
                
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    # Return to main menu
                    self.running = False
                    return True  # Signal to return to menu, not quit game
                    
                elif event.key == pygame.K_r:
                    # Reset scores
                    self.player_score = 0
                    self.ai_score = 0
                    self.sound_manager.play_sound("menu_select")
                    
                elif event.key == pygame.K_p:
                    self.paused = not self.paused
                    self.sound_manager.play_sound("menu_select")
                    
                elif event.key == pygame.K_SPACE and self.paused:
                    self.paused = False
                    self.sound_manager.play_sound("menu_select")

    def run(self):
        clock = pygame.time.Clock()
        tutorial_shown = True  # Set to False to show tutorial
        
        while self.running:
            if not tutorial_shown:
                self.draw_tutorial()
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        self.running = False
                        self.cleanup()
                        return False
                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_SPACE:
                            tutorial_shown = True
                        elif event.key == pygame.K_ESCAPE:
                            self.running = False
                            self.cleanup()
                            return True
            else:
                # Handle events first
                return_to_menu = self.handle_events()
                if return_to_menu is not None:  # None means continue game
                    self.cleanup()
                    return return_to_menu
                
                if not self.paused:
                    # Process camera input
                    ret, frame = self.cap.read()
                    if ret:
                        self.frame = cv2.flip(frame, 1)  # Mirror the frame
                        # Process hand landmarks
                        self.process_frame()
                
                # Draw game state
                try:
                    self.draw_game_state()
                    if self.paused:
                        self.draw_pause_menu()
                    self.update_particles()
                    pygame.display.flip()
                except pygame.error:
                    # Handle display surface errors
                    self.init_display()
            
            clock.tick(60)
        
        self.cleanup()
        return False

if __name__ == "__main__":
    game = RockPaperScissors()
    game.run()