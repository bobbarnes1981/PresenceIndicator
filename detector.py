import sqlite3
import subprocess
from time import sleep
from threading import Thread

class Device(object):
	def __init__(self, mac, hostname, alias, ip, connected):
		self.mac = mac
		self.hostname = hostname
		self.alias = alias
		self.ip = ip
		self.connected = connected

class Detector(object):
	def __init__(self):
		self.db_name = 'presence.db'
		self.create()
		self.update([])
	def create(self):
		con = sqlite3.connect(self.db_name)
		cur = con.cursor()
		cur.execute('''
			CREATE TABLE IF NOT EXISTS devices (
				mac TEXT
					CONSTRAINT mac_pk PRIMARY KEY
					CONSTRAINT mac_unique UNIQUE
					CONSTRAINT mac_notnull NOT NULL,
				hostname TEXT,
				alias TEXT,
				ip TEXT,
				connected INTEGER);
		''')
		con.commit()
		con.close()
	def update(self, devices):
		con = sqlite3.connect(self.db_name)
		cur = con.cursor()
		cur.execute('''
			UPDATE devices SET connected = 0;
		''')
		for device in devices:
			cur.execute('''
				SELECT mac FROM DEVICES WHERE mac = ?
			''', (device.mac,))
			if cur.fetchone():
				cur.execute('''
					UPDATE devices SET
					hostname = ?,
					ip = ?,
					connected = 1
					WHERE mac = ?
				''', (device.hostname, device.ip, device.mac))
			else:
				cur.execute('''
					INSERT INTO devices
					(mac, hostname, alias, ip, connected)
					VALUES
					(?, ?, ?, ?, ?);
				''', (device.mac, device.hostname, device.alias, device.ip, 1))
		con.commit()
		con.close()
	def start(self):
		self.running = True
		while self.running == True:
			found_devices = []
			result = subprocess.check_output('sudo arp-scan -l', shell=True)
			lines = result.split('\n')
			#start at 2 so we miss the header
			for i in range(2, len(lines)):
				if lines[i] == '':
					# break at first space (end of list)
					break
				data = lines[i].split('\t')
				device = Device(data[1], data[2], '', data[0], 1)
				found_devices.append(device)
			self.update(found_devices)
			sleep(10)
	def stop(self):
		self.running = False
	def get_devices(self):
		con = sqlite3.connect(self.db_name)
		cur = con.cursor()
		cur.execute('''
				SELECT mac, hostname, alias, ip, connected FROM devices;
			''')
		devices = []
		for row in cur.fetchall():
			devices.append(Device(row[0], row[1], row[2], row[3], row[4]))
		con.close()
		return devices
	def get_device(self, mac):
		con = sqlite3.connect(self.db_name)
		cur = con.cursor()
		cur.execute('''
				SELECT mac, hostname, alias, ip, connected FROM devices WHERE mac = ?;
			''', (mac,))
		row = cur.fetchone()
		device = Device(row[0], row[1], row[2], row[3], row[4])
		con.close()
		return device
	def set_alias(self, mac, alias):
		con = sqlite3.connect(self.db_name)
		cur = con.cursor()
		cur.execute('''
				UPDATE devices SET alias = ? WHERE mac = ?;
			''', (alias, mac))
		con.commit()
		con.close()

detector = Detector()
t = Thread(target=detector.start)
t.start()
while True:
	cmd = raw_input('cmd>')
	if cmd == 'q':
		detector.stop()
		break
	elif cmd == 'i':
		devices = detector.get_devices()
		for device in devices:
			print('--------------------')
			print(device.mac)
			print(device.hostname)
			print(device.alias)
			print(device.ip)
	elif cmd == 's':
		mac = raw_input('mac>')
		device = detector.get_device(mac)
		print('--------------------')
		print(device.mac)
		print(device.hostname)
		print(device.alias)
		print(device.ip)
		alias = raw_input('alias>')
		detector.set_alias(mac, alias)
		device = detector.get_device(mac)
		print('--------------------')
		print(device.mac)
		print(device.hostname)
		print(device.alias)
		print(device.ip)
	else:
		print('[q]uit\n[i]nfo\n[s]et')

