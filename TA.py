from mininet.topo import Topo
class MyTopo (Topo):
	#"Simple topology example.“
	def __init__(self):
		Topo.__init__(self)
		leftHost = self.addHost('h1')
		rightHost = self.addHost('h2')
		leftSwitch = self.addSwitch('s1')
		rightSwitch = self.addSwitch('s2')
		# Add links
		self.addLink(leftHost,leftSwitch)
		self.addLink(leftSwitch,rightSwitch)
		self.addLink(rightHost, rightSwitch)
topos = {'ta':(lambda: MyTopo())}
