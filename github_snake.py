import pygame
import sys
import datetime
import json
import requests
import numpy as np
from PIL import Image
import colorsys
import random

# GitHub API configuration
GITHUB_USERNAME = "OSOSerious"
GITHUB_API_URL = f"https://api.github.com/users/{GITHUB_USERNAME}/events/public"
GITHUB_CONTRIB_URL = f"https://api.github.com/users/{GITHUB_USERNAME}/events"

# Colors
BACKGROUND_COLOR = (13, 17, 23)  # GitHub dark theme
GRID_COLOR = (30, 37, 46)  # Softer grid lines
TEXT_COLOR = (201, 209, 217)  # Light text
FOOD_COLORS = [(46, 160, 67), (87, 171, 90), (140, 203, 110)]  # GitHub greens

class ContributionSnake:
    def __init__(self, width=800, height=400):
        pygame.init()
        self.width = width
        self.height = height
        self.screen = pygame.display.set_mode((width, height))
        pygame.display.set_caption("GitHub Contribution Snake")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont('Arial', 16)
        self.title_font = pygame.font.SysFont('Arial', 24, bold=True)
        
        # Snake properties
        self.grid_size = 20
        self.snake_pos = [(width//2, height//2)]
        self.direction = [self.grid_size, 0]
        self.snake_speed = 5
        self.snake_color = (46, 160, 67)
        
        # Contribution data
        self.contributions = self.get_contributions()
        self.food_positions = self.generate_food_positions()
        self.score = 0
        
        # Recording
        self.recording = False
        self.frames = []
        self.frame_count = 0
        
        # Effects
        self.particles = []
        self.eaten_positions = set()

    def get_contributions(self):
        """Fetch contribution data from GitHub API"""
        try:
            headers = {'Accept': 'application/vnd.github.v3+json'}
            response = requests.get(GITHUB_CONTRIB_URL, headers=headers)
            if response.status_code == 200:
                events = response.json()
                contributions = []
                for event in events:
                    if event['type'] == 'PushEvent':
                        count = len(event.get('payload', {}).get('commits', []))
                        date = datetime.datetime.strptime(event['created_at'], '%Y-%m-%dT%H:%M:%SZ')
                        contributions.append((count, date))
                return contributions
            return []
        except Exception as e:
            print(f"Error fetching contributions: {e}")
            return []

    def generate_food_positions(self):
        """Generate food positions based on contributions"""
        positions = []
        margin = self.grid_size * 2
        
        for _ in range(min(len(self.contributions), 50)):
            x = random.randint(margin, self.width - margin)
            y = random.randint(margin, self.height - margin)
            x = x - (x % self.grid_size)  # Snap to grid
            y = y - (y % self.grid_size)
            positions.append((x, y))
            
        return positions

    def add_particle(self, pos, color):
        """Add eating effect particle"""
        angle = random.random() * 2 * np.pi
        speed = random.random() * 3
        self.particles.append({
            'pos': list(pos),
            'velocity': [np.cos(angle) * speed, np.sin(angle) * speed],
            'ttl': 20,
            'color': color,
            'size': random.randint(2, 4)
        })

    def update_particles(self):
        """Update and draw particles"""
        self.particles = [p for p in self.particles if p['ttl'] > 0]
        
        for particle in self.particles:
            particle['ttl'] -= 1
            particle['pos'][0] += particle['velocity'][0]
            particle['pos'][1] += particle['velocity'][1]
            
            alpha = int(255 * (particle['ttl'] / 20))
            color = (*particle['color'], alpha)
            pos = (int(particle['pos'][0]), int(particle['pos'][1]))
            
            if 0 <= pos[0] < self.width and 0 <= pos[1] < self.height:
                pygame.draw.circle(self.screen, color, pos, particle['size'])

    def draw_grid(self):
        """Draw contribution grid"""
        for x in range(0, self.width, self.grid_size):
            pygame.draw.line(self.screen, GRID_COLOR, (x, 0), (x, self.height), 1)
        for y in range(0, self.height, self.grid_size):
            pygame.draw.line(self.screen, GRID_COLOR, (0, y), (self.width, y), 1)

    def draw_food(self):
        """Draw contribution food"""
        for pos in self.food_positions:
            if pos not in self.eaten_positions:
                color = random.choice(FOOD_COLORS)
                pygame.draw.circle(self.screen, color, pos, self.grid_size//2)

    def draw_snake(self):
        """Draw snake"""
        for i, pos in enumerate(self.snake_pos):
            color = (46, 160, 67) if i == 0 else (87, 171, 90)
            pygame.draw.circle(self.screen, color, (int(pos[0]), int(pos[1])), self.grid_size//2)

    def draw_stats(self):
        """Draw statistics panel"""
        panel_width = 200
        panel_height = 100
        panel_x = 10
        panel_y = 10
        
        # Background
        panel_surface = pygame.Surface((panel_width, panel_height))
        panel_surface.fill((30, 37, 46))
        panel_surface.set_alpha(200)
        self.screen.blit(panel_surface, (panel_x, panel_y))
        
        # Stats
        total_contributions = sum(count for count, _ in self.contributions)
        recent_contributions = sum(count for count, date in self.contributions 
                                 if (datetime.datetime.now() - date).days <= 7)
        
        stats = [
            f"Contributions: {total_contributions}",
            f"Last 7 Days: {recent_contributions}",
            f"Eaten: {self.score}",
            "R: Record | ESC: Exit"
        ]
        
        for i, text in enumerate(stats):
            text_surface = self.font.render(text, True, TEXT_COLOR)
            self.screen.blit(text_surface, (panel_x + 10, panel_y + 10 + i*20))

    def update_snake(self):
        """Update snake position and check collisions"""
        head_x, head_y = self.snake_pos[0]
        
        # Random direction changes
        if random.random() < 0.02:  # 2% chance to change direction
            directions = [(self.grid_size, 0), (-self.grid_size, 0), 
                         (0, self.grid_size), (0, -self.grid_size)]
            self.direction = random.choice(directions)
        
        # Move snake
        new_x = head_x + self.direction[0]
        new_y = head_y + self.direction[1]
        
        # Wrap around screen
        new_x = new_x % self.width
        new_y = new_y % self.height
        
        # Update position
        self.snake_pos.insert(0, (new_x, new_y))
        
        # Check for food collision
        head_rect = pygame.Rect(new_x - self.grid_size//2, new_y - self.grid_size//2, 
                              self.grid_size, self.grid_size)
        
        for food_pos in self.food_positions:
            if food_pos not in self.eaten_positions:
                food_rect = pygame.Rect(food_pos[0] - self.grid_size//2, food_pos[1] - self.grid_size//2,
                                      self.grid_size, self.grid_size)
                if head_rect.colliderect(food_rect):
                    self.eaten_positions.add(food_pos)
                    self.score += 1
                    for _ in range(10):
                        self.add_particle(food_pos, random.choice(FOOD_COLORS))
                    break
        
        # Remove tail if no food eaten
        if len(self.snake_pos) > max(5, self.score + 5):
            self.snake_pos.pop()

    def save_frame(self):
        """Save current frame for GIF"""
        if self.recording and len(self.frames) < 100:  # Limit to 100 frames
            data = pygame.surfarray.array3d(self.screen)
            self.frames.append(data)

    def save_gif(self):
        """Save recorded frames as GIF"""
        if self.frames:
            print("Saving GIF...")
            frames_pil = [Image.fromarray(frame.transpose(1, 0, 2)) for frame in self.frames]
            frames_pil[0].save(
                'contribution_snake.gif',
                save_all=True,
                append_images=frames_pil[1:],
                duration=50,
                loop=0
            )
            print("GIF saved as contribution_snake.gif")
            self.frames = []
            self.recording = False

    def run(self):
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    elif event.key == pygame.K_r:
                        self.recording = not self.recording
                        if not self.recording:
                            self.save_gif()

            self.screen.fill(BACKGROUND_COLOR)
            self.draw_grid()
            self.draw_food()
            self.update_snake()
            self.draw_snake()
            self.update_particles()
            self.draw_stats()
            self.save_frame()
            
            pygame.display.flip()
            self.clock.tick(30)
            self.frame_count += 1

            # Check if all food is eaten
            if len(self.eaten_positions) == len(self.food_positions):
                self.food_positions = self.generate_food_positions()
                self.eaten_positions.clear()

        pygame.quit()
        if self.recording:
            self.save_gif()
        sys.exit()

if __name__ == "__main__":
    game = ContributionSnake()
    game.run()
