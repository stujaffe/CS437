
import picar_4wd as fc
import time

if __name__ == "__main__":

    speed = 10
    
    fc.forward(speed)

    time.sleep(5)

    fc.stop()

