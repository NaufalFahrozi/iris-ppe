"""Aturan kepatuhan APD IRIS: kaitkan helm & rompi ke orang berdasarkan posisi kotak (tanpa kelas "no-helmet").

Kotak dalam piksel (x1, y1, x2, y2). Kelas model: 0 person, 1 head, 2 helmet, 3 safety-vest.
"""

from collections import deque
from dataclasses import dataclass, field

PERSON, HEAD, HELMET, VEST = 0, 1, 2, 3

# Area relatif terhadap kotak orang (0 = atas, 1 = bawah)
HELMET_TOP_ZONE = (-0.1, 0.2)  # tepi atas helm harus di sini (helm dipakai = di puncak kepala)
TORSO_ZONE = (0.15, 0.75)      # pusat rompi harus di sini
# Helm memakai tepi atas, bukan pusat: kotak helm sebagian dataset membungkus seluruh kepala, sehingga pada close-up
# (kepala memenuhi separuh kotak orang) pusatnya jatuh di bawah area kepala walau helm jelas dipakai.


@dataclass
class Box:
    x1: float
    y1: float
    x2: float
    y2: float
    conf: float = 1.0

    @property
    def cx(self): return (self.x1 + self.x2) / 2

    @property
    def cy(self): return (self.y1 + self.y2) / 2

    @property
    def w(self): return self.x2 - self.x1

    @property
    def h(self): return self.y2 - self.y1


def _inside_zone(item: Box, person: Box, zone: tuple[float, float], margin: float = 0.1, use_top: bool = False) -> bool:
    """Pusat item (atau tepi atasnya jika use_top) berada dalam rentang vertikal `zone` dan horizontal kotak orang."""
    rel_y = ((item.y1 if use_top else item.cy) - person.y1) / max(person.h, 1e-6)
    in_x = person.x1 - margin * person.w <= item.cx <= person.x2 + margin * person.w
    return in_x and zone[0] <= rel_y <= zone[1]


def assign_ppe(persons: list[Box], helmets: list[Box], vests: list[Box]) -> list[dict]:
    """Untuk tiap orang: apakah ada helm di area kepala dan rompi di area badan.

    Satu item APD hanya diberikan ke satu orang (yang pusatnya paling dekat), agar orang tanpa helm yang berdiri di
    belakang orang berhelm tidak ikut dianggap patuh.
    """
    result = [{"helmet": False, "vest": False} for _ in persons]
    for items, key, zone, use_top in ((helmets, "helmet", HELMET_TOP_ZONE, True), (vests, "vest", TORSO_ZONE, False)):
        for it in items:
            candidates = [i for i, p in enumerate(persons) if _inside_zone(it, p, zone, use_top=use_top)]
            if not candidates:
                continue
            best = min(candidates, key=lambda i: (persons[i].cx - it.cx) ** 2 + (persons[i].cy - it.cy) ** 2)
            result[best][key] = True
    return result


def in_roi(person: Box, roi: list[tuple[float, float]] | None, width: int, height: int) -> bool:
    """Titik kaki orang (tengah bawah kotak) di dalam poligon ROI (koordinat ternormalisasi 0..1)."""
    if not roi:
        return True
    x, y = person.cx / width, person.y2 / height
    inside = False
    for (x1, y1), (x2, y2) in zip(roi, roi[1:] + roi[:1]):
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1 + 1e-12) + x1:
            inside = not inside
    return inside


VOTE_WINDOW_S = 1.0  # status APD = mayoritas deteksi dalam jendela waktu ini (tidak bergantung FPS)
MIN_TRACK_AGE_S = 1.0  # orang baru dihitung setelah terlihat selama ini (deteksi palsu sesaat, mis. benda di tepi frame)


@dataclass
class TrackState:
    """Riwayat per track ID: voting dalam jendela waktu agar status tidak berkedip, plus timer pelanggaran."""
    history: deque = field(default_factory=deque)  # (waktu, helm, rompi)
    violation_since: float | None = None
    last_seen: float = 0.0
    first_seen: float | None = None

    def update(self, helmet: bool, vest: bool, now: float, window_s: float = VOTE_WINDOW_S) -> dict:
        self.history.append((now, helmet, vest))
        while self.history and now - self.history[0][0] > window_s:
            self.history.popleft()
        self.last_seen = now
        if self.first_seen is None:
            self.first_seen = now
        n = len(self.history)
        h = sum(x[1] for x in self.history) * 2 >= n  # mayoritas (seri dianggap patuh)
        v = sum(x[2] for x in self.history) * 2 >= n
        if h and v:
            self.violation_since = None
        elif self.violation_since is None:
            self.violation_since = now
        return {"helmet": h, "vest": v,
                "violation_s": 0.0 if self.violation_since is None else round(now - self.violation_since, 1),
                "confirmed": now - self.first_seen >= MIN_TRACK_AGE_S}


class ComplianceTracker:
    """Kumpulan TrackState per ID; track yang hilang lebih dari `forget_s` dibuang.

    Jika tracker memberi ID baru untuk orang yang sama (ID switch, sering terjadi pada objek kecil/terhalang), state
    diwariskan dari track yang baru hilang (<= `relink_s`) dan posisinya dekat, agar timer pelanggaran tidak reset.
    """

    def __init__(self, forget_s: float = 3.0, relink_s: float = 1.5, relink_dist: float = 0.6):
        self.tracks: dict[int, TrackState] = {}
        self.where: dict[int, tuple[float, float, float]] = {}  # id -> (cx, cy, tinggi) terakhir
        self.forget_s, self.relink_s, self.relink_dist = forget_s, relink_s, relink_dist

    def _relink(self, track_id: int, box: Box, now: float) -> None:
        best, best_d = None, None
        for tid, st in self.tracks.items():
            if tid == track_id or st.last_seen >= now or now - st.last_seen > self.relink_s or tid not in self.where:
                continue
            cx, cy, h = self.where[tid]
            d = ((cx - box.cx) ** 2 + (cy - box.cy) ** 2) ** 0.5
            if d <= self.relink_dist * max(h, box.h) and (best_d is None or d < best_d):
                best, best_d = tid, d
        if best is not None:
            self.tracks[track_id] = self.tracks.pop(best)
            self.where.pop(best, None)

    def update(self, track_id: int, helmet: bool, vest: bool, now: float, box: Box | None = None) -> dict:
        if track_id not in self.tracks and box is not None:
            self._relink(track_id, box, now)
        state = self.tracks.setdefault(track_id, TrackState())
        if box is not None:
            self.where[track_id] = (box.cx, box.cy, box.h)
        return state.update(helmet, vest, now)

    def prune(self, now: float) -> None:
        for tid in [t for t, s in self.tracks.items() if now - s.last_seen > self.forget_s]:
            del self.tracks[tid]
            self.where.pop(tid, None)
