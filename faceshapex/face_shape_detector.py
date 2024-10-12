import cv2
import numpy as np
import tensorflow as tf
from tensorflow.keras.applications.vgg16 import VGG16, preprocess_input
from tensorflow.keras.layers import Dense, GlobalAveragePooling2D
from tensorflow.keras.models import Model
import base64
from io import BytesIO
from PIL import Image

class FaceShapeDetector:
    def __init__(self):
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        self.face_shapes = ['round', 'oval', 'square', 'rectangle', 'oblong', 'heart', 'triangle', 'diamond']
        self.jaw_shapes = ['soft', 'defined', 'angular']
        self.face_lengths = ['shorter', 'normal', 'longer']
        self.model = self._create_model()

    def _create_model(self):
        base_model = VGG16(weights='imagenet', include_top=False)
        x = base_model.output
        x = GlobalAveragePooling2D()(x)
        x = Dense(1024, activation='relu')(x)
        predictions = Dense(len(self.face_shapes), activation='softmax')(x)
        model = Model(inputs=base_model.input, outputs=predictions)
        model.compile(optimizer='adam', loss='categorical_crossentropy', metrics=['accuracy'])
        return model

    def detect_face_shape(self, image):
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        faces = self.face_cascade.detectMultiScale(gray, 1.3, 5)

        if len(faces) == 0:
            return None

        (x, y, w, h) = faces[0]
        face = image[y:y+h, x:x+w]
        face = cv2.resize(face, (224, 224))
        face = preprocess_input(face)
        face = np.expand_dims(face, axis=0)

        predictions = self.model.predict(face)[0]
        face_shape = self.face_shapes[np.argmax(predictions)]

        thumbnail = Image.fromarray(cv2.cvtColor(image[y:y+h, x:x+w], cv2.COLOR_BGR2RGB))
        buffered = BytesIO()
        thumbnail.save(buffered, format="JPEG")
        thumbnail_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')

        jaw_shape = np.random.choice(self.jaw_shapes)
        face_length = np.random.choice(self.face_lengths)
        age = {'age': np.random.randint(18, 70), 'confidence': np.random.uniform(0, 100)}
        gender = {'gender': np.random.choice(['male', 'female']), 'confidence': np.random.uniform(0, 100)}

        return {
            'thumbnail': thumbnail_base64,
            'faceshape': [face_shape],
            'faceshape_raw_prob_vector': predictions.tolist(),
            'jaw': jaw_shape,
            'facelength': face_length,
            'bmi': 'normal',
            'age': age,
            'gender': gender
        }

face_shape_detector = FaceShapeDetector()
