import cv2
import numpy as np
import math
import random

import sc2
from sc2.game_data import Cost
from sc2.constants import UnitTypeId
from sc2.position import Point2
from sc2 import Race

#TODO: Manage upgrades

#An empty bot to let the other do whatever he wants
class MapBot(sc2.BotAI):
    def __init__(self, playerID=1, race=Race.Zerg):
        self.playerID = playerID
        self.race = race
        self.last_spawn_time = 0
        self.spawn_time = 100 # iterations
        self.nwaves = 0
        self.units_are_alive = True
        self.wave_finished = False #TODO: function with time AND unit health ?
        if self.race == Race.Zerg:
            self.spawnable_units = [
                    UnitTypeId.ZERGLING,
                    UnitTypeId.ROACH,
                    UnitTypeId.HYDRALISK,
                    UnitTypeId.MUTALISK,
                    UnitTypeId.CORRUPTOR,
                    UnitTypeId.ULTRALISK,
                    UnitTypeId.QUEEN,
                    UnitTypeId.BANELING,
                    UnitTypeId.BROODLORD
                ]
        elif self.race == Race.Terran:
            self.spawnable_units = [
                    UnitTypeId.MARINE,
                    UnitTypeId.GHOST,
                    UnitTypeId.MARAUDER,
                    UnitTypeId.REAPER,
                    UnitTypeId.HELLION,
                    UnitTypeId.SIEGETANK,
                    UnitTypeId.THOR,
                    UnitTypeId.HELLIONTANK,
                    UnitTypeId.CYCLONE,
                    UnitTypeId.RAVEN,
                    UnitTypeId.VIKINGFIGHTER,
                    UnitTypeId.MEDIVAC,
                    UnitTypeId.BATTLECRUISER,
                    UnitTypeId.BANSHEE,
                    UnitTypeId.LIBERATOR
                ]
    
    ## ==== ON-STEP

    async def on_step(self, iteration):
        if iteration == 0:
            await self.client.debug_control_enemy()
            await self.client.debug_show_map()
            print("BOT "+str(self.playerID)+": Super user mode enabled")
        
        # Displays the map using opencv
        await self.display_map()

        # Spawn units every self.spawn_time seconds
        await self.start_attack()
        if iteration > self.last_spawn_time + self.spawn_time:
            if not self.units_are_alive:
                # Spawn units and tell them to attack
                await self.spawn_units(2000)
                self.units_are_alive = True
                self.last_spawn_time = iteration
                self.nwaves += 1
            else:
                # Kills all units
                await self.cleanup_units()
                self.units_are_alive = False

        # End the game after enough waves are done
        if self.nwaves > 10:
            print("BOT "+str(self.playerID)+": Wave "+str(self.nwaves)+" reached, leaving the game.")
            await self._client.leave()
    

    ## ==== METHODs

    async def spawn_units(self, ressources):
        """ Spawns units for the amount of ressources given, for each player """
        # Spawning units for player 1 (Zerg)
        spawn_info = []
        ressources_left = ressources
        spawn_location = self._game_info.map_center - Point2((6, 6)) if self.race == Race.Zerg else self._game_info.map_center + Point2((6, 6))
        while ressources_left > 100:
            for unit in self.spawnable_units:
                unit_cost = self.calculate_cost(unit)
                # Adding the cost of previous tech unit if necessary
                if unit == UnitTypeId.BROODLORD:  unit_cost += self.calculate_cost(UnitTypeId.CORRUPTOR)
                elif unit == UnitTypeId.BANELING: unit_cost += self.calculate_cost(UnitTypeId.ZERGLING)
                elif unit == UnitTypeId.LURKER:   unit_cost += self.calculate_cost(UnitTypeId.HYDRALISK)

                unit_cost = unit_cost.minerals + unit_cost.vespene
                amount = int(random.uniform(0, 1)*int(ressources_left/unit_cost))
                if amount > 0 and random.uniform(0, 1) < 1./len(self.spawnable_units):
                    print("Added "+str(amount)+" unit "+str(unit)+" for a cost of "+str(unit_cost*amount))
                    ressources_left -= unit_cost*amount
                    spawn_info.append([unit, amount, spawn_location, self.playerID])
        print("Ressources left for"+str(self.race)+": "+str(ressources_left))
        
        # Spaning selected units
        await self._client.debug_create_unit(spawn_info)
        print("Spawned units of wave "+str(self.nwaves))


    async def cleanup_units(self):
        """ Destroys every units of both players """
        if self.units.tags:
            await self.client.debug_kill_unit(self.units.tags)
        print("Killed all units.")


    async def start_attack(self):
        """ Order the player to attack the middle of the map """
        for unit in self.units:
            self.do(unit.attack(self._game_info.map_center))

    async def display_map(self):
        """ Just a display to know what is going on in the game """
        game_data = np.zeros((self.game_info.map_size[1], self.game_info.map_size[0], 3), np.uint8)

        for unit in self.units.ready:
            pos = unit.position
            cv2.circle(game_data, (int(pos[0]), int(pos[1])), int(unit.radius*8), (255, 255, 255), math.ceil(int(unit.radius*0.5)))

        for unit in self.units.enemy:
            pos = unit.position
            cv2.circle(game_data, (int(pos[0]), int(pos[1])), int(unit.radius*8), (125, 125, 125), math.ceil(int(unit.radius*0.5)))

        # flip horizontally to make our final fix in visual representation:
        grayed = cv2.cvtColor(game_data, cv2.COLOR_BGR2GRAY)
        self.flipped = cv2.flip(grayed, 0)

        resized = cv2.resize(self.flipped, dsize=None, fx=2, fy=2)

        cv2.imshow(str(self.playerID), resized)
        cv2.waitKey(1)
