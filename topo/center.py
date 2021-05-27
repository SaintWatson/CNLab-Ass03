from mininet.topo import Topo


class DataCenter(Topo):
	def __init__(self, n):
		Topo.__init__(self)

		self.n = n 

		switches = []
		blocks = []
		hosts = []

		for i in range(self.n):
			switches.append(self.addSwitch('s{}'.format(i+1)))

			for j in range(4):
				blocks.append(self.addSwitch('s{}_{}'.format(i+1, j+1)))

			self.addLink(blocks[i*4], blocks[i*4+2])
			self.addLink(blocks[i*4], blocks[i*4+3])

			self.addLink(blocks[i*4+1], blocks[i*4+2])
			self.addLink(blocks[i*4+1], blocks[i*4+3])


		for i in range(self.n):
			for j in range(self.n):
				if i % 2 == 0 :
					self.addLink(switches[i], blocks[j*4+0])
				if i % 2 != 0 :
					self.addLink(switches[i], blocks[j*4+1])


		for i in range(self.n * 4):
			hosts.append(self.addHost('h{}'.format(i+1)))

		for i in range(self.n * 4):
			if i % 4 == 0 or i % 4 == 1:
				self.addLink(hosts[i], blocks[(i//4)*4+2])
			elif i % 4 == 2 or i % 4 == 3  :
				self.addLink(hosts[i], blocks[(i//4)*4+3])

topos = {'center':(lambda:DataCenter(5))}
