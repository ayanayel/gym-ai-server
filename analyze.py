import sys
import cv2
import mediapipe as mp
import math

image_path = sys.argv[1]

mp_pose = mp.solutions.pose
mp_draw = mp.solutions.drawing_utils
pose = mp_pose.Pose(
    static_image_mode=True,
    model_complexity=2,
    min_detection_confidence=0.4
)

image = cv2.imread(image_path)
if image is None:
    print("Error: image not found")
    exit()

image = cv2.rotate(image, cv2.ROTATE_180)
image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
results = pose.process(image_rgb)

def get_point(landmarks, idx):
    lm = landmarks[idx]
    return (lm.x, lm.y, lm.visibility)

def angle_between(A, B, C):
    """
    حساب الزاوية عند النقطة B بين خطي BA و BC
    """
    ax, ay = A[0] - B[0], A[1] - B[1]
    cx, cy = C[0] - B[0], C[1] - B[1]
    dot = ax * cx + ay * cy
    mag_a = math.sqrt(ax**2 + ay**2)
    mag_c = math.sqrt(cx**2 + cy**2)
    if mag_a * mag_c == 0:
        return 0
    cos_angle = max(-1, min(1, dot / (mag_a * mag_c)))
    return math.degrees(math.acos(cos_angle))

def vertical_deviation(top, bottom):
    """
    قياس انحراف النقطة العلوية عن الرأسي بالنسبة للسفلى
    بيرجع زاوية انحراف عن الخط الرأسي (0 = مستقيم تماماً)
    """
    dx = top[0] - bottom[0]
    dy = top[1] - bottom[1]
    if dy == 0:
        return 90
    angle_from_vertical = abs(math.degrees(math.atan2(dx, abs(dy))))
    return angle_from_vertical

if results.pose_landmarks:
    lm = results.pose_landmarks.landmark

    mp_draw.draw_landmarks(image, results.pose_landmarks, mp_pose.POSE_CONNECTIONS)
    output_path = image_path.split('.')[0] + "_output.jpg"
    cv2.imwrite(output_path, image)


    nose         = get_point(lm, 0)
    left_shoulder  = get_point(lm, 11)
    right_shoulder = get_point(lm, 12)
    left_hip       = get_point(lm, 23)
    right_hip      = get_point(lm, 24)
    left_knee      = get_point(lm, 25)
    right_knee     = get_point(lm, 26)
    left_ankle     = get_point(lm, 27)
    right_ankle    = get_point(lm, 28)
    left_ear       = get_point(lm, 7)
    right_ear      = get_point(lm, 8)

    use_left = left_shoulder[2] > right_shoulder[2]

    shoulder = left_shoulder if use_left else right_shoulder
    hip      = left_hip      if use_left else right_hip
    knee     = left_knee     if use_left else right_knee
    ankle    = left_ankle    if use_left else right_ankle
    ear      = left_ear      if use_left else right_ear

   
    shoulder_hip_deviation = vertical_deviation(shoulder, hip)


    hip_angle = angle_between(shoulder, hip, knee)

    
    head_forward_ratio = 0
    if ear[2] > 0.4 and shoulder[2] > 0.4:
        head_forward_ratio = abs(ear[0] - shoulder[0])


    shoulder_level_diff = abs(left_shoulder[1] - right_shoulder[1])
    both_shoulders_visible = left_shoulder[2] > 0.5 and right_shoulder[2] > 0.5

    full_body_deviation = vertical_deviation(shoulder, ankle) if ankle[2] > 0.4 else None


    issues = []

 
    if shoulder_hip_deviation > 15:
        issues.append(f"body tilted ({shoulder_hip_deviation:.1f}° from vertical)")


    if hip_angle < 140:
        issues.append(f"bent posture at hips ({hip_angle:.1f}°)")


    if head_forward_ratio > 0.07:
        issues.append(f"head too far forward")


    if both_shoulders_visible and shoulder_level_diff > 0.04:
        issues.append("uneven shoulders")
   
    if full_body_deviation is not None and full_body_deviation > 18:
        issues.append(f"overall body lean ({full_body_deviation:.1f}°)")

 
    if len(issues) == 0:
        print("Correct posture")
    else:
        print("Bad posture: " + ", ".join(issues))

else:
    print("Posture unclear")