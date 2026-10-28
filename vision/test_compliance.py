"""Uji aturan kepatuhan dengan kotak buatan. Jalankan: .venv\\Scripts\\python vision/test_compliance.py"""

from compliance import Box, ComplianceTracker, assign_ppe, in_roi

PERSON_A = Box(100, 100, 200, 400)  # tinggi 300: kepala y 100-205, badan y 145-325
PERSON_B = Box(300, 100, 400, 400)


def test_full_ppe():
    r = assign_ppe([PERSON_A], [Box(130, 95, 170, 130)], [Box(110, 180, 190, 300)])
    assert r == [{"helmet": True, "vest": True}]


def test_missing_vest():
    r = assign_ppe([PERSON_A], [Box(130, 95, 170, 130)], [])
    assert r == [{"helmet": True, "vest": False}]


def test_helmet_held_in_hand_does_not_count():
    # helm dipegang di pinggang (pusat y = 290, area badan bawah) bukan di kepala
    r = assign_ppe([PERSON_A], [Box(180, 270, 220, 310)], [Box(110, 180, 190, 300)])
    assert r[0]["helmet"] is False


def test_ppe_goes_to_nearest_person_only():
    # dua orang, satu helm milik B; A tidak boleh ikut dianggap memakai helm
    r = assign_ppe([PERSON_A, PERSON_B], [Box(330, 95, 370, 130)], [])
    assert r[0]["helmet"] is False and r[1]["helmet"] is True


def test_roi_uses_feet_point():
    roi = [(0.0, 0.5), (0.5, 0.5), (0.5, 1.0), (0.0, 1.0)]  # kuadran kiri bawah
    assert in_roi(PERSON_A, roi, 800, 600)      # kaki (150, 400) -> (0.19, 0.67)
    assert not in_roi(PERSON_B, roi, 300, 600)  # kaki (350, 400) -> (1.17, 0.67)


def test_vote_smooths_flicker_and_timer():
    t = ComplianceTracker()
    for i in range(6):
        s = t.update(1, True, True, now=i * 0.5)
    assert s["violation_s"] == 0.0
    s = t.update(1, False, True, now=3.0)       # satu frame helm hilang: mayoritas masih patuh
    assert s["helmet"] is True
    for i in range(8):
        s = t.update(1, False, True, now=3.5 + i * 0.5)
    assert s["helmet"] is False and s["violation_s"] > 0
    t.prune(now=100)
    assert not t.tracks


def test_no_flapping_at_high_fps():
    # Regresi uji video: helm terdeteksi ~1 dari 3 frame pada 35 FPS -> status harus stabil (tidak berkedip)
    t = ComplianceTracker()
    flips, prev = 0, None
    for i in range(140):  # 4 detik
        s = t.update(1, i % 3 == 0, True, now=i / 35)
        if i > 35:
            flips += prev is not None and s["helmet"] != prev
            prev = s["helmet"]
    assert flips == 0 and prev is False


if __name__ == "__main__":
    tests = [v for k, v in dict(globals()).items() if k.startswith("test_")]
    for fn in tests:
        fn()
        print(f"PASS {fn.__name__}")
    print(f"{len(tests)}/{len(tests)} lulus")
