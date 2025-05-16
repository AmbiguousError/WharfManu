import pygame
import math
import sys
import random

# --- Constants ---
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 1200 # Changed from 600 to 900
FPS = 60

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BLUE = (0, 0, 255)
STEEL_BLUE = (70, 130, 180) # Lighter water color
SKY_BLUE = (135, 206, 235)
BROWN = (139, 69, 19)
DARK_BROWN = (101, 67, 33)
RED = (255, 0, 0) # Torso color
DARK_RED = (200, 0, 0) # Legs color
GREEN = (0, 255, 0)
YELLOW = (255, 255, 0)
GRAY = (150, 150, 150)
SPLASH_COLOR = (240, 248, 255) # AliceBlue for splash
GOLD = (255, 215, 0)
BANNER_BG = (60, 60, 60)
BANNER_TEXT_COLOR = WHITE


# Physics
GRAVITY = 0.3
ROTATION_SPEED_INPUT = 5
ANGULAR_DAMPING = 0.98
GRAVITY_TORQUE_EFFECT = 0.05
MIN_JUMP_VELOCITY = -4
GOOD_JUMP_VELOCITY = -8
MAX_JUMP_VELOCITY = -14 # Max jump height
FORWARD_PUSH = 2
PIKE_SPEED = 3
MAX_PIKE_ANGLE = 135
MIN_PIKE_ANGLE = 0

# Game Objects Properties
WHARF_TOP_Y = 300
WHARF_WIDTH = 120
WHARF_THICKNESS = 20
WHARF_POST_WIDTH = 15
WHARF_POST_SPACING = 40

WATER_LEVEL = SCREEN_HEIGHT - 100 # Adjusted from SCREEN_HEIGHT - 250

DIVER_WIDTH = 15
DIVER_HEIGHT = 50
TORSO_HEIGHT = DIVER_HEIGHT // 2
LEGS_HEIGHT = DIVER_HEIGHT - TORSO_HEIGHT
DIVER_START_X = WHARF_WIDTH - DIVER_WIDTH
DIVER_START_Y = WHARF_TOP_Y - WHARF_THICKNESS // 2 - DIVER_HEIGHT // 2

# Timing Bar Properties
TIMING_BAR_WIDTH = 200
TIMING_BAR_HEIGHT = 20
TIMING_BAR_X = (SCREEN_WIDTH - TIMING_BAR_WIDTH) // 2
TIMING_BAR_Y = SCREEN_HEIGHT - 50
TIMING_BAR_SPEED = 3
TIMING_TARGET_ZONE_WIDTH = 40
TIMING_PERFECT_ZONE_WIDTH = 10

# Scoring
NUM_JUDGES = 5
# ENTRY_WIDTH_PENALTY_FACTOR = 2.0 # This factor is no longer used in the new scoring.
MAX_HIGH_SCORES = 3

# Splash Animation
MAX_SPLASH_PARTICLES_BASE = 50
PARTICLE_LIFETIME = 30
PARTICLE_GRAVITY = 0.2
PARTICLE_MAX_SPEED = 4

# Game States
ON_PLATFORM = 0
PRE_JUMP = 1
DIVING = 2
IN_WATER = 3 # This state is brief, used for calculations before GAME_OVER
GAME_OVER = 4
COMPETITION_OVER = 5

# Delays
RESTART_DELAY = 1500 # Milliseconds (1.5 seconds) on final screen
# *** NEW: Delay for showing final dive score ***
SCORE_DISPLAY_DELAY = 2000 # Milliseconds (2 seconds)

# --- Game Setup ---
pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("WHARF MANU!")
clock = pygame.time.Clock()
# Fonts
font = pygame.font.Font(None, 36)
small_font = pygame.font.Font(None, 24)
score_font = pygame.font.Font(None, 30)
title_font = pygame.font.Font(None, 48)
banner_font = pygame.font.Font(None, 60)


