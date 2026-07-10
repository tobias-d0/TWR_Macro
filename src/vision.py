import json
import heapq
import cv2
import numpy as np

from src.config import CROPPED_DIR, CROP_CONFIG_PATH


class SpawnDetector:
    def __init__(self):
        self.crop_box = self._load_crop_box()
        self.templates = self._load_templates()

    def _load_crop_box(self):
        with open(CROP_CONFIG_PATH, "r") as f:
            return json.load(f)

    def _load_templates(self):
        target_size = (
            self.crop_box["w"],
            self.crop_box["h"]
        )

        spawn_images = {}

        for spawn_folder in CROPPED_DIR.iterdir():
            if not spawn_folder.is_dir():
                continue

            images = []

            for image_path in spawn_folder.iterdir():
                if image_path.suffix.lower() not in [".png", ".jpg", ".jpeg"]:
                    continue

                image = cv2.imread(str(image_path), cv2.IMREAD_GRAYSCALE)

                if image is None:
                    continue

                image = cv2.resize(
                    image,
                    target_size,
                    interpolation=cv2.INTER_AREA
                )

                images.append(image.astype(np.float32))

            if images:
                spawn_images[spawn_folder.name] = images

        templates = []

        for spawn_name, images in spawn_images.items():
            average = np.mean(images, axis=0)
            average = average.astype(np.uint8)

            templates.append({
                "spawn": spawn_name,
                "image": average
            })

        if not templates:
            raise RuntimeError("No templates found in data/cropped")

        return templates

    def crop(self, image_bgr):
        x = self.crop_box["x"]
        y = self.crop_box["y"]
        w = self.crop_box["w"]
        h = self.crop_box["h"]

        return image_bgr[y:y+h, x:x+w]

    def detect_spawn(self, image_bgr):
        cropped = self.crop(image_bgr)

        cropped_gray = cv2.cvtColor(
            cropped,
            cv2.COLOR_BGR2GRAY
        )

        scores = []

        for template in self.templates:
            result = cv2.matchTemplate(
                cropped_gray,
                template["image"],
                cv2.TM_CCOEFF_NORMED
            )

            scores.append({
                "spawn": template["spawn"],
                "score": float(result[0][0]),
                "file": "average"
            })

        top_scores = heapq.nlargest(
            len(scores),
            scores,
            key=lambda x: x["score"]
        )

        return top_scores[0], top_scores