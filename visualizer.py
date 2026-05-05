# visualizer.py

import pygame
import math
import random
import colorsys
import os
import time


class Particle:
    __slots__ = ("x", "y", "vx", "vy", "life", "max_life", "size", "color")

    def __init__(self, x, y, vx, vy, life, size, color):
        self.x, self.y = x, y
        self.vx, self.vy = vx, vy
        self.life = life
        self.max_life = life
        self.size = size
        self.color = color

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.vx *= 0.98
        self.vy *= 0.98
        self.life -= 1

    def alive(self):
        return self.life > 0


class Visualizer:
    """
    Modes:
        0 -> Particle Burst
        1 -> Spectrum Bars
        2 -> Mandala
        3 -> Waveform Ribbon
        4 -> Nebula
    """

    MODE_NAMES = [
        "Particle Burst",
        "Spectrum Bars",
        "Mandala",
        "Waveform Ribbon",
        "Nebula"
    ]

    def __init__(self, width=1000, height=700):
        pygame.init()
        self.width = width
        self.height = height
        self.screen = pygame.display.set_mode((width, height), pygame.DOUBLEBUF)
        pygame.display.set_caption("Audio Visual Art — PRO")
        self.clock = pygame.time.Clock()

        self.amplitude = 0.0
        self.frequency = 0.0
        self.spectrum = [0.0] * 32
        self.beat = False

        self.mode = 0
        self.running = True
        self.fullscreen = False
        self.angle = 0.0
        self.hue = 0.0
        self.particles = []
        self.waveform_history = []
        self.beat_flash = 0.0

        self.fade_layer = pygame.Surface((width, height), pygame.SRCALPHA)
        self.fade_layer.fill((10, 10, 20, 35))

        self.font = pygame.font.SysFont("Arial", 18, bold=True)
        self.small_font = pygame.font.SysFont("Arial", 13)

    def update(self, amplitude, frequency, spectrum=None, beat=False):
        self.amplitude = amplitude
        self.frequency = frequency
        if spectrum is not None:
            self.spectrum = spectrum
        self.beat = beat

        target_hue = min(frequency / 2000.0, 1.0)
        self.hue += (target_hue - self.hue) * 0.05
        self.angle += 0.01 + amplitude * 0.05

        self.waveform_history.append(amplitude)
        if len(self.waveform_history) > self.width // 2:
            self.waveform_history.pop(0)

        if beat:
            self.beat_flash = 1.0
            self._spawn_beat_particles()

        self.beat_flash *= 0.9

    def switch_mode(self, mode=None):
        if mode is None:
            self.mode = (self.mode + 1) % len(self.MODE_NAMES)
        else:
            self.mode = mode % len(self.MODE_NAMES)

    def draw(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    self.switch_mode()
                elif event.key == pygame.K_ESCAPE:
                    self.running = False
                elif event.key == pygame.K_f:
                    self._toggle_fullscreen()
                elif event.key == pygame.K_s:
                    self._screenshot()
                elif pygame.K_1 <= event.key <= pygame.K_5:
                    self.switch_mode(event.key - pygame.K_1)

        self.screen.blit(self.fade_layer, (0, 0))

        if self.beat_flash > 0.05:
            flash = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
            alpha = int(40 * self.beat_flash)
            flash.fill((255, 255, 255, alpha))
            self.screen.blit(flash, (0, 0))

        color = self._hue_color(self.hue)

        if self.mode == 0:
            self._draw_particles(color)
        elif self.mode == 1:
            self._draw_spectrum_bars(color)
        elif self.mode == 2:
            self._draw_mandala(color)
        elif self.mode == 3:
            self._draw_waveform_ribbon(color)
        elif self.mode == 4:
            self._draw_nebula(color)

        self._draw_hud()
        pygame.display.flip()
        self.clock.tick(60)

    def quit(self):
        pygame.quit()

    def _hue_color(self, h, s=0.85, v=1.0):
        r, g, b = colorsys.hsv_to_rgb(h % 1.0, s, v)
        return (int(r * 255), int(g * 255), int(b * 255))

    def _spawn_beat_particles(self):
        cx, cy = self.width // 2, self.height // 2
        count = int(30 + self.amplitude * 80)

        for _ in range(count):
            angle = random.uniform(0, math.tau)
            speed = random.uniform(2, 8) * (1 + self.amplitude)
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed
            life = random.randint(40, 80)
            size = random.randint(2, 5)
            hue = (self.hue + random.uniform(-0.1, 0.1)) % 1.0
            color = self._hue_color(hue)
            self.particles.append(Particle(cx, cy, vx, vy, life, size, color))

        if len(self.particles) > 800:
            self.particles = self.particles[-800:]

    def _draw_particles(self, color):
        if self.amplitude > 0.05:
            cx, cy = self.width // 2, self.height // 2
            for _ in range(int(self.amplitude * 6)):
                a = random.uniform(0, math.tau)
                s = random.uniform(1, 4)
                self.particles.append(
                    Particle(
                        cx, cy,
                        math.cos(a) * s,
                        math.sin(a) * s,
                        random.randint(30, 60),
                        random.randint(2, 4),
                        color
                    )
                )

        new_particles = []
        for p in self.particles:
            p.update()
            if p.alive():
                alpha_ratio = p.life / p.max_life
                r = int(p.color[0] * alpha_ratio)
                g = int(p.color[1] * alpha_ratio)
                b = int(p.color[2] * alpha_ratio)
                pygame.draw.circle(self.screen, (r, g, b), (int(p.x), int(p.y)), p.size)
                new_particles.append(p)

        self.particles = new_particles

    def _draw_spectrum_bars(self, color):
        n = len(self.spectrum)
        if n == 0:
            return

        bar_w = self.width / n
        cy = self.height // 2

        for i, val in enumerate(self.spectrum):
            h = int(val * self.height * 0.45)
            x = int(i * bar_w)
            hue = (self.hue + i / n * 0.3) % 1.0
            c = self._hue_color(hue)

            pygame.draw.rect(self.screen, c, (x + 2, cy - h, max(1, int(bar_w - 4)), h))
            pygame.draw.rect(self.screen, c, (x + 2, cy, max(1, int(bar_w - 4)), h))

    def _draw_mandala(self, color):
        cx, cy = self.width // 2, self.height // 2
        layers = 6
        spikes = 12
        base_r = 50 + self.amplitude * 200

        for L in range(layers):
            r_outer = base_r + L * 25
            r_inner = r_outer * 0.5
            pts = []

            for i in range(spikes * 2):
                rr = r_outer if i % 2 == 0 else r_inner
                theta = self.angle * (1 + L * 0.2) + i * math.pi / spikes
                x = cx + rr * math.cos(theta)
                y = cy + rr * math.sin(theta)
                pts.append((x, y))

            hue = (self.hue + L * 0.08) % 1.0
            c = self._hue_color(hue)
            pygame.draw.polygon(self.screen, c, pts, width=2)

    def _draw_waveform_ribbon(self, color):
        if len(self.waveform_history) < 2:
            return

        cy = self.height // 2
        pts_top, pts_bot = [], []

        for i, v in enumerate(self.waveform_history):
            x = i * (self.width / max(1, len(self.waveform_history)))
            offset = v * self.height * 0.4
            pts_top.append((x, cy - offset))
            pts_bot.append((x, cy + offset))

        if len(pts_top) >= 2:
            pygame.draw.lines(self.screen, color, False, pts_top, 3)
            pygame.draw.lines(self.screen, color, False, pts_bot, 3)

    def _draw_nebula(self, color):
        cx, cy = self.width // 2, self.height // 2
        max_r = int(80 + self.amplitude * 350)
        layers = 25

        for i in range(layers, 0, -1):
            r = int(max_r * i / layers)
            ratio = i / layers
            hue = (self.hue + ratio * 0.2) % 1.0
            c = self._hue_color(hue, s=0.8, v=ratio)
            surf = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
            alpha = int(30 * (1 - ratio) + 10)
            pygame.draw.circle(surf, (*c, alpha), (r, r), r)
            self.screen.blit(surf, (cx - r, cy - r), special_flags=pygame.BLEND_RGBA_ADD)

    def _draw_hud(self):
        mode_text = f"Mode {self.mode + 1}/5: {self.MODE_NAMES[self.mode]}"
        info = self.font.render(mode_text, True, (255, 255, 255))
        self.screen.blit(info, (15, 12))

        hint = self.small_font.render(
            "SPACE: next  |  1-5: select  |  F: fullscreen  |  S: screenshot  |  ESC: quit",
            True,
            (180, 180, 200)
        )
        self.screen.blit(hint, (15, self.height - 22))

        if self.beat_flash > 0.3:
            beat_text = self.font.render("BEAT", True, (255, 80, 120))
            self.screen.blit(beat_text, (self.width - 90, 12))

    def _toggle_fullscreen(self):
        self.fullscreen = not self.fullscreen
        flags = pygame.FULLSCREEN if self.fullscreen else pygame.DOUBLEBUF
        self.screen = pygame.display.set_mode((self.width, self.height), flags)

    def _screenshot(self):
        os.makedirs("screenshots", exist_ok=True)
        path = f"screenshots/art_{int(time.time())}.png"
        pygame.image.save(self.screen, path)
        print(f"Saved: {path}")