import sc2

#An empty bot to let the other do whatever he wants
class EmptyBot(sc2.BotAI):
    def __init__(self):
        pass
    
    def on_step(self):
        pass