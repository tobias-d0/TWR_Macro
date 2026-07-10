import json
import heapq
import cv2

from src.config import CROPPED_DIR, CROP_CONFIG_PATH


class SpawnDetector:
    def __init__(self):
        self.crop_box = self._load_crop_box()
        self.templates = self._load_templates()

    def _load_crop_box(self):
        with open(CROP_CONFIG_PATH, "r") as f:
            return json.load(f)

    def _load_templates(self):
        templates = []

        target_size = (
            self.crop_box["w"],
            self.crop_box["h"]
        )

        for spawn_folder in CROPPED_DIR.iterdir():
            if not spawn_folder.is_dir():
                continue

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

                # Preprocess once
                image = cv2.GaussianBlur(image, (3, 3), 0)

                templates.append({
                    "spawn": spawn_folder.name,
                    "file": image_path.name,
                    "image": image
                })

        if not templates:
            raise RuntimeError("No templates found in data/cropped")

        return templates

    def crop(self, image_bgr):
        x = self.crop_box["x"]
        y = self.crop_box["y"]
        w = self.crop_box["w"]
        h = self.crop_box["h"]

        return image_bgr[y:y + h, x:x + w]

    def detect_spawn(self, image_bgr):
        cropped = self.crop(image_bgr)

        cropped_gray = cv2.cvtColor(
            cropped,
            cv2.COLOR_BGR2GRAY
        )

        # Apply same preprocessing
        cropped_gray = cv2.GaussianBlur(
            cropped_gray,
            (3, 3),
            0
        )

        best_per_spawn = {}

        for template in self.templates:
            result = cv2.matchTemplate(
                cropped_gray,
                template["image"],
                cv2.TM_CCOEFF_NORMED
            )

            score = float(result[0][0])

            spawn = template["spawn"]

            if (
                spawn not in best_per_spawn
                or score > best_per_spawn[spawn]["score"]
            ):
                best_per_spawn[spawn] = {
                    "score": score,
                    "spawn": spawn,
                    "file": template["file"]
                }

        top_scores = heapq.nlargest(
            len(best_per_spawn),
            best_per_spawn.values(),
            key=lambda x: x["score"]
        )

        return top_scores[0], top_scores