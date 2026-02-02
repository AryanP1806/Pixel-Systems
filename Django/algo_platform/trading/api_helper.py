from NorenRestApiPy.NorenApi import NorenApi

class NorenApiPy(NorenApi):
    def __init__(self):
        # These are the standard production endpoints for Shoonya (Finvasia)
        NorenApi.__init__(self, 
            host='https://api.shoonya.com/NorenWClientTP/', 
            websocket='wss://api.shoonya.com/NorenWSTP/'
        )