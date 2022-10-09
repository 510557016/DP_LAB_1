#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Sep 30 14:40:52 2022

@author: LOYICHUN
"""

import paho.mqtt.client as mqtt
import time
import json
import threading
import logging
import numpy as np
import cv2
import os
import base64
import pickle
import matplotlib.pylab as plt

#定義0I0P
NCTU_IP = "140.113.208.103"
LOCAL_IP = "127.0.0.1"
brokerIP = NCTU_IP

clients=[
{"broker":brokerIP,"port":1883,"name":"blank","sub_topic":"deep_learn_lecture_5","pub_topic":"deep_learning_lecture_5"},
{"broker":brokerIP,"port":1883,"name":"blank","sub_topic":"secret_photo_5"      ,"pub_topic":"deep_learning_lecture_5"},
{"broker":brokerIP,"port":1883,"name":"blank","sub_topic":"server_response_5"   ,"pub_topic":"deep_learning_lecture_5"},
{"broker":brokerIP,"port":1883,"name":"blank","sub_topic":"dist_data"           ,"pub_topic":"deep_learning_lecture_5"}
]

nclients=len(clients)
out_queue=[] 

def coverToCV2(data):
   imdata = base64.b64decode(data)
   buf = pickle.loads(imdata)
   image = cv2.imdecode(buf,cv2.IMREAD_COLOR)
   return image

#判斷內容
def on_message(client, userdata, message):
   time.sleep(1)
   
   topic = message.topic
   #msg=str(message.payload.decode('utf-8'))
   cmds = json.loads(message.payload)
   #print("on message topic=",topic)
   #print("on message cmds=",cmds)
   
   #每次都去判斷讀回覆的內容
   if 'text' in cmds:
      #訊息寫入 out list
      out_queue.append(cmds['text'])
      time.sleep(2)
      #print("queue length=",len(out_queue))
      for x in range(len(out_queue)):
         print(out_queue.pop())
   #回覆data寫入檔案
   if 'data' in cmds:  
      for i in range(len(cmds['data'])):
         img = coverToCV2(cmds['data'][i])
         filename = 'photo_'+ str(i) + '.png' 
         cv2.imwrite('/home/lenovo/DP/receive_folder/'+filename,img)
         if not os.path.exists('undistortion_folder'):  
            os.makedirs('undistortion_folder')
   
   if 'dist_data' in cmds:
      #print("cmds=",cmds)
      #img = coverToCV2(cmds['dist_data'][i])
      img = coverToCV2(cmds['dist_data'])
      cv2.imwrite('/home/lenovo/DP/receive_folder/dist_image.png',img)

   #寫完後魚眼   
      os.system('python3.8 undistortion.py')
        
      
#TODO3 : set topic you want to subscribe  
def on_connect(client, userdata, flags, rc):
	#print("connect with result code:"+str(rc))
	if rc==0:
		client.connected_flag=True #set flag
		#print("client=",client)
		for i in range(nclients):
			if clients[i]["client"]==client: 
				topic=clients[i]["sub_topic"]
				break
			
		print("sub_topic =",topic)
		client.subscribe(topic)
	else:
		print("Bad connection Returned code=",rc)
		client.loop_stop() 

def on_disconnect(client, userdata, rc):
   pass
   print("client disconnected ok")

#TODO2 : setup MQTT client
def Create_connections():
   for i in range(nclients):
      cname="client"+str(i) # 幾個 client
      t=int(time.time()) #unix time
      client_id =cname+str(t) #create unique client_id
      client = mqtt.Client(client_id)             #create new instance
      #將 address,id,name 加入 clients[i]
      clients[i]["client"]=client 
      clients[i]["client_id"]=client_id
      clients[i]["cname"]=cname
      #print("clients[i] Addr",clients[i]["client"])
      #print("clients[i]=",clients[i])
      #取出 client[i] broker port
      broker=clients[i]["broker"]
      port=clients[i]["port"]
      try:
         client.connect(broker,port)           #establish connection
      except:
         print("Connection Fialed to broker ",broker)
         continue
    
      client.on_connect = on_connect
      client.on_disconnect = on_disconnect
      #client.on_publish = on_publish
      client.on_message = on_message
      while not client.connected_flag:
         client.loop(0.01) #check for messages
         time.sleep(0.05)

#thread loop
def multi_loop(nclients,flag=True):
   while flag:
      for i in range(nclients):
         client=clients[i]["client"]
         client.loop(0.01)         

#start program
mqtt.Client.connected_flag=False 
no_threads=threading.active_count()
print("current threads =",no_threads)
print("Creating Connections ",nclients," clients")

Create_connections()
#start thread run multi loop 
t = threading.Thread(target=multi_loop,args=(nclients,True))
t.start()
print("All clients connected ")
time.sleep(5)

count = 0
no_threads=threading.active_count()
print("current threads =",no_threads)
print(" === Start Publishing === ")
#TODO6 : setup MQTT client

#TODO7 : send msg to get echo
client=clients[0]["client"]
pub_topic=clients[0]["pub_topic"]
payload = {'text' : "test hello" }
if client.connected_flag:
	client.publish(pub_topic,json.dumps(payload))
	time.sleep(0.1)
	print("publishing client 0 : send msg to get echo")

#TODO8 : send msg to get hint
client=clients[1]["client"]
pub_topic=clients[1]["pub_topic"]
payload = {'request' : "photo" }
if client.connected_flag:
   if not os.path.exists('receive_folder'):  
         os.makedirs('receive_folder')
   
   client.publish(pub_topic,json.dumps(payload))
   time.sleep(0.1)
   print("publishing client 1 : send msg to get hint") 

#TODO9 : send msg to get 10 photo
client=clients[2]["client"]
pub_topic=clients[2]["pub_topic"]
payload = {'request' : "EC234_NOL" }
if client.connected_flag:
   client.publish(pub_topic,json.dumps(payload))
   time.sleep(0.1)
   print("publishing client 2 : send msg to get 10 photo")      

#TODO9 : send msg to get 1 photo undistort
client=clients[3]["client"]
pub_topic=clients[3]["pub_topic"]
payload = {'request' : 'dist_photo' }
if client.connected_flag:
   client.publish(pub_topic,json.dumps(payload))
   time.sleep(0.1)
   print("publishing client 3 : send msg to get 1 photo undistort")  
