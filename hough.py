import numpy as np
import os
import cv2
from scipy.optimize import leastsq
from math import pi

def test_circles(img_src):
    '''
        inputs:
            the ROI part of original image
        return: 
            (x,y,r)
            x is the width axis,
            y is the height axis,
            r is the radis 
    '''
    img_part=img_src.copy()
    #转为灰度图
    img_gray = cv2.cvtColor(img_part,cv2.COLOR_BGR2GRAY)
    img_gray=cv2.GaussianBlur(img_gray,(5,5),0,0)

    #找出圆形
    circles = cv2.HoughCircles(img_gray,cv2.HOUGH_GRADIENT,1.2,20,param1=60,param2=30,minRadius=5,maxRadius=0)
    if circles is None:
        # print("No circles are detected!")
        return 0,0,0
    circles = np.uint16(np.around(circles)) #数组：x，y坐标,半径r的值
    circle=circles[0]
    if len(circle) > 1 :
        print("detect more than one circles!")
    return circle[0][0],circle[0][1],circle[0][2]

def canny_edge(filename,origin):
    '''
        origin可以是RGB图像,也可以是灰度图像
    '''
    canny_edges = cv2.Canny(origin, 100, 200) # 100是最小阈值,200是最大阈值
    # show_img(canny_edges)
    tar_path=os.path.join("./edge_canny/",filename+"_canny.bmp")
    cv2.imwrite(tar_path,canny_edges)
    return canny_edges

def radius(x, y, xc, yc):
    '''
    计算每一个点到圆心的距离
    '''
    return np.sqrt((x-xc)**2 + (y-yc)**2)

def f(c, x, y):
    '''
    Cost Function	
    '''
    Ri = radius(x, y, *c)
    return np.square(Ri - Ri.mean())

def least_squares_circle(coords):
    """
    Circle fit using least-squares solver.
    Inputs:

        - coords, list or numpy array with len>2 of the form:
        [
    [x_coord, y_coord],
    ...,
    [x_coord, y_coord]
    ]
        or numpy array of shape (n, 2)

    Outputs:

        - xc : x-coordinate of solution center (float)
        - yc : y-coordinate of solution center (float)
        - R : Radius of solution (float)
        - residu : MSE of solution against training data (float)
    """

    x, y = None, None
    if isinstance(coords, np.ndarray):
        x = coords[:, 0]
        y = coords[:, 1]
    elif isinstance(coords, list):
        x = np.array([point[0] for point in coords])
        y = np.array([point[1] for point in coords])
    else:
        raise Exception("Parameter 'coords' is an unsupported type: " + str(type(coords)))

    # coordinates of the barycenter
    x_m = np.mean(x)
    y_m = np.mean(y)
    center_estimate = x_m, y_m
    center, _ = leastsq(f, center_estimate, args=(x, y))
    xc, yc = center
    Ri       = radius(x, y, *center) # 每一个点到估计的圆心的距离
    R        = Ri.mean() # 距离平均值
    residu   = np.sum((Ri - R)**2)
    return xc, yc, R, residu


def ring_filter(edge_orin):
    H,W=edge_orin.shape
    x0,y0=W/2,H/2
    R=min(x0,y0)
    R_up,R_dn=1.1*R,0.9*R #调节比例
    R_up2,R_dn2=R_up*R_up,R_dn*R_dn
    dotlist=[]
    mask = np.empty((H, W),dtype=np.bool_)
    for i in range(W):
        for j in range(H):
            pos=(i-x0)*(i-x0)+(j-y0)*(j-y0)
            if pos < R_dn2 or pos > R_up2:
                mask[j][i]=True # 非法区域,设为0
            else:
                mask[j][i]=False # 合法区域，设为1
                if edge_orin[j][i]==255:
                    dotlist.append((j,i))
    edge_orin[mask]=0
    # show_img(edge)
    dots=np.array(dotlist,dtype=np.uint8)
    return dots