import pygame
import numpy as np
import cv2
import mediapipe as mp
from utils.sound_manager import SoundManager
import math

class SnakeGame:
    def __init__(self):
        # Initialize Pygame
        pygame.init()
        self.WIDTH = 1024
        self.HEIGHT = 768
        self.GRID_SIZE = 32
        self.GRID_WIDTH = self.WIDTH // self.GRID_SIZE
        self.GRID_HEIGHT = self.HEIGHT // self.GRID_SIZE
        
        self.screen = pygame.display.set_mode((self.WIDTH, self.HEIGHT), pygame.RESIZABLE)
        pygame.display.set_caption("AI Snake Game")
        
        # Initialize MediaPipe
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=1,
            min_detection_confidence=0.7,
            min_tracking_confidence=0.7
        )
        self.cap = cv2.VideoCapture(0)
        self.hand_control = False  # Toggle for hand controls
        
        # Colors
        self.WHITE = (255, 255, 255)
        self.BLACK = (0, 0, 0)
        self.GREEN = (50, 255, 50)
        self.RED = (255, 50, 50)
        self.BLUE = (0, 150, 255)
        self.PURPLE = (147, 0, 211)
        self.GRAY = (50, 50, 50)
        self.ACCENT = (255, 165, 0)
        self.YELLOW = (255, 255, 0)
        
        # Initialize game objects
        self.snake = None
        self.direction = None
        self.food = None
        self.obstacles = None
        self.special_food = None
        self.special_food_timer = None
        self.score = None
        self.game_over = None
        self.show_tutorial = None
        self.paused = None
        self.ai_mode = None
        self.path = None
        
        # Fonts
        self.title_font = pygame.font.Font(None, 74)
        self.font = pygame.font.Font(None, 48)
        self.small_font = pygame.font.Font(None, 36)
        
        # Particles
        self.particles = []
        
        # Sound
        self.sound_manager = SoundManager()
        
        # Initialize game objects in correct order
        self.snake = [(self.GRID_WIDTH//2, self.GRID_HEIGHT//2)]
        self.direction = (1, 0)
        self.score = 0
        self.obstacles = []  # Initialize obstacles list first
        self.food = None
        self.special_food = None
        self.special_food_timer = 0
        self.game_over = False
        self.show_tutorial = True
        self.paused = False
        self.ai_mode = False
        self.path = []
        
        # Now spawn game objects
        self.food = self.spawn_food()  # Spawn food
        self.spawn_obstacles()  # Then spawn obstacles
        self.special_food = self.spawn_special_food()
        if self.special_food:
            self.special_food_timer = 60
    
    def spawn_food(self):
        while True:
            x = np.random.randint(0, self.GRID_WIDTH)
            y = np.random.randint(0, self.GRID_HEIGHT)
            pos = (x, y)
            if pos not in self.snake and pos not in self.obstacles:
                return pos
    
    def spawn_special_food(self):
        if np.random.random() < 0.2:  # 20% chance
            while True:
                x = np.random.randint(0, self.GRID_WIDTH)
                y = np.random.randint(0, self.GRID_HEIGHT)
                pos = (x, y)
                if pos not in self.snake and pos != self.food and pos not in self.obstacles:
                    return pos
        return None
    
    def spawn_obstacles(self):
        num_obstacles = 5
        for _ in range(num_obstacles):
            while True:
                x = np.random.randint(0, self.GRID_WIDTH)
                y = np.random.randint(0, self.GRID_HEIGHT)
                pos = (x, y)
                if pos not in self.snake and pos != self.food and pos not in self.obstacles:
                    self.obstacles.append(pos)
                    break
    
    def create_particles(self, x, y, color):
        grid_x = x * self.GRID_SIZE + self.GRID_SIZE//2
        grid_y = y * self.GRID_SIZE + self.GRID_SIZE//2
        for _ in range(10):
            particle = {
                "x": grid_x,
                "y": grid_y,
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
            self.screen.blit(surf, (particle["x"] - particle["size"]/2, particle["y"] - particle["size"]/2))
    
    def find_path_to_food(self):
        target = self.food if not self.special_food else self.special_food
        start = self.snake[0]
        queue = [(start, [start])]
        visited = set([start])
        
        while queue:
            current, path = queue.pop(0)
            if current == target:
                return path[1:] if len(path) > 1 else []
            
            for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                next_x = (current[0] + dx) % self.GRID_WIDTH
                next_y = (current[1] + dy) % self.GRID_HEIGHT
                next_pos = (next_x, next_y)
                
                if (next_pos not in visited and 
                    next_pos not in self.snake[:-1] and 
                    next_pos not in self.obstacles):
                    queue.append((next_pos, path + [next_pos]))
                    visited.add(next_pos)
        return []
    
    def update_game_state(self):
        if self.paused or self.game_over or self.show_tutorial:
            return
        
        # Update special food timer
        if self.special_food:
            self.special_food_timer -= 1
            if self.special_food_timer <= 0:
                self.special_food = None
        
        # AI mode path finding
        if self.ai_mode and not self.path:
            self.path = self.find_path_to_food()
        
        # Move snake
        if self.ai_mode and self.path:
            next_pos = self.path[0]
            self.direction = (
                (next_pos[0] - self.snake[0][0]) % self.GRID_WIDTH,
                (next_pos[1] - self.snake[0][1]) % self.GRID_HEIGHT
            )
            self.path = self.path[1:]
        
        head_x = (self.snake[0][0] + self.direction[0]) % self.GRID_WIDTH
        head_y = (self.snake[0][1] + self.direction[1]) % self.GRID_HEIGHT
        new_head = (head_x, head_y)
        
        # Check collisions
        if (new_head in self.snake[:-1] or 
            new_head in self.obstacles):
            self.game_over = True
            return
        
        self.snake.insert(0, new_head)
        
        # Check food collision
        if new_head == self.food:
            self.score += 1
            self.create_particles(self.food[0], self.food[1], self.GREEN)
            self.food = self.spawn_food()
            if not self.special_food:
                self.special_food = self.spawn_special_food()
                if self.special_food:
                    self.special_food_timer = 60
        elif new_head == self.special_food:
            self.score += 5
            self.create_particles(self.special_food[0], self.special_food[1], self.PURPLE)
            self.special_food = None
        else:
            self.snake.pop()
        
        self.update_particles()
    
    def draw_snake_segment(self, pos, is_head=False, is_tail=False, prev_pos=None, next_pos=None):
        x, y = pos
        cell_size = self.GRID_SIZE
        screen_x = x * cell_size
        screen_y = y * cell_size
        
        # Colors for gradient effect
        base_color = self.GREEN
        dark_color = (int(base_color[0] * 0.7), int(base_color[1] * 0.7), int(base_color[2] * 0.7))
        
        if is_head:
            # Draw head with eyes and tongue
            pygame.draw.rect(self.screen, base_color, (screen_x, screen_y, cell_size, cell_size), border_radius=8)
            
            # Add gradient effect
            pygame.draw.rect(self.screen, dark_color, (screen_x + 4, screen_y + 4, cell_size - 8, cell_size - 8), border_radius=6)
            
            # Draw eyes
            eye_color = self.WHITE
            pupil_color = self.BLACK
            eye_radius = cell_size // 6
            pupil_radius = eye_radius // 2
            
            # Position eyes based on direction
            if self.direction == (1, 0):  # Right
                eye_positions = [(screen_x + cell_size - 10, screen_y + 8), (screen_x + cell_size - 10, screen_y + cell_size - 12)]
            elif self.direction == (-1, 0):  # Left
                eye_positions = [(screen_x + 10, screen_y + 8), (screen_x + 10, screen_y + cell_size - 12)]
            elif self.direction == (0, -1):  # Up
                eye_positions = [(screen_x + 8, screen_y + 10), (screen_x + cell_size - 12, screen_y + 10)]
            else:  # Down
                eye_positions = [(screen_x + 8, screen_y + cell_size - 10), (screen_x + cell_size - 12, screen_y + cell_size - 10)]
            
            for eye_pos in eye_positions:
                pygame.draw.circle(self.screen, eye_color, eye_pos, eye_radius)
                pygame.draw.circle(self.screen, pupil_color, eye_pos, pupil_radius)
            
            # Draw tongue occasionally
            if pygame.time.get_ticks() % 2000 < 1000:  # Flick tongue every 2 seconds
                tongue_start = (screen_x + cell_size//2, screen_y + cell_size//2)
                if self.direction == (1, 0):  # Right
                    tongue_end = (tongue_start[0] + 12, tongue_start[1])
                    fork1 = (tongue_end[0] + 4, tongue_end[1] - 4)
                    fork2 = (tongue_end[0] + 4, tongue_end[1] + 4)
                elif self.direction == (-1, 0):  # Left
                    tongue_end = (tongue_start[0] - 12, tongue_start[1])
                    fork1 = (tongue_end[0] - 4, tongue_end[1] - 4)
                    fork2 = (tongue_end[0] - 4, tongue_end[1] + 4)
                elif self.direction == (0, -1):  # Up
                    tongue_end = (tongue_start[0], tongue_start[1] - 12)
                    fork1 = (tongue_end[0] - 4, tongue_end[1] - 4)
                    fork2 = (tongue_end[0] + 4, tongue_end[1] - 4)
                else:  # Down
                    tongue_end = (tongue_start[0], tongue_start[1] + 12)
                    fork1 = (tongue_end[0] - 4, tongue_end[1] + 4)
                    fork2 = (tongue_end[0] + 4, tongue_end[1] + 4)
                
                pygame.draw.line(self.screen, self.RED, tongue_start, tongue_end, 2)
                pygame.draw.line(self.screen, self.RED, tongue_end, fork1, 2)
                pygame.draw.line(self.screen, self.RED, tongue_end, fork2, 2)
        
        else:
            # Draw body segments with gradient and connection
            segment_rect = pygame.Rect(screen_x + 2, screen_y + 2, cell_size - 4, cell_size - 4)
            
            # Determine segment orientation
            if prev_pos and next_pos:
                if prev_pos[0] == next_pos[0]:  # Vertical
                    segment_rect.height += 4
                    segment_rect.y -= 2
                elif prev_pos[1] == next_pos[1]:  # Horizontal
                    segment_rect.width += 4
                    segment_rect.x -= 2
            
            # Draw segment with rounded corners
            pygame.draw.rect(self.screen, base_color, segment_rect, border_radius=6)
            
            # Add gradient effect
            inner_rect = segment_rect.inflate(-6, -6)
            pygame.draw.rect(self.screen, dark_color, inner_rect, border_radius=4)
            
            # Add scales effect (small circles) on body segments
            if not is_tail:
                for i in range(2):
                    for j in range(2):
                        scale_x = screen_x + cell_size//3 * (i + 1) - cell_size//6
                        scale_y = screen_y + cell_size//3 * (j + 1) - cell_size//6
                        pygame.draw.circle(self.screen, dark_color, (scale_x, scale_y), 2)

    def draw_game_state(self):
        # Draw grid (optional, comment out for cleaner look)
        # for x in range(0, self.WIDTH, self.GRID_SIZE):
        #     pygame.draw.line(self.screen, self.GRAY, (x, 0), (x, self.HEIGHT))
        # for y in range(0, self.HEIGHT, self.GRID_SIZE):
        #     pygame.draw.line(self.screen, self.GRAY, (0, y), (self.WIDTH, y))
        
        # Draw snake
        for i, pos in enumerate(self.snake):
            is_head = (i == 0)
            is_tail = (i == len(self.snake) - 1)
            prev_pos = self.snake[i-1] if i > 0 else None
            next_pos = self.snake[i+1] if i < len(self.snake)-1 else None
            self.draw_snake_segment(pos, is_head, is_tail, prev_pos, next_pos)
        
        # Draw food with glow effect
        if self.food:
            x, y = self.food
            screen_x = x * self.GRID_SIZE
            screen_y = y * self.GRID_SIZE
            
            # Draw glow
            glow_radius = self.GRID_SIZE
            glow_surface = pygame.Surface((glow_radius * 2, glow_radius * 2), pygame.SRCALPHA)
            for radius in range(glow_radius, 0, -2):
                alpha = int((radius / glow_radius) * 100)
                pygame.draw.circle(glow_surface, (*self.RED[:3], alpha), (glow_radius, glow_radius), radius)
            self.screen.blit(glow_surface, (screen_x - glow_radius + self.GRID_SIZE//2, 
                                          screen_y - glow_radius + self.GRID_SIZE//2))
            
            # Draw main food
            pygame.draw.circle(self.screen, self.RED, 
                             (screen_x + self.GRID_SIZE//2, screen_y + self.GRID_SIZE//2), 
                             self.GRID_SIZE//3)
        
        # Draw special food with sparkle effect
        if self.special_food:
            x, y = self.special_food
            screen_x = x * self.GRID_SIZE + self.GRID_SIZE//2
            screen_y = y * self.GRID_SIZE + self.GRID_SIZE//2
            
            # Draw shimmering effect
            time = pygame.time.get_ticks()
            for i in range(8):
                angle = (time / 500.0 + i * math.pi / 4) % (2 * math.pi)
                radius = 6 + math.sin(time / 200.0) * 2
                sparkle_x = screen_x + math.cos(angle) * radius
                sparkle_y = screen_y + math.sin(angle) * radius
                pygame.draw.circle(self.screen, self.PURPLE, (int(sparkle_x), int(sparkle_y)), 2)
            
            # Draw main special food
            pygame.draw.circle(self.screen, self.PURPLE, (screen_x, screen_y), self.GRID_SIZE//4)
        
        # Draw obstacles
        for obstacle in self.obstacles:
            x, y = obstacle
            screen_x = x * self.GRID_SIZE
            screen_y = y * self.GRID_SIZE
            
            # Draw rock-like obstacle
            points = [
                (screen_x + 4, screen_y + self.GRID_SIZE//2),
                (screen_x + self.GRID_SIZE//2, screen_y + 4),
                (screen_x + self.GRID_SIZE - 4, screen_y + self.GRID_SIZE//2),
                (screen_x + self.GRID_SIZE//2, screen_y + self.GRID_SIZE - 4)
            ]
            pygame.draw.polygon(self.screen, self.GRAY, points)
            
            # Add some detail lines
            for i in range(3):
                start_pos = (screen_x + 8 + i * 8, screen_y + 8 + i * 4)
                end_pos = (start_pos[0] + 8, start_pos[1] + 4)
                pygame.draw.line(self.screen, self.BLACK, start_pos, end_pos, 2)
    
    def draw_ui_overlay(self):
        # Draw semi-transparent overlay for UI elements
        overlay = pygame.Surface((self.WIDTH, 80), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))
        
        # Draw score with shadow and glow
        score_text = f"Score: {self.score}"
        shadow_surf = self.font.render(score_text, True, (0, 0, 0))
        text_surf = self.font.render(score_text, True, self.WHITE)
        
        # Add glow effect
        glow_surf = pygame.Surface(text_surf.get_size(), pygame.SRCALPHA)
        glow_surf.blit(text_surf, (0, 0))
        for i in range(3):
            pygame.draw.rect(glow_surf, (*self.GREEN, 50-i*15), 
                           glow_surf.get_rect().inflate(i*2, i*2), 1)
        
        self.screen.blit(shadow_surf, (22, 22))
        self.screen.blit(glow_surf, (20, 20))
        self.screen.blit(text_surf, (20, 20))
        
        # Draw game controls with icons
        controls = [
            ("⌨️ Arrows", "Move"),
            ("🤚 H", "Hand Control: " + ("ON" if self.hand_control else "OFF")),
            ("🤖 A", "AI Mode: " + ("ON" if self.ai_mode else "OFF")),
            ("⏸️ P", "Pause"),
            ("🏠 ESC", "Menu")
        ]
        
        x = 200
        for icon_text, control_text in controls:
            # Draw icon
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
            glow_surf = self.font.render(title_text, True, (*self.GREEN, 100-i*30))
            glow_rect = glow_surf.get_rect(center=(self.WIDTH//2, self.HEIGHT//2 - 60))
            self.screen.blit(glow_surf, glow_rect.inflate(i*4, i*4))
        
        self.screen.blit(title_surf, title_rect)
        
        # Draw menu options
        options = [
            ("▶️ Press SPACE to Resume", self.WHITE),
            ("🔄 Press R to Restart", self.WHITE),
            ("🏠 Press ESC for Menu", self.ACCENT)
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
        
        # Draw game over title with glow effect
        title_text = "Game Over!"
        title_surf = self.font.render(title_text, True, self.RED)
        title_rect = title_surf.get_rect(center=(self.WIDTH//2, self.HEIGHT//2 - 60))
        
        # Add pulsing glow effect
        pulse = math.sin(pygame.time.get_ticks() * 0.005) * 0.5 + 0.5
        for i in range(3):
            # Create a surface with per-pixel alpha for the glow
            glow_surf = pygame.Surface(title_surf.get_size(), pygame.SRCALPHA)
            # Render the text in red
            temp_surf = self.font.render(title_text, True, self.RED)
            glow_surf.blit(temp_surf, (0, 0))
            # Scale the surface for the glow effect
            size_mult = 1 + (i * 0.1)
            scaled_size = (int(glow_surf.get_width() * size_mult), 
                         int(glow_surf.get_height() * size_mult))
            glow_surf = pygame.transform.smoothscale(glow_surf, scaled_size)
            # Apply the pulse alpha
            glow_surf.set_alpha(int(100 * pulse) - i * 30)
            # Center the glow
            glow_rect = glow_surf.get_rect(center=title_rect.center)
            self.screen.blit(glow_surf, glow_rect)
        
        # Draw the main text
        self.screen.blit(title_surf, title_rect)
        
        # Draw score
        score_text = f"Score: {self.score}"
        score_surf = self.small_font.render(score_text, True, self.WHITE)
        score_rect = score_surf.get_rect(center=(self.WIDTH//2, self.HEIGHT//2))
        self.screen.blit(score_surf, score_rect)
        
        # Draw options
        options = [
            ("🔄 Press SPACE to Restart", self.WHITE),
            ("🏠 Press ESC for Menu", self.YELLOW)
        ]
        
        for i, (text, color) in enumerate(options):
            text_surf = self.small_font.render(text, True, color)
            text_rect = text_surf.get_rect(center=(self.WIDTH//2, self.HEIGHT//2 + 60 + i*40))
            self.screen.blit(text_surf, text_rect)
    
    def draw_tutorial(self):
        overlay = pygame.Surface((self.WIDTH, self.HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 128))
        self.screen.blit(overlay, (0, 0))
        
        title = self.title_font.render("AI Snake Game", True, self.WHITE)
        tutorial_text = [
            "Use Arrow Keys to control the snake",
            "Press 'A' to toggle AI mode",
            "Collect red food to grow",
            "Purple food gives bonus points!",
            "Avoid obstacles and yourself",
            "",
            "Press SPACE to start",
            "ESC to quit anytime"
        ]
        
        y = self.HEIGHT//2 - len(tutorial_text)*20
        self.screen.blit(title, (self.WIDTH//2 - title.get_width()//2, y - 100))
        
        for line in tutorial_text:
            text = self.small_font.render(line, True, self.WHITE)
            self.screen.blit(text, (self.WIDTH//2 - text.get_width()//2, y))
            y += 40
    
    def get_hand_direction(self):
        success, image = self.cap.read()
        if not success:
            return None
        
        # Flip the image horizontally for a later selfie-view display
        image = cv2.flip(image, 1)
        
        # Convert the BGR image to RGB
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        # Process the image and detect hands
        results = self.hands.process(image)
        
        if results.multi_hand_landmarks:
            hand_landmarks = results.multi_hand_landmarks[0]  # Get the first hand
            
            # Get index finger tip and palm base positions
            index_tip = hand_landmarks.landmark[self.mp_hands.HandLandmark.INDEX_FINGER_TIP]
            palm_base = hand_landmarks.landmark[self.mp_hands.HandLandmark.WRIST]
            
            # Calculate direction vector
            dx = index_tip.x - palm_base.x
            dy = index_tip.y - palm_base.y
            
            # Set thresholds for movement detection
            threshold = 0.15  # Increased threshold for more deliberate movements
            
            # Determine predominant direction with priority to horizontal movement
            if abs(dx) > threshold:
                if dx > 0:
                    return (1, 0)  # Right
                else:
                    return (-1, 0)  # Left
            elif abs(dy) > threshold:
                if dy > 0:
                    return (0, 1)  # Down
                else:
                    return (0, -1)  # Up
            
        return None
    
    def reset_game(self):
        # Reset game objects in correct order
        self.snake = [(self.GRID_WIDTH//2, self.GRID_HEIGHT//2)]
        self.direction = (1, 0)
        self.score = 0
        self.obstacles = []  # Initialize obstacles list first
        self.food = None
        self.special_food = None
        self.special_food_timer = 0
        self.game_over = False
        self.show_tutorial = True
        self.paused = False
        self.ai_mode = False
        self.path = []
        
        # Now spawn game objects
        self.food = self.spawn_food()  # Spawn food
        self.spawn_obstacles()  # Then spawn obstacles
        self.special_food = self.spawn_special_food()
        if self.special_food:
            self.special_food_timer = 60
    
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
                    elif event.key == pygame.K_F11:
                        pygame.display.toggle_fullscreen()
                    elif event.key == pygame.K_p:
                        self.paused = not self.paused
                    elif event.key == pygame.K_h:
                        self.hand_control = not self.hand_control
                    elif event.key == pygame.K_a and not self.game_over:
                        self.ai_mode = not self.ai_mode
                        self.path = []
                    elif event.key == pygame.K_SPACE:
                        if self.game_over:
                            self.reset_game()
                        elif self.show_tutorial:
                            self.show_tutorial = False
                        elif self.paused:
                            self.paused = False
                    elif not self.game_over and not self.paused and not self.show_tutorial and not self.hand_control:
                        if event.key == pygame.K_UP and self.direction != (0, 1):
                            self.direction = (0, -1)
                        elif event.key == pygame.K_DOWN and self.direction != (0, -1):
                            self.direction = (0, 1)
                        elif event.key == pygame.K_LEFT and self.direction != (1, 0):
                            self.direction = (-1, 0)
                        elif event.key == pygame.K_RIGHT and self.direction != (-1, 0):
                            self.direction = (1, 0)
            
            # Handle hand controls
            if self.hand_control and not self.game_over and not self.paused and not self.show_tutorial:
                hand_dir = self.get_hand_direction()
                if hand_dir:
                    if hand_dir[0] != -self.direction[0] or hand_dir[1] != -self.direction[1]:
                        self.direction = hand_dir
            
            # Update game state
            self.update_game_state()
            
            # Draw everything
            self.screen.fill(self.BLACK)
            self.draw_game_state()
            self.draw_particles()
            self.draw_ui_overlay()
            
            if self.show_tutorial:
                self.draw_tutorial()
            elif self.game_over:
                self.draw_game_over()
            elif self.paused:
                self.draw_pause_menu()
            
            pygame.display.flip()
            clock.tick(10)  # Snake speed
        
        # Clean up
        self.cap.release()
        self.hands.close()
        pygame.quit()
        return return_to_menu

if __name__ == "__main__":
    game = SnakeGame()
    game.run()
