from math import pi, sin, cos
from direct.showbase.ShowBase import ShowBase
from direct.task import Task
from direct.actor.Actor import Actor
from pandac.PandaModules import * 
from panda3d.core import Texture, TextureStage
from pandac.PandaModules import TransparencyAttrib 
from direct.gui.OnscreenImage import OnscreenImage
from random import *
from Picker import Picker
 
class Game(ShowBase):

	def __init__(self):
		ShowBase.__init__(self)
		#these store your position on the X/Y plane
		self.nx = 0.0
		self.ny = 0.0
		
		#create a picker for selecting entities [not currently working correctly]
		self.mousePicker=Picker() 
 
        # Add the spinCameraTask procedure to the task manager.
		self.taskMgr.add(self.moveCameraTask, "MoveCameraTask")
		base.setBackgroundColor(0.0, 0.0, 0.0)
 
        # Load and texture a ship
		self.testShip = Actor("cube.egg")
		self.testShip.setScale(0.1, 0.1, 0.01)
		t1 = loader.loadTexture("sprites/progart.png")
		t2 = TextureStage("sprites/progart.png")
		self.testShip.setTexture(t2, t1)	
		self.testShip.reparentTo(self.render)
		self.testShip.setPos(0, 0, 6)
		self.testShip.setTransparency(1) 
		self.mousePicker.makePickable(self.testShip)
		
		#spawn some stars
		self.buildStars(5,10)
		
		#Add a star plane
		b=OnscreenImage(parent=render2d, image="sprites/stars.jpg") 
		base.cam.node().getDisplayRegion(0).setSort(20)

    # Define procedures to move the camera.
	def moveForward(self):
		self.ny += 0.5
	def moveBack(self):
		self.ny -= 0.5
	def moveRight(self):
		self.nx += 0.5
	def moveLeft(self):
		self.nx -= 0.5
	#update camera position
	def moveCameraTask(self, task):
		#handle key presses
		self.accept("w", self.moveForward)
		self.accept("s", self.moveBack)
		self.accept("d", self.moveRight)
		self.accept("a", self.moveLeft)
		#handle continued key press
		self.accept("w-repeat", self.moveForward)
		self.accept("s-repeat", self.moveBack)
		self.accept("d-repeat", self.moveRight)
		self.accept("a-repeat", self.moveLeft)
		#accept mouse input
		self.accept("mouse1", self.mousePicker.printMe)
		
		self.camera.setPos(self.nx, self.ny, 20)
		#self.camera.lookAt(self.testShip)
		self.camera.setHpr(0,-75,0)
		return Task.cont
		
	def buildStars(self, number, dist):
		for i in range(0, number):
			self.star = Actor("cube.egg")
			self.star.setScale(1, 1, 0)
			t1 = loader.loadTexture("sprites/star1.png")
			t2 = TextureStage("sprites/star1.png")
			self.star.setTexture(t2, t1)	
			self.star.reparentTo(self.render)
			self.star.setPos(random()*dist, random()*dist, random()*dist)
			self.star.setTransparency(1) 
			#set a tag to the new star so we can select it
			self.mousePicker.makePickable(self.star) 
		
	

	


			
				

app = Game()
app.run()