import cv2
import mediapipe as mp
import math
import mido
import time 
class HandGestureMIDIController:
    GESTURE_TO_CC = {
        "Index": 20,
        "Middle": 21,
        "Ring": 22,
        "Pinky": 23,
        "Depth": 24
    }

    MIN_DEPTH = 0.13
    MAX_DEPTH = 0.48

    def __init__(self, midi_port='IAC Driver Bus 1'):
        # Initialize MediaPipe Hands
        self.mp_hands = mp.solutions.hands
        self.mp_drawing = mp.solutions.drawing_utils
        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=1,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )

        # MIDI setup
        self.midi_output = mido.open_output(midi_port)  # Replace with your virtual MIDI port name

        # Mapping mode flag
        self.mapping_mode = False
        self.selected_finger = ""

    def getMode(self):
        return self.mapping_mode
    
    def enableMode(self):
        self.mapping_mode = True

    def disableMode(self):
        self.mapping_mode = False

    def setMappingMode(self,val):
        self.mapping_mode = val

    def send_finger(self, finger):
        self.selected_finger = finger
        if self.selected_finger in self.GESTURE_TO_CC:
            cc_number = self.GESTURE_TO_CC[self.selected_finger]
            self.midi_output.send(mido.Message('control_change', channel=0, control=cc_number, value=64))
            print("sent:", finger)
            time.sleep(0.5)


    def enter_mapping_mode(self, finger):
        self.selected_finger = finger
        while self.mapping_mode:
            if self.selected_finger in self.GESTURE_TO_CC:
                cc_number = self.GESTURE_TO_CC[self.selected_finger]
                self.midi_output.send(mido.Message('control_change', channel=0, control=cc_number, value=64))

    @staticmethod
    def calculate_distance(point1, point2):
        return math.sqrt((point1[0] - point2[0]) ** 2 +
                         (point1[1] - point2[1]) ** 2 +
                         (point1[2] - point2[2]) ** 2)

    @staticmethod
    def normalize_distance(distance, min_dist, max_dist):
        return max(0, min(1, (distance - min_dist) / (max_dist - min_dist))) * 100

    @staticmethod
    def normalize_depth(depth, min_depth, max_depth):
        return max(0, min(1, (depth - min_depth) / (max_depth - min_depth))) * 100

    def adjust_finger_percentage_based_on_palm_distance(self, finger_distance, palm_distance, constant_w=0.5):
        return (finger_distance / (palm_distance * constant_w)) * 100

    def capture_frame(self, frame):
        results = self.hands.process(frame)
        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                # Draw landmarks on the frame
                self.mp_drawing.draw_landmarks(frame, hand_landmarks, self.mp_hands.HAND_CONNECTIONS)

                # Get thumb tip position
                thumb_tip = [hand_landmarks.landmark[self.mp_hands.HandLandmark.THUMB_TIP].x,
                             hand_landmarks.landmark[self.mp_hands.HandLandmark.THUMB_TIP].y,
                             hand_landmarks.landmark[self.mp_hands.HandLandmark.THUMB_TIP].z]

                # Get fingertip positions
                finger_tips = [
                    hand_landmarks.landmark[self.mp_hands.HandLandmark.INDEX_FINGER_TIP],
                    hand_landmarks.landmark[self.mp_hands.HandLandmark.MIDDLE_FINGER_TIP],
                    hand_landmarks.landmark[self.mp_hands.HandLandmark.RING_FINGER_TIP],
                    hand_landmarks.landmark[self.mp_hands.HandLandmark.PINKY_TIP]
                ]

                # Get the top of the palm (base of the index finger)
                palm_top = [hand_landmarks.landmark[self.mp_hands.HandLandmark.INDEX_FINGER_MCP].x,
                            hand_landmarks.landmark[self.mp_hands.HandLandmark.INDEX_FINGER_MCP].y,
                            hand_landmarks.landmark[self.mp_hands.HandLandmark.INDEX_FINGER_MCP].z]

                # Get the bottom of the palm (wrist)
                palm_bottom = [hand_landmarks.landmark[self.mp_hands.HandLandmark.WRIST].x,
                               hand_landmarks.landmark[self.mp_hands.HandLandmark.WRIST].y,
                               hand_landmarks.landmark[self.mp_hands.HandLandmark.WRIST].z]

                # Calculate palm distance
                palm_distance = self.calculate_distance(palm_top, palm_bottom)
                normalized_depth = self.normalize_depth(palm_distance, self.MIN_DEPTH, self.MAX_DEPTH)

                midi_value_depth = int((normalized_depth / 100) * 127)
                midi_value_depth = max(0, min(127, midi_value_depth))
                midi_message_depth = mido.Message('control_change', channel=0, control=24, value=midi_value_depth)
                self.midi_output.send(midi_message_depth)

                cv2.putText(frame, f"Depth: {int(normalized_depth)}",
                            (10, 180), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)

                for i, finger_tip in enumerate(finger_tips):
                    finger_distance = self.calculate_distance(thumb_tip, [finger_tip.x, finger_tip.y, finger_tip.z])
                    adjusted_percentage = self.adjust_finger_percentage_based_on_palm_distance(finger_distance, palm_distance, 1.5)

                    midi_value = int((adjusted_percentage / 100) * 127)
                    midi_value = max(0, min(127, midi_value))

                    midi_message = mido.Message('control_change', channel=0, control=20 + i, value=midi_value)
                    self.midi_output.send(midi_message)

                    cv2.putText(frame, f"Finger {i+1}: {int(adjusted_percentage)}%",
                                (10, 30 + i * 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)
        return frame

