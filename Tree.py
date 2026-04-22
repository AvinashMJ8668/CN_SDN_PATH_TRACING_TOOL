from mininet.topo import Topo


class DiamondTopo(Topo):
    def build(self):

        s1 = self.addSwitch("s1")
        s2 = self.addSwitch("s2")
        s3 = self.addSwitch("s3")
        s4 = self.addSwitch("s4")

        h1 = self.addHost("h1")
        h2 = self.addHost("h2")

        self.addLink(h1, s1)
        self.addLink(s1, s2)  # Path A
        self.addLink(s1, s3)  # Path B
        self.addLink(s2, s4)
        self.addLink(s3, s4)
        self.addLink(s4, h2)


topos = {"diamond": (lambda: DiamondTopo())}
