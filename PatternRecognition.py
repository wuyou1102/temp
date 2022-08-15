# coding=utf-8
import cv2
import gc
import scipy
import threading

lock = threading.Lock()


def query_image_sift(part, whole):
    global lock
    lock.acquire()
    try:
        import os
        img1 = cv2.imread(part, 0)
        img2 = cv2.imread(whole, 0)

        # Initiate SIFT detector
        # sift = cv2.SIFT()
        sift = cv2.SIFT_create()
        print("sssssssssssssssss")
        # find the keypoints and descriptors with SIFT
        kp1, des1 = sift.detectAndCompute(img1, None)
        print("sssssssssssssssss")
        kp2, des2 = sift.detectAndCompute(img2, None)
        print("sssssssssssssssss")
        index_params = dict(algorithm=0, trees=5)
        search_params = dict(checks=50)  # or pass empty dictionary
        flann = cv2.FlannBasedMatcher(index_params, search_params)
        print("sssssssssssssssss")
        matches = flann.knnMatch(des1, des2, k=2)
        goods = list()
        point_list = list()
        print("sssssssssssssssss")
        for m, n in matches:
            if m.distance < 0.75 * n.distance:
                point_list.append((kp2[m.trainIdx].pt[0], kp2[m.trainIdx].pt[1]))
                goods.append(m)
        __draw_matches_sift(img1, kp1, img2, kp2, matches=goods)
        print(float(len(goods)) / len(matches))
        if float(len(goods)) / len(matches) < 0.2:
            return False
        del img1
        del img2
        gc.collect()
    finally:
        lock.release()
    print("sssssssssssssssss")
    return __centre_point(point_list=point_list)


def __draw_matches_sift(img1, kp1, img2, kp2, matches):
    """
    img1,img2 - Grayscale images
    kp1,kp2 - Detected list of keypoints through any of the OpenCV keypoint
              detection algorithms
    matches - A list of matches of corresponding keypoints through any
              OpenCV keypoint matching algorithm
    """
    rows1, cols1 = img1.shape[:2]
    rows2, cols2 = img2.shape[:2]
    view = scipy.zeros((max([rows1, rows2]), cols1 + cols2, 3), scipy.uint8)
    # Place the first image to the left
    view[:rows1, :cols1, 0] = img1
    # Place the next image to the right of it
    view[:rows2, cols1:, 0] = img2
    view[:, :, 1] = view[:, :, 0]
    view[:, :, 2] = view[:, :, 0]
    for match in matches:
        # draw the keypoints
        # print m.queryIdx, m.trainIdx, m.distance
        color = tuple([scipy.random.randint(0, 255) for _ in range(3)])
        # print 'kp1,kp2',kp1,kp2
        cv2.line(view, (int(kp1[match.queryIdx].pt[0]), int(kp1[match.queryIdx].pt[1])),
                 (int(kp2[match.trainIdx].pt[0] + cols1), int(kp2[match.trainIdx].pt[1])), color)
        # Show the image
    cv2.imshow('Matched Features', view)
    cv2.waitKey(0)
    cv2.destroyWindow('Matched Features')
    # from scipy import misc
    # misc.imsave('lena_new_sz.png', view)


def __centre_point(point_list):
    x_list = list()
    y_list = list()
    for x, y in point_list:
        x_list.append(x)
        y_list.append(y)
    avg_x = sum(x_list) / len(x_list)
    avg_y = sum(y_list) / len(y_list)
    return (avg_x), int(avg_y)


if __name__ == '__main__':
    query_image_sift(
        part=r'C:/Users/YouWu/Pictures/2.png',
        whole=r'C:/Users/YouWu/Pictures/1.png')
