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
    #make some stars
    self.initCamera()
    self.initPicker()
    self.stars = self.makeStars(10, 10)
    taskMgr.add(self.moveCameraTask, "MoveCameraTask")
    taskMgr.add(self.mouseTask, 'mouseTask')  
	
  def makeStars(self, number, dist):
    starEntities = []
    for i in range(number):
      starEntities.append(Star(dist,i))
    return starEntities
    
  def initCamera(self):
	#initialize a camera
    base.disableMouse()                          #Disble mouse camera control
    base.camera.setPosHpr(0, -13.75, 6, 0, -25, 0)    #Set the camera  
    b=OnscreenImage(parent=render2d, image="sprites/stars.jpg") 
    base.cam.node().getDisplayRegion(0).setSort(20)    

  def initPicker(self):
    #This will represent the index of the currently highlited square
    self.hiSq = False
    #define positional variables
    self.nx = 0.0
    self.ny = 0.0
	  #set up mouse picking
    self.picker = CollisionTraverser()            #Make a traverser
    self.pq = CollisionHandlerQueue()         #Make a handler
    self.pickerNode = CollisionNode('mouseRay')
    self.pickerNP = base.camera.attachNewNode(self.pickerNode)
    self.pickerNode.setFromCollideMask(BitMask32.bit(1))
    self.pickerRay = CollisionRay()               #Make our ray
    self.pickerNode.addSolid(self.pickerRay)      #Add it to the collision node
    self.picker.addCollider(self.pickerNP, self.pq)
	
  def mouseTask(self, task):
    if self.hiSq is not False:
      self.stars[self.hiSq].model.setColor(WHITE)
      self.hiSq = False
	  #define some temp variables
    i = None
    #Check to see if we can access the mouse. We need it to do anything else
    if base.mouseWatcherNode.hasMouse():
      #get the mouse position
      mpos = base.mouseWatcherNode.getMouse()
      #Set the position of the ray based on the mouse position
      self.pickerRay.setFromLens(base.camNode, mpos.getX(), mpos.getY())
      self.starNode = render.attachNewNode("starnode")
      for star in self.stars:
        star.model.reparentTo(self.starNode)
      self.picker.traverse(self.starNode)
      if self.pq.getNumEntries() > 0:
        self.pq.sortEntries()
        try:
          i = int(self.pq.getEntry(0).getIntoNode().getTag('star'))
        except:
          i = None
        #Set the highlight on the picked square
        if i: self.stars[i].model.setColor(HIGHLIGHT)
        if i: self.hiSq = i
        if i: self.highlighted = (self.stars[i].getPosition())
	
	#allow the user to input a destination
    #if i: self.accept("mouse1", self.updateTarget)
    return Task.cont

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
  # Define procedures to move the camera.
  def moveForward(self):
     self.ny += 0.5
  def moveBack(self):
    self.ny -= 0.5
  def moveRight(self):
    self.nx += 0.5
  def moveLeft(self):
    self.nx -= 0.5

class Star(DirectObject):
  def __init__(self, dist, i):
    self.pos = (random() * dist, random() * dist, random() * dist)
    self.model = loader.loadModel("models/square")
    self.model.setPos(starPos(dist))
    self.model.setColor(WHITE)
    self.model.find("**/polygon").node().setIntoCollideMask(BitMask32.bit(1))
    self.model.find("**/polygon").node().setTag('star', str(i))
    t1 = loader.loadTexture("sprites/star1.png")
    t2 = TextureStage("sprites/star1.png")
    self.model.setTexture(t2, t1)	
    self.model.setScale(2,2,2)	
    self.model.setTransparency(1)
  def getPosition(self):
    return self.pos 
    

	
#Do the main initialization and start 3D rendering
w = World()
run()

