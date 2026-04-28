import math
import random
from array import array

import pygame


class SoundManager:
    def __init__(self, sample_rate=44100):
        self.sample_rate = sample_rate
        self.enabled = False
        self._sounds = {}
        self._init_audio()
        if self.enabled:
            self._build_spell_sounds()

    def _init_audio(self):
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(frequency=self.sample_rate, size=-16, channels=1, buffer=512)
            self.enabled = True
        except pygame.error:
            # Keep game functional even when audio devices are unavailable.
            self.enabled = False

    def _make_wave(self, duration_ms, synth, volume=0.5):
        sample_count = max(1, int(self.sample_rate * duration_ms / 1000))
        samples = array("h")
        attack = max(1, int(sample_count * 0.08))
        release = max(1, int(sample_count * 0.2))
        sustain_end = max(attack, sample_count - release)

        for i in range(sample_count):
            t = i / self.sample_rate
            if i < attack:
                env = i / attack
            elif i >= sustain_end:
                env = max(0.0, 1.0 - (i - sustain_end) / release)
            else:
                env = 1.0
            val = synth(t)
            clamped = max(-1.0, min(1.0, val * env * volume))
            samples.append(int(clamped * 32767))

        return pygame.mixer.Sound(buffer=samples.tobytes())

    def _tone(self, freq_start, freq_end, duration_ms=180, volume=0.55, overtone=0.0, vibrato=0.0):
        duration_s = duration_ms / 1000

        def synth(t):
            p = min(1.0, t / max(0.001, duration_s))
            freq = freq_start + (freq_end - freq_start) * p
            if vibrato > 0:
                freq += math.sin(2 * math.pi * 10 * t) * vibrato
            base = math.sin(2 * math.pi * freq * t)
            if overtone > 0:
                base += overtone * math.sin(2 * math.pi * (freq * 2.0) * t)
            return base / (1.0 + overtone)

        return self._make_wave(duration_ms, synth, volume=volume)

    def _noise_burst(self, duration_ms=150, volume=0.4):
        def synth(_t):
            return random.uniform(-1.0, 1.0)

        return self._make_wave(duration_ms, synth, volume=volume)

    def _mix(self, *sounds):
        if not sounds:
            return None
        lengths = [s.get_length() for s in sounds]
        total_ms = int(max(lengths) * 1000)
        sample_count = max(1, int(self.sample_rate * total_ms / 1000))
        mixed = array("h", [0] * sample_count)

        for sound in sounds:
            raw = array("h", sound.get_raw())
            for i, v in enumerate(raw):
                if i >= sample_count:
                    break
                nv = mixed[i] + v
                mixed[i] = max(-32768, min(32767, nv))
        return pygame.mixer.Sound(buffer=mixed.tobytes())

    def _build_spell_sounds(self):
        fire = self._mix(
            self._tone(220, 110, duration_ms=170, volume=0.45, overtone=0.35),
            self._noise_burst(duration_ms=120, volume=0.14),
        )
        frost = self._tone(980, 420, duration_ms=190, volume=0.43, vibrato=6.0)
        lightning = self._mix(
            self._tone(1800, 340, duration_ms=90, volume=0.6, overtone=0.45),
            self._noise_burst(duration_ms=75, volume=0.18),
        )
        arcane = self._tone(520, 860, duration_ms=140, volume=0.45, overtone=0.2, vibrato=4.0)
        drain = self._tone(420, 170, duration_ms=210, volume=0.44, overtone=0.3)
        shield = self._tone(300, 700, duration_ms=180, volume=0.38, vibrato=5.0)
        blink = self._tone(1400, 260, duration_ms=130, volume=0.42, overtone=0.25)
        counter = self._mix(
            self._tone(1200, 900, duration_ms=120, volume=0.45),
            self._tone(900, 1200, duration_ms=120, volume=0.34),
        )
        heal = self._tone(300, 720, duration_ms=220, volume=0.36, overtone=0.15)
        phoenix = self._mix(
            self._tone(540, 980, duration_ms=180, volume=0.42, overtone=0.25),
            self._noise_burst(duration_ms=110, volume=0.1),
        )
        minotaur = self._tone(130, 95, duration_ms=210, volume=0.5, overtone=0.35)
        griffin = self._tone(700, 1020, duration_ms=170, volume=0.37, overtone=0.22)
        whelp = self._mix(
            self._tone(420, 640, duration_ms=130, volume=0.33),
            self._noise_burst(duration_ms=90, volume=0.08),
        )
        golem = self._tone(90, 70, duration_ms=240, volume=0.56, overtone=0.18)

        self._sounds = {
            "Fireball": fire,
            "Frost Bolt": frost,
            "Lightning": lightning,
            "Arcane Missile": arcane,
            "Mana Drain": drain,
            "Shield": shield,
            "Blink": blink,
            "Counterspell": counter,
            "Heal": heal,
            "Phoenix Dive": phoenix,
            "Minotaur": minotaur,
            "Griffin": griffin,
            "Dragon Whelp": whelp,
            "Golem Guard": golem,
        }

    def play_spell(self, spell_name):
        if not self.enabled:
            return
        sound = self._sounds.get(spell_name)
        if sound is not None:
            sound.play()
