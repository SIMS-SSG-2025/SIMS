import serial
import numpy as np
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import cv2
import threading
import time
import re

# === CONFIGURATION ===
PORT = "COM4"
BAUD = 115200
TIMEOUT = 0.05
WIDTH, HEIGHT = 100, 100

# === SERIAL COMMUNICATION ===
def send_command(ser, cmd):
    ser.write((cmd + "\r\n").encode())
    time.sleep(0.2)
    resp = ser.read_all().decode(errors="ignore").strip()
    return resp

def get_unit_value():
    """Query AT+UNIT? and parse UNIT value."""
    with serial.Serial(PORT, BAUD, timeout=1) as ser:
        resp = send_command(ser, "AT+UNIT?")
        resp1 = send_command(ser, "AT+FPS=15") #frame locks the sensor to 5 FPS
        resp2 = send_command(ser, "AT+DISP=3") # sets the sensor to a certain mode that only puts data through usb and LCD
    print("UNIT response:", resp)
    match = re.search(r"\+UNIT:(\d+\.?\d*)", resp)
    if match:
        unit_val = float(match.group(1))
    else:
        unit_val = 0.0
    print(f"UNIT = {unit_val}")
    return unit_val

def read_frame(ser):
    buf = bytearray()
    while True:
        buf.extend(ser.read(4096))
        start = buf.find(b'\x00\xff')
        if start >= 0 and len(buf) > start + 4:
            frame_len = buf[start+2] | (buf[start+3] << 8)
            total_len = frame_len + 4
            if len(buf) >= start + total_len:
                frame = buf[start:start + total_len]
                del buf[:start + total_len]
                return frame

def parse_frame(frame):
    info = frame[4:20]
    payload = frame[20:-2]
    seq = int.from_bytes(info[0:4], "little")
    return seq, payload

def to_heatmap(payload):
    expected = WIDTH * HEIGHT
    if len(payload) < expected:
        payload = payload + bytes(expected - len(payload))
    img = np.frombuffer(payload[:expected], np.uint8).reshape((HEIGHT, WIDTH))
    heatmap = cv2.applyColorMap(img, cv2.COLORMAP_JET)
    return heatmap, img

