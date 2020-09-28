import gamelib
import random
import math
import warnings
from sys import maxsize
import json
from gamelib.util import debug_write

################### Structure (defense) units: [defined in ALL_UNITS variable in gamelib/game_state.py]
######### DESTRUCTOR: Turret
######### FILTER: Wall
######### ENCRYPTOR: Factory

################### Mobile (offense) units: [defined in ALL_UNITS variable in gamelib/game_state.py]
######### SCRAMBLER: Interceptor
######### PING: Scout
######### EMP: Demolisher

"""
Most of the algo code you write will be in this file unless you create new
modules yourself. Start by modifying the 'on_turn' function.

Advanced strategy tips: 

  - You can analyze action frames by modifying on_action_frame function

  - The GameState.map object can be manually manipulated to create hypothetical 
  board states. Though, we recommended making a copy of the map to preserve 
  the actual current map state.
"""

#### global variables:
locations_of_not_upgraded_factories = []
locations_of_not_upgraded_turrets = []
if random.uniform(0, 1) <= 0.5:
    attack_from_left_side = False
else:
    attack_from_left_side = True


class AlgoStrategy(gamelib.AlgoCore):
    def __init__(self):
        super().__init__()
        seed = random.randrange(maxsize)
        random.seed(seed)
        gamelib.debug_write('Random seed: {}'.format(seed))

    def on_game_start(self, config):
        """ 
        Read in config and perform any initial setup here 
        """
        gamelib.debug_write('Configuring your custom algo strategy...')
        self.config = config
        global FILTER, ENCRYPTOR, DESTRUCTOR, PING, EMP, SCRAMBLER, BITS, CORES
        FILTER = config["unitInformation"][0]["shorthand"]
        ENCRYPTOR = config["unitInformation"][1]["shorthand"]
        DESTRUCTOR = config["unitInformation"][2]["shorthand"]
        PING = config["unitInformation"][3]["shorthand"]
        EMP = config["unitInformation"][4]["shorthand"]
        SCRAMBLER = config["unitInformation"][5]["shorthand"]
        BITS = 1
        CORES = 0
        # This is a good place to do initial setup
        self.scored_on_locations = []

    
        

    def on_turn(self, turn_state):
        """
        This function is called every turn with the game state wrapper as
        an argument. The wrapper stores the state of the arena and has methods
        for querying its state, allocating your current resources as planned
        unit deployments, and transmitting your intended deployments to the
        game engine.
        """
        game_state = gamelib.GameState(self.config, turn_state)
        gamelib.debug_write('Performing turn {} of your custom algo strategy'.format(game_state.turn_number))
        game_state.suppress_warnings(True)  #Comment or remove this line to enable warnings.

        self.starter_strategy(game_state)

        game_state.submit_turn()


    """
    NOTE: All the methods after this point are part of the sample starter-algo
    strategy and can safely be replaced for your custom algo.
    """

    def starter_strategy(self, game_state):
        """
        For defense we will use a spread out layout and some Scramblers early on.
        We will place destructors near locations the opponent managed to score on.
        For offense we will use long range EMPs if they place stationary units near the enemy's front.
        If there are no stationary units to attack in the front, we will send Pings to try and score quickly.
        """
        # First, place basic defenses
        # self.build_defences(game_state)
        # Now build reactive defenses based on where the enemy scored
        # self.build_reactive_defense(game_state)

        #### settings:
        thickness_of_forward_defense_turrets = 1
        period_for_upgrade_turrets = 4
        threshold_mobilePoints_for_closeTo_attack_phase = 10
        upgrade_turrets_randomly = False

        #### attack phase:
        if game_state.get_resource(BITS) >= threshold_mobilePoints_for_closeTo_attack_phase:
            close_to_attack_phase = True
        else:
            close_to_attack_phase = False

        # check if it is attack phase:
        if close_to_attack_phase:
            attack_phase = True
        else:
            attack_phase = False
        for coor1 in range(0, 27+1):
            for coor2 in range(0, 13+1):
                if attack_from_left_side:
                    if coor2 == (13 - coor1) or coor2 == (14 - coor1):
                        if game_state.contains_stationary_unit([coor1,coor2]):
                            attack_phase = False
                else:
                    if coor2 == (coor1 - 13) or coor2 == (coor1 - 14):
                        if game_state.contains_stationary_unit([coor1,coor2]):
                            attack_phase = False
        if attack_phase:
            # place side walls:
            if attack_from_left_side:
                game_state.attempt_spawn(FILTER, [15, 2])
                game_state.attempt_remove([15, 2])
            else:
                game_state.attempt_spawn(FILTER, self.flip_locations([15, 2]))
                game_state.attempt_remove(self.flip_locations([15, 2]))
            for coor1 in range(0, 27+1):
                for coor2 in range(0, 13+1):
                    if attack_from_left_side:
                        if coor2 == (15 - coor1):
                            game_state.attempt_spawn(FILTER, [coor1, coor2])
                            game_state.attempt_remove([coor1, coor2])
                    else:
                        if coor2 == (coor1 - 12):
                            game_state.attempt_spawn(FILTER, [coor1, coor2])
                            game_state.attempt_remove([coor1, coor2])
            game_state.attempt_spawn(DESTRUCTOR, [0, 13])
            game_state.attempt_spawn(DESTRUCTOR, [27, 13])
            game_state.attempt_upgrade([0, 13])
            game_state.attempt_upgrade([27, 13])
            iteration_index = 0
            while True:
                location_interceptor = [[13, 0]]
                location_demolisher = [[13, 0]]
                if attack_from_left_side:
                    location_interceptor = self.flip_locations(location_interceptor)
                    location_demolisher = self.flip_locations(location_demolisher)
                can_place_interceptor = (game_state.get_resource(BITS) >= game_state.type_cost(SCRAMBLER)[BITS])
                can_place_demolisher = (game_state.get_resource(BITS) >= game_state.type_cost(EMP)[BITS])
                if (not can_place_interceptor) and (not can_place_demolisher):
                    break
                if (iteration_index == 0 or iteration_index == 1) and game_state.get_resource(BITS) >= game_state.type_cost(SCRAMBLER)[BITS]:
                    #### placing interceptor:
                    game_state.attempt_spawn(SCRAMBLER, location_interceptor)
                elif (iteration_index == 2):
                    iteration_index = 0
                    if game_state.get_resource(BITS) >= game_state.type_cost(EMP)[BITS]:
                        #### placing demolisher:
                        game_state.attempt_spawn(EMP, location_demolisher)
                iteration_index += 1

        #### placing walls on the side:
        # locations_side_walls = [[0,13],[1,12],[2,11],[3,10],[4,9]]
        locations_side_walls = [[1,12],[2,11],[3,10],[4,9]]
        if close_to_attack_phase or attack_phase:
            if attack_from_left_side:
                game_state.attempt_spawn(FILTER, self.flip_locations(locations_side_walls))
            else:
                game_state.attempt_spawn(FILTER, locations_side_walls)
        else:
            locations_side_walls.extend(self.flip_locations(locations_side_walls))
            game_state.attempt_spawn(FILTER, locations_side_walls)

        #### place turret next to factory:
        if game_state.turn_number >= 1:
            game_state.attempt_spawn(DESTRUCTOR, [14,3])
        
        #### placing other defenders:
        wall_coor1_from_left = 5-1
        wall_coor1_from_right = 22+1
        for inf_loop_iterator in range(1000):
            can_place_wall = game_state.get_resource(CORES) >= game_state.type_cost(FILTER)[CORES]
            can_place_turret = game_state.get_resource(CORES) >= game_state.type_cost(DESTRUCTOR)[CORES]     
            can_place_factory = game_state.get_resource(CORES) >= game_state.type_cost(ENCRYPTOR)[CORES]     
            if (not can_place_wall) and (not can_place_turret) and (not can_place_factory):
                break

            #### place edge turrets:
            if game_state.turn_number >= 1:
                game_state.attempt_spawn(DESTRUCTOR, [12, 8])
                game_state.attempt_spawn(DESTRUCTOR, [15, 8])
                game_state.attempt_spawn(DESTRUCTOR, [5, 11])
                game_state.attempt_spawn(DESTRUCTOR, [22, 11])
                game_state.attempt_spawn(DESTRUCTOR, [0, 13])
                game_state.attempt_spawn(DESTRUCTOR, [27, 13])
            if game_state.turn_number >= 2:
                game_state.attempt_upgrade([12, 8])
                game_state.attempt_upgrade([15, 8])
                game_state.attempt_upgrade([0, 13])
                game_state.attempt_upgrade([27, 13])
            if game_state.turn_number == 2:
                game_state.attempt_upgrade([5, 11])
                game_state.attempt_upgrade([22, 11])

            #### placing middle walls:
            if game_state.turn_number >= 1:
                n_trials_place_wall = 1000 
                for trial_index in range(n_trials_place_wall):
                    ### placing walls in the forward defense:
                    wall_coor2 = 9
                    wall_coor1_from_left += 1
                    wall_coor1_from_right -= 1
                    if (not close_to_attack_phase) and (not attack_phase):
                        if wall_coor1_from_left <= 12:
                            #### grow defenders from left:
                            game_state.attempt_spawn(FILTER, [wall_coor1_from_left, wall_coor2])
                        if wall_coor1_from_right >= 15:
                            #### grow defenders from right:
                            game_state.attempt_spawn(FILTER, [wall_coor1_from_right, wall_coor2])
                    else:
                        if attack_from_left_side:
                            if wall_coor1_from_left >= 6 and wall_coor1_from_left <= 12:
                                #### grow defenders from left:
                                game_state.attempt_spawn(FILTER, [wall_coor1_from_left, wall_coor2])
                            if wall_coor1_from_right >= 15:
                                #### grow defenders from right:
                                game_state.attempt_spawn(FILTER, [wall_coor1_from_right, wall_coor2])
                        else:
                            if wall_coor1_from_left <= 12:
                                #### grow defenders from left:
                                game_state.attempt_spawn(FILTER, [wall_coor1_from_left, wall_coor2])
                            if wall_coor1_from_right >= 15 and wall_coor1_from_right <= 21:
                                #### grow defenders from right:
                                game_state.attempt_spawn(FILTER, [wall_coor1_from_right, wall_coor2])
                    if wall_coor1_from_left > 12 and wall_coor1_from_right < 15:
                        break
            
            #### upgrade side walls:
            if game_state.turn_number >= 2:
                game_state.attempt_upgrade(locations_side_walls)

            #### upgrade middle walls:
            for i in range(5, 12+1):
                location = [i, 9]
                game_state.attempt_upgrade(location)
                location = self.flip_locations(location)
                game_state.attempt_upgrade(location)
            game_state.attempt_upgrade([[13,8],[14,8]])
            game_state.attempt_upgrade([[13,7],[14,7]])

            #### place vertical walls:
            if game_state.turn_number >= 3:
                game_state.attempt_spawn(FILTER, [12, 10])
                game_state.attempt_spawn(FILTER, [15, 10])
                game_state.attempt_spawn(FILTER, [12, 11])
                game_state.attempt_spawn(FILTER, [15, 11])
                game_state.attempt_spawn(FILTER, [12, 12])
                game_state.attempt_spawn(FILTER, [15, 12])
                game_state.attempt_spawn(FILTER, [13, 8])
                game_state.attempt_spawn(FILTER, [14, 8])
                game_state.attempt_spawn(FILTER, [13, 7])
                game_state.attempt_spawn(FILTER, [14, 7])

            # #### place turrets sparsely:
            # row_of_turrets = 8
            # if game_state.turn_number >= 1:
            #     least_busy_score = 1000
            #     best_location_turret = None
            #     for coordinate1 in range(7,20+1):
            #         for coordinate2 in range(row_of_turrets,row_of_turrets-thickness_of_forward_defense_turrets,-1):
            #             location_turret = [coordinate1, coordinate2]
            #             if game_state.game_map.in_arena_bounds(location_turret) and (not game_state.contains_stationary_unit(location_turret)):
            #                 busy_score = self.calculate_how_busy_neighborhood_is_in_the_same_row(game_state, location_turret, neighborhood_size=2)
            #                 if busy_score < least_busy_score:
            #                     least_busy_score = busy_score
            #                     best_location_turret = location_turret
            #     if best_location_turret is not None:
            #         success_spawn_turret = game_state.attempt_spawn(DESTRUCTOR, best_location_turret)
            #         if success_spawn_turret:
            #             locations_of_not_upgraded_turrets.append(best_location_turret)

            #### place other turrets:
            locations = [[11,8],[12,7],[13,6],[10,8],[9,8]]
            for location_ in locations:
                success_spawn_turret = game_state.attempt_spawn(DESTRUCTOR, location_)
                if success_spawn_turret:
                    break
                success_spawn_turret = game_state.attempt_spawn(DESTRUCTOR, self.flip_locations(location_))
                if success_spawn_turret:
                    break
                success_upgrade_turret = game_state.attempt_upgrade(location_)
                if success_upgrade_turret:
                    break
                success_upgrade_turret = game_state.attempt_upgrade(self.flip_locations(location_))
                if success_upgrade_turret:
                    break
                

            #### placing factory:
            is_factory_placed = False
            upgraded_a_factory = False
            if can_place_factory:
                for coordinate_y in range(2, 10):
                    for coordinate_x in range(22, 5-1, -1):
                        location_factory = [coordinate_x, coordinate_y]
                        if game_state.game_map.in_arena_bounds(location_factory) and (not game_state.contains_stationary_unit(location_factory)) and self.is_above_the_V_border(location_factory):
                            if len(locations_of_not_upgraded_factories) != 0:
                                location_to_be_upgraded = locations_of_not_upgraded_factories[0]
                                success_upgrade = game_state.attempt_upgrade(location_to_be_upgraded)
                                if success_upgrade == 1:
                                    upgraded_a_factory = True
                                    locations_of_not_upgraded_factories.remove(location_to_be_upgraded)
                            success_spawn = game_state.attempt_spawn(ENCRYPTOR, location_factory)
                            if success_spawn == 1:
                                is_factory_placed = True
                                locations_of_not_upgraded_factories.append(location_factory)
                        if is_factory_placed and upgraded_a_factory:
                            break
                    if is_factory_placed and upgraded_a_factory:
                        break


                # #### upgrade turrets:
                # if (game_state.turn_number % period_for_upgrade_turrets == 0) and len(locations_of_not_upgraded_turrets) != 0:
                #     if (not attack_from_left_side):
                #         first_side_turret = [24, 12]
                #         second_side_turret = [3, 12]
                #     else:
                #         first_side_turret = [3, 12]
                #         second_side_turret = [24, 12]
                #     success_upgrade_turret = game_state.attempt_upgrade(first_side_turret)
                #     success_upgrade_turret = game_state.attempt_upgrade(second_side_turret)
                #     locations_of_not_upgraded_turrets_justFirstRow = []
                #     for location_ in locations_of_not_upgraded_turrets:
                #         if location_[1] == 12:
                #             locations_of_not_upgraded_turrets_justFirstRow.append(location_)
                #     if len(locations_of_not_upgraded_turrets_justFirstRow) != 0:
                #         locations_turret_to_upgrade = locations_of_not_upgraded_turrets_justFirstRow
                #     else:
                #         locations_turret_to_upgrade = locations_of_not_upgraded_turrets
                #     if upgrade_turrets_randomly:
                #         upgrade_turret_index = random.randint(0, len(locations_turret_to_upgrade) - 1)
                #         success_upgrade_turret = game_state.attempt_upgrade(locations_turret_to_upgrade[upgrade_turret_index])
                #         if success_upgrade_turret == 1:
                #             locations_of_not_upgraded_turrets.remove(locations_turret_to_upgrade[upgrade_turret_index])
                #     else:
                #         least_busy_score_turret_upgraded = 1000
                #         best_location_turret_upgrade = None
                #         for location in locations_turret_to_upgrade:
                #             busy_score_turret_upgraded = self.calculate_how_busy_neighborhood_is_for_notUpgradedTurrets(game_state=game_state, location=location, locations_turrets=locations_turret_to_upgrade, locations_turrets_not_upgraded=locations_of_not_upgraded_turrets, neighborhood_size=3)
                #             if busy_score_turret_upgraded < least_busy_score_turret_upgraded:
                #                 least_busy_score_turret_upgraded = busy_score_turret_upgraded
                #                 best_location_turret_upgrade = location
                #         if best_location_turret_upgrade is not None:
                #             success_upgrade_turret = game_state.attempt_upgrade(best_location_turret_upgrade)
                #             if success_upgrade_turret == 1:
                #                 locations_of_not_upgraded_turrets.remove(best_location_turret_upgrade)

            # #### remove some forward-side walls for attacking:
            # if attack_phase or close_to_attack_phase:
            #     locations_remove_walls = [[26,13], [27,13]]
            #     if attack_from_left_side:
            #         locations_remove_walls = self.flip_locations(locations_remove_walls)
            #     game_state.attempt_remove(locations_remove_walls)

            
            
        #### placing attackers (offenders):
        if game_state.turn_number == 0:
            while True:
                #### placing interceptor:
                if game_state.get_resource(BITS) >= game_state.type_cost(SCRAMBLER)[BITS]:
                    game_state.attempt_spawn(SCRAMBLER, [[22, 8]])
                else:
                    break
        if game_state.turn_number == 1:
            while True:
                #### placing interceptor:
                if game_state.get_resource(BITS) >= game_state.type_cost(SCRAMBLER)[BITS]:
                    game_state.attempt_spawn(SCRAMBLER, [[5, 8]])
                else:
                    break
        else:
            if close_to_attack_phase:
                for coor1 in range(0, 27+1):
                    for coor2 in range(0, 13+1):
                        if attack_from_left_side:
                            if coor2 == (13 - coor1) or coor2 == (14 - coor1):
                                game_state.attempt_remove([coor1, coor2])
                        else:
                            if coor2 == (coor1 - 13) or coor2 == (coor1 - 14):
                                game_state.attempt_remove([coor1, coor2])
    

    ##################### functions:

    def flip_locations(self, locations):
        if type(locations[0]) == int:
            locations = [locations]
        locations = [[13-(location[0]-14), location[1]] for location in locations]
        return locations

    def is_forward_defense_complete(self, game_state, thickness_of_forward_defense=3):
        is_complete = True
        for coordinate1 in range(3,24+1):
            the_column_is_empty = True
            for coordinate2 in range(12,12-thickness_of_forward_defense,-1):
                if game_state.contains_stationary_unit([coordinate1, coordinate2]):
                    the_column_is_empty = False
            if the_column_is_empty:
                is_complete = False
                break
        return is_complete
            
    def is_above_the_V_border(self, location):
        x = location[0]
        y = location[1]
        is_above_the_right_line = (y >= x - 12)
        is_above_the_left_line = (y >= -x + 15)
        return is_above_the_right_line and is_above_the_left_line

    def calculate_how_busy_neighborhood_is(self, game_state, location, neighborhood_size):
        busy_score = 0
        for coordinate1 in range(location[0]-neighborhood_size, location[0]+neighborhood_size+1):
            for coordinate2 in range(location[1]-neighborhood_size, location[1]+neighborhood_size+1):
                location_neighbor = [coordinate1, coordinate2]
                is_neighbor_the_location_itself = (location_neighbor[0] == location[0]) and (location_neighbor[1] == location[1])
                is_neighbor_on_righthand_walls = (location_neighbor[1] == location_neighbor[0] - 12)
                if (not is_neighbor_the_location_itself) and game_state.game_map.in_arena_bounds(location_neighbor) and game_state.contains_stationary_unit(location_neighbor) and (not is_neighbor_on_righthand_walls):
                    busy_score += 1
        return busy_score

    def calculate_how_busy_neighborhood_is_in_the_same_row(self, game_state, location, neighborhood_size):
        busy_score = 0
        for coordinate1 in range(location[0]-neighborhood_size, location[0]+neighborhood_size+1):
            coordinate2 = location[1]
            location_neighbor = [coordinate1, coordinate2]
            is_neighbor_the_location_itself = (location_neighbor[0] == location[0]) and (location_neighbor[1] == location[1])
            is_neighbor_on_righthand_walls = (location_neighbor[1] == location_neighbor[0] - 12)
            if (not is_neighbor_the_location_itself) and game_state.game_map.in_arena_bounds(location_neighbor) and game_state.contains_stationary_unit(location_neighbor) and (not is_neighbor_on_righthand_walls):
                busy_score += 1
        return busy_score

    def calculate_how_busy_neighborhood_is_for_notUpgradedTurrets(self, game_state, location, locations_turrets, locations_turrets_not_upgraded, neighborhood_size):
        busy_score = 0
        for coordinate1 in range(location[0]-neighborhood_size, location[0]+neighborhood_size+1):
            for coordinate2 in range(location[1]-neighborhood_size, location[1]+neighborhood_size+1):
                location_neighbor = [coordinate1, coordinate2]
                is_neighbor_the_location_itself = (location_neighbor[0] == location[0]) and (location_neighbor[1] == location[1])
                if (not is_neighbor_the_location_itself) and game_state.game_map.in_arena_bounds(location_neighbor) and (location_neighbor in locations_turrets) and (location_neighbor not in locations_turrets_not_upgraded):
                    busy_score += 1
        return busy_score

    def build_Turret_defences(self, game_state, locations, put_wall_in_front=None, upgrade_them=None):
        """
        Build basic defenses using hardcoded locations.
        Remember to defend corners and avoid placing units in the front where enemy EMPs can attack them.
        """
        # Useful tool for setting up your base locations: https://www.kevinbai.design/terminal-map-maker
        # More community tools available at: https://terminal.c1games.com/rules#Download

        # Place destructors that attack enemy units
        destructor_locations = locations
        # attempt_spawn will try to spawn units if we have resources, and will check if a blocking unit is already there
        game_state.attempt_spawn(DESTRUCTOR, destructor_locations)
        
        filter_locations = []
        upgrade_locations = []
        for index, location in enumerate(locations):
            if put_wall_in_front is not None:
                if put_wall_in_front[index] == 1:
                    filter_locations.append([location[0], location[1]+1])
            if upgrade_them is not None:
                if upgrade_them[index] == 1:
                    upgrade_locations.append(location)
        # Place filters in front of destructors to soak up damage for them
        if len(filter_locations) != 0:
            game_state.attempt_spawn(FILTER, filter_locations)
        # upgrade filters so they soak more damage
        if len(upgrade_locations) != 0:
            game_state.attempt_upgrade(upgrade_locations)

    def build_reactive_defense(self, game_state):
        """
        This function builds reactive defenses based on where the enemy scored on us from.
        We can track where the opponent scored by looking at events in action frames 
        as shown in the on_action_frame function
        """
        for location in self.scored_on_locations:
            # Build destructor one space above so that it doesn't block our own edge spawn locations
            build_location = [location[0], location[1]+1]
            game_state.attempt_spawn(DESTRUCTOR, build_location)

    def stall_with_scramblers(self, game_state):
        """
        Send out Scramblers at random locations to defend our base from enemy moving units.
        """
        # We can spawn moving units on our edges so a list of all our edge locations
        friendly_edges = game_state.game_map.get_edge_locations(game_state.game_map.BOTTOM_LEFT) + game_state.game_map.get_edge_locations(game_state.game_map.BOTTOM_RIGHT)
        
        # Remove locations that are blocked by our own firewalls 
        # since we can't deploy units there.
        deploy_locations = self.filter_blocked_locations(friendly_edges, game_state)
        
        # While we have remaining bits to spend lets send out scramblers randomly.
        while game_state.get_resource(BITS) >= game_state.type_cost(SCRAMBLER)[BITS] and len(deploy_locations) > 0:
            # Choose a random deploy location.
            deploy_index = random.randint(0, len(deploy_locations) - 1)
            deploy_location = deploy_locations[deploy_index]
            
            game_state.attempt_spawn(SCRAMBLER, deploy_location)
            """
            We don't have to remove the location since multiple information 
            units can occupy the same space.
            """

    def emp_line_strategy(self, game_state):
        """
        Build a line of the cheapest stationary unit so our EMP's can attack from long range.
        """
        # First let's figure out the cheapest unit
        # We could just check the game rules, but this demonstrates how to use the GameUnit class
        stationary_units = [FILTER, DESTRUCTOR, ENCRYPTOR]
        cheapest_unit = FILTER
        for unit in stationary_units:
            unit_class = gamelib.GameUnit(unit, game_state.config)
            if unit_class.cost[game_state.BITS] < gamelib.GameUnit(cheapest_unit, game_state.config).cost[game_state.BITS]:
                cheapest_unit = unit

        # Now let's build out a line of stationary units. This will prevent our EMPs from running into the enemy base.
        # Instead they will stay at the perfect distance to attack the front two rows of the enemy base.
        for x in range(27, 5, -1):
            game_state.attempt_spawn(cheapest_unit, [x, 11])

        # Now spawn EMPs next to the line
        # By asking attempt_spawn to spawn 1000 units, it will essentially spawn as many as we have resources for
        game_state.attempt_spawn(EMP, [24, 10], 1000)

    def least_damage_spawn_location(self, game_state, location_options):
        """
        This function will help us guess which location is the safest to spawn moving units from.
        It gets the path the unit will take then checks locations on that path to 
        estimate the path's damage risk.
        """
        damages = []
        # Get the damage estimate each path will take
        for location in location_options:
            path = game_state.find_path_to_edge(location)
            damage = 0
            for path_location in path:
                # Get number of enemy destructors that can attack the final location and multiply by destructor damage
                damage += len(game_state.get_attackers(path_location, 0)) * gamelib.GameUnit(DESTRUCTOR, game_state.config).damage_i
            damages.append(damage)
        
        # Now just return the location that takes the least damage
        return location_options[damages.index(min(damages))]

    def detect_enemy_unit(self, game_state, unit_type=None, valid_x = None, valid_y = None):
        total_units = 0
        for location in game_state.game_map:
            if game_state.contains_stationary_unit(location):
                for unit in game_state.game_map[location]:
                    if unit.player_index == 1 and (unit_type is None or unit.unit_type == unit_type) and (valid_x is None or location[0] in valid_x) and (valid_y is None or location[1] in valid_y):
                        total_units += 1
        return total_units
        
    def filter_blocked_locations(self, locations, game_state):
        filtered = []
        for location in locations:
            if not game_state.contains_stationary_unit(location):
                filtered.append(location)
        return filtered

    def on_action_frame(self, turn_string):
        """
        This is the action frame of the game. This function could be called 
        hundreds of times per turn and could slow the algo down so avoid putting slow code here.
        Processing the action frames is complicated so we only suggest it if you have time and experience.
        Full doc on format of a game frame at: https://docs.c1games.com/json-docs.html
        """
        # Let's record at what position we get scored on
        state = json.loads(turn_string)
        events = state["events"]
        breaches = events["breach"]
        for breach in breaches:
            location = breach[0]
            unit_owner_self = True if breach[4] == 1 else False
            # When parsing the frame data directly, 
            # 1 is integer for yourself, 2 is opponent (StarterKit code uses 0, 1 as player_index instead)
            if not unit_owner_self:
                gamelib.debug_write("Got scored on at: {}".format(location))
                self.scored_on_locations.append(location)
                gamelib.debug_write("All locations: {}".format(self.scored_on_locations))


if __name__ == "__main__":
    algo = AlgoStrategy()
    algo.start()
