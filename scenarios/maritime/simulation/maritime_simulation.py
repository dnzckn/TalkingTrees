"""Maritime Threat Detection Simulation.

Synthetic sensor data generator and response simulator.
All randomness seeded for reproducibility. No real hardware or network.

Generates hydrophone acoustic events, classification results, radar tracks,
and response decisions for a coastal monitoring scenario.
"""

import math
import time
from dataclasses import dataclass, field
from typing import Any

import numpy as np


@dataclass
class Target:
    """A simulated maritime target with trajectory and acoustic signature."""

    target_id: str
    target_type: str  # "hostile", "cargo", "fishing", "wildlife"
    trajectory: list[dict] = field(default_factory=list)
    acoustic_signature: dict = field(default_factory=dict)
    is_threat: bool = False

    def position_at(self, time_s: float) -> dict | None:
        """Interpolate position at given time."""
        if not self.trajectory:
            return None
        # Find bracketing waypoints
        before = None
        after = None
        for wp in self.trajectory:
            if wp["time_s"] <= time_s:
                before = wp
            if wp["time_s"] >= time_s and after is None:
                after = wp
        if before is None:
            return None
        if after is None or before is after:
            return before
        # Linear interpolation
        t = (time_s - before["time_s"]) / max(after["time_s"] - before["time_s"], 0.001)
        return {
            "lat": before["lat"] + t * (after["lat"] - before["lat"]),
            "lon": before["lon"] + t * (after["lon"] - before["lon"]),
            "heading": after.get("heading", 0),
            "speed_kts": before.get("speed_kts", 0),
        }

    def acoustic_at(
        self, time_s: float, observer_lat: float, observer_lon: float, rng
    ) -> dict | None:
        """Return acoustic event as seen from observer, or None if too quiet."""
        pos = self.position_at(time_s)
        if pos is None:
            return None

        dist_km = _haversine_km(observer_lat, observer_lon, pos["lat"], pos["lon"])
        if dist_km < 0.01:
            dist_km = 0.01

        # Transmission loss (spherical spreading + absorption)
        source_level = self.acoustic_signature.get("source_level_db", 140)
        tl = 20 * math.log10(dist_km * 1000) + 0.5 * dist_km  # rough TL model
        received_level = source_level - tl

        if received_level < 40:  # below any practical detection
            return None

        bearing = _bearing_deg(observer_lat, observer_lon, pos["lat"], pos["lon"])

        return {
            "received_level_db": received_level,
            "bearing_deg": bearing,
            "frequency_peak_hz": self.acoustic_signature.get("frequency_peak_hz", 200),
            "bandwidth_hz": self.acoustic_signature.get("bandwidth_hz", 100),
        }


@dataclass
class Hydrophone:
    """A simulated underwater acoustic sensor node."""

    node_id: str
    lat: float
    lon: float
    noise_floor_db: float = 45.0
    detection_threshold_db: float = 55.0


@dataclass
class RestrictedZone:
    """Polygon defining restricted waters."""

    vertices: list[tuple[float, float]] = field(default_factory=list)

    def contains(self, lat: float, lon: float) -> bool:
        """Ray-casting point-in-polygon test."""
        n = len(self.vertices)
        if n < 3:
            return False
        inside = False
        j = n - 1
        for i in range(n):
            yi, xi = self.vertices[i]
            yj, xj = self.vertices[j]
            if ((yi > lon) != (yj > lon)) and (lat < (xj - xi) * (lon - yi) / (yj - yi) + xi):
                inside = not inside
            j = i
        return inside


# Confusion matrices for acoustic classification
CONFUSION_MATRIX = {
    "vessel": {"vessel": 0.88, "wildlife": 0.04, "noise": 0.05, "miss": 0.03},
    "wildlife": {"vessel": 0.05, "wildlife": 0.85, "noise": 0.05, "miss": 0.05},
    "noise": {"vessel": 0.03, "wildlife": 0.02, "noise": 0.90, "miss": 0.05},
}


