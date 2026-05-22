import traceback
from deepface import DeepFace

try:
    res = DeepFace.analyze('uploads/fcde634bbf6c469d9247580025cf948d.jpeg', actions=['gender'], enforce_detection=False, silent=True)
    print(res)
except Exception as e:
    traceback.print_exc()
