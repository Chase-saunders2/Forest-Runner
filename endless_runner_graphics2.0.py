# endless_runner_complete.py
# Side-view endless runner with graphics, pause, and high-score tracking.

import pygame, random, sys, os

# ---------------- Setup ----------------
pygame.init()
SCREEN_W, SCREEN_H = 960, 540
FPS = 60
GROUND_Y = SCREEN_H - 110
WHITE = (255, 255, 255)

# create display before loading images
screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
pygame.display.set_caption("Endless Runner (Side View)")

# detect asset path
if getattr(sys, "frozen", False):
    BASE_PATH = sys._MEIPASS
else:
    BASE_PATH = os.path.dirname(__file__)
ASSET_DIR = os.path.join(BASE_PATH, "assets")

# --------------- Load images ---------------
def load_image(name, scale=None):
    path = os.path.join(ASSET_DIR, name)
    img = pygame.image.load(path).convert_alpha()
    if scale:
        img = pygame.transform.smoothscale(img, scale)
    return img

bg_far = load_image("bg_far.png", (SCREEN_W, SCREEN_H))
bg_mid = load_image("bg_mid.png", (SCREEN_W, int(SCREEN_H * 0.6)))
bg_ground = load_image("bg_ground.png", (SCREEN_W, int(SCREEN_H * 0.25)))

player_run = [load_image(f"player_run_{i}.png", (64, 80)) for i in (1, 2, 3)]
player_jump = load_image("player_jump.png", (64, 80))
player_slide = load_image("player_slide.png", (64, 60))

coin_frames = [load_image(f"coin_{i}.png", (32, 32)) for i in (1, 2, 3)]
obstacle_imgs = [
    load_image("obstacle_log.png", (64, 48)),
    load_image("obstacle_rock.png", (64, 48)),
]

# --------------- Helpers ---------------
class Animator:
    def __init__(self, frames, fps=8):
        self.frames, self.fps = frames, fps
        self.index, self.timer = 0, 0
    def update(self, dt):
        if len(self.frames) <= 1: return
        self.timer += dt
        if self.timer >= 1000 / self.fps:
            self.timer = 0
            self.index = (self.index + 1) % len(self.frames)
    def get(self):
        return self.frames[self.index]

class Player:
    def __init__(self):
        self.x, self.y = 150, GROUND_Y - 80
        self.w, self.h = 64, 80
        self.vel_y = 0
        self.jumping = False
        self.sliding = False
        self.slide_timer = 0
        self.anim = Animator(player_run, 8)
        self.current = player_run[0]

    def rect(self): return pygame.Rect(self.x, self.y, self.w, self.h)

    def jump(self):
        if not self.jumping and not self.sliding:
            self.jumping = True
            self.vel_y = -18   # stronger jump

    def slide(self):
        if not self.jumping and not self.sliding:
            self.sliding = True
            self.slide_timer = 300

    def update(self, dt):
        self.anim.update(dt)
        if self.jumping:
            self.vel_y += 0.8
            self.y += self.vel_y
            if self.y >= GROUND_Y - self.h:
                self.y = GROUND_Y - self.h
                self.vel_y = 0
                self.jumping = False
        if self.sliding:
            self.slide_timer -= dt
            if self.slide_timer <= 0:
                self.sliding = False
        if self.jumping:
            self.current = player_jump
        elif self.sliding:
            self.current = player_slide
        else:
            self.current = self.anim.get()

    def draw(self, surf):
        surf.blit(self.current, (self.x, self.y))

class Coin:
    def __init__(self, x):
        self.x = x
        self.y = random.randint(GROUND_Y - 160, GROUND_Y - 60)
        self.w = self.h = 32
        self.anim = Animator(coin_frames, 10)
    def rect(self): return pygame.Rect(self.x, self.y, self.w, self.h)
    def update(self, dt, speed):
        self.x -= speed; self.anim.update(dt)
    def draw(self, surf): surf.blit(self.anim.get(), (self.x, self.y))

class Obstacle:
    def __init__(self, x):
        self.img = random.choice(obstacle_imgs)
        self.w, self.h = self.img.get_size()
        self.x, self.y = x, GROUND_Y - self.h
    def rect(self): return pygame.Rect(self.x, self.y, self.w, self.h)
    def update(self, dt, speed): self.x -= speed
    def draw(self, surf): surf.blit(self.img, (self.x, self.y))