class MaritimeSimulator:
    """Generates synthetic sensor events for the maritime threat detection scenario.

    Fully deterministic given a seed. No real hardware or network required.
    """

    def __init__(self, seed: int = 42):
        self.rng = np.random.default_rng(seed)
        self.targets: list[Target] = []
        self.hydrophones: list[Hydrophone] = []
        self.zone = RestrictedZone(
            vertices=[
                (38.92, -76.35),
                (38.92, -76.30),
                (38.90, -76.30),
                (38.90, -76.35),
            ]
        )
        self.time_s = 0.0
        self.radar_online = True

        self._setup_hydrophones()
        self._setup_targets()

    def _setup_hydrophones(self):
        """Place 12 hydrophones along coastline."""
        base_lat, base_lon = 38.91, -76.36
        for i in range(12):
            self.hydrophones.append(
                Hydrophone(
                    node_id=f"hydrophone_{i:02d}",
                    lat=base_lat + (i * 0.002),
                    lon=base_lon + float(self.rng.uniform(-0.005, 0.005)),
                )
            )

    def _setup_targets(self):
        """Generate ground truth targets with trajectories."""
        # Hostile vessel: approaches from east, enters zone at ~t=65s
        self.targets.append(
            Target(
                target_id="hostile_01",
                target_type="hostile",
                trajectory=self._linear_trajectory(
                    start_time=0,
                    end_time=300,
                    start_pos=(38.91, -76.25),
                    end_pos=(38.91, -76.38),
                    speed_kts=8.0,
                ),
                acoustic_signature={
                    "frequency_peak_hz": 340,
                    "bandwidth_hz": 120,
                    "source_level_db": 155,
                },
                is_threat=True,
            )
        )

        # Cargo ships
        for i in range(2):
            self.targets.append(
                Target(
                    target_id=f"cargo_{i:02d}",
                    target_type="cargo",
                    trajectory=self._linear_trajectory(
                        start_time=20 + i * 30,
                        end_time=280,
                        start_pos=(38.895, -76.40),
                        end_pos=(38.895, -76.20),
                        speed_kts=12.0,
                    ),
                    acoustic_signature={
                        "frequency_peak_hz": 120,
                        "bandwidth_hz": 200,
                        "source_level_db": 170,
                    },
                )
            )

        # Fishing boats
        for i in range(3):
            center_lat = 38.915 + i * 0.003
            center_lon = -76.34 + i * 0.002
            self.targets.append(
                Target(
                    target_id=f"fishing_{i:02d}",
                    target_type="fishing",
                    trajectory=self._loiter_trajectory(
                        center_lat, center_lon, radius_km=0.5, start_time=10 + i * 20
                    ),
                    acoustic_signature={
                        "frequency_peak_hz": 450,
                        "bandwidth_hz": 80,
                        "source_level_db": 140,
                    },
                )
            )

        # Marine wildlife
        for i in range(10):
            start_lat = 38.90 + float(self.rng.uniform(0, 0.03))
            start_lon = -76.36 + float(self.rng.uniform(0, 0.08))
            self.targets.append(
                Target(
                    target_id=f"wildlife_{i:02d}",
                    target_type="wildlife",
                    trajectory=self._random_walk(start_lat, start_lon, speed_kts=3.0),
                    acoustic_signature={
                        "frequency_peak_hz": 800 + int(self.rng.integers(0, 2000)),
                        "bandwidth_hz": 50,
                        "source_level_db": 130,
                    },
                )
            )

    def _linear_trajectory(self, start_time, end_time, start_pos, end_pos, speed_kts):
        steps = max(int(end_time - start_time), 2)
        return [
            {
                "time_s": start_time + i * (end_time - start_time) / steps,
                "lat": start_pos[0] + i * (end_pos[0] - start_pos[0]) / steps,
                "lon": start_pos[1] + i * (end_pos[1] - start_pos[1]) / steps,
                "heading": _bearing_deg(start_pos[0], start_pos[1], end_pos[0], end_pos[1]),
                "speed_kts": speed_kts,
            }
            for i in range(steps + 1)
        ]

    def _loiter_trajectory(self, center_lat, center_lon, radius_km, start_time):
        waypoints = []
        for t in range(int(start_time), 300, 5):
            angle = (t - start_time) * 0.1  # slow circle
            dlat = (radius_km / 111.0) * math.cos(angle)
            dlon = (radius_km / (111.0 * math.cos(math.radians(center_lat)))) * math.sin(angle)
            waypoints.append({
                "time_s": float(t),
                "lat": center_lat + dlat,
                "lon": center_lon + dlon,
                "heading": math.degrees(angle + math.pi / 2) % 360,
                "speed_kts": 3.0,
            })
        return waypoints

    def _random_walk(self, start_lat, start_lon, speed_kts):
        waypoints = []
        lat, lon = start_lat, start_lon
        for t in range(0, 300, 10):
            dlat = float(self.rng.normal(0, 0.001))
            dlon = float(self.rng.normal(0, 0.001))
            lat += dlat
            lon += dlon
            waypoints.append({
                "time_s": float(t),
                "lat": lat,
                "lon": lon,
                "heading": float(self.rng.uniform(0, 360)),
                "speed_kts": speed_kts,
            })
        return waypoints

    # ── Simulated sensor responses ──

    def hydrophone_scan(self, node_id: str, time_s: float) -> list[dict]:
        """Return acoustic events detected by a specific hydrophone at given time."""
        hydrophone = next(h for h in self.hydrophones if h.node_id == node_id)
        detections = []

        for target in self.targets:
            event = target.acoustic_at(time_s, hydrophone.lat, hydrophone.lon, self.rng)
            if event and event["received_level_db"] > hydrophone.detection_threshold_db:
                detections.append({
                    "node_id": node_id,
                    "timestamp": time_s,
                    "acoustic_energy_db": round(event["received_level_db"] + float(self.rng.normal(0, 2)), 1),
                    "bearing_deg": round(event["bearing_deg"] + float(self.rng.normal(0, 3)), 1),
                    "frequency_peak_hz": round(event["frequency_peak_hz"] + float(self.rng.normal(0, 20)), 0),
                    "bandwidth_hz": event["bandwidth_hz"],
                    "duration_ms": round(float(self.rng.uniform(200, 800)), 0),
                    "_ground_truth_target": target.target_id,
                })

        # Environmental false alarms
        if float(self.rng.random()) < 0.1:
            detections.append({
                "node_id": node_id,
                "timestamp": time_s,
                "acoustic_energy_db": round(hydrophone.noise_floor_db + float(self.rng.uniform(5, 15)), 1),
                "bearing_deg": round(float(self.rng.uniform(0, 360)), 1),
                "frequency_peak_hz": round(float(self.rng.uniform(50, 2000)), 0),
                "bandwidth_hz": round(float(self.rng.uniform(10, 500)), 0),
                "duration_ms": round(float(self.rng.uniform(50, 300)), 0),
                "_ground_truth_target": None,
            })

        return detections

    def classify_acoustic(self, acoustic_energy_db: float, frequency_peak_hz: float, **kwargs) -> dict:
        """Simulated acoustic classifier using confusion matrix."""
        ground_truth = kwargs.get("_ground_truth_target")

        if ground_truth is None:
            true_class = "noise"
        else:
            target = next((t for t in self.targets if t.target_id == ground_truth), None)
            if target is None:
                true_class = "noise"
            elif target.target_type in ("hostile", "cargo", "fishing"):
                true_class = "vessel"
            elif target.target_type == "wildlife":
                true_class = "wildlife"
            else:
                true_class = "noise"

        probs = CONFUSION_MATRIX[true_class]
        predicted = str(self.rng.choice(list(probs.keys()), p=list(probs.values())))
        if predicted == "miss":
            predicted = "noise"

        confidence = float(
            self.rng.uniform(0.75, 0.98) if predicted == true_class else self.rng.uniform(0.40, 0.80)
        )

        return {
            "classification": predicted,
            "confidence": round(confidence, 3),
            "_ground_truth": true_class,
        }

    def radar_track(self, bearing_deg: float, time_s: float, **kwargs) -> dict:
        """Simulated radar track acquisition."""
        if not self.radar_online:
            return {"track_id": None, "status": "no_track", "radar_offline": True}

        ground_truth = kwargs.get("_ground_truth_target")
        if ground_truth is None:
            return {"track_id": None, "status": "no_track"}

        target = next((t for t in self.targets if t.target_id == ground_truth), None)
        if target is None:
            return {"track_id": None, "status": "no_track"}

        pos = target.position_at(time_s)
        if pos is None:
            return {"track_id": None, "status": "no_track"}

        in_zone = self.zone.contains(pos["lat"], pos["lon"])

        return {
            "track_id": f"TRK-{ground_truth}",
            "status": "confirmed",
            "lat": pos["lat"] + float(self.rng.normal(0, 0.00015)),
            "lon": pos["lon"] + float(self.rng.normal(0, 0.00015)),
            "heading_deg": pos["heading"] + float(self.rng.normal(0, 3)),
            "speed_kts": pos["speed_kts"] + float(self.rng.normal(0, 0.5)),
            "in_restricted_zone": in_zone,
            "track_quality": round(float(self.rng.uniform(0.85, 0.99)), 2),
        }

    def point_in_zone(self, lat: float, lon: float) -> bool:
        return self.zone.contains(lat, lon)

    # ── Simulation runner ──

    def run(
        self,
        duration_s: float = 300,
        realtime_factor: float = 10.0,
        event_callback=None,
        failure_schedule: dict | None = None,
    ):
        """Run the full simulation.

        Args:
            duration_s: Total simulation time in seconds
            realtime_factor: Speed multiplier (10 = 10x faster)
            event_callback: Called with (event_type, event_data)
            failure_schedule: {time_s: failure_event}
        """
        if failure_schedule is None:
            failure_schedule = {
                60: {"type": "radar_offline"},
                120: {"type": "radar_online"},
                200: {"type": "event_burst", "count": 30},
            }

        dt = 1.0 / realtime_factor
        self.time_s = 0.0

        while self.time_s < duration_s:
            # Check failure schedule
            for trigger_time, failure in failure_schedule.items():
                if abs(self.time_s - trigger_time) < 1.0 and self.time_s >= trigger_time:
                    if failure["type"] == "radar_offline":
                        self.radar_online = False
                    elif failure["type"] == "radar_online":
                        self.radar_online = True

                    if event_callback:
                        event_callback("failure_injection", {"time_s": self.time_s, **failure})

            # Generate hydrophone events
            for hydrophone in self.hydrophones:
                detections = self.hydrophone_scan(hydrophone.node_id, self.time_s)
                for detection in detections:
                    if event_callback:
                        event_callback("hydrophone_detection", detection)

            self.time_s += 1.0
            time.sleep(dt)


def _haversine_km(lat1, lon1, lat2, lon2):
    """Haversine distance in km."""
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _bearing_deg(lat1, lon1, lat2, lon2):
    """Bearing from point 1 to point 2 in degrees."""
    dlon = math.radians(lon2 - lon1)
    y = math.sin(dlon) * math.cos(math.radians(lat2))
    x = math.cos(math.radians(lat1)) * math.sin(math.radians(lat2)) - math.sin(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.cos(dlon)
    return (math.degrees(math.atan2(y, x)) + 360) % 360
