import json
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

        for spawn_folder in CROPPED_DIR.iterdir():
            if not spawn_folder.is_dir():
                continue

            for image_path in spawn_folder.iterdir():
                if image_path.suffix.lower() not in [".png", ".jpg", ".jpeg"]:
                    continue

                image = cv2.imread(str(image_path), cv2.IMREAD_GRAYSCALE)

                if image is None:
                    continue

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
        cropped_gray = cv2.cvtColor(cropped, cv2.COLOR_BGR2GRAY)

        scores = []

        for template in self.templates:
            template_img = template["image"]

            template_img = cv2.resize(
                template_img,
                (cropped_gray.shape[1], cropped_gray.shape[0])
            )

            result = cv2.matchTemplate(
                cropped_gray,
                template_img,
                cv2.TM_CCOEFF_NORMED
            )

            score = float(result[0][0])

            scores.append({
                "score": score,
                "spawn": template["spawn"],
                "file": template["file"]
            })

        scores.sort(key=lambda x: x["score"], reverse=True)

        return scores[0], scores[:10]