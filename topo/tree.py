from mininet.topo import Topo
import sys
class Tree(Topo):
	def __init__(self):
		Topo.__init__(self)

		#switch
		rootSwitch = self.addSwitch('s1')
		leftSwitch = self.addSwitch('s2')
		midSwitch = self.addSwitch('s3')
		rightSwitch = self.addSwitch('s4')

		# host 
		host1 = self.addHost('h1')
		host2 = self.addHost('h2')
		host3 = self.addHost('h3')
		host4 = self.addHost('h4')
		host5 = self.addHost('h5')

		# links 
		self.addLink(rootSwitch, leftSwitch)
		self.addLink(rootSwitch, midSwitch)
		self.addLink(rootSwitch, rightSwitch)

		self.addLink(leftSwitch, host1)
		self.addLink(leftSwitch, host2)

		self.addLink(midSwitch, host3)
		self.addLink(midSwitch, host4)

		self.addLink(rightSwitch, host5)

n = int(sys.argv[1])
topos = {'tree':(lambda:Tree())}
