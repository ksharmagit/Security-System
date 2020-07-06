import numpy as np
import cv2
import time
import os
from os import listdir
from os.path import isfile, join
import imutils
import datetime
import requests
from enum import Enum
from twilio.rest import Client
import winsound

account_sid = 'your-account-sid-from-twilio'
auth_token = 'your-auth-token-from-twilio'
client = Client(account_sid, auth_token)

cap = cv2.VideoCapture(1)
start_time = time.time()
frame_array = []

# Make sure that images folder already exists
pathOut = './images/'
fps = 4
timelapse = 0.25
image_counter = 0
min_delta_area = 500
scale_percent = 60 	
text = "Unoccupied"

class MODE(Enum):
	OCCUPIED = 0
	UNOCCUPIED = 1
state = MODE.UNOCCUPIED

print ("Starting the video capture ...")
time.sleep(10)
print ("Started.")

# Reading the first frame
ret, frame = cap.read()
firstFrame = cv2.createBackgroundSubtractorMOG2(600, 200, True)
#firstFrame = cv2.createBackgroundSubtractorKNN()

# Calculate the desired height and width of the frames
width = int(frame.shape[1] * scale_percent / 100)
height = int(frame.shape[0] * scale_percent / 100)
print ("Width = " + str(width) + " Height = " + str(height))
dim = (width, height)

print ("First frame captured")

while(True):

	time.sleep(timelapse)
	
	ret, frame = cap.read()
	
	if not ret:
		continue
	
	image_counter += 1
	
	# resize the captured frame
	resizedFrame = cv2.resize(frame, dim, interpolation = cv2.INTER_AREA)

	# fetch the foreground mask
	fgmask = firstFrame.apply(resizedFrame)
	
	# Count the pixels disturbed
	pixel_disturbances = np.count_nonzero(fgmask)
	
	print("Frame: %d, Pixel Count: %d" % (image_counter, pixel_disturbances))
	
	if(image_counter > 1 and pixel_disturbances > 1500):
		if(state == MODE.UNOCCUPIED):						# We're switching from unoccupied to occupied. Start the alarm
			print ("Starting the alarm")
			winsound.PlaySound("alarm.wav", winsound.SND_ASYNC | winsound.SND_ALIAS )
			state = MODE.OCCUPIED
			print ("Sending text to alert")
			message = client.messages \
               .create(
                     body="Motion detected in the patio. Check out the recorded video",
                     from_='+your-twilio-number',
                     to='+your-registered-phone-number-with-twilio'
                 )
		cv2.putText(resizedFrame, "Movement Detected", (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2, cv2.LINE_AA)
		frame_array.append(resizedFrame)
		print ("Stored frame array length is now " + str(len(frame_array)))
	else:
		if(state == MODE.OCCUPIED):							# We're switching from occupied to unoccupied. Save the files
			winsound.PlaySound(None, winsound.SND_ASYNC)	# stop the alarm
			video_location = pathOut + "video" + str(datetime.datetime.now().strftime("%d-%B-%Y-%I-%M-%S%p")) + ".avi"
			print ("Video location is " + video_location)
			out = cv2.VideoWriter(video_location,cv2.VideoWriter_fourcc(*'DIVX'), fps, dim)
			for i in range(len(frame_array)):
				print("Writing frame " + str(i) + " to the video file")
				#cv2.imwrite( "./images/frame" + str(i) + ".jpg", frame_array[i])
				out.write(frame_array[i])					# writing to the video file
			out.release()
			frame_array.clear()
			state = MODE.UNOCCUPIED
			print ("Frame array length is now " + str(len(frame_array)))

	cv2.putText(resizedFrame, datetime.datetime.now().strftime("%d %B %Y %I:%M:%S%p"), (170, 235), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 0, 255), 1, cv2.LINE_AA)
	cv2.imshow('Frame', resizedFrame)
	cv2.imshow('Mask', fgmask)
	
	if cv2.waitKey(1) & 0xFF == ord('q'):	# If 'q' pressed, break out of the loop
		break

# When everything is done, release the capture
ca1p.release()
cv2.destroyAllWindows()
