import threading
import csv
import traceback
from cyber.python.cyber_py3 import cyber
from modules.localization.proto.imu_pb2 import CorrectedImu
from modules.localization.proto.gps_pb2 import Gps
from modules.perception.proto.perception_obstacle_pb2 import PerceptionObstacles
from modules.drivers.proto.sensor_image_pb2 import CompressedImage
import zmq






# odometry_file_name = "odometry_messages.csv"
# imu_file_name = "imu_message.csv"
# perception_obstacles_file_name = "perception_obstacles.csv"




# def imu_message_parser_callback(data, socket):
	# print('imu', data)
	# global imu_file_name
	# try:
	# 	csv_is_empty = check_csv_file_empty(imu_file_name)
	#
	# 	with open(imu_file_name, mode='a') as csv_file:
	# 		fieldnames = ['TimeStamp','LinearAcceleration','LinearAcceleration_x','LinearAcceleration_y', 'LinearAcceleration_z',
	# 					  'AngularVelocity', 'AngularVelocity_x','AngularVelocity_y','AngularVelocity_z',
	# 					  'EulerAngles', 'EulerAngles_x','EulerAngles_y','EulerAngles_z']
	#
	# 		writer = csv.DictWriter(csv_file,fieldnames=fieldnames)
	#
	# 		if(csv_is_empty):
	# 			writer.writeheader()
	# 			csv_is_empty = False
	#
	# 		writer.writerow({'TimeStamp': data.header.timestamp_sec,
	# 						'LinearAcceleration': '',
	# 						'LinearAcceleration_x': data.imu.linear_acceleration.x,
	# 						'LinearAcceleration_y': data.imu.linear_acceleration.y,
	# 						'LinearAcceleration_z': data.imu.linear_acceleration.z,
	# 						'AngularVelocity': '',
	# 						'AngularVelocity_x': data.imu.angular_velocity.x,
	# 						'AngularVelocity_y': data.imu.angular_velocity.y,
	# 						'AngularVelocity_z': data.imu.angular_velocity.z,
	# 						'EulerAngles':'',
	# 						'EulerAngles_x': data.imu.euler_angles.x,
	# 						'EulerAngles_y': data.imu.euler_angles.y,
	# 						'EulerAngles_z': data.imu.euler_angles.z})
	#
	# except:
	# 	print(traceback.format_exc())



def odometry_message_parser_callback(data, socket):
	data_to_send = [data.header.timestamp_sec, data.header.sequence_num, data.localization.position.x, data.localization.position.y, data.localization.position.z]
	data_to_send_str = 'odometry:'+','.join([str(x) for x in data_to_send])
	socket.send_string(data_to_send_str, flags=zmq.NOBLOCK)
	# print('data_to_send_str', data_to_send_str)


def perception_obstacles_callback(data, socket):
	data_to_send = [data.header.timestamp_sec, data.header.sequence_num, len(data.perception_obstacle)]

	for i in range(len(data.perception_obstacle)):
		i_pos = [data.perception_obstacle[i].position.x, data.perception_obstacle[i].position.y, data.perception_obstacle[i].position.z]
		data_to_send.extend(i_pos)

	data_to_send_str = 'perception_obstacles:'+','.join([str(x) for x in data_to_send])
	socket.send_string(data_to_send_str, flags=zmq.NOBLOCK)
	# print('data_to_send_str', data_to_send_str)


def front_camera_callback(data, socket):

	data_to_send = [str(data.header.timestamp_sec).encode(), str(data.header.sequence_num).encode(), data.data]
	data_to_send_str = b':data_delimiter:'.join(data_to_send)
	socket.send(data_to_send_str, flags=zmq.NOBLOCK)

	# socket.send(data.data, flags=zmq.NOBLOCK)




if __name__=='__main__':
	docker_ip = "localhost"
	context = zmq.Context.instance()

	socket_odometry = context.socket(zmq.PAIR)
	socket_perception_obstacles = context.socket(zmq.PAIR)
	socket_front_camera = context.socket(zmq.PAIR)

	socket_odometry.connect("tcp://" + docker_ip + ":5561")
	socket_perception_obstacles.connect("tcp://" + docker_ip + ":5562")
	socket_front_camera.connect("tcp://" + docker_ip + ":5563")


	cyber.init()
	message_parser_node = cyber.Node("message_parser")

	message_parser_node.create_reader("/apollo/sensor/gnss/odometry", Gps, odometry_message_parser_callback, socket_odometry)
	message_parser_node.create_reader("/apollo/perception/obstacles_gt", PerceptionObstacles, perception_obstacles_callback, socket_perception_obstacles)

	message_parser_node.create_reader("/apollo/sensor/camera/front_6mm/image/compressed", CompressedImage, front_camera_callback, socket_front_camera)

	message_parser_node.spin()
	cyber.shutdown()


	socket_odometry.close()
	socket_perception_obstacles.close()
	context.term()
