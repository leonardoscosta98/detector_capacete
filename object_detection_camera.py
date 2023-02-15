import tensorflow as tf
from object_detection.utils import config_util
from object_detection.protos import pipeline_pb2
from google.protobuf import text_format
import os
import win10toast
from PySide2.QtWidgets import(QApplication, QFileDialog,
 QMainWindow, QMessageBox, QTableWidget, QTableWidgetItem, QWidget, QCheckBox, QSystemTrayIcon)
from ui_main import Ui_MainWindow
from PySide2.QtGui import QIcon
from object_detection.utils import label_map_util
from object_detection.utils import visualization_utils as viz_utils
from object_detection.builders import model_builder
import cv2 
import numpy as np
from matplotlib import pyplot as plt


from threading import Thread
import sys
from collections import defaultdict
import pathlib 
import datetime




class MainWindow(QMainWindow, Ui_MainWindow):
    
    def __init__(self):
        super(MainWindow, self).__init__()
        self.setupUi(self)
        self.setWindowTitle("Detector de Capacete")
        self.setIcon() 

        self.btn_conectar.clicked.connect(self.conectaCamera)
    
    def setIcon(self):
        appIcon = QIcon('.\\new_icon_helmet.png')
        self.setWindowIcon(appIcon)

    
    def conectaCamera(self):

      endereco = self.txt_endereco.text()

      if (endereco == '') and (self.webcam.isChecked() == False):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Information)
        msg.setWindowTitle("Falha na Conexão")
        msg.setText("Não foi possivel conectar-se a câmera.")
        msg.exec_()

        return None

      WORKSPACE_PATH        = './workspace'
      # SCRIPTS_PATH          = '/Users/DSN-09/Desktop/detecta_capacete/models/research/scripts'
      # APIMODEL_PATH         = '/Users/DSN-09/Desktop/detecta_capacete/models'
      ANNOTATION_PATH       = './workspace/annotations' 
      # IMAGE_PATH            = '/workspace/images'
      MODEL_PATH            = './workspace/models'
      # PRETRAINED_MODEL_PATH = '/workspace/pre-trained-models'
      CONFIG_PATH           = './workspace/models/my_ssd_mobnet/pipeline.config'
      CHECKPOINT_PATH       = './workspace/models/my_ssd_mobnet/'
      
      CUSTOM_MODEL_NAME = 'my_ssd_mobnet' 
      
      CONFIG_PATH = MODEL_PATH+'/'+CUSTOM_MODEL_NAME+'/pipeline.config'
      
      # Load pipeline config and build a detection model
      configs = config_util.get_configs_from_pipeline_file(CONFIG_PATH)
      detection_model = model_builder.build(model_config=configs['model'], is_training=False)

      # Restore checkpoint
      ckpt = tf.compat.v2.train.Checkpoint(model=detection_model)
      ckpt.restore(os.path.join(CHECKPOINT_PATH, 'ckpt-61')).expect_partial()
      
      @tf.function
      def detect_fn(image):
        image, shapes = detection_model.preprocess(image)
        prediction_dict = detection_model.predict(image, shapes)
        detections = detection_model.postprocess(prediction_dict, shapes)
        return detections
      
      
      import cv2 
      import numpy as np
      from matplotlib import pyplot as plt
        
      category_index = label_map_util.create_category_index_from_labelmap(ANNOTATION_PATH+'/label_map.pbtxt')      

      
      try:
        leitura = False
        if (self.webcam.isChecked()) == True:
          cap = cv2.VideoCapture(0)
        else:  
          cap = cv2.VideoCapture(endereco)
        
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        notification = win10toast.ToastNotifier()
        
        while(cap.isOpened()):
          try:
            # Capture frame-by-frame
                # self.close()
                leitura = True
                ret, frame = cap.read()
                image_np = np.array(frame)
                
                input_tensor = tf.convert_to_tensor(np.expand_dims(image_np, 0), dtype=tf.float32)
                detections = detect_fn(input_tensor)
                
                num_detections = int(detections.pop('num_detections'))
                detections = {key: value[0, :num_detections].numpy()
                              for key, value in detections.items()}
                detections['num_detections'] = num_detections

                # detection_classes should be ints.
                detections['detection_classes'] = detections['detection_classes'].astype(np.int64)

                label_id_offset = 1
                image_np_with_detections = image_np.copy()

                marcador = viz_utils.visualize_boxes_and_labels_on_image_array(
                              image_np_with_detections,
                              detections['detection_boxes'],
                              detections['detection_classes']+label_id_offset,
                              detections['detection_scores'],
                              category_index,
                              use_normalized_coordinates=True,
                              max_boxes_to_draw=5,
                              min_score_thresh=.5,
                              agnostic_mode=False)

                if (marcador[1] == 'Aqua') and (self.checkBox.isChecked() == False):
                  notification.show_toast('Alerta!', 'Foi detectado funcionario(s) sem capacete', duration=3, icon_path = "./new_icon.ico")

                cv2.imshow('Detector de capacete',  cv2.resize(image_np_with_detections, (800, 600)))
                
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    cap.release()
                    break
          except Exception as e:
           pass
        if leitura == False:
          raise  
        cap.release()
        cv2.destroyAllWindows()
      except:
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Information)
        msg.setWindowTitle("Falha na Conexão")
        msg.setText("Não foi possivel conectar-se a câmera.")
        msg.exec_()

        return None
    
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    app.exec_()


