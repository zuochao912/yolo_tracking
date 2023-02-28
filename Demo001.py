import cv2
import time
import numpy as np

cap = cv2.VideoCapture(0) #打开相机，只有一个摄像头则一般编号为0
cap.set(cv2.CAP_PROP_FRAME_WIDTH,1280)    #设置分辨率
cap.set(cv2.CAP_PROP_FRAME_HEIGHT,480) 
# ret, frame = cap.read()
# print frame.shape
while(1):
    # get a frame
    ret, frame = cap.read() #读取一副图像
    # show a frame
    cv2.imshow("LenaCV", frame)	#显示图像 
    if cv2.waitKey(1) & 0xFF == ord('q'): #按q结束
        break
cap.release()
cv2.destroyAllWindows() 