from math import pi, sin, cos
 
from direct.showbase.ShowBase import ShowBase
from direct.task import Task
from direct.actor.Actor import Actor
from pandac.PandaModules import * 
from panda3d.core import Texture, TextureStage

from pandac.PandaModules import TransparencyAttrib 

 
class MyApp(ShowBase):
	#global position variables
	nx = 0.0
	ny = 0.0

	def __init__(self):
		ShowBase.__init__(self)
        # Add the spinCameraTask procedure to the task manager.
		self.taskMgr.add(self.moveCameraTask, "MoveCameraTask")
		base.setBackgroundColor(0.0, 0.0, 0.0)
 
        # Load and texture a ship
		self.pandaActor = Actor("cube.egg")
		self.pandaActor.setScale(1, 1, 1)
		t1 = loader.loadTexture("progart.png")
		t2 = TextureStage("progart.png")
		self.pandaActor.setTexture(t2, t1)	
		self.pandaActor.reparentTo(self.render)
 
    # Define procedures to move the camera.
	def moveforward(self):
		self.ny -= 0.001
	def moveback(self):
		self.ny += 0.001
	def moveright(self):
		self.nx -= 0.001
	def moveleft(self):
		self.nx += 0.001
	#update camera position
	def moveCameraTask(self, task):
		self.accept("w", self.moveforward)
		self.accept("s", self.moveback)
		self.accept("d", self.moveright)
		self.accept("a", self.moveleft)
		
		self.camera.setPos(self.nx, self.ny, 20)
		#self.pandaActor.setPos(0, 0, 3)
		self.camera.lookAt(self.pandaActor)
		return Task.cont
	


			
				

app = MyApp()
app.run()