# --- Game Variables ---
game_state = ON_PLATFORM
diver_x = DIVER_START_X; diver_y = DIVER_START_Y
diver_vx = 0; diver_vy = 0
diver_angle = 0; diver_angular_velocity = 0
pike_angle = 0
total_rotation = 0; somersaults = 0
entry_angle = 0; entry_width = 0
timing_bar_value = 0; timing_bar_direction = 1
current_attempt = 1
attempt_scores = []; judge_scores_display = []; total_score = 0
splash_particles = []
high_scores = []
# Timers for delays
competition_over_entry_time = 0
game_over_entry_time = 0 # *** NEW: Timer for score display delay ***

# --- Helper Functions ---

def draw_text(text, font_to_use, color, surface, x, y, center=False):
    textobj = font_to_use.render(text, True, color)
    textrect = textobj.get_rect();
    if center: textrect.center = (x, y)
    else: textrect.topleft = (x, y)
    surface.blit(textobj, textrect)

def reset_dive():
    global game_state, diver_x, diver_y, diver_vx, diver_vy, diver_angle, pike_angle
    global total_rotation, somersaults, entry_angle, entry_width, timing_bar_value
    global timing_bar_direction, diver_angular_velocity, judge_scores_display, splash_particles
    # Reset dive variables, keep attempt number and scores
    game_state = ON_PLATFORM; diver_x = DIVER_START_X; diver_y = DIVER_START_Y
    diver_vx = 0; diver_vy = 0; diver_angle = 0; diver_angular_velocity = 0; pike_angle = 0
    total_rotation = 0; somersaults = 0; entry_angle = 0; entry_width = 0
    judge_scores_display = []; timing_bar_value = 0; timing_bar_direction = 1
    splash_particles = []

def start_new_competition():
    global current_attempt, attempt_scores, total_score
    current_attempt = 1; attempt_scores = []; total_score = 0
    reset_dive()

def create_splash(x, y, intensity_factor):
    intensity_factor = max(0, min(1, intensity_factor))
    num_particles = int(MAX_SPLASH_PARTICLES_BASE * intensity_factor)
    for _ in range(num_particles):
        angle = random.uniform(math.pi * 1.1, math.pi * 1.9);
        speed = random.uniform(1, PARTICLE_MAX_SPEED * (intensity_factor * 0.8 + 0.2))
        vx = math.cos(angle) * speed; vy = math.sin(angle) * speed
        lifetime = PARTICLE_LIFETIME + random.randint(-5, 5)
        splash_particles.append([x + random.uniform(-5, 5), y, vx, vy, lifetime])

# --- Game Loop ---
running = True
start_new_competition()

