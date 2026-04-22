from mininet.topo import Topo

class CustomTopo(Topo):
    """
    Ring topology aligned with policies.json:

                        h1 (10.0.0.1)    h2 (10.0.0.2)
                                 \          /
                               [s1: BLACKLIST]
                               /             \
                              /               \
    h6 (10.0.0.6) -- [s4: ALLOW ALL]     [s2: ALLOW ALL] -- h3 (10.0.0.3)
                              \               /
                               \             /
                               [s3: WHITELIST]
                                 /          \
                        h5 (10.0.0.5)    h4 (10.0.0.4)
    """

    def build(self):
        # Add switches
        s1 = self.addSwitch('s1')
        s2 = self.addSwitch('s2')
        s3 = self.addSwitch('s3')
        s4 = self.addSwitch('s4')

        # Add hosts
        h1 = self.addHost('h1', ip='10.0.0.1/24', mac='00:00:00:00:00:01')
        h2 = self.addHost('h2', ip='10.0.0.2/24', mac='00:00:00:00:00:02')
        h3 = self.addHost('h3', ip='10.0.0.3/24', mac='00:00:00:00:00:03')
        h4 = self.addHost('h4', ip='10.0.0.4/24', mac='00:00:00:00:00:04')
        h5 = self.addHost('h5', ip='10.0.0.5/24', mac='00:00:00:00:00:05')
        h6 = self.addHost('h6', ip='10.0.0.6/24', mac='00:00:00:00:00:06')

        # Connect switches in a closed ring
        self.addLink(s1, s2)
        self.addLink(s2, s3)
        self.addLink(s3, s4)
        self.addLink(s4, s1)

        # Connect hosts to their respective switches
        self.addLink(h1, s1)
        self.addLink(h2, s1)
        self.addLink(h3, s2)
        self.addLink(h4, s3)
        self.addLink(h5, s3)
        self.addLink(h6, s4)

topos = {'custom': (lambda: CustomTopo())}