# === TKINTER APPLICATION ===
class MaixSenseApp:
    def __init__(self, root, unit_value):
        self.unit_value = unit_value
        self.to_close = False # för att kunna använda koden i annat python program
        self.root = root
        self.root.title("MaixSense UART Heatmap Viewer (100x100)")
        self.root.geometry("600x720")

        self.serial = serial.Serial(PORT, BAUD, timeout=TIMEOUT)
        self.running = True
        self.latest_heatmap = None
        self.latest_gray = None
        self.reference_gray = None #skapar en först bild som ska användas som referens för att kunna mäta skillnad i pixel djup
        self.to_close = False

        # Status bar
        self.status_var = tk.StringVar(value=f"Connected to {PORT} @ {BAUD} | UNIT={unit_value}")
        ttk.Label(root, textvariable=self.status_var, font=("Consolas", 12)).pack(pady=5)
        # Canvas
        self.canvas = tk.Canvas(root, width=WIDTH*4, height=HEIGHT*4, bg="black")
        self.canvas.pack(padx=10, pady=10)
        self.canvas.bind("<Motion>", self.on_mouse_move)

        # Pixel info label
        self.pixel_info = tk.StringVar(value="Hover to see pixel value and distance")
        ttk.Label(root, textvariable=self.pixel_info, font=("Consolas", 11)).pack(pady=5)

        # Stop button
        ttk.Button(root, text="Stop", command=self.stop).pack(pady=10)
        # Reader thread
        self.thread = threading.Thread(target=self.reader_loop, daemon=True)
        self.thread.start()
        self.update_canvas_loop()

    def stop(self):
        self.running = False
        self.serial.close()
        self.root.quit()

    def reader_loop(self):
        while self.running:
            try:
                frame = read_frame(self.serial)
                if frame:
                    seq, payload = parse_frame(frame)
                    heatmap, gray = to_heatmap(payload)
                    self.latest_heatmap = cv2.cvtColor(heatmap, cv2.COLOR_BGR2RGB)
                    self.latest_gray = gray
                    #self.status_var.set(f"Frame #{seq} | UNIT={self.unit_value}")
                    if self.reference_gray is None: #skapar en refernece fram till senare
                        self.reference_gray = gray.copy()
                        print("Reference frame captured")
                        
                    self.status_var.set("Live feed LiDAR camera")
                    diff = cv2.absdiff(self.latest_gray, self.reference_gray)
                    blurred_diff = cv2.GaussianBlur(diff,(5,5),0)
                    _, thresh = cv2.threshold(blurred_diff, 150, 255, cv2.THRESH_BINARY)
                    thresh=cv2.morphologyEx(thresh, cv2.MORPH_OPEN, np.ones((3,3),np.uint8))
                    changed_pixels = cv2.countNonZero(thresh)
                    #print(diff)
                    if changed_pixels > 300:
                        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE) #ger start pixel i x, y för ett objekt som har kommit in i bild och ger en bred och höjd för objektet 

                        color_frame = cv2.cvtColor(self.latest_gray, cv2.COLOR_GRAY2BGR)

                        for contour in contours:
                            area = cv2.contourArea(contour)
                            if area < 50:
                                continue  # skip small noise

                            # Get bounding box (x, y, width, height)
                            #x, y, w, h = cv2.boundingRect(contour)

                            # Draw the contour and bounding box in red
                            #cv2.drawContours(color_frame, [contour], -1, (0, 0, 255), 1)
                            #cv2.rectangle(color_frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                            
                            print(f"⚠Varning! Objekt hittat! Bounding box: x={x}, y={y}, w={x+w}, h={y+h}")# w={w}, h={h}
                            self.set_lidar_status(True)
                        #print(f"⚠Varning - {changed_pixels} pixlar ändrade")//ger en random pixel i det fält som har ändrats
                        #ys, xs = np.where(thresh > 0)
                        #print(f"⚠{len(xs)} pixels change, exampel: {(xs[0],ys[0])}")
                        #color_frame = cv2.cvtColor(self.latest_gray,cv2.COLOR_GRAY2BGR)
                        #color_frame[thresh > 0] = [0, 0, 255]
                    #
                    #if len(xs) > 0: #skriver ut en valfri vald pixel som har ändrats och antalet pixlar som har ändrats.
                        #print(f"⚠{len(xs)} pixels change, exampel: {(xs[0],ys[0])}")
                    #if cv2.countNonZero(thresh)> 300:
                        #print("⚠️VARNING: Något är för nära")
                        #(diff > 180): # kollar alla pixlar om någon ändrar djup till närmare än 150 enheters avstånd
                        #print("⚠️VARNING: Något är för nära") #ger en varning i shellet
                        #self.varning_frame = gray.copy()
                        #cv2.imwrite("warning_frame.png", gray)
                        #self.status_var.set("⚠️VARNING: Något är för nära")
                        #diff_map= cv2.applyColormap(diff, cv2.COLORMAP_JET)
                    else:
                        color_frame = cv2.cvtColor(self.latest_gray, cv2.COLOR_GRAY2BGR)
                        self.status_var.set("Live feed LiDAR camera")
                        self.set_lidar_status(False)
            except Exception as e:
                self.status_var.set(f"Error: {e}")
                time.sleep(0.1)

    def update_canvas_loop(self):
        if self.latest_heatmap is not None:
            img = Image.fromarray(self.latest_heatmap)
            img = img.resize((WIDTH*4, HEIGHT*4), Image.NEAREST)
            self.tk_img = ImageTk.PhotoImage(img)
            self.canvas.create_image(0, 0, anchor="nw", image=self.tk_img)
        if self.running:
            self.root.after(50, self.update_canvas_loop)

    def on_mouse_move(self, event):
        if self.latest_gray is None:
            return
        x = int(event.x / 4)
        y = int(event.y / 4)
        if 0 <= x < WIDTH and 0 <= y < HEIGHT:
            p = int(self.latest_gray[y, x])
            if self.unit_value != 0:
                distance = p * self.unit_value
            else:
                distance = (p / 5.1) ** 2
            self.pixel_info.set(f"({x},{y}) = {p} → distance = {distance:.2f} units")
        else:
            self.pixel_info.set("Outside image")
            
    def get_lidar_status(self):
        return self.to_close
    
    def set_lidar_status(self, status: bool):
        self.to_close = status

# === MAIN ===
if __name__ == "__main__":
    unit_val = get_unit_value()
    root = tk.Tk()
    app = MaixSenseApp(root, unit_val)
    root.mainloop()
