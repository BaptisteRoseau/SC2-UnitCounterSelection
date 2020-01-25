import cv2
import numpy as np
import math
import random

import sc2
from sc2.game_data import Cost
from sc2.constants import UnitTypeId
from sc2.position import Point2

#TODO: Manage upgrades

#An empty bot to let the other do whatever he wants
class MapBot(sc2.BotAI):
    def __init__(self, title=1):
        self.title = title
        self.last_spawn_time = 0
        self.spawn_time = 100 # iterations
        self.nwaves = 0
        self.units_are_alive = True
        self.wave_finished = False #TODO: function with time AND unit health ?
        self.spawnable_units_zerg = [
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
        self.spawnable_units_terran = [
                UnitTypeId.MARINE,
                UnitTypeId.GHOST,
                UnitTypeId.MARAUDER,
                UnitTypeId.REAPER,
                UnitTypeId.HELLION,
                UnitTypeId.SIEGETANK,
                UnitTypeId.THOR,
                UnitTypeId.WIDOWMINE,
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
            await self.client.debug_fast_build()
            await self.client.debug_show_map()
            await self.client.debug_free()
            print("BOT "+str(self.title)+": Super user mode enabled")
        
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
            print("BOT "+str(self.title)+": Wave "+str(self.nwaves)+" reached, leaving the game.")
            await self._client.leave()
    

    ## ==== METHODs

    async def spawn_units(self, ressources):
        """ Spawns units for the amount of ressources given, for each player """
        # Spawning units for player 1 (Zerg)
        spawn_info_zerg = []
        ressources_left = ressources
        while ressources_left > 100:
            for unit in self.spawnable_units_zerg:
                unit_cost = self.calculate_cost(unit)
                # Adding the cost of previous tech unit if necessary
                if unit == UnitTypeId.BROODLORD:  unit_cost += self.calculate_cost(UnitTypeId.CORRUPTOR)
                elif unit == UnitTypeId.BANELING: unit_cost += self.calculate_cost(UnitTypeId.ZERGLING)
                elif unit == UnitTypeId.LURKER:   unit_cost += self.calculate_cost(UnitTypeId.HYDRALISK)

                unit_cost = unit_cost.minerals + unit_cost.vespene
                amount = int(random.uniform(0, 1)*int(ressources_left/unit_cost))
                if amount > 0 and random.uniform(0, 1) < 1./len(self.spawnable_units_zerg):
                    print("Added "+str(amount)+" unit "+str(unit)+" for a cost of "+str(unit_cost*amount))
                    ressources_left -= unit_cost*amount
                    spawn_info_zerg.append([unit, amount, self._game_info.map_center - Point2((6, 6)), 1])
        print("Ressources left for Zerg: "+str(ressources_left))

        # Spawning units for player 2 (Terran)
        spawn_info_terran = []
        ressources_left = ressources
        while ressources_left > 100:
            for unit in self.spawnable_units_terran:
                unit_cost = self.calculate_cost(unit)
                unit_cost = unit_cost.minerals + unit_cost.vespene
                amount = int(random.uniform(0, 1)*int(ressources_left/unit_cost))
                if amount > 0 and random.uniform(0, 1) < 1./len(self.spawnable_units_terran):
                    print("Added "+str(amount)+" unit "+str(unit)+" for a cost of "+str(unit_cost))
                    ressources_left -= unit_cost*amount
                    spawn_info_terran.append([unit, amount, self._game_info.map_center + Point2((6, 6)), 2])
        print("Ressources left for Terran: "+str(ressources_left))

        # Spaning selected units
        await self._client.debug_create_unit(spawn_info_zerg)
        await self._client.debug_create_unit(spawn_info_terran)
        print("Spawned units of wave "+str(self.nwaves))


    async def cleanup_units(self):
        """ Destroys every units of both players """
        if self.units.tags:
            await self.client.debug_kill_unit(self.units.tags)
        if self.units.enemy.tags:
            await self.client.debug_kill_unit(self.units.enemy.tags)
        print("Killed all units.")


    async def start_attack(self):
        """ Order the player and his opponent units to attack """
        for unit in self.units:
            self.do(unit.attack(self._game_info.map_center))
        for unit in self.units.enemy:
            self.do(unit.attack(self._game_info.map_center))
        #TODO attack from enemy


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

        cv2.imshow(str(self.title), resized)
        cv2.waitKey(1)
