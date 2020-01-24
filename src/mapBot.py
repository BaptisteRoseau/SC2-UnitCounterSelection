import cv2
import numpy as np
import math
import random
import os

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
        self.iter_last_step = 0
        self.wait_iter = 0 # iterations
        self.nwaves = 1008
        self.step = 0
        self.wave_units = [] # contains [unitTypeID, amount]
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
                    UnitTypeId.VIKINGFIGHTER,
                    UnitTypeId.MEDIVAC,
                    UnitTypeId.BATTLECRUISER,
                    UnitTypeId.BANSHEE,
                    UnitTypeId.LIBERATOR
                ]
    
    ## ==== ON-STEP

    async def on_step(self, iteration):
        if iteration == 0:
            await self._client.debug_control_enemy()
            await self._client.debug_show_map()
            await self._client.move_camera(self._game_info.map_center - Point2((0, 3)))
            await self.cleanup_units()
            print("BOT "+str(self.playerID)+": Super user mode enabled")
        
        # Displays the map using opencv
        #await self.display_map()

        await self.start_attack() # Constantly attacking on the middle of the map
        if iteration > self.iter_last_step + self.wait_iter:
            self.iter_last_step = iteration
            if self.step == 0:
                # Spawn units and tell them to attack
                self.nwaves += 1
                await self.spawn_units(2000)
                self.step += 1
                self.wait_iter = 120 #iterations
            elif self.step == 1:
                # Save result of the battle
                await self.save_battle_result_unit_composition()
                self.step += 1
                self.wait_iter = 5 #iterations
            else:
                # Kills all units
                await self.cleanup_units()
                self.step = 0
                self.wait_iter = 2 #iterations


        # End the game after enough waves are done
        if self.nwaves > 10000:
            print("BOT "+str(self.playerID)+": Wave "+str(self.nwaves)+" reached, leaving the game.")
            await self._client.leave()
    

    ## ==== METHODS

    async def spawn_units(self, ressources):
        """ Spawns units for the amount of ressources given, for each player """
        spawn_info = []
        ressources_left = ressources
        spawn_location = self._game_info.map_center - Point2((12, 12)) if self.race == Race.Zerg else self._game_info.map_center + Point2((12, 12))
        while ressources_left > 100:
            for unit in self.spawnable_units:
                unit_cost = self.calculate_cost(unit)
                # Adding the cost of previous tech unit if necessary
                if unit == UnitTypeId.BROODLORD:  unit_cost += self.calculate_cost(UnitTypeId.CORRUPTOR)
                elif unit == UnitTypeId.BANELING: unit_cost += self.calculate_cost(UnitTypeId.ZERGLING)
                elif unit == UnitTypeId.LURKER:   unit_cost += self.calculate_cost(UnitTypeId.HYDRALISK)
                elif unit == UnitTypeId.ZERGLING:   unit_cost = Cost(25, 0) # A pair of Zerglings cost 50 minerals

                unit_cost = unit_cost.minerals + unit_cost.vespene
                amount = int(random.uniform(0, 1)*int(ressources_left/unit_cost))
                if amount > 0 and random.uniform(0, 1) < 1./len(self.spawnable_units):
                    # Adding the unit to the list of units that will fight
                    # If the unit is already in the list, just adding the amount 
                    found = False
                    for i in range(len(self.wave_units)):
                        if self.wave_units[i][0] == unit:
                            self.wave_units[i][1] += amount
                            spawn_info[i][1] += amount
                            found = True
                    # Else, just create a new couple [unit, amount]
                    if not found:
                        spawn_info.append([unit, amount, spawn_location, self.playerID])
                        self.wave_units.append([unit, amount]) # Saving which units were spawned for this wave
                    # Updating ressources left
                    ressources_left -= unit_cost*amount
                    print("Added "+str(amount)+" unit "+str(unit)+" for a cost of "+str(unit_cost*amount)+" (already in list: "+str(found)+")")

        print("Ressources left for"+str(self.race)+": "+str(ressources_left))
        
        # Spawning selected units
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

    def hp_of(self, unitID, unitInitialAmount):
        """ Returns the mean of the percentage of health of each unit of type unitID """
        units = self.units(unitID)
        if not units: return 0 # units is empty

        hp = 0
        for unit in units:
            hp += unit.health_percentage
        return hp/unitInitialAmount

    def hp_all(self, unitInitialAmount):
        """ Returns the mean of the percentage of health of each unit of the player """
        units = self.units
        if not units: return 0. # units is empty
        
        hp = 0
        for unit in units:
            hp += unit.health_percentage
        return hp/unitInitialAmount

    async def save_battle_result_unit_composition(self):
        """ Saves the units hp into a file as a numpy array. """
        assert self.wave_units

        # Creating input array from units selected for this wave
        # Array: [unit amount, unit hp percentage, unit amount, unit hp percentage, ..., upgrade1, upgrade2, ..]
        inputArr = np.zeros(2*len(self.spawnable_units)+5, dtype=np.float32) # +5 because 5 upgrades
        for unit in self.wave_units:
            idx = self.spawnable_units.index(unit[0])
            inputArr[2*idx]    += unit[1] # unit amount
            inputArr[2*idx + 1] = 1. # hp percentage
        
        # Adding upgrades
        idx = 2*len(self.spawnable_units)
        inputArr[idx]     = 1.
        inputArr[idx + 1] = 1.
        inputArr[idx + 2] = 1.
        inputArr[idx + 3] = 1.
        inputArr[idx + 4] = 1.

        # Saving directories
        pathInput  = os.path.join("data", "Bot"+str(self.playerID), "INPUT")
        pathOutput = os.path.join("data", "Bot"+str(self.playerID), "OUTPUT")
        
        # Saving input array
        np.savetxt(os.path.join(pathInput, "InputWave"+str(self.nwaves)+".csv"), inputArr)
        print("Saved "+os.path.join(pathInput, "InputWave"+str(self.nwaves)+".csv"))

        # Calculating result of the fight
        units_initial_amount = 0
        for a in self.wave_units:
            units_initial_amount += a[1]
        result = self.hp_all(units_initial_amount)
        print("Result:", result)

        # Saving output array
        np.savetxt(os.path.join(pathOutput, "OutputWave"+str(self.nwaves)+".csv"),
                   np.array([result], dtype=np.float32))
        print("Saved "+os.path.join(pathOutput, "OutputWave"+str(self.nwaves)+".csv"))

        # Reseting units used
        self.wave_units = []

    
    async def save_battle_result_topology(self):
        #TODO
        pass

    #Just a tool to show the map on Linux
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