# --------------- High Score Handling ---------------
def load_high_score():
    try:
        with open("highscore.txt", "r") as f:
            return int(f.read().strip())
    except Exception:
        return 0

def save_high_score(score):
    with open("highscore.txt", "w") as f:
        f.write(str(score))

# --------------- Main Game Loop ---------------
def main():
    clock = pygame.time.Clock()
    font = pygame.font.SysFont(None, 36)

    high_score = load_high_score()
    player, objects, coins = Player(), [], []
    bg_far_x = bg_mid_x = bg_ground_x = 0
    score, speed, game_state = 0, 6, "Start"
    last_spawn = last_coin = 0
    paused = False

    while True:
        dt = clock.tick(FPS)
        for e in pygame.event.get():
            if e.type == pygame.QUIT: pygame.quit(); sys.exit()
            if e.type == pygame.KEYDOWN:
                if e.key in (pygame.K_q, pygame.K_ESCAPE): pygame.quit(); sys.exit()
                if e.key == pygame.K_SPACE:
                    if game_state == "Start": game_state = "Running"
                    elif game_state == "GameOver": return main()
                    else: player.jump()
                if e.key == pygame.K_DOWN: player.slide()
                if e.key == pygame.K_p and game_state == "Running":
                    paused = not paused

        # pause screen
        if paused and game_state == "Running":
            screen.fill((0, 0, 0))
            t = font.render("PAUSED - Press P to Resume", True, WHITE)
            screen.blit(t, (SCREEN_W//2 - t.get_width()//2, SCREEN_H//2))
            pygame.display.flip()
            continue

        if game_state == "Running":
            player.update(dt)
            bg_far_x -= speed * 0.2; bg_mid_x -= speed * 0.4; bg_ground_x -= speed
            if bg_far_x <= -SCREEN_W: bg_far_x = 0
            if bg_mid_x <= -SCREEN_W: bg_mid_x = 0
            if bg_ground_x <= -SCREEN_W: bg_ground_x = 0

            now = pygame.time.get_ticks()
            if now - last_spawn > 1500:
                last_spawn = now; objects.append(Obstacle(SCREEN_W + 50))
            if now - last_coin > 800:
                last_coin = now; coins.append(Coin(SCREEN_W + 50))

            for o in list(objects):
                o.update(dt, speed)
                if o.x + o.w < 0: objects.remove(o)
                if o.rect().colliderect(player.rect()):
                    game_state = "GameOver"

            for c in list(coins):
                c.update(dt, speed)
                if c.x + c.w < 0: coins.remove(c)
                if c.rect().colliderect(player.rect()):
                    score += 10
                    coins.remove(c)

            score += int(speed * 0.1)
            if score % 500 == 0: speed += 0.05

        # ---------------- Draw ----------------
        screen.fill((135, 206, 235))
        for (img, x, yoff) in [
            (bg_far, bg_far_x, 0),
            (bg_far, bg_far_x + SCREEN_W, 0),
            (bg_mid, bg_mid_x, SCREEN_H - bg_mid.get_height() - 120),
            (bg_mid, bg_mid_x + SCREEN_W, SCREEN_H - bg_mid.get_height() - 120),
            (bg_ground, bg_ground_x, SCREEN_H - bg_ground.get_height()),
            (bg_ground, bg_ground_x + SCREEN_W, SCREEN_H - bg_ground.get_height())
        ]:
            screen.blit(img, (x, yoff))

        for c in coins: c.draw(screen)
        for o in objects: o.draw(screen)
        player.draw(screen)

        # scores
        stext = font.render(f"Score: {score}", True, WHITE)
        htext = font.render(f"High Score: {high_score}", True, WHITE)
        screen.blit(stext, (10, 10))
        screen.blit(htext, (10, 40))

        if game_state == "Start":
            t = font.render("Press SPACE to Start", True, WHITE)
            screen.blit(t, (SCREEN_W//2 - t.get_width()//2, SCREEN_H//2))
        elif game_state == "GameOver":
            t = font.render("Game Over - Press SPACE to Restart", True, WHITE)
            screen.blit(t, (SCREEN_W//2 - t.get_width()//2, SCREEN_H//2))

        # update high score if beaten
        if score > high_score:
            high_score = score
            save_high_score(high_score)

        pygame.display.flip()

if __name__ == "__main__":
    main()

