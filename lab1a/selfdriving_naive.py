import picar_4wd as fc
import logging
import time
import random

class NaiveSD(object):
	def __init__(self, angle_range: int = 120, us_step: int = 20, speed: int = 10) -> None:
		self.distance_to_obj = -2
		self.current_angle = 0
		self.angle_range = angle_range
		self.max_angle = self.angle_range/2
		self.min_angle = self.angle_range/2*-1
		self.us_step = us_step
		self.speed = speed
		self.logger = logging.getLogger()
		logging.basicConfig(format='%(asctime)s,%(msecs)03d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s',
    			datefmt='%Y-%m-%d:%H:%M:%S',
    			level=logging.DEBUG)
		fc.servo.set_angle(0)
	
	def get_distance(self) -> int:
		"""
		Gets the distance reading from the Ultrasonic sensor.
		"""
		dist = fc.us.get_distance()
		self.logger.info(f"Distance from object: {dist}cm")
		return dist
	
	def scan_step_nsd(self) -> None:
		"""
		Uses the Servo/Ultrasonic sensor to scan the immediate area and return the distance.
		Borrows code from the picar_4wd.__init__.scan_step() and picar4wd.__init__.get_distance_at() methods.
		"""
		self.current_angle += self.us_step
		if self.current_angle >= self.max_angle:
			self.current_angle = self.max_angle
			self.us_step = self.us_step*-1
		elif self.current_angle <= self.min_angle:
			self.current_angle = self.min_angle
			self.us_step = self.us_step*-1
		
		fc.servo.set_angle(self.current_angle)
		self.distance_to_obj = self.get_distance()
		self.logger.info(f"Set distance to object at {self.distance_to_obj}cm for angle {self.current_angle}")
		time.sleep(0.04)
		
		return None
	
	def avoid_object(self) -> None:
		"""
		Stops the car and reverses it to avoid potential object.
		"""
		self.logger.info("Detected potential object. Stopping and reversing.")
		fc.stop()
		fc.backward(self.speed)
		backward_time = random.uniform(0.5,1)
		time.sleep(backward_time)

		return None
	
	def new_direction(self) -> None:
		"""
		Uses the random library to determine which direction to turn in a 50/50 split. Then sleeps for a given amount
		of time so the car has time to make the turn.
		"""
		# random.random() returns a float from [0.0,1.0)
		if random.random() < 0.5:
			fc.turn_left(75)
			self.logger.info("Turning left")
		else:
			fc.turn_right(75)
			self.logger.info("Turning right")
		turn_time = random.uniform(0.5,1)
		time.sleep(turn_time)

	def drive(self) -> None:
		"""
		Primary drive function.
		"""
		while True:
			fc.forward(self.speed)
			self.scan_step_nsd()
			self.logger.info(f"Current distance to object: {self.distance_to_obj}.")
			if self.distance_to_obj < 20 and self.distance_to_obj > -2:
				self.avoid_object()
				self.new_direction()
				fc.forward(self.speed)

if __name__ == "__main__":
	try:
		roomba = NaiveSD()
		roomba.drive()
	finally:
		fc.stop()

