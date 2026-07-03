import os
import json
import cv2

CROPPED_DIR = "data/cropped"
CONFIG_PATH = "data/crop_config.json"


def load_crop_config():
    with open(CONFIG_PATH, "r") as f:
        return json.load(f)


def crop_image(image, box):
    x = box["x"]
    y = box["y"]
    w = box["w"]
    h = box["h"]

    return image[y:y + h, x:x + w]


def load_template_images():
    images = []

    for spawn_folder in os.listdir(CROPPED_DIR):
        spawn_path = os.path.join(CROPPED_DIR, spawn_folder)

        if not os.path.isdir(spawn_path):
            continue

        for file in os.listdir(spawn_path):
            if file.lower().endswith((".png", ".jpg", ".jpeg")):
                path = os.path.join(spawn_path, file)
                image = cv2.imread(path, cv2.IMREAD_GRAYSCALE)

                if image is not None:
                    images.append((spawn_folder, file, image))

    return images


def compare_images(test_img, template_img):
    template_img = cv2.resize(
        template_img,
        (test_img.shape[1], test_img.shape[0])
    )

    result = cv2.matchTemplate(
        test_img,
        template_img,
        cv2.TM_CCOEFF_NORMED
    )

    return float(result[0][0])


def main():
    if not os.path.exists(CONFIG_PATH):
        print("Missing crop config.")
        print("Run crop_tool.py first.")
        return

    templates = load_template_images()

    if len(templates) == 0:
        print("No template images found in data/cropped")
        return

    box = load_crop_config()

    test_path = input("Enter path to uncropped test image: ").strip().replace('"', "")

    uncropped = cv2.imread(test_path, cv2.IMREAD_GRAYSCALE)

    if uncropped is None:
        print("Could not read test image.")
        return

    test_image = crop_image(uncropped, box)

    scores = []

    for spawn, filename, template_img in templates:
        score = compare_images(test_image, template_img)
        scores.append((score, spawn, filename))

    scores.sort(reverse=True)

    print("\nTop matches:")
    for score, spawn, filename in scores[:10]:
        print(f"{spawn:10s} | {score:.4f} | {filename}")

    best_score, best_spawn, best_file = scores[0]

    print("\nDetected spawn:")
    print(f"{best_spawn} using {best_file}")
    print(f"Confidence score: {best_score:.4f}")


if __name__ == "__main__":
    main()