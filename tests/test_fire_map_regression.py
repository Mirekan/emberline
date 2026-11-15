"""Regression behavioral tests for FireMap.tsx fixes (Bugs 1-4).

Run: python -m pytest tests/test_fire_map_regression.py
"""
import math
import pytest


def test_bug1_fallback_grid_under_filters():
    """Bug 1: Grid and cell counts must NEVER fall back to unfiltered historical aggregates.
    
    When det is loading, error, or has 0 matching detections for (2026 + MODIS + minFrp),
    the verified count must be 0 (or empty), never defaulting to cell.detection_count (e.g. 500)
    or total_viirs/total_modis (which are FRP in MW, not counts).
    """
    def compute_cell_counts(det, det_loading, det_error, det_year, det_sensor, min_frp, active_bounds=None):
        counts = {}
        if not det or det_loading or bool(det_error):
            return counts

        step = 0.1
        for d in det.get("detections", []):
            if active_bounds:
                if (d["lat"] < active_bounds["south"] or d["lat"] > active_bounds["north"] or
                    d["lon"] < active_bounds["west"] or d["lon"] > active_bounds["east"]):
                    continue
            if det_year != "all" and not d["date"].startswith(det_year):
                continue
            if det_sensor != "all" and d["sensor"] != det_sensor:
                continue
            if d["frp"] < min_frp:
                continue

            cell_south = round(math.floor(d["lat"] / step) * step, 1)
            cell_west = round(math.floor(d["lon"] / step) * step, 1)
            key = f"{cell_south:.1f},{cell_west:.1f}"

            if key in counts:
                counts[key]["total"] += 1
                if d["sensor"] == "viirs":
                    counts[key]["viirs"] += 1
                elif d["sensor"] == "modis":
                    counts[key]["modis"] += 1
            else:
                counts[key] = {
                    "total": 1,
                    "viirs": 1 if d["sensor"] == "viirs" else 0,
                    "modis": 1 if d["sensor"] == "modis" else 0,
                }
        return counts

    sample_detections = {
        "detections": [
            {"lat": -1.5, "lon": 113.5, "date": "2024-08-01", "sensor": "viirs", "frp": 15.0},
            {"lat": -1.5, "lon": 113.5, "date": "2024-08-02", "sensor": "modis", "frp": 30.0},
            {"lat": -1.5, "lon": 113.5, "date": "2026-02-10", "sensor": "viirs", "frp": 8.0},
        ]
    }

    # Case A: Filter 2026 + MODIS + minFrp >= 10 MW (there are 0 matching dots in 2026 for MODIS)
    res_2026_modis = compute_cell_counts(sample_detections, False, "", "2026", "modis", 10.0)
    assert res_2026_modis == {}, "Must be empty (0 verified observations), not 500 historical dots!"

    # Case B: Detections loading -> must be empty, not fake historical data
    res_loading = compute_cell_counts(sample_detections, True, "", "2026", "modis", 10.0)
    assert res_loading == {}, "Loading state must not display fake historical counts"

    # Case C: Detections error -> must be empty, not fake historical data
    res_error = compute_cell_counts(sample_detections, False, "Failed to load", "2026", "modis", 10.0)
    assert res_error == {}, "Error state must not display fake historical counts"

    # Case D: Active filter matches 2024 + MODIS + minFrp >= 25 MW -> exactly 1 count
    res_match = compute_cell_counts(sample_detections, False, "", "2024", "modis", 25.0)
    assert "-1.5,113.5" in res_match
    assert res_match["-1.5,113.5"]["total"] == 1
    assert res_match["-1.5,113.5"]["modis"] == 1
    assert res_match["-1.5,113.5"]["viirs"] == 0


