import traceback
import tf_keras as keras

try:
    print("Loading model...")
    model = keras.models.load_model(r'C:\Users\vivek\.deepface\weights\gender_model_weights.h5')
    print("Success!")
except Exception as e:
    traceback.print_exc()
