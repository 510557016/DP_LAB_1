import cv2
import numpy as np
import os
import glob
import matplotlib.pylab as plt
import configparser
import json

#checkerboard： 棋盤格的格點數目
checkerboard = 7 
CHECKERBOARD = np.array([checkerboard,checkerboard],dtype=np.int32)
#魚眼圖片的路徑
imgsPath = '/home/lenovo/DP/receive_folder/'
config = configparser.ConfigParser()
config.read('config.ini')
alpha = 0
#k均值算法之图像分割
#cv2.TERM_CRITERIA_EPS :精确度（误差）满足epsilon停止。
#cv2.TERM_CRITERIA_MAX_ITER：迭代次数超过max_iter停止。
#cv2.TERM_CRITERIA_EPS+cv2.TERM_CRITERIA_MAX_ITER，两者合体，任意一个满足结束。

subpix_criteria = (cv2.TERM_CRITERIA_EPS+cv2.TERM_CRITERIA_MAX_ITER, 30, 0.0001)

#鱼眼相机校正
calibration_flags = cv2.fisheye.CALIB_RECOMPUTE_EXTRINSIC+cv2.fisheye.CALIB_CHECK_COND+cv2.fisheye.CALIB_FIX_SKEW
#產生一個 float32 7 * 7 3D零矩陣
objp = np.zeros((1, CHECKERBOARD[0]*CHECKERBOARD[1], 3), np.float32)
#print(objp)
#reshape(m,n) 改变维度为m行、n列
x = objp[0, :, :2] = np.mgrid[0:CHECKERBOARD[0], 0:CHECKERBOARD[1].T].reshape(-1, 2)
_img_shape = None
objpoints = [] 
imgpoints = []
images = glob.glob(imgsPath + '*.png')
#print("images=",images)
nimages = len(images)
for fname in images:
	img = cv2.imread(fname)
	#plt.figure('original image')
	#plt.imshow(img[..., ::-1])
	#if _img_shape == None:
		#_img_shape = img.shape[:2]
	#else:
		#assert _img_shape == img.shape[:2]
    
    #彩色影像轉灰階
    #TODO 12 : convert image to gary
	gray = cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)	
	#print("gray=",gray)
	#int cvFindChessboardCorners
	#( const void* image, CvSize pattern_size, CvPoint2D32f* corners, int* corner_count = NULL, int flags = CV_CALIB_CB_ADAPTIVE_THRESH );
	#Image: 			輸入的棋盤圖，必須是8位的灰度或者彩色圖像。
	#pattern_size:    	棋盤圖中每行和每列角點的個數。
	#ret:               檢測到角點       
	#Corners:     		檢測到的角點
	#corner_count:     	輸出，角點的個數。如果不是NULL，函數將檢測到的角點的個數存儲於此變量。
	#Flags:    			各種操作標誌，可以是0或者下面值的組合：
	#CV_CALIB_CB_ADAPTIVE_THRESH - 使用自適應閾值（通過平均圖像亮度計算得到）將圖像轉換爲黑白圖，而不是一個固定的閾值。
	#CV_CALIB_CB_NORMALIZE_IMAGE - 在利用固定閾值或者自適應的閾值進行二值化之前，先使用cvNormalizeHist來均衡化圖像亮度。
	#CV_CALIB_CB_FILTER_QUADS - 使用其他的準則（如輪廓面積，周長，方形形狀）來去除在輪廓檢測階段檢測到的錯誤方塊
	
    #TODO 13 : find the image point by openCV
	ret,corners= cv2.findChessboardCorners(gray, CHECKERBOARD,None)
	#print("ret=",ret)
	#print("corners=",corners)
	if ret == True:	
		objpoints.append(objp)
		#cv::cornerSubPix()对检测到的角点作进一步的优化计算，可使角点的精度达到亚像素级别
		#void cv::cornerSubPix(
		#cv::InputArray image, 			// 输入图像
		#cv::InputOutputArray corners, 	// 角点（既作为输入也作为输出）
		#cv::Size winSize, 				// 区域大小为 NXN; N=(winSize*2+1)
		#cv::Size zeroZone, 			// 类似于winSize，但是总具有较小的范围，Size(-1,-1)表示忽略
		#cv::TermCriteria criteria 		// 停止优化的标准);
		cv2.cornerSubPix(gray,corners,(5,5),(-1,-1),subpix_criteria)
		imgpoints.append(corners)
	
	#double 	cv::s(
	#InputArrayOfArrays objectPoints, 
	#InputArrayOfArrays imagePoints, 
	#Size imageSize, 
	#InputOutputArray cameraMatrix, 
	#InputOutputArray distCoeffs, 
	#OutputArrayOfArrays rvecs, 
	#OutputArrayOfArrays tvecs, 
	#OutputArray stdDeviationsIntrinsics, 
	#OutputArray stdDeviationsExtrinsics, 
	#OutputArray perViewErrors, int flags=0, 
	#TermCriteria criteria=TermCriteria(TermCriteria::COUNT+TermCriteria::EPS, 30, DBL_EPSILON))

	#TOOD14 : get camera matrix and dist matrix by openCV
	ret,cameraMatrix,distCoeffs,rvecs,tvecs = cv2.calibrateCamera(objpoints, imgpoints, gray.shape, None, None)
	#print("cameraMatrix=",str(cameraMatrix.tolist()))
	#print("distCoeffs=",str(distCoeffs.tolist()))
	config['intrinsic']['ks']=str(cameraMatrix.tolist())
	config['intrinsic']['dist']=str(distCoeffs.tolist())

	#cv::getOptimalNewCameraMatrix(
	#InputArray cameraMatrix, 
	#InputArray distCoeffs, 
	#Size imageSize, 
	#double alpha, 
	#Size newImgSize=Size(), 
	#Rect *validPixROI=0, 
	#bool centerPrincipalPoint=false)
	
	#TODO15 : get optimal new camera matrix, alpha = 0
	NewcameraMatrix, validPixROI=cv2.getOptimalNewCameraMatrix(cameraMatrix,distCoeffs,img.shape[:2],alpha,img.shape[:2])
	#print("NewcameraMatrix=",str(NewcameraMatrix.tolist()))
	config['intrinsic']['newcameramtx']=str(NewcameraMatrix.tolist())

	with open('config.ini', 'w') as configfile:
		config.write(configfile)
#out for

ks = np.array(json.loads(config['intrinsic']['ks']))
dist = np.array(json.loads(config['intrinsic']['dist']))
newcameramtx = np.array(json.loads(config['intrinsic']['newcameramtx'])) 
#print(ks)

#TODO16: undistortion image by openCV 
img = glob.glob(imgsPath + '*.png')
for fname in img:
	origin_img = cv2.imread(fname)
	#void cv::undistort	(	
	#InputArray 	src,
	#OutputArray 	dst,
	#InputArray 	cameraMatrix,
	#InputArray 	distCoeffs,
	#InputArray 	newCameraMatrix = noArray() 
	#)	
	undistortion_img = cv2.undistort(origin_img,ks,dist,newcameramtx)
	name = os.path.basename(fname)
	out_name = '/home/lenovo/DP/undistortion_folder/D_'+ name
	cv2.imwrite(out_name,undistortion_img) 
