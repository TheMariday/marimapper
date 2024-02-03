import cv2

def moment_test(image):

    image_grey = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    ret, image_thresh = cv2.threshold(image_grey, 64, 255, cv2.THRESH_TOZERO)

    contours, hierarchy = cv2.findContours(image_thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    cv2.drawContours(image, contours, -1, (255, 0, 0), 1)

    m = cv2.moments(image_thresh)

    if m["m00"] > 0:

        center_of_mass = (int(m["m10"] / m["m00"]), int(m["m01"] / m["m00"]))

        cv2.drawMarker(image, center_of_mass, (0,255,0) ,thickness=2)