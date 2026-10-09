import pygame
import random
import math
from array import array

from game.beat import (
    Note,
    LANES,
    LANE_KEYS,
    LANE_LABELS,
    LANE_COLORS
)


WIDTH = 480
HEIGHT = 640
FPS = 60

# Task 3: BPM-synced spawning
BPM = 120
BEAT_INTERVAL = 60.0 / BPM

HIT_Y = HEIGHT - 80
HIT_WINDOW = 30

BG = (15, 10, 25)

LANE_W = WIDTH // LANES


class GameEngine:

    def __init__(self):

        pygame.init()

        # =========================================================
        # Task 1: Sound effects
        # =========================================================

        self.audio_enabled = False
        self.hit_sounds = {}

        try:

            pygame.mixer.init(
                frequency=44100,
                size=-16,
                channels=1,
                buffer=512
            )

            self.audio_enabled = True

            self.hit_sounds = {
                "PERFECT": self._create_hit_sound(
                    880,
                    0.08
                ),

                "GREAT": self._create_hit_sound(
                    660,
                    0.08
                ),

                "OK": self._create_hit_sound(
                    440,
                    0.08
                )
            }

        except pygame.error:

            self.audio_enabled = False

        # =========================================================
        # Window
        # =========================================================

        self.screen = pygame.display.set_mode(
            (WIDTH, HEIGHT)
        )

        pygame.display.set_caption(
            "Rhythm Tap"
        )

        self.clock = pygame.time.Clock()

        self.font = pygame.font.SysFont(
            "monospace",
            26,
            bold=True
        )

        self.big_font = pygame.font.SysFont(
            "monospace",
            44,
            bold=True
        )

        self.reset()

    # =============================================================
    # Task 1: Create sound
    # =============================================================

    def _create_hit_sound(
        self,
        frequency,
        duration
    ):

        sample_rate = 44100

        samples = array("h")

        total_samples = int(
            sample_rate * duration
        )

        for i in range(total_samples):

            t = i / sample_rate

            envelope = (
                1.0
                - i / total_samples
            )

            value = int(
                12000
                * envelope
                * math.sin(
                    2
                    * math.pi
                    * frequency
                    * t
                )
            )

            samples.append(value)

        return pygame.mixer.Sound(
            buffer=samples.tobytes()
        )

    # =============================================================
    # Task 1: Play sound
    # =============================================================

    def play_hit_sound(self, grade):

        if not self.audio_enabled:
            return

        sound = self.hit_sounds.get(
            grade
        )

        if sound:
            sound.play()

    # =============================================================
    # Reset
    # =============================================================

    def reset(self):

        self.notes = []

        self.score = 0
        self.combo = 0
        self.max_combo = 0
        self.misses = 0

        # Task 3
        self.next_beat_time = (
            pygame.time.get_ticks()
            + BEAT_INTERVAL * 1000
        )

        self.speed = 5

        self.frame = 0

        self.feedback = []

        self.game_over = False

        # Task 4
        self.perfect_count = 0
        self.great_count = 0
        self.ok_count = 0
        self.grade_miss_count = 0

    # =============================================================
    # Task 3: Spawn notes on BPM beats
    # =============================================================

    def spawn_note(self):

        lane = random.randint(
            0,
            LANES - 1
        )

        # Task 2:
        # 25% chance of a hold note.
        is_hold = (
            random.random() < 0.25
        )

        self.notes.append(
            Note(
                lane,
                y=-30,
                speed=self.speed,
                is_hold=is_hold
            )
        )

    # =============================================================
    # Task 4: Grade tracking
    # =============================================================

    def record_grade(self, grade):

        if grade == "PERFECT":

            self.perfect_count += 1

        elif grade == "GREAT":

            self.great_count += 1

        elif grade == "OK":

            self.ok_count += 1

        elif grade == "MISS":

            self.grade_miss_count += 1

    # =============================================================
    # Input handling
    # =============================================================

    def handle_events(self):

        for event in pygame.event.get():

            if event.type == pygame.QUIT:

                return False

            # -----------------------------------------------------
            # Key pressed
            # -----------------------------------------------------

            if event.type == pygame.KEYDOWN:

                if event.key == pygame.K_r:

                    self.reset()

                elif not self.game_over:

                    for lane, key in enumerate(
                        LANE_KEYS
                    ):

                        if event.key == key:

                            self.process_tap(
                                lane
                            )

            # -----------------------------------------------------
            # Key released
            # -----------------------------------------------------

            elif event.type == pygame.KEYUP:

                if not self.game_over:

                    for lane, key in enumerate(
                        LANE_KEYS
                    ):

                        if event.key == key:

                            self.release_hold(
                                lane
                            )

        return True

    # =============================================================
    # Find closest note
    # =============================================================

    def find_closest_note(self, lane):

        best = None

        best_dist = float("inf")

        for note in self.notes:

            if (
                note.lane == lane
                and not note.hit
                and not note.missed
                and not note.holding
            ):

                # For hold notes, judge the head
                # at the hit line.
                distance = abs(
                    note.y
                    + Note.HEIGHT // 2
                    - HIT_Y
                )

                if distance < best_dist:

                    best_dist = distance

                    best = note

        return best, best_dist

    # =============================================================
    # Normal tap / start hold
    # =============================================================

    def process_tap(self, lane):

        note, distance = (
            self.find_closest_note(
                lane
            )
        )

        lane_x = (
            lane * LANE_W
            + LANE_W // 2
        )

        # ---------------------------------------------------------
        # No valid note
        # ---------------------------------------------------------

        if (
            note is None
            or distance > HIT_WINDOW
        ):

            self.record_grade(
                "MISS"
            )

            self.combo = 0

            self.feedback.append(
                [
                    "MISS",
                    (220, 60, 60),
                    40,
                    lane_x,
                    HIT_Y - 30
                ]
            )

            return

        # ---------------------------------------------------------
        # Task 2: Hold note
        # ---------------------------------------------------------

        if note.is_hold:

            # The initial press successfully
            # catches the hold note.
            note.holding = True
            note.hold_started = True
            note.hold_progress = 0

            # Lock the head exactly onto the hit line.
            note.y = (
                HIT_Y
                - Note.HEIGHT // 2
            )

            self.feedback.append(
                [
                    "HOLD",
                    (100, 220, 255),
                    40,
                    lane_x,
                    HIT_Y - 30
                ]
            )

            return

        # ---------------------------------------------------------
        # Normal note
        # ---------------------------------------------------------

        note.hit = True

        if distance < 8:

            grade = "PERFECT"

            points = 300

            color = (
                255,
                220,
                0
            )

        elif distance < 18:

            grade = "GREAT"

            points = 200

            color = (
                100,
                220,
                100
            )

        else:

            grade = "OK"

            points = 100

            color = (
                180,
                180,
                255
            )

        # Task 4
        self.record_grade(
            grade
        )

        # Combo
        self.combo += 1

        self.max_combo = max(
            self.max_combo,
            self.combo
        )

        # Score
        self.score += (
            points
            * max(
                1,
                self.combo // 5
            )
        )

        # Task 1
        self.play_hit_sound(
            grade
        )

        self.feedback.append(
            [
                grade,
                color,
                40,
                lane_x,
                HIT_Y - 30
            ]
        )

    # =============================================================
    # Task 2: Release hold
    # =============================================================

    def release_hold(self, lane):

        for note in self.notes:

            if (
                note.lane == lane
                and note.is_hold
                and note.holding
                and not note.hit
                and not note.missed
            ):

                # -------------------------------------------------
                # Successfully completed hold
                # -------------------------------------------------

                if (
                    note.hold_progress
                    >= note.hold_duration
                ):

                    self.complete_hold(
                        note
                    )

                # -------------------------------------------------
                # Released too early
                # -------------------------------------------------

                else:

                    note.missed = True

                    note.holding = False

                    self.record_grade(
                        "MISS"
                    )

                    self.combo = 0

                    self.feedback.append(
                        [
                            "MISS",
                            (220, 60, 60),
                            40,
                            lane * LANE_W
                            + LANE_W // 2,
                            HIT_Y - 30
                        ]
                    )

                break

    # =============================================================
    # Task 2: Successfully complete hold
    # =============================================================

    def complete_hold(self, note):

        # Prevent double judging.
        if note.hit:
            return

        note.hit = True

        note.holding = False

        note.hold_progress = (
            note.hold_duration
        )

        # ---------------------------------------------------------
        # A complete hold is a PERFECT
        # ---------------------------------------------------------

        self.record_grade(
            "PERFECT"
        )

        self.combo += 1

        self.max_combo = max(
            self.max_combo,
            self.combo
        )

        self.score += (
            300
            * max(
                1,
                self.combo // 5
            )
        )

        # Task 1
        self.play_hit_sound(
            "PERFECT"
        )

        self.feedback.append(
            [
                "PERFECT",
                (255, 220, 0),
                40,
                note.lane * LANE_W
                + LANE_W // 2,
                HIT_Y - 30
            ]
        )

    # =============================================================
    # Update
    # =============================================================

    def update(self):

        if self.game_over:

            return

        self.frame += 1

        # ---------------------------------------------------------
        # Task 3: BPM spawning
        # ---------------------------------------------------------

        current_time = (
            pygame.time.get_ticks()
        )

        while (
            current_time
            >= self.next_beat_time
        ):

            self.spawn_note()

            self.next_beat_time += (
                BEAT_INTERVAL * 1000
            )

        # ---------------------------------------------------------
        # Increase speed over time
        # ---------------------------------------------------------

        if self.frame % 600 == 0:

            self.speed = min(
                10,
                self.speed + 0.5
            )

        # ---------------------------------------------------------
        # Keyboard state
        # ---------------------------------------------------------

        keys = pygame.key.get_pressed()

        # ---------------------------------------------------------
        # Update notes
        # ---------------------------------------------------------

        for note in self.notes:

            # -----------------------------------------------------
            # Hold note currently being held
            # -----------------------------------------------------

            if note.holding:

                key = LANE_KEYS[
                    note.lane
                ]

                # Player is still holding key.
                if keys[key]:

                    note.hold_progress += 1

                    # -------------------------------------------------
                    # 1 second completed
                    # -------------------------------------------------

                    if (
                        note.hold_progress
                        >= note.hold_duration
                    ):

                        self.complete_hold(
                            note
                        )

                # -------------------------------------------------
                # Player released key
                # -------------------------------------------------

                else:

                    # KEYUP normally handles this,
                    # but this also protects against
                    # missing the event.
                    note.missed = True

                    note.holding = False

                    self.record_grade(
                        "MISS"
                    )

                    self.combo = 0

                    self.feedback.append(
                        [
                            "MISS",
                            (220, 60, 60),
                            40,
                            note.lane * LANE_W
                            + LANE_W // 2,
                            HIT_Y - 30
                        ]
                    )

                continue

            # -----------------------------------------------------
            # Normal note movement
            # -----------------------------------------------------

            note.update()

            # -----------------------------------------------------
            # Missed note
            # -----------------------------------------------------

            if (
                not note.hit
                and not note.missed
                and note.y
                > HIT_Y
                + HIT_WINDOW
                + Note.HEIGHT
            ):

                note.missed = True

                self.misses += 1

                self.record_grade(
                    "MISS"
                )

                self.combo = 0

        # ---------------------------------------------------------
        # Remove finished notes
        # ---------------------------------------------------------

        self.notes = [
            note
            for note in self.notes
            if not (
                note.hit
                or (
                    note.missed
                    and note.y
                    > HEIGHT + 10
                )
            )
        ]

        # ---------------------------------------------------------
        # Feedback timer
        # ---------------------------------------------------------

        self.feedback = [

            [
                text,
                color,
                ttl - 1,
                x,
                y
            ]

            for (
                text,
                color,
                ttl,
                x,
                y
            ) in self.feedback

            if ttl > 1
        ]

        # ---------------------------------------------------------
        # Game over
        # ---------------------------------------------------------

        if self.misses >= 15:

            self.game_over = True

    # =============================================================
    # Draw
    # =============================================================

    def draw(self):

        self.screen.fill(
            BG
        )

        # ---------------------------------------------------------
        # Lane dividers
        # ---------------------------------------------------------

        for i in range(
            LANES + 1
        ):

            pygame.draw.line(
                self.screen,
                (40, 40, 60),
                (
                    i * LANE_W,
                    0
                ),
                (
                    i * LANE_W,
                    HEIGHT
                ),
                1
            )

        # ---------------------------------------------------------
        # Hit line
        # ---------------------------------------------------------

        pygame.draw.line(
            self.screen,
            (80, 80, 100),
            (
                0,
                HIT_Y
            ),
            (
                WIDTH,
                HIT_Y
            ),
            2
        )

        # ---------------------------------------------------------
        # Lane buttons
        # ---------------------------------------------------------

        for i in range(LANES):

            lane_x = (
                i * LANE_W
                + LANE_W // 2
            )

            pygame.draw.rect(
                self.screen,
                LANE_COLORS[i],
                pygame.Rect(
                    lane_x
                    - Note.WIDTH // 2,
                    HIT_Y - 12,
                    Note.WIDTH,
                    24
                ),
                border_radius=6
            )

            label = self.font.render(
                LANE_LABELS[i],
                True,
                (20, 20, 20)
            )

            self.screen.blit(
                label,
                (
                    lane_x
                    - label.get_width() // 2,
                    HIT_Y - 10
                )
            )

        # ---------------------------------------------------------
        # Notes
        # ---------------------------------------------------------

        for note in self.notes:

            if note.hit:

                continue

            lane_x = (
                note.lane * LANE_W
                + LANE_W // 2
            )

            rect = note.get_rect(
                lane_x
            )

            pygame.draw.rect(
                self.screen,
                LANE_COLORS[
                    note.lane
                ],
                rect,
                border_radius=5
            )

            # -----------------------------------------------------
            # Hold progress
            # -----------------------------------------------------

            if note.is_hold:

                progress = min(
                    1.0,
                    note.hold_progress
                    / note.hold_duration
                )

                if progress > 0:

                    progress_height = int(
                        rect.height
                        * progress
                    )

                    pygame.draw.rect(
                        self.screen,
                        (255, 255, 255),
                        pygame.Rect(
                            rect.x,
                            rect.bottom
                            - progress_height,
                            rect.width,
                            progress_height
                        ),
                        border_radius=5
                    )

        # ---------------------------------------------------------
        # Feedback
        # ---------------------------------------------------------

        for (
            text,
            color,
            ttl,
            x,
            y
        ) in self.feedback:

            surface = self.font.render(
                text,
                True,
                color
            )

            alpha = min(
                255,
                ttl * 7
            )

            surface.set_alpha(
                alpha
            )

            self.screen.blit(
                surface,
                (
                    x
                    - surface.get_width() // 2,
                    y
                )
            )

        # ---------------------------------------------------------
        # HUD
        # ---------------------------------------------------------

        score_text = self.font.render(
            f"Score: {self.score}",
            True,
            (220, 220, 220)
        )

        combo_text = self.font.render(
            f"Combo: {self.combo}x",
            True,
            (255, 220, 80)
        )

        miss_text = self.font.render(
            f"Misses: {self.misses}/15",
            True,
            (220, 100, 100)
        )

        self.screen.blit(
            score_text,
            (10, 10)
        )

        self.screen.blit(
            combo_text,
            (10, 40)
        )

        self.screen.blit(
            miss_text,
            (
                WIDTH - 170,
                10
            )
        )

        # ---------------------------------------------------------
        # Task 4
        # ---------------------------------------------------------

        if self.game_over:

            self.draw_grade_summary()

        pygame.display.flip()

    # =============================================================
    # Task 4: Grade summary
    # =============================================================

    def draw_grade_summary(self):

        overlay = pygame.Surface(
            (WIDTH, HEIGHT),
            pygame.SRCALPHA
        )

        overlay.fill(
            (0, 0, 0, 210)
        )

        self.screen.blit(
            overlay,
            (0, 0)
        )

        # ---------------------------------------------------------
        # Accuracy
        # ---------------------------------------------------------

        total_judged = (
            self.perfect_count
            + self.great_count
            + self.ok_count
            + self.grade_miss_count
        )

        successful_hits = (
            self.perfect_count
            + self.great_count
            + self.ok_count
        )

        if total_judged > 0:

            accuracy = (
                successful_hits
                / total_judged
                * 100
            )

        else:

            accuracy = 0.0

        # ---------------------------------------------------------
        # Title
        # ---------------------------------------------------------

        title = self.big_font.render(
            "GRADE SUMMARY",
            True,
            (255, 255, 255)
        )

        self.screen.blit(
            title,
            (
                WIDTH // 2
                - title.get_width() // 2,
                90
            )
        )

        # ---------------------------------------------------------
        # Results
        # ---------------------------------------------------------

        lines = [

            (
                f"PERFECT: {self.perfect_count}",
                (255, 220, 0)
            ),

            (
                f"GREAT:   {self.great_count}",
                (100, 220, 100)
            ),

            (
                f"OK:      {self.ok_count}",
                (180, 180, 255)
            ),

            (
                f"MISS:    {self.grade_miss_count}",
                (220, 100, 100)
            ),

            (
                f"Accuracy: {accuracy:.2f}%",
                (255, 255, 255)
            ),

            (
                f"Score: {self.score}",
                (220, 220, 220)
            ),

            (
                f"Max Combo: {self.max_combo}x",
                (255, 220, 80)
            )
        ]

        y = 180

        for text, color in lines:

            surface = self.font.render(
                text,
                True,
                color
            )

            self.screen.blit(
                surface,
                (
                    WIDTH // 2
                    - surface.get_width() // 2,
                    y
                )
            )

            y += 42

        # ---------------------------------------------------------
        # Restart
        # ---------------------------------------------------------

        restart = self.font.render(
            "Press R to Restart",
            True,
            (180, 180, 180)
        )

        self.screen.blit(
            restart,
            (
                WIDTH // 2
                - restart.get_width() // 2,
                510
            )
        )

    # =============================================================
    # Main loop
    # =============================================================

    def run(self):

        running = True

        while running:

            running = self.handle_events()

            self.update()

            self.draw()

            self.clock.tick(
                FPS
            )

        pygame.quit()