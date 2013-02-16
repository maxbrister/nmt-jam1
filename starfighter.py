from math import pi, sin, cos
from direct.showbase.ShowBase import ShowBase
from direct.task import Task
from direct.actor.Actor import Actor
from pandac.PandaModules import * 
from panda3d.core import Texture, TextureStage
from pandac.PandaModules import TransparencyAttrib 
from direct.gui.OnscreenImage import OnscreenImage
from random import *

 
class Game(ShowBase):

	def __init__(self):
		ShowBase.__init__(self)
		#these store your position on the X/Y plane
		self.nx = 0.0
		self.ny = 0.0
		
		#setup collision detection
		#Since we are using collision detection to do picking, we set it up like
		#any other collision detection system with a traverser and a handler
		self.picker = CollisionTraverser()            #Make a traverser
		self.pq     = CollisionHandlerQueue()         #Make a handler
		#Make a collision node for our picker ray
		self.pickerNode = CollisionNode('mouseRay')
		#Attach that node to the camera since the ray will need to be positioned
		#relative to it
		self.pickerNP = camera.attachNewNode(self.pickerNode)
		#Everything to be picked will use bit 1. This way if we were doing other
		#collision we could seperate it
		self.pickerNode.setFromCollideMask(BitMask32.bit(1))
		self.pickerRay = CollisionRay()               #Make our ray
		self.pickerNode.addSolid(self.pickerRay)      #Add it to the collision node
		#Register the ray as something that can cause collisions
		self.picker.addCollider(self.pickerNP, self.pq)
		#self.picker.showCollisions(render)
 
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
		self.accept("mouse1", self.pickObject)
		
		self.camera.setPos(self.nx, self.ny, 20)
		#self.camera.lookAt(self.testShip)
		self.camera.setHpr(0,-75,0)
		return Task.cont
		
	def pickObject(self):
		#Check to see if we can access the mouse. We need it to do anything else
		if base.mouseWatcherNode.hasMouse():
			#get the mouse position
			mpos = base.mouseWatcherNode.getMouse()
		  
			#Set the position of the ray based on the mouse position
			self.pickerRay.setFromLens(base.camNode, mpos.getX(), mpos.getY())
			nearPoint = render.getRelativePoint(camera, self.pickerRay.getOrigin())
			#Same thing with the direction of the ray
			nearVec = render.getRelativeVector(camera, self.pickerRay.getDirection())
		  
			self.picker.traverse(render)
			
			if self.pq.getNumEntries() > 0:
				#if we have hit something, sort the hits so that the closest
				#is first, and highlight that node
				self.pq.sortEntries()
				i = int(self.pq.getEntry(0).getIntoNode().getTag('pickable'))
				print i
				return None
			print "No objects found!"
			return None
     
		
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
			self.star.setTag('pickable', str(i))
			#self.star.find("**/polygon").node().setIntoCollideMask( BitMask32.bit(1))

		
	

	


			
				

app = Game()
app.run()