"""
delf.py

Landmark identification using DELF (local feature matching) + GPS filtering.

Usage:
    python delf.py --lat 27.7215 --lon 85.3620 --image query.jpg

Requires:
    pip install tensorflow tensorflow-hub numpy scipy pillow

Folder structure expected:
    data/landmark_data.json
    data/<landmark_folder>/<image files>

First run will build and cache descriptors to landmark_db.pkl (slow).
Subsequent runs load the cache (fast).
"""

import os
import json
import pickle
import argparse
from math import radians, sin, cos, sqrt, atan2

import numpy as np
import tensorflow as tf
import tensorflow_hub as hub
from PIL import Image
from scipy.spatial import cKDTree

META_PATH = "data/landmark_data.json"
IMAGES_DIR = "data/"
CACHE_PATH = "landmark_db.pkl"

SEARCH_RADIUS_M = 150       # GPS filter radius
MATCH_THRESHOLD = 15        # min matching features to count as a hit
DISTANCE_UPPER_BOUND = 0.8  # descriptor distance cutoff for a valid match

_delf_model = None


def get_delf():
    """Lazy-load the DELF model from TF Hub (downloads once, then cached locally by TF Hub)."""
    global _delf_model
    if _delf_model is None:
        print("Loading DELF model...")
        _delf_model = hub.load("https://tfhub.dev/google/delf/1").signatures["default"]
    return _delf_model


def load_image(path, max_size=800):
    img = Image.open(path).convert("RGB")
    img.thumbnail((max_size, max_size))
    return np.array(img)


def run_delf(image_np):
    delf = get_delf()
    float_image = tf.image.convert_image_dtype(image_np, tf.float32)
    return delf(
        image=float_image,
        score_threshold=tf.constant(100.0),
        image_scales=tf.constant([0.25, 0.3536, 0.5, 0.7071, 1.0, 1.4142, 2.0]),
        max_feature_num=tf.constant(1000),
    )


def haversine(lat1, lon1, lat2, lon2):
    """Distance in meters between two lat/lon points."""
    R = 6371000
    dlat, dlon = radians(lat2 - lat1), radians(lon2 - lon1)
    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    return R * 2 * atan2(sqrt(a), sqrt(1 - a))


def build_landmark_db():
    """Extract DELF descriptors for every reference image, grouped by landmark. Cached to disk."""
    if os.path.exists(CACHE_PATH):
        print(f"Loading cached landmark DB from {CACHE_PATH}")
        with open(CACHE_PATH, "rb") as f:
            return pickle.load(f)

    print("No cache found. Building landmark DB from scratch (this may take a while)...")
    with open(META_PATH) as f:
        meta = json.load(f)

    db = {}
    for landmark_id, info in meta.items():
        landmark_dir = os.path.join(IMAGES_DIR, info["folder"])
        descriptors_per_image = []

        for img_file in info["images"]:
            img_path = os.path.join(landmark_dir, img_file)
            print(f"  extracting features: {img_path}")
            img = load_image(img_path)
            result = run_delf(img)
            descriptors_per_image.append(result["descriptors"].numpy())

        db[landmark_id] = {
            "name": info["name"],
            "description": info["description"],
            "lat": info["lat"],
            "lon": info["lon"],
            "descriptors_per_image": descriptors_per_image,
        }

    with open(CACHE_PATH, "wb") as f:
        pickle.dump(db, f)
    print(f"Saved DB cache to {CACHE_PATH}")
    return db


def get_candidates(db, user_lat, user_lon, radius_m=SEARCH_RADIUS_M):
    return {
        lid: entry
        for lid, entry in db.items()
        if haversine(user_lat, user_lon, entry["lat"], entry["lon"]) <= radius_m
    }


def match_descriptors(query_desc, ref_desc):
    """Count how many query descriptors have a close match in the reference descriptors."""
    if len(ref_desc) == 0 or len(query_desc) == 0:
        return 0
    tree = cKDTree(ref_desc)
    distances, indices = tree.query(query_desc, distance_upper_bound=DISTANCE_UPPER_BOUND)
    return int(np.sum(indices != len(ref_desc)))


def identify_landmark(db, user_lat, user_lon, image_path):
    candidates = get_candidates(db, user_lat, user_lon)
    if not candidates:
        return {"match": False, "reason": "no known landmark within search radius"}

    query_img = load_image(image_path)
    query_result = run_delf(query_img)
    query_descriptors = query_result["descriptors"].numpy()

    best_id, best_score = None, 0
    for landmark_id, entry in candidates.items():
        score = max(
            match_descriptors(query_descriptors, ref_desc)
            for ref_desc in entry["descriptors_per_image"]
        )
        if score > best_score:
            best_score, best_id = score, landmark_id

    if best_id is None or best_score < MATCH_THRESHOLD:
        return {"match": False, "reason": "no confident match", "best_score": best_score}

    entry = db[best_id]
    return {
        "match": True,
        "id": best_id,
        "name": entry["name"],
        "description": entry["description"],
        "score": best_score,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--lat", type=float, required=True)
    parser.add_argument("--lon", type=float, required=True)
    parser.add_argument("--image", type=str, required=True)
    args = parser.parse_args()

    db = build_landmark_db()
    result = identify_landmark(db, args.lat, args.lon, args.image)

    print("\n--- Result ---")
    if result["match"]:
        print(f"Landmark: {result['name']}")
        print(f"Description: {result['description']}")
        print(f"Match score: {result['score']}")
    else:
        print(f"No match: {result['reason']}")


if __name__ == "__main__":
    main()