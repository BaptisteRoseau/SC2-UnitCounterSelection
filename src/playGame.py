import sc2
from sc2 import Race, Difficulty
from sc2.player import Bot, Computer

from emptyBot import EmptyBot
from mapBot import MapBot

import random
from datetime import datetime 

maps = [
    "AbiogenesisLE",
    "AbyssalReefLE",
    "AcidPlantLE",
    "AcolyteLE",
    "AscensiontoAiurLE",
    "AutomatonLE",
    "BackwaterLE",
    "BattleontheBoardwalkLE",
    "BlackpinkLE",
    "BloodBoilLE",
    "CatalystLE",
    "CyberForestLE",
    "DefendersLandingLE",
    "EastwatchLE",
    "FrostLE",
    "InterloperLE",
    "KairosJunctionLE",
    "KingsCoveLE",
    "MechDepotLE",
    "NeonVioletSquareLE",
    "NewRepugnancyLE",
    "OdysseyLE",
    "PortAleksanderLE",
    "ProximaStationLE",
    "SequencerLE",
    "YearZeroLE"
]

replay_name = "replays/" + datetime.now().strftime("%m-%d-%Y_%H-%M-%S") + ".SC2Replay"

def main():
    sc2.run_game(sc2.maps.get(maps[random.randint(0, len(maps) - 1)]), [
        Bot(Race.Zerg, MapBot()),
        Computer(Race.Terran, Difficulty.Medium)
    ], realtime=False, save_replay_as=replay_name)

if __name__ == '__main__':
    main()
