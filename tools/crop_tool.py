import os
import json
import cv2

RAW_DIR = "data/raw_uncropped"
CROPPED_DIR = "data/cropped"
CONFIG_PATH = "data/crop_config.json"

selected_box = None
drawing = False
start_x, start_y = 0, 0


def find_first_image():
    for root, dirs, files in os.walk(RAW_DIR):
        for file in files:
            if file.lower().endswith((".png", ".jpg", ".jpeg")):
                return os.path.join(root, file)
    return None


def mouse_callback(event, x, y, flags, param):
    global selected_box, drawing, start_x, start_y

    image = param["image"]
    preview = image.copy()

    if event == cv2.EVENT_LBUTTONDOWN:
        drawing = True
        start_x, start_y = x, y

    elif event == cv2.EVENT_MOUSEMOVE and drawing:
        cv2.rectangle(preview, (start_x, start_y), (x, y), (0, 255, 0), 2)
        cv2.imshow("Select crop area", preview)

    elif event == cv2.EVENT_LBUTTONUP:
        drawing = False

        x1 = min(start_x, x)
        y1 = min(start_y, y)
        x2 = max(start_x, x)
        y2 = max(start_y, y)

        selected_box = {
            "x": x1,
            "y": y1,
            "w": x2 - x1,
            "h": y2 - y1
        }

        cv2.rectangle(preview, (x1, y1), (x2, y2), (0, 255, 0), 2)
        cv2.imshow("Select crop area", preview)

        print(f"Selected crop: {selected_box}")


def save_crop_config(box):
    os.makedirs("data", exist_ok=True)

    with open(CONFIG_PATH, "w") as f:
        json.dump(box, f, indent=4)

    print(f"Saved crop config to {CONFIG_PATH}")


def load_crop_config():
    with open(CONFIG_PATH, "r") as f:
        return json.load(f)


def crop_all_images(box):
    os.makedirs(CROPPED_DIR, exist_ok=True)

    x = box["x"]
    y = box["y"]
    w = box["w"]
    h = box["h"]

    count = 0

    for spawn_folder in os.listdir(RAW_DIR):
        raw_spawn_path = os.path.join(RAW_DIR, spawn_folder)

        if not os.path.isdir(raw_spawn_path):
            continue

        cropped_spawn_path = os.path.join(CROPPED_DIR, spawn_folder)
        os.makedirs(cropped_spawn_path, exist_ok=True)

        for file in os.listdir(raw_spawn_path):
            if not file.lower().endswith((".png", ".jpg", ".jpeg")):
                continue

            input_path = os.path.join(raw_spawn_path, file)
            output_path = os.path.join(cropped_spawn_path, file)

            image = cv2.imread(input_path)

            if image is None:
                print(f"Could not read: {input_path}")
                continue

            crop = image[y:y + h, x:x + w]
            cv2.imwrite(output_path, crop)

            count += 1

    print(f"Cropped {count} images into {CROPPED_DIR}")


def select_crop_area():
    image_path = find_first_image()

    if image_path is None:
        print(f"No images found in {RAW_DIR}")
        return None

    image = cv2.imread(image_path)

    if image is None:
        print(f"Could not open image: {image_path}")
        return None

    print(f"Using image: {image_path}")
    print("Drag a rectangle around the useful landmark area.")
    print("Press ENTER to confirm.")
    print("Press ESC to cancel.")

    cv2.namedWindow("Select crop area", cv2.WINDOW_NORMAL)
    cv2.imshow("Select crop area", image)
    cv2.setMouseCallback("Select crop area", mouse_callback, {"image": image})

    while True:
        key = cv2.waitKey(1) & 0xFF

        if key == 13:  # ENTER
            break

        if key == 27:  # ESC
            cv2.destroyAllWindows()
            print("Cancelled.")
            return None

    cv2.destroyAllWindows()
    return selected_box


def main():
    print("1 = Select new crop area and crop all images")
    print("2 = Use saved crop area and crop all images")

    choice = input("Choose option: ").strip()

    if choice == "1":
        box = select_crop_area()

        if box is None:
            print("No crop selected.")
            return

        save_crop_config(box)
        crop_all_images(box)

    elif choice == "2":
        if not os.path.exists(CONFIG_PATH):
            print("No saved crop config found.")
            return

        box = load_crop_config()
        print(f"Loaded crop config: {box}")
        crop_all_images(box)

    else:
        print("Invalid choice.")


if __name__ == "__main__":
    main()