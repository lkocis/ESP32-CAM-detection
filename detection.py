import cv2

url = "http://192.168.1.188/stream"
cap = cv2.VideoCapture(url)

if not cap.isOpened():
    print("Error opening video stream or file")