while running:
    dt = clock.tick(FPS) / 1000.0
    current_time = pygame.time.get_ticks() # Get current time for delay checks

    # Event Handling
    keys = pygame.key.get_pressed()
    for event in pygame.event.get():
        if event.type == pygame.QUIT: running = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                if game_state == ON_PLATFORM: game_state = PRE_JUMP; timing_bar_value = 0; timing_bar_direction = 1
                elif game_state == PRE_JUMP:
                    target_center = 50; perfect_zone_half = TIMING_PERFECT_ZONE_WIDTH / 2 / (TIMING_BAR_WIDTH / 100); target_zone_half = TIMING_TARGET_ZONE_WIDTH / 2 / (TIMING_BAR_WIDTH / 100)
                    jump_power = MIN_JUMP_VELOCITY
                    if abs(timing_bar_value - target_center) <= perfect_zone_half: jump_power = MAX_JUMP_VELOCITY
                    elif abs(timing_bar_value - target_center) <= target_zone_half: jump_power = GOOD_JUMP_VELOCITY
                    game_state = DIVING; diver_vy = jump_power; diver_vx = FORWARD_PUSH; diver_angular_velocity = 0
                elif game_state == GAME_OVER:
                    # Allow reset only if it's NOT the final dive waiting for auto-transition
                    if current_attempt <= 3:
                        reset_dive()
                elif game_state == COMPETITION_OVER:
                    # Check for restart delay before allowing restart
                    if current_time - competition_over_entry_time > RESTART_DELAY:
                        start_new_competition()

    # --- State Updates & Transitions ---

    # Input & Physics Update (DIVING state)
    if game_state == DIVING:
        # Somersault Rotation
        target_angular_velocity_change = 0
        if keys[pygame.K_LEFT]: target_angular_velocity_change = -ROTATION_SPEED_INPUT
        if keys[pygame.K_RIGHT]: target_angular_velocity_change = ROTATION_SPEED_INPUT
        if target_angular_velocity_change != 0: diver_angular_velocity = target_angular_velocity_change
        else: angle_rad = math.radians(diver_angle); gravity_torque = -GRAVITY_TORQUE_EFFECT * math.cos(angle_rad); diver_angular_velocity *= ANGULAR_DAMPING; diver_angular_velocity += gravity_torque
        diver_angle = (diver_angle + diver_angular_velocity) % 360
        total_rotation += diver_angular_velocity; somersaults = int(abs(total_rotation) // 360)
        # Pike/Tuck Control
        if keys[pygame.K_UP]: pike_angle += PIKE_SPEED
        if keys[pygame.K_DOWN]: pike_angle -= PIKE_SPEED
        pike_angle = max(MIN_PIKE_ANGLE, min(MAX_PIKE_ANGLE, pike_angle))
        # Positional Physics
        diver_vy += GRAVITY; diver_x += diver_vx; diver_y += diver_vy
        # Water Entry Check
        angle_rad = math.radians(diver_angle); half_h = DIVER_HEIGHT / 2; half_w = DIVER_WIDTH / 2
        lowest_point_y = diver_y + abs(half_h * math.cos(angle_rad)) + abs(half_w * math.sin(angle_rad))
        if lowest_point_y >= WATER_LEVEL:
            # --- Enter Water ---
            game_state = IN_WATER # Brief state for calcs
            entry_angle = diver_angle
            # Calculate entry width
            head_offset_x = -(TORSO_HEIGHT) * math.sin(math.radians(diver_angle)); legs_angle = diver_angle - pike_angle; feet_offset_x = (LEGS_HEIGHT) * math.sin(math.radians(legs_angle))
            head_x = diver_x + head_offset_x; feet_x = diver_x + feet_offset_x; entry_width = abs(head_x - feet_x)
            # Create Splash
            splash_intensity = max(0, min(1, (entry_width / DIVER_HEIGHT))); create_splash(diver_x, WATER_LEVEL, splash_intensity)
            
            # Scoring Calculation (Splash Only) - MODIFIED FOR BIGGER SPLASH = HIGHER SCORE
            judge_scores = []; base_entry_score = max(0, min(10, (entry_width / DIVER_HEIGHT) * 10)) 
            
            for _ in range(NUM_JUDGES): random_factor = random.uniform(-0.5, 0.5); judge_score = max(0, min(10, base_entry_score + random_factor)); judge_scores.append(round(judge_score, 1))
            judge_scores.sort(); judge_scores_display = judge_scores[:]; valid_scores = judge_scores[1:-1] if len(judge_scores) > 2 else judge_scores
            summed_judge_score = sum(valid_scores)
            final_dive_score = round(summed_judge_score, 2)
            attempt_scores.append(final_dive_score); total_score = sum(attempt_scores)

            # --- Transition to GAME_OVER (Always) ---
            game_state = GAME_OVER
            game_over_entry_time = current_time # Record entry time for potential delay
            current_attempt += 1 # Increment attempt number *before* checking if competition is over

    # Timing Bar Logic
    elif game_state == PRE_JUMP:
        timing_bar_value += timing_bar_direction * TIMING_BAR_SPEED
        if timing_bar_value >= 100: timing_bar_value = 100; timing_bar_direction = -1
        elif timing_bar_value <= 0: timing_bar_value = 0; timing_bar_direction = 1

    # *** NEW: Automatic transition after final dive's GAME_OVER display ***
    elif game_state == GAME_OVER:
        # Check if this was the final dive (attempt number is now > 3)
        if current_attempt > 3:
            # Check if the display delay has passed
            if current_time - game_over_entry_time > SCORE_DISPLAY_DELAY:
                # Update high scores before transitioning
                high_scores.append(total_score)
                high_scores.sort(reverse=True)
                high_scores = high_scores[:MAX_HIGH_SCORES]
                # Transition to final competition screen
                game_state = COMPETITION_OVER
                competition_over_entry_time = current_time # Record entry time for restart delay

    # Update Splash Particles
    if splash_particles:
        for p in splash_particles[:]: p[0] += p[2]; p[1] += p[3]; p[3] += PARTICLE_GRAVITY; p[4] -= 1;
        if p[4] <= 0: splash_particles.remove(p)

    # --- Drawing ---
    screen.fill(SKY_BLUE)

    # Draw Banner
    banner_height = 50
    pygame.draw.rect(screen, BANNER_BG, (0, 0, SCREEN_WIDTH, banner_height))
    draw_text("WHARF MANU!", banner_font, BANNER_TEXT_COLOR, screen, SCREEN_WIDTH // 2, banner_height // 2, center=True)

    # Wharf & Water
    pygame.draw.rect(screen, BROWN, (0, WHARF_TOP_Y - WHARF_THICKNESS, WHARF_WIDTH, WHARF_THICKNESS)); num_posts = int(WHARF_WIDTH // (WHARF_POST_WIDTH + WHARF_POST_SPACING));
    for i in range(num_posts): post_x = WHARF_POST_SPACING // 2 + i * (WHARF_POST_WIDTH + WHARF_POST_SPACING); pygame.draw.rect(screen, DARK_BROWN, (post_x, WHARF_TOP_Y, WHARF_POST_WIDTH, SCREEN_HEIGHT - WHARF_TOP_Y))
    pygame.draw.rect(screen, STEEL_BLUE, (0, WATER_LEVEL, SCREEN_WIDTH, SCREEN_HEIGHT - WATER_LEVEL))

    # Diver Drawing
    if game_state not in [IN_WATER, GAME_OVER, COMPETITION_OVER]: # Don't draw diver once submerged or on score screens
        hip_x, hip_y = int(diver_x), int(diver_y)
        # Draw Torso
        torso_surf = pygame.Surface((DIVER_WIDTH, TORSO_HEIGHT), pygame.SRCALPHA); torso_surf.fill((0,0,0,0)); pygame.draw.rect(torso_surf, RED, (0, 0, DIVER_WIDTH, TORSO_HEIGHT))
        rotated_torso = pygame.transform.rotate(torso_surf, -diver_angle); torso_rect = rotated_torso.get_rect(center=(hip_x, hip_y))
        pivot_offset_x_torso = (TORSO_HEIGHT / 2) * math.sin(math.radians(diver_angle)); pivot_offset_y_torso = (TORSO_HEIGHT / 2) * math.cos(math.radians(diver_angle))
        torso_rect.center = (hip_x + pivot_offset_x_torso, hip_y - pivot_offset_y_torso); screen.blit(rotated_torso, torso_rect)
        # Draw Legs
        legs_surf = pygame.Surface((DIVER_WIDTH, LEGS_HEIGHT), pygame.SRCALPHA); legs_surf.fill((0,0,0,0)); pygame.draw.rect(legs_surf, DARK_RED, (0, 0, DIVER_WIDTH, LEGS_HEIGHT))
        legs_display_angle = diver_angle - pike_angle; rotated_legs = pygame.transform.rotate(legs_surf, -legs_display_angle); legs_rect = rotated_legs.get_rect(center=(hip_x, hip_y))
        pivot_offset_x_legs = (LEGS_HEIGHT / 2) * math.sin(math.radians(legs_display_angle)); pivot_offset_y_legs = (LEGS_HEIGHT / 2) * math.cos(math.radians(legs_display_angle))
        legs_rect.center = (hip_x - pivot_offset_x_legs, hip_y + pivot_offset_y_legs); screen.blit(rotated_legs, legs_rect)

    # Draw Splash Particles (Draw even on score screens for effect)
    if splash_particles:
        for p in splash_particles: pygame.draw.circle(screen, SPLASH_COLOR, (int(p[0]), int(p[1])), 2)

    # UI / Text & Timing Bar
    ui_y_offset = banner_height + 10
    # Display attempt number (adjusting for 1-based index vs state)
    display_attempt = current_attempt if game_state < GAME_OVER else current_attempt - 1
    if game_state != COMPETITION_OVER and display_attempt <= 3 :
        draw_text(f"Attempt: {display_attempt} / 3", score_font, BLACK, screen, SCREEN_WIDTH - 150, ui_y_offset); ui_y_offset += 30
    # Display scores for current competition
    if len(attempt_scores) > 0 and game_state != ON_PLATFORM:
        prev_score_text = "Scores: " + ", ".join([f"{s:.2f}" for s in attempt_scores])
        draw_text(prev_score_text, small_font, BLACK, screen, SCREEN_WIDTH - 250, ui_y_offset, center=False); ui_y_offset += 25

    if game_state == ON_PLATFORM: draw_text("Press SPACE to Start Jump Timing", font, BLACK, screen, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2, center=True)
    elif game_state == PRE_JUMP:
        draw_text("Press SPACE to Jump!", font, BLACK, screen, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2, center=True); pygame.draw.rect(screen, GRAY, (TIMING_BAR_X, TIMING_BAR_Y, TIMING_BAR_WIDTH, TIMING_BAR_HEIGHT))
        target_zone_rect = pygame.Rect(0, 0, TIMING_TARGET_ZONE_WIDTH, TIMING_BAR_HEIGHT); target_zone_rect.center = (TIMING_BAR_X + TIMING_BAR_WIDTH // 2, TIMING_BAR_Y + TIMING_BAR_HEIGHT // 2); pygame.draw.rect(screen, YELLOW, target_zone_rect)
        perfect_zone_rect = pygame.Rect(0, 0, TIMING_PERFECT_ZONE_WIDTH, TIMING_BAR_HEIGHT); perfect_zone_rect.center = (TIMING_BAR_X + TIMING_BAR_WIDTH // 2, TIMING_BAR_Y + TIMING_BAR_HEIGHT // 2); pygame.draw.rect(screen, GREEN, perfect_zone_rect)
        indicator_x = TIMING_BAR_X + int(timing_bar_value * TIMING_BAR_WIDTH / 100); pygame.draw.rect(screen, BLACK, (indicator_x - 2, TIMING_BAR_Y, 4, TIMING_BAR_HEIGHT))
    elif game_state == DIVING: draw_text(f"Somersaults: {somersaults}", font, BLACK, screen, 10, banner_height + 10); draw_text("Arrows: Left/Right=Rotate, Up/Down=Pike/Tuck", small_font, BLACK, screen, 10, banner_height + 50); draw_text(f"Pike: {int(pike_angle)}°", small_font, BLACK, screen, 10, banner_height + 80)
    elif game_state == GAME_OVER or game_state == COMPETITION_OVER:
        mid_x = SCREEN_WIDTH // 2; res_y = SCREEN_HEIGHT // 2 - 160

        # Display Dive Results (Common for both GAME_OVER and COMPETITION_OVER)
        dive_num_display = len(attempt_scores) # Dive number is the index + 1
        draw_text(f"Dive {dive_num_display} Results", font, BLACK, screen, mid_x, res_y, center=True); res_y += 40
        draw_text(f"Somersaults: {somersaults}", score_font, BLACK, screen, mid_x, res_y, center=True); res_y += 30
        
        # MODIFIED entry_score_base_display and entry_desc logic
        entry_desc = ""; entry_score_base_display = max(0, min(10, (entry_width / DIVER_HEIGHT) * 10)) # Reflects new scoring: bigger splash = higher score
        if entry_score_base_display > 9.0: entry_desc = "Epic Splash!"        # e.g., Score 9.01 - 10
        elif entry_score_base_display > 7.0: entry_desc = "Massive Splash!"   # e.g., Score 7.01 - 9.0
        elif entry_score_base_display > 4.0: entry_desc = "Good Splash!"      # e.g., Score 4.01 - 7.0
        else: entry_desc = "Little Splash."                                    # e.g., Score 0 - 4.0
        draw_text(f"Entry: {entry_desc} (Width: {entry_width:.1f})", score_font, BLACK, screen, mid_x, res_y, center=True); res_y += 40
        
        judge_text = "Judges: ";
        if judge_scores_display: judge_text += " ".join([f"{s:.1f}" for s in judge_scores_display]) + f" (Dropped: {judge_scores_display[0]:.1f}, {judge_scores_display[-1]:.1f})"
        draw_text(judge_text, score_font, BLACK, screen, mid_x, res_y, center=True); res_y += 30
        last_dive_score = attempt_scores[-1] if attempt_scores else 0
        draw_text(f"Dive Score: {last_dive_score:.2f}", font, BLACK, screen, mid_x, res_y, center=True); res_y += 50

        # Display State-Specific Info
        if game_state == GAME_OVER:
             draw_text(f"Total Score: {total_score:.2f}", font, BLACK, screen, mid_x, res_y, center=True); res_y += 40
             # Show appropriate message based on whether it's the final dive waiting for delay
             if current_attempt > 3: # This means it was the 3rd dive, waiting for auto-transition
                  draw_text("...", font, BLACK, screen, mid_x, res_y, center=True) # Indicate waiting
             else: # It was dive 1 or 2
                  draw_text("Press SPACE for next dive", font, BLACK, screen, mid_x, res_y, center=True)
        elif game_state == COMPETITION_OVER:
             draw_text(f"Final Total Score: {total_score:.2f}", title_font, GOLD, screen, mid_x, res_y, center=True); res_y += 50
             # Display High Scores (Top 3)
             draw_text("High Scores:", font, BLACK, screen, mid_x, res_y, center=True); res_y += 35
             if high_scores:
                 num_scores_to_show = min(len(high_scores), MAX_HIGH_SCORES)
                 for i in range(num_scores_to_show):
                     score_val = high_scores[i] # Renamed variable to avoid conflict if any
                     rank_text = f"{i+1}. {score_val:.2f}"
                     # A simpler check: just highlight if the score value matches the last total_score calculated
                     is_current_score_highlight = (score_val == total_score)

                     color = GOLD if is_current_score_highlight else BLACK
                     draw_text(rank_text, score_font, color, screen, mid_x, res_y, center=True)
                     res_y += 30
                 res_y += (MAX_HIGH_SCORES - num_scores_to_show) * 30 # Padding if less than 3 scores
             else:
                 draw_text("None yet!", score_font, GRAY, screen, mid_x, res_y, center=True); res_y += 30 * MAX_HIGH_SCORES
             res_y += 20
             # Display restart message, considering delay
             restart_message = "Press SPACE to Play Again"
             if current_time - competition_over_entry_time <= RESTART_DELAY:
                 restart_message = "..." # Indicate waiting for restart delay
             draw_text(restart_message, font, BLACK, screen, mid_x, res_y, center=True)

    # Update Display
    pygame.display.flip()

# Cleanup
pygame.quit()
sys.exit()