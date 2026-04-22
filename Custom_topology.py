from mininet.topo import Topo

class CustomTopo(Topo):
    """
    Triangle topology aligned with policies.json:

      h1 (10.0.0.1)                    h3 (10.0.0.3)
      h2 (10.0.0.2)                    |
           |                           |
           |                     [s2: ALLOW ALL]
           |                    /              \\
      [s1: BLACKLIST] ----------                [s3: WHITELIST]
       - blocks h1<->h4 (IP)                     - ICMP only
       - blocks h2<->h3 (MAC)                         |
       - blocks UDP                             h4 (10.0.0.4)
    """

    def build(self):
        s1 = self.addSwitch('s1')
        s2 = self.addSwitch('s2')
        s3 = self.addSwitch('s3')

        h1 = self.addHost('h1', ip='10.0.0.1/24', mac='00:00:00:00:00:01')
        h2 = self.addHost('h2', ip='10.0.0.2/24', mac='00:00:00:00:00:02')
        h3 = self.addHost('h3', ip='10.0.0.3/24', mac='00:00:00:00:00:03')
        h4 = self.addHost('h4', ip='10.0.0.4/24', mac='00:00:00:00:00:04')

        # connect switches
        self.addLink(s1, s2)
        self.addLink(s2, s3)
        self.addLink(s3, s1)

        # connect hosts to switches
        self.addLink(h1, s1)
        self.addLink(h2, s1)
        self.addLink(h3, s2)
        self.addLink(h4, s3)

topos = {'custom': (lambda: CustomTopo())}
