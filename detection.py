import cv2
import requests
import numpy as np
import os
from datetime import datetime
import glob
import time
import threading

# Postavke
URL = "http://192.168.1.188/capture"
FOLDER_PATH = "C:/Users/LKocis/Downloads/ESP 32 CAM detection/ESP32-CAM-detection/pictures"  
event = threading.Event()

def take_picture():
    print("--- CONTROLS ---")
    print("Press 's' for taking a picture")
    print("Press 'ESC' for exit")

    while True:
        try:
            response = requests.get(URL, timeout=5)
            
            if response.status_code == 200:
                img_array = np.array(bytearray(response.content), dtype=np.uint8)
                frame = cv2.imdecode(img_array, cv2.IMREAD_COLOR)

                if frame is not None:
                    cv2.imshow("ESP32-CAM Live Preview", frame)
                
                key = cv2.waitKey(1) & 0xFF

                # If 's' -> save picture
                if key == ord('s'):
                    time = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
                    file_name = f"img_{time}.jpg"
                    full_path = os.path.join(FOLDER_PATH, file_name)
                    
                    cv2.imwrite(full_path, frame)
                    print(f"Taken and saved: {file_name}")

                    # Activate detect_red_color
                    event.set()

                # If 'ESC' (kod 27) -> exit
                elif key == 27:
                    print("Closing program...")
                    break
            else:
                print(f"Error: Camera not available (Status: {response.status_code})")
                break

        except Exception as e:
            print(f"There has been an error: {e}")
            break

    cv2.destroyAllWindows()

def detect_red_color():
    while True:
        # Wait for take_picture to save picture
        event.wait() 
        
        try:
            search_path = os.path.join(FOLDER_PATH, "*.jpg")
            images = glob.glob(search_path)
            if not images:
                event.clear()
                continue
                
            last_img_path = max(images, key=os.path.getmtime)
            img = cv2.imread(last_img_path)
            
            if img is None:
                event.clear()
                continue

            hsv_img = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

            # Red masks
            lower_red1 = np.array([0, 100, 100])
            upper_red1 = np.array([10, 255, 255])
            lower_red2 = np.array([160, 100, 100])
            upper_red2 = np.array([180, 255, 255])

            mask1 = cv2.inRange(hsv_img, lower_red1, upper_red1)
            mask2 = cv2.inRange(hsv_img, lower_red2, upper_red2)
            red_mask = cv2.add(mask1, mask2)

            kernel = np.ones((5, 5), "uint8")
            red_mask = cv2.dilate(red_mask, kernel)

            contours, _ = cv2.findContours(red_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            found = False
            for contour in contours:
                area = cv2.contourArea(contour)
                if area > 500:
                    x, y, w, h = cv2.boundingRect(contour)
                    cv2.rectangle(img, (x, y), (x + w, y + h), (0, 0, 255), 2)
                    cv2.putText(img, "Red Object", (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                    found = True
            
            if found:
                print(f"--- Detection done: Red color found in {os.path.basename(last_img_path)}")
            
            start_time = time.time()
            while time.time() - start_time < 3:
                cv2.imshow("Detection Result", img)
                if cv2.waitKey(1) & 0xFF == 27: # ESC allowed while picture is showing  
                    break
            
            cv2.destroyWindow("Detection Result")
            os.remove(last_img_path)
            print("Picture deleted.")
            print("Ready for another picture...")
            
        except Exception as e:
            print(f"Error in detection: {e}")
        
        event.clear() # Reset event for new picture


if __name__ == "__main__":
    t_detect = threading.Thread(target=detect_red_color, daemon=True)
    t_detect.start()

    take_picture()