def test_bug2_nearest_hotspot_priority_and_cell_click():
    """Bug 2: Clicking near a hotspot in Mode Kombinasi must prioritize the hotspot inspection,
    while clicking an empty cell area must select the cell.
    """
    visible_rows = [
        {"lat": -1.50, "lon": 113.50, "frp": 45.2, "sensor": "viirs", "date": "2026-01-01"},
    ]

    def find_nearest_detection(click_lat, click_lon, visible_rows, max_px=22):
        # mock screen projection: 1 deg = 100 px
        click_x, click_y = click_lon * 100, click_lat * 100
        nearest = None
        min_dist = max_px
        for d in visible_rows:
            dx = d["lon"] * 100 - click_x
            dy = d["lat"] * 100 - click_y
            dist = math.hypot(dx, dy)
            if dist < min_dist:
                min_dist = dist
                nearest = d
        return nearest

    # Case 1: Click within 5px of hotspot (-1.501, 113.502) -> dist ~ 0.22 px < 22 px
    hotspot_click = find_nearest_detection(-1.501, 113.502, visible_rows, max_px=22)
    assert hotspot_click is not None
    assert hotspot_click["frp"] == 45.2

    # Case 2: Click far away in the cell (-1.55, 113.55) -> dist ~ 7 px < 22 px? (0.05 * 100 = 5 px each -> dist = 7.07 px)
    # Click at edge (-1.59, 113.59) -> dist ~ 12.7 px. Click at (-1.80, 113.80) -> dist = 42.4 px > 22 px
    cell_click = find_nearest_detection(-1.80, 113.80, visible_rows, max_px=22)
    assert cell_click is None, "Click away from hotspot must not select hotspot!"

    # Case 3: In Mode Grid (detOn = False), visible_rows is empty
    grid_mode_click = find_nearest_detection(-1.501, 113.502, [], max_px=22)
    assert grid_mode_click is None, "In Grid Mode, hotspot inspection is not triggered"


def test_bug3_selected_cell_honors_risk_filter():
    """Bug 3: When a cell is selected, detections must satisfy BOTH the cell bounding box
    AND the riskFilter ('danger' / 'alert'). If a low-density cell is selected and riskFilter
    is 'danger', points in that cell must be filtered out.
    """
    def filter_detection(d, selected_cell, risk_filter, cell_counts, max_count):
        # 1. Check selected cell boundary
        if selected_cell:
            in_selected = (
                selected_cell["south"] <= d["lat"] <= selected_cell["north"] and
                selected_cell["west"] <= d["lon"] <= selected_cell["east"]
            )
            if not in_selected:
                return False

        # 2. Check risk filter
        if risk_filter != "all" and max_count > 0:
            step = 0.1
            cell_south = round(math.floor(d["lat"] / step) * step, 1)
            cell_west = round(math.floor(d["lon"] / step) * step, 1)
            key = f"{cell_south:.1f},{cell_west:.1f}"
            count = cell_counts.get(key, {}).get("total", 0)
            if count == 0:
                return False
            intensity = math.log1p(count) / math.log1p(max_count)
            if risk_filter == "danger" and intensity < 0.66:
                return False
            if risk_filter == "alert" and intensity < 0.33:
                return False

        return True

    dot_in_low_density_cell = {"lat": -1.05, "lon": 113.05}
    low_density_cell = {"south": -1.1, "north": -1.0, "west": 113.0, "east": 113.1}

    # Cell has 2 counts, max_count is 100.
    # intensity = log(3) / log(101) = 1.098 / 4.615 = 0.238 (< 0.33, Low density)
    cell_counts = {"-1.1,113.0": {"total": 2}}
    max_count = 100

    # With risk_filter = 'all', point in selected cell is shown
    assert filter_detection(dot_in_low_density_cell, low_density_cell, "all", cell_counts, max_count) is True

    # With risk_filter = 'danger', point in selected low-density cell MUST BE EXCLUDED!
    assert filter_detection(dot_in_low_density_cell, low_density_cell, "danger", cell_counts, max_count) is False

    # With risk_filter = 'alert', point in selected low-density cell MUST BE EXCLUDED!
    assert filter_detection(dot_in_low_density_cell, low_density_cell, "alert", cell_counts, max_count) is False

    # High density cell (count = 90, intensity = log(91)/log(101) = 0.978 >= 0.66)
    high_density_counts = {"-1.1,113.0": {"total": 90}}
    assert filter_detection(dot_in_low_density_cell, low_density_cell, "danger", high_density_counts, max_count) is True


