from math import pi, sin, cos
from direct.showbase.ShowBase import ShowBase
from direct.task import Task
from direct.actor.Actor import Actor
from pandac.PandaModules import * 
from panda3d.core import Texture, TextureStage
from pandac.PandaModules import TransparencyAttrib 
from direct.gui.OnscreenImage import OnscreenImage
import direct.directbase.DirectStart
from panda3d.core import CollisionTraverser,CollisionNode
from panda3d.core import CollisionHandlerQueue,CollisionRay
from panda3d.core import AmbientLight,DirectionalLight,LightAttrib
from panda3d.core import TextNode
from panda3d.core import Point3,Vec3,Vec4,BitMask32
from direct.gui.OnscreenText import OnscreenText
from direct.showbase.DirectObject import DirectObject
from direct.task.Task import Task
from random import * 
import sys


#First we define some contants for the colors
BLACK = Vec4(0,0,0,1)
WHITE = Vec4(1,1,1,1)
HIGHLIGHT = Vec4(0,1,1,1)

#Now we define some helper functions that we will need later

def PointAtZ(z, point, vec):
  return point + vec * ((z-point.getZ()) / vec.getZ())

#A handy little function for getting the proper position for a given square
def starPos(dist):
  return random()*dist, random()*dist, random()*dist

class World(DirectObject):
  def __init__(self):
    #define positional variables
    self.nx = 0.0
    self.ny = 0.0
	
	#define a current target position
    self.target = (0,0,0)

	#initialize a camera
    base.disableMouse()                          #Disble mouse camera control
    base.camera.setPosHpr(0, -13.75, 6, 0, -25, 0)    #Set the camera

	#set up mouse picking
    self.picker = CollisionTraverser()            #Make a traverser
    self.pq = CollisionHandlerQueue()         #Make a handler
    self.pickerNode = CollisionNode('mouseRay')
    self.pickerNP = base.camera.attachNewNode(self.pickerNode)
    self.pickerNode.setFromCollideMask(BitMask32.bit(1))
    self.pickerRay = CollisionRay()               #Make our ray
    self.pickerNode.addSolid(self.pickerRay)      #Add it to the collision node
    self.picker.addCollider(self.pickerNP, self.pq)
	
    #Add a star plane
    b=OnscreenImage(parent=render2d, image="sprites/stars.jpg") 
    base.cam.node().getDisplayRegion(0).setSort(20)

    #add a task for moving the camera
    taskMgr.add(self.moveCameraTask, "MoveCameraTask")
    base.setBackgroundColor(0.0, 0.0, 0.0)

	#make some stars
    starIndex = self.makeStars(10, 5)
	
	#make some ships (this is a test function, and should be replaced by our real ship-spawning code ASAP)
    self.selected = starIndex = self.testShips(5, 2)

    #This will represent the index of the currently highlited square
    self.hiSq = False

    #Start the task that handles the picking
    self.mouseTask = taskMgr.add(self.mouseTask, 'mouseTask')

	#Start the task that handles the picking
    self.moveShipsTask = taskMgr.add(self.moveShipsTask, 'moveShipsTask')
	
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
		
    base.camera.setPos(self.nx, self.ny, 20)
    #self.camera.lookAt(self.testShip)
    base.camera.setHpr(0,-75,0)
    return Task.cont

  def mouseTask(self, task):
    #This task deals with the highlighting and dragging based on the mouse
    
    #First, clear the current highlight
    if self.hiSq is not False:
      self.starEntities[self.hiSq].setColor(WHITE)
      self.hiSq = False
      
    #Check to see if we can access the mouse. We need it to do anything else
    if base.mouseWatcherNode.hasMouse():
      #get the mouse position
      mpos = base.mouseWatcherNode.getMouse()
      
      #Set the position of the ray based on the mouse position
      self.pickerRay.setFromLens(base.camNode, mpos.getX(), mpos.getY())
      
      #Do the actual collision pass (Do it only on the starEntities for
      #efficiency purposes)
      self.picker.traverse(self.stars)
      if self.pq.getNumEntries() > 0:
        #if we have hit something, sort the hits so that the closest
        #is first, and highlight that node
        self.pq.sortEntries()
        i = int(self.pq.getEntry(0).getIntoNode().getTag('square'))
        #Set the highlight on the picked square
        self.starEntities[i].setColor(HIGHLIGHT)
        self.hiSq = i
        self.highlighted = (self.starEntities[i].getX(), self.starEntities[i].getY(), self.starEntities[i].getZ())
	
	#allow the user to input a destination
    self.accept("mouse1", self.updateTarget)
		
    return Task.cont
  def updateTarget(self):
    self.target = self.highlighted
  
  def makeStars(self, number, dist):
    self.stars = render.attachNewNode("starnode")
    self.starEntities = [None for i in range(number)]
    for i in range(number):
      #Load, parent, color, and position the model (a single square polygon)
      self.starEntities[i] = loader.loadModel("models/square")
      self.starEntities[i].reparentTo(self.stars)
      self.starEntities[i].setPos(starPos(dist))
      self.starEntities[i].setColor(WHITE)
      self.starEntities[i].find("**/polygon").node().setIntoCollideMask(BitMask32.bit(1))
      self.starEntities[i].find("**/polygon").node().setTag('square', str(i))
      t1 = loader.loadTexture("sprites/star1.png")
      t2 = TextureStage("sprites/star1.png")
      self.starEntities[i].setTexture(t2, t1)	
      self.starEntities[i].setScale(2,2,2)	
      self.starEntities[i].setTransparency(1) 	  
    return self.starEntities

  def testShips(self, number, dist):
    self.ships = render.attachNewNode("shipnode")
    self.shipEntities = [None for i in range(number)]
    for i in range(number):
      #Load, parent, color, and position the model (a single square polygon)
      self.shipEntities[i] = loader.loadModel("models/square")
      self.shipEntities[i].reparentTo(self.stars)
      self.shipEntities[i].setPos(starPos(dist))
      self.shipEntities[i].setColor(WHITE)
      self.shipEntities[i].find("**/polygon").node().setIntoCollideMask(BitMask32.bit(1))
      self.shipEntities[i].find("**/polygon").node().setTag('square', str(i))
      t1 = loader.loadTexture("sprites/progart.png")
      t2 = TextureStage("sprites/star1.png")
      self.shipEntities[i].setTexture(t2, t1)
      self.shipEntities[i].setScale(0.3,0.3,0.3)		  
      self.shipEntities[i].setTransparency(1) 	  
    return self.shipEntities

  def moveShipsTask(self, task):
    for i, ship in enumerate(self.selected):
      x = ship.getX()
      y = ship.getY()
      z = ship.getZ()
      nx = self.target[0] + i/10.0
      ny = self.target[1] 
      nz = self.target[2]
	  
      print nx, ny, nz
      print x, y, z
	  
      if x > nx: x -= 0.1
      if x < nx: x += 0.1	 
      if y > ny: y -= 0.1
      if y < ny: y += 0.1
      if z > nz: z -= 0.1
      if z < nz: z += 0.1	  
      ship.setPos(x,y,z)
    return Task.cont


	
#Do the main initialization and start 3D rendering
w = World()
run()

