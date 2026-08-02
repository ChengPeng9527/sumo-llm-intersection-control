from xml.etree import ElementTree as Et
import matplotlib.pyplot as plt

plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False

tree_queue = Et.parse("queue_output.xml")
root_queue = tree_queue.getroot()

queue_length_data = []
queue_time_data = []

for child in root_queue.findall("data"):
	time_step = child.attrib["timestep"]
	for lanes in child.findall("lanes"):
		step_queue_time = 0.
		step_queue_length = 0.
		for lane in lanes.findall("lane"):
			dic = lane.attrib
			queueing_time = float(dic["queueing_time"])
			queue_length = float(dic["queueing_length_experimental"])
			step_queue_time += queueing_time
			step_queue_length += queue_length
		queue_time_data.append((float(time_step), step_queue_time))
		queue_length_data.append((float(time_step), step_queue_length))

fig1, axes1 = plt.subplots(2, 1, figsize=(19.20, 10.80))
fig1.suptitle('交叉口的车流队伍总长度与总维持时间', fontsize=14, fontweight='bold', y=0.92)
x_queue_time_data, y_queue_time_data = zip(*queue_time_data)
axes1[0].plot(x_queue_time_data, y_queue_time_data, label="交叉口口排队总时长", color="#3b6291")
axes1[0].set_xlabel("仿真时间步长(s)", fontweight="bold", fontsize=12)
axes1[0].set_ylabel("交叉口队列总时长(s)", fontweight="bold", fontsize=12)
axes1[0].legend(loc="upper right", fontsize=8)

x_queue_length_data, y_queue_length_data = zip(*queue_length_data)
axes1[1].plot(x_queue_length_data, y_queue_length_data, label="交叉口口排队总长度", color="#0E986F")
axes1[1].set_xlabel("仿真时间步长(s)", fontweight="bold", fontsize=12)
axes1[1].set_ylabel("交叉口队列总长度(m)", fontweight="bold", fontsize=12)
axes1[1].legend(loc="upper right", fontsize=8)

tree_summary = Et.parse("summary.xml")
root_summary = tree_summary.getroot()

inserted_vehicles_data = []
sum_delay_data = []
mean_delay_data = []
sum_delay = 0
for child in root_summary.findall("step"):
	total_data = child.attrib
	inserted_vehicles = total_data["inserted"]
	mean_speed = total_data["meanSpeed"]
	mean_waiting_time = total_data["meanWaitingTime"]
	individual_delay = float(total_data["waiting"])
	mean_delay_data.append(float(mean_waiting_time))
	inserted_vehicles_data.append(float(inserted_vehicles))
	sum_delay += individual_delay
	sum_delay_data.append(sum_delay)

fig2,axes2 = plt.subplots(2, 1, figsize=(10.08, 10.08))
fig2.suptitle('交叉口的平均延误和总延误', fontsize=14, fontweight='bold', y=0.92)

axes2[0].plot(inserted_vehicles_data, sum_delay_data, label="交叉口总延误", color="#C1282D")
axes2[0].set_xlabel("插入车辆数(辆)", fontweight="bold", fontsize=12)
axes2[0].set_ylabel("交叉口总延误(s)", fontweight="bold", fontsize=12)
axes2[0].legend(loc="lower right", fontsize=8)

axes2[1].plot(inserted_vehicles_data, mean_delay_data, label="交叉口平均延误", color="#F29221")
axes2[1].set_xlabel("插入车辆数(辆)", fontweight="bold", fontsize=12)
axes2[1].set_ylabel("交叉口平均延误(s)", fontweight="bold", fontsize=12)
axes2[1].legend(loc="lower right", fontsize=8)

plt.show()