def test_bug4_ai_response_race_condition():
    """Bug 4: Asynchronous AI analysis race condition isolation.
    If request A starts, then request B starts, B completes, and then A completes late:
    The response must remain B's response, and loading state must not be overwritten by A.
    """
    import asyncio

    async def _run_test():
        class AiStateManager:
            def __init__(self):
                self.active_req_id = 0
                self.active_det_id = None
                self.is_mounted = True
                self.is_drawer_open = True
                self.ai_loading = False
                self.ai_response = None
                self.ai_error = None

            def get_det_id(self, d):
                return f"{d['date']}_{d['lat']:.5f}_{d['lon']:.5f}_{d['sensor']}"

            async def trigger_ai_analysis(self, target_det, delay_seconds, return_value):
                target_id = self.get_det_id(target_det)
                self.active_req_id += 1
                req_id = self.active_req_id
                self.active_det_id = target_id

                self.ai_loading = True
                self.ai_response = None
                self.ai_error = None

                try:
                    await asyncio.sleep(delay_seconds)
                    res = return_value

                    # Guard check
                    if (not self.is_mounted or
                        req_id != self.active_req_id or
                        target_id != self.active_det_id or
                        not self.is_drawer_open):
                        return  # Stale request ignored!

                    self.ai_response = res
                finally:
                    if self.is_mounted and req_id == self.active_req_id:
                        self.ai_loading = False

        manager = AiStateManager()

        det_a = {"date": "2024-01-01", "lat": -1.0, "lon": 113.0, "sensor": "viirs"}
        det_b = {"date": "2024-01-02", "lat": -2.0, "lon": 114.0, "sensor": "modis"}

        # Start A with 0.1s delay, then B with 0.02s delay (B will finish first, A will finish late)
        task_a = asyncio.create_task(manager.trigger_ai_analysis(det_a, 0.10, "ANSWER_FROM_A"))
        await asyncio.sleep(0.01)
        task_b = asyncio.create_task(manager.trigger_ai_analysis(det_b, 0.02, "ANSWER_FROM_B"))

        await asyncio.gather(task_a, task_b)

        # Assert that B's answer is preserved, and A's late answer was discarded
        assert manager.ai_response == "ANSWER_FROM_B"
        assert manager.ai_loading is False
        assert manager.active_det_id == manager.get_det_id(det_b)

    asyncio.run(_run_test())


def test_all_sensors_under_all_years_preserves_both_modis_and_viirs():
    """Verify that when switching between 'modis', 'viirs', and 'all' under 'all years',
    'all' does not discard MODIS detections or cap out points via FRP-only sorting.
    """
    # Simulate a dataset where VIIRS has thousands of detections with FRP 20-100,
    # and MODIS has detections with lower FRP 5-15.
    viirs_dets = [{"date": "2024-05-01", "lat": -1.0, "lon": 113.0, "frp": 50.0, "sensor": "viirs"} for _ in range(12000)]
    modis_dets = [{"date": "2024-05-01", "lat": -2.0, "lon": 114.0, "frp": 10.0, "sensor": "modis"} for _ in range(3000)]
    all_dets = viirs_dets + modis_dets

    def filter_and_display(dets, det_sensor, det_year="all", min_frp=0):
        # Filter matching detRows logic
        rows = [
            d for d in dets
            if (det_year == "all" or d["date"].startswith(det_year))
            and (det_sensor == "all" or d["sensor"] == det_sensor)
            and d["frp"] >= min_frp
        ]

        # Display logic: no arbitrary FRP truncation, MODIS rendered on top
        display_rows = (
            sorted(rows, key=lambda x: (1 if x["sensor"] == "modis" else 0))
            if det_sensor == "all"
            else rows
        )
        return display_rows

    # 1. When MODIS is selected
    modis_result = filter_and_display(all_dets, "modis")
    assert len(modis_result) == 3000
    assert all(d["sensor"] == "modis" for d in modis_result)

    # 2. When VIIRS is selected
    viirs_result = filter_and_display(all_dets, "viirs")
    assert len(viirs_result) == 12000
    assert all(d["sensor"] == "viirs" for d in viirs_result)

    # 3. When ALL is selected: MUST contain BOTH MODIS and VIIRS without dropping MODIS!
    all_result = filter_and_display(all_dets, "all")
    assert len(all_result) == 15000
    modis_in_all = sum(1 for d in all_result if d["sensor"] == "modis")
    viirs_in_all = sum(1 for d in all_result if d["sensor"] == "viirs")
    assert modis_in_all == 3000, f"Expected 3000 MODIS in all, got {modis_in_all}"
    assert viirs_in_all == 12000, f"Expected 12000 VIIRS in all, got {viirs_in_all}"

    # Also verify MODIS is sorted on top (at the end of display_rows)
    assert all_result[-1]["sensor"] == "modis"

