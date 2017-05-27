# -*- coding: utf-8 -*-
"""
Main file for ghost in the cell.
"""
from sys import stderr


def print_err(*args):
    """Print on error output."""
    print(*args, file=stderr)
    stderr.flush()


INCREASE_CONDITION = 0
ATTACK_DIST = 500
DEF_DIST = 500
BOMB_DIST = [4, 6, 8, 10]


# =========
class Game:
    """
    Class representing a game.
    """

    # =================
    def __init__(self):
        """Constructor"""
        self.__all_factory = []
        self.__current_turn = 0
        self.__sent_bombs = {}  # turn per factory id
        self.__nb_enemy_cyborg = 0
        self.__nb_mine_cyborg = 0

    # =====================================
    def next_turn(self, nb_enemy, nb_mine):
        """Apply next turn."""
        self.__current_turn += 1
        self.__nb_enemy_cyborg = nb_enemy
        self.__nb_mine_cyborg = nb_mine

        self.__set_closest_enemy_factories()

    # ======================================
    def __set_closest_enemy_factories(self):
        """..."""
        # Get the list of enemy factory from which "self" is the closest
        closest_dict = {}  # {enemy_id:[mine_id, dist]}
        for fi, f in enumerate(self.__all_factory):
            f.reset_closest_enemies()
            if f.is_mine():
                cur_closest_dict = f.get_enemies_dist()
                for fi_enemy, d in cur_closest_dict.items():
                    if fi_enemy not in closest_dict.keys() or d < closest_dict[fi_enemy][1]:
                        closest_dict[fi_enemy] = [fi, d]

        for fi_enemy, [fi, _] in closest_dict.items():
            self.__all_factory[fi].add_closest_enemy(fi_enemy)

    # ==============================
    def add_factory(self, factory_id):
        """Add a factory to the game"""
        nb_factory = max(len(self.__all_factory), factory_id + 1)
        while len(self.__all_factory) < nb_factory:
            self.__all_factory.append(Factory(len(self.__all_factory)))

    # ===================================================
    def set_factory_dist(self, factory1, factory2, dist):
        """Set the distance between two factories"""
        self.__all_factory[factory1].set_dist(factory2, dist, self.__all_factory[factory2])
        self.__all_factory[factory2].set_dist(factory1, dist, self.__all_factory[factory1])

    # ========================================================================
    def set_factory_info(self, factory_id, owner, nb_cyborg, prod, disabled_turn, coming_cyborg):
        """Set new info to a factory"""
        self.__all_factory[factory_id].set_info(owner, nb_cyborg, prod, disabled_turn, coming_cyborg)

    # ===================
    def get_orders(self):
        """Compute best order to give to all factories."""
        orders_per_factory = {}
        enemy_estimated_orders = self.__get_enemy_impacting_moves()
        my_moves = [{}]
        for fi, f in enumerate(self.__all_factory):
            if f.is_mine():
                orders_per_factory[fi] = f.get_orders(self.__nb_enemy_cyborg,
                                                      self.__nb_mine_cyborg,
                                                      enemy_estimated_orders,
                                                      my_moves)
                self.__update_my_moves(my_moves, orders_per_factory[fi], fi)
        orders = self.__post_treat_orders(orders_per_factory)
        return orders

    def __update_my_moves(self, my_moves, factory_orders, fi):
        move_orders = factory_orders[0]
        for destination, nb in move_orders:
            if destination not in my_moves[-1].keys():
                my_moves[-1][destination] = {}
            d = self.__all_factory[fi].get_distance(destination)
            if d not in my_moves[-1][destination].keys():
                my_moves[-1][destination][d] = 0
            my_moves[-1][destination][d] += nb

    def __get_enemy_impacting_moves(self):
        """You don't get it?"""
        orders_per_factory = {}
        for fi, f in enumerate(self.__all_factory):
            if f.is_enemy():
                orders_per_factory[fi] = f.get_orders(self.__nb_enemy_cyborg,
                                                      self.__nb_mine_cyborg)
        estimated_orders = [{}]
        for fi, orders in orders_per_factory.items():
            move_orders = orders[0]
            for destination, nb in move_orders:
                if destination not in estimated_orders[-1].keys():
                    estimated_orders[-1][destination] = {}
                d = self.__all_factory[fi].get_distance(destination)
                if d not in estimated_orders[-1][destination].keys():
                    estimated_orders[-1][destination][d] = 0
                estimated_orders[-1][destination][d] += nb
        # print_err("estimated_orders", estimated_orders)
        return estimated_orders

    # ================================================
    def __post_treat_orders(self, orders_per_factory):
        """Post treat orders, remove opposite moves between factories."""
        final_move_orders = {}  # source, destination, nb
        final_bomb_order = []  # [source, destination]
        final_increase_order = []
        for fi, [move_order, bomb_order, increase_order] in orders_per_factory.items():
            for [destination, nb] in move_order:
                # if fi not in final_move_orders.keys():
                #     final_move_orders[fi] = {}
                # if destination not in final_move_orders[fi].keys():
                #     final_move_orders[fi][destination] = nb
                # else:
                #     final_move_orders[fi][destination] += nb
                if destination in final_move_orders.keys() and fi in final_move_orders[destination].keys():
                    if nb < final_move_orders[destination][fi]:
                        final_move_orders[destination][fi] -= nb
                    else:
                        if nb > final_move_orders[destination][fi]:
                            if fi not in final_move_orders.keys():
                                final_move_orders[fi] = {}
                            final_move_orders[fi][destination] = nb - final_move_orders[destination][fi]
                        del final_move_orders[destination][fi]
                else:
                    if fi not in final_move_orders.keys():
                        final_move_orders[fi] = {}
                    final_move_orders[fi][destination] = nb
            if bomb_order is not None:
                for target_fi in bomb_order:
                    final_bomb_order.append([fi, target_fi])
            if increase_order:
                final_increase_order.append(fi)
        orders = ""
        for src, d in final_move_orders.items():
            for destination, nb in d.items():
                if orders != "":
                    orders += ";MOVE " + str(src) + " " + str(destination) + " " + str(nb)
                else:
                    orders = "MOVE " + str(src) + " " + str(destination) + " " + str(nb)
        for src, destination in final_bomb_order:
            if self.__all_factory[destination].get_future_state(src, final_move_orders) == "e" and \
               (destination not in self.__sent_bombs.keys() or
               self.__sent_bombs[destination] + 9 < self.__current_turn):
                if orders != "":
                    orders += ";BOMB " + str(src) + " " + str(destination)
                else:
                    orders = "BOMB " + str(src) + " " + str(destination)
                self.__sent_bombs[destination] = self.__current_turn
        for fi in final_increase_order:
            if orders != "":
                orders += ";INC " + str(fi)
            else:
                orders = "INC " + str(fi)
        if orders == "":
            orders = "WAIT"
        return orders

    # ================
    def display(self):
        """Display the state of the game."""
        for i, f in enumerate(self.__all_factory):
            print_err(str(i) + " " + str(f) + "\n")


# ============
class Factory:
    """Class of a factory."""

    # =============================
    def __init__(self, factory_id):
        """Constructor"""
        self.__id = factory_id
        self.__owner = "n"
        self.__nb_cyborg = None
        self.__production = None
        self.__turn_until_product_back = 0
        self.__coming_cyborgs = {'m': [], 'e': []}
        self.__connections = {}
        self.__closest_enemies = []

    # ====================================================
    def get_orders(self, nb_enemy_cyborg, nb_mine_cyborg, estimated_enemy_moves=None, my_moves=None):
        """Get the orders for one given factory."""
        considered_owner = "m"
        if estimated_enemy_moves is None:
            considered_owner = "e"
        increase_order = False
        move_orders = []
        available_cyborg = self.__nb_cyborg
        pre_move_orders = self.__get_moves_orders(nb_enemy_cyborg, nb_mine_cyborg,
                                                  available_cyborg, estimated_enemy_moves, my_moves,
                                                  forced_mode="attack")
        # print_err("get_orders, pre_move_orders=", self.__id, pre_move_orders)
        for [destination, nb] in pre_move_orders:
            if self.__connections[destination][0].get_production() > 1:
                available_cyborg -= nb
                move_orders.append([destination, nb])
        if self.__increase_production_order(nb_enemy_cyborg, nb_mine_cyborg, estimated_enemy_moves, available_cyborg):
            increase_order = True
            available_cyborg -= 10

        # print_err("get_orders", self.__id, available_cyborg, increase_order)
        post_move_orders = []
        if len(self.__coming_cyborgs[considered_owner]) == 0 or self.__production == 3:
            post_move_orders = self.__get_moves_orders(nb_enemy_cyborg, nb_mine_cyborg,
                                                       available_cyborg, estimated_enemy_moves, my_moves)
        for order in post_move_orders:
            move_orders.append(order)
        # print_err("moves_order =", move_orders)
        bomb_orders = self.__get_bomb_orders(estimated_enemy_moves, my_moves)

        return move_orders, bomb_orders, increase_order

    # ==============================================================================
    def __get_moves_orders(self, nb_enemy_cyborg, nb_mine_cyborg, available_cyborg, estimated_enemy_moves, my_moves,
                           forced_mode="defense"):
        """Compute best moves for the factory to first defend, then attack."""
        move_orders = []
        no_more_order = False
        treated_destinations = []
        # Look for all possible orders (while the factory can take control or help another)
        target_type = forced_mode
        while not no_more_order or target_type != "attack":
            # print_err("-----------------", self.__id)
            if no_more_order:
                if target_type == "defense":
                    orders = self.__look_for_factory_to_increase(nb_enemy_cyborg, nb_mine_cyborg, estimated_enemy_moves,
                                                                 my_moves, available_cyborg)
                    for order in orders:
                        move_orders.append(order)
                        available_cyborg -= order[1]
                    target_type = "attack"
                elif target_type == "wall":
                    target_type = "attack"
            # no_more_target_factory = stop criteria -> while we have a move, we look for another
            target, no_more_target_factory = self.__get_target(target_type, treated_destinations, estimated_enemy_moves)
            # print_err(target)
            # Target found, factory can attack or help
            if target[0] is not None:
                # Compute the number of cyborg necessary to take control or save
                f, nb_turn = self.__connections[target[0]]
                if target_type != "wall":
                    nb_cyborg_per_turn = f.get_needed_cyborg(nb_turn + 1, estimated_enemy_moves, my_moves)
                else:
                    nb_cyborg_per_turn = {nb_turn: self.__nb_cyborg-1}
                # if estimated_enemy_moves is not None:
                #     print_err("Target found:", self.__id, target[0], nb_cyborg_per_turn, available_cyborg, nb_turn)
                # If not enough, we just give up for now (should be changed for defense...)
                # compute linear percent
                percent = 100
                # if target_type == "attack":
                #     MAX_DIST = 19
                #     MIN_DIST = 4
                #     a = 100 / (MIN_DIST - MAX_DIST)
                #     b = -a * MAX_DIST
                #     percent = min(100, a * nb_turn + b)
                # check_available = available_cyborg + available_cyborg * percent / 100
                check_available = available_cyborg * percent / 100
                # print_err("check_available =", check_available, percent)
                nb_sent_cyborg = 0
                nb_cyborg = nb_cyborg_per_turn[nb_turn]
                if True:
                    # for nb_cyborg in nb_cyborg_per_turn.values():
                    # print_err(nb_cyborg)
                    # print_err(self.__id, target[0], nb_cyborg, check_available)
                    if target[0] is not None and 0 < nb_cyborg <= check_available:
                        # print_err("Et si on entre", self.__id, target[0], nb_cyborg)
                        percent_cyborg = int(nb_cyborg * percent / 100)
                        new_nb_sent_cyborg = max(min(available_cyborg, percent_cyborg), 1)
                        # print_err("Try attack!", percent_cyborg, new_nb_sent_cyborg)
                        # print_err("check danger ----", self.__id, nb_sent_cyborg)
                        if not self.is_in_danger(estimated_enemy_moves, new_nb_sent_cyborg):
                            nb_sent_cyborg = new_nb_sent_cyborg
                # print_err(nb_sent_cyborg)
                if nb_sent_cyborg > 0:
                    # print_err(percent, nb_turn, available_cyborg, nb_cyborg,
                    #           nb_sent_cyborg, check_available, percent_cyborg)
                    move_orders.append([target[0], nb_sent_cyborg])
                    available_cyborg -= nb_sent_cyborg

                # Factory treated! Don't forget that or infinite loop! ^.^
                treated_destinations.append(target[0])
                # print_err(available_cyborg, len(treated_destinations), move_orders)
            # Keep at least one cyborg just in case...
            no_more_order = no_more_target_factory  # available_cyborg < 2 or no_more_target_factory

        # check if cyborg available to send to increase directly
        for i, [fi, nb] in enumerate(move_orders):
            if available_cyborg >= 10 and \
                            self.__connections[fi][0].get_production() < 3 and \
                    not self.is_in_danger(estimated_enemy_moves, nb + 10):
                move_orders[i][1] += 10

        return move_orders

    # =====================================================================
    def __increase_production_order(self, nb_enemy_cyborg, nb_mine_cyborg, estimated_enemy_moves, available_cyborg):
        """Check if increase production is worth it."""
        # print_err("increase self?", self.__id, self.is_in_danger(estimated_enemy_moves, 10))
        order = False
        nb_cyborg_more = INCREASE_CONDITION * nb_mine_cyborg / 100
        already_sent = self.__nb_cyborg - available_cyborg
        # print_err("increase cond", self.__id, INCREASE_CONDITION, nb_enemy_cyborg, nb_mine_cyborg, nb_cyborg_more)
        # print_err(already_sent, self.is_in_danger(estimated_enemy_moves, already_sent+10))
        if INCREASE_CONDITION == 0 or nb_enemy_cyborg <= (nb_mine_cyborg - nb_cyborg_more):
            if (self.__production == 0 and available_cyborg >= 10 or
                self.__production == 1 and available_cyborg >= 10 or
                self.__production == 2 and available_cyborg >= 10) and \
               not self.is_in_danger(estimated_enemy_moves, already_sent + 10):
                order = True
        return order

    # ==========================
    def __get_bomb_orders(self, estimated_enemy_moves, my_moves):
        """Bomb order..."""
        # print_err("Bomb order...", self.__id, estimated_enemy_moves)
        # print_err("Bomb order...", self.__closest_enemies)
        orders = []
        best_factory_enemy = [None, None]
        for fi in self.__closest_enemies:
            f = self.__connections[fi][0]
            if best_factory_enemy[0] is None:
                best_factory_enemy = [f, fi]
            elif f.get_production() > best_factory_enemy[0].get_production():
                best_factory_enemy = [f, fi]
            elif f.get_nb_cyborg() > best_factory_enemy[0].get_nb_cyborg():
                best_factory_enemy = [f, fi]
        if best_factory_enemy[0] is not None:
            f, dist = self.__connections[best_factory_enemy[1]]
            production = f.get_effective_production()
            cyborg = f.get_nb_cyborg()
            if production == 0 and cyborg > 20 and dist < BOMB_DIST[0] or \
               production == 1 and cyborg > 10 and dist < BOMB_DIST[1] or \
               production == 2 and cyborg > 5 and dist < BOMB_DIST[2] or \
               production == 3 and dist < BOMB_DIST[3]:
                nb_cyborg_per_turn = f.get_needed_cyborg(dist + 1, estimated_enemy_moves, my_moves)
                if nb_cyborg_per_turn[dist + 1] > 0:
                    # print_err("BOMB", best_factory_enemy[1], nb_cyborg_per_turn)
                    orders.append(best_factory_enemy[1])
        return orders

    def get_effective_production(self):
        """..."""
        if self.__turn_until_product_back > 0:
            return 0
        return self.__production

    # ==============================================================
    def __get_target(self, target_type, treated_destinations, estimated_enemy_moves):
        """Get the best target for the given factory"""
        # print_err("get_target", target_type, self.__id, treated_destinations, estimated_enemy_moves)
        target = [None, -1]  # if of factory, production of factory, number of cyborg in it
        no_more_target_factory = True
        cur_dist = float("inf")
        if target_type == "wall":
            cur_dist = self.__check_enemy_dist(estimated_enemy_moves is not None)
        for fi, [f, d] in self.__connections.items():
            check_owner = f.is_mine
            if estimated_enemy_moves is None:
                check_owner = f.is_enemy
            # If factory already treated we don't test it (allows to find same type of factory but more far)
            if fi not in treated_destinations:
                if (target_type == "attack" and not check_owner() or
                   target_type == "defense" and check_owner()):
                    # Take the closest with better production
                    if target_type == "attack" and d < ATTACK_DIST or \
                       target_type == "defense" and d < DEF_DIST:
                        if f.get_production() >= target[1] and \
                           f.get_production() >= 0 and \
                           self.__id != fi and \
                           d <= cur_dist:
                            cur_dist = d
                            target = [fi, f.get_production()]
                            # print_err(target, d)
                            no_more_target_factory = False
                elif target_type == "wall":
                    # if self.__id == 5:
                    #     print_err("__get_target - wall", fi, f.__check_enemy_dist(estimated_enemy_moves is not None), cur_dist)
                    if check_owner and f.__check_enemy_dist() < cur_dist:
                        cur_dist = f.__check_enemy_dist(estimated_enemy_moves is not None)
                        target = [fi, f.get_production()]
                        no_more_target_factory = False

        return target, no_more_target_factory

    def __check_enemy_dist(self, check_mine=True):
        """..."""
        dist = float("inf")
        for fi, [f, d] in self.__connections.items():
            check_owner = f.is_mine
            if not check_mine:
                check_owner = f.is_enemy
            if not check_owner() and d < dist:
                dist = d
        return dist

    # ==================================================================
    def is_in_danger(self, estimated_enemy_moves, nb_less_cyborg=0):
        """Check if the factory is going to be taken."""
        considered_owner = "m"
        considered_enemy = "e"
        if estimated_enemy_moves is None:
            considered_owner = "e"
            considered_enemy = "m"
        enemy_factory_dist_cyborg = []
        for fi, [factory, dist] in self.__connections.items():
            if estimated_enemy_moves is not None and factory.is_enemy() or factory.is_mine():
                enemy_factory_dist_cyborg.append([dist, factory.get_nb_cyborg()])
        # Check each time
        # print_err("in danger", self.__id, self.__nb_cyborg, nb_less_cyborg)
        diff = {0: self.__nb_cyborg - nb_less_cyborg}  # per time
        for d, nb_cyborg in enemy_factory_dist_cyborg:
            if d in [1] and False:
                diff[d] = -nb_cyborg  # - self.__production
        for n, t in self.__coming_cyborgs[considered_owner]:
            if t not in diff.keys():
                for i in range(t + 1):
                    if i not in diff.keys():
                        diff[i] = diff[i - 1]
                        if i >= self.__turn_until_product_back:
                            diff[i] += self.__production
            diff[t] += n
        for n, t in self.__coming_cyborgs[considered_enemy]:
            if t not in diff.keys():
                for i in range(t + 1):
                    if i not in diff.keys():
                        diff[i] = diff[i - 1]
                        if i >= self.__turn_until_product_back:
                            diff[i] += self.__production
            diff[t] -= n

        if estimated_enemy_moves is not None and self.__id in estimated_enemy_moves[0].keys():
            for t, n in estimated_enemy_moves[0][self.__id].items():
                if t not in diff.keys():
                    for i in range(t + 1):
                        if i not in diff.keys():
                            diff[i] = diff[i - 1]
                            if i >= self.__turn_until_product_back:
                                diff[i] += self.__production
                diff[t] -= estimated_enemy_moves[0][self.__id][t]

        # print_err(diff)
        for t, n in diff.items():
            if n < 0:
                return True
        return False

    # ===================================================
    def __look_for_factory_to_increase(self, nb_enemy_cyborg, nb_mine_cyborg, estimated_enemy_moves, my_moves,
                                       available_cyborg):
        # print_err("look_to_increase", self.__id, nb_enemy_cyborg, nb_mine_cyborg, estimated_enemy_moves)
        targets = []
        cur_send_cyborg = 0
        nb_cyborg_more = INCREASE_CONDITION * nb_mine_cyborg / 100
        if INCREASE_CONDITION == 0 or nb_enemy_cyborg <= (nb_mine_cyborg - nb_cyborg_more):
            no_more_fact = False
            already_treated = []
            while not no_more_fact:
                no_more_fact = True
                closest_target = [None, 7, 0]
                for fi, [f, d] in self.__connections.items():
                    if fi not in already_treated:
                        check_owner = f.is_mine
                        if estimated_enemy_moves is None:
                            check_owner = f.is_enemy
                        if check_owner() and 0 <= f.get_production() < 3 and d < closest_target[1]:
                            nb_cyborg_to_send = 10 + f.get_needed_cyborg(d, estimated_enemy_moves, my_moves)[d]
                            if nb_cyborg_to_send > 0 and not self.is_in_danger(estimated_enemy_moves,
                                                                               cur_send_cyborg + nb_cyborg_to_send):
                                if available_cyborg >= nb_cyborg_to_send:
                                    no_more_fact = False
                                    closest_target = [fi, d, nb_cyborg_to_send]
                if closest_target[0] is not None:
                    targets.append([closest_target[0], closest_target[2]])
                    already_treated.append(closest_target[0])
                    cur_send_cyborg += closest_target[2]
        # print_err("look_to_increase", self.__id, targets)
        return targets

    # ====================================================
    def get_future_state(self, factory_id, current_moves):
        """
        Get the state of the factory (enemy/mine/neutral) according to
        the distance from the factory_id.
        :param factory_id: the id of the factory to consider the distance from
        :type factory_id: int
        :param current_moves: the current decided moves {src:{destination:nb_cy}}
        :type current_moves: dict{int:{int:int}}
        :return: The state
        :rtype: "e"|"m"|"n"
        """
        # coming_cyborg = {"m":{time:nb}, "e":{time:nb}}
        coming_cyborg = {"m": {}, "e": {}}
        for owner in ["e", "m"]:
            for nb, t in self.__coming_cyborgs[owner]:
                if t not in coming_cyborg[owner].keys():
                    coming_cyborg[owner][t] = 0
                coming_cyborg[owner][t] += nb

        for src, dict_src in current_moves.items():
            if self.__id in dict_src.keys():
                nb = dict_src[self.__id]
                _, d = self.__connections[src]
                if d not in coming_cyborg["m"].keys():
                    coming_cyborg["m"][d] = 0
                coming_cyborg["m"][d] += nb

        current_owner = self.__owner
        nb_cyborg_in_factory = self.__nb_cyborg

        _, d = self.__connections[factory_id]
        for t in range(d + 1):
            if current_owner != "n":
                if self.__turn_until_product_back == 0:
                    nb_cyborg_in_factory += self.__production
            if t not in coming_cyborg["m"].keys():
                coming_cyborg["m"][t] = 0
            if t not in coming_cyborg["e"].keys():
                coming_cyborg["e"][t] = 0
            nb_cyborg_left = coming_cyborg["m"][t] - coming_cyborg["e"][t]
            winner = "m"
            if nb_cyborg_left < 0:
                winner = "e"
            elif nb_cyborg_left == 0:
                winner = "n"
            nb_cyborg_left = abs(nb_cyborg_left)
            if winner != "n":
                if winner != current_owner:
                    nb_cyborg_in_factory -= nb_cyborg_left
                    if nb_cyborg_in_factory < 0:
                        current_owner = winner
                        nb_cyborg_in_factory = abs(nb_cyborg_in_factory)
                else:
                    nb_cyborg_in_factory += nb_cyborg_left
        return current_owner

    # ======================
    def get_nb_cyborg(self):
        """Get number of cyborg currently in the factory."""
        return self.__nb_cyborg

    # =======================
    def get_production(self):
        """Get the production of the factory."""
        return self.__production

    # ================
    def is_mine(self):
        """Check if factory is mine."""
        return self.__owner == "m"

    # ==================
    def is_enemy(self):
        """Check if factory belongs to enemy."""
        return self.__owner == "e"

    # ==========================
    def get_needed_cyborg(self, nb_turn, estimated_enemy_moves, my_moves):
        """Get number of cyborg to take control or save the factory."""
        # if estimated_enemy_moves is not None:
        #     print_err("get_needed_cy", self.__id, self.__coming_cyborgs, nb_turn, estimated_enemy_moves)
        considered_owner = "m"
        considered_enemy = "e"
        if estimated_enemy_moves is None:
            considered_owner = "e"
            considered_enemy = "m"
        needed_cyborg = {}
        if self.__owner == considered_owner:
            needed_cyborg[0] = -self.__nb_cyborg
        else:
            needed_cyborg[0] = self.__nb_cyborg + 1
        current_owner = self.__owner
        for i in range(1, nb_turn + 1):
            if i not in needed_cyborg.keys():
                needed_cyborg[i] = needed_cyborg[i - 1]
            if i >= self.__turn_until_product_back:
                if current_owner == considered_owner:
                    needed_cyborg[i] -= self.__production
                elif current_owner == considered_enemy:
                    needed_cyborg[i] += self.__production
            for n, t in self.__coming_cyborgs[considered_owner]:
                if t == i:
                    needed_cyborg[i] -= n
                    if needed_cyborg[i] < 0:
                        current_owner = considered_owner
            for n, t in self.__coming_cyborgs[considered_enemy]:
                if t == i:
                    if current_owner == "n":
                        needed_cyborg[i] = abs((needed_cyborg[i] - 1) - n)
                    else:
                        needed_cyborg[i] += n
                    if needed_cyborg[i] > 0:
                        current_owner = considered_enemy
                        needed_cyborg[i] += 1
            if estimated_enemy_moves is not None and \
               self.__id in estimated_enemy_moves[0].keys() and \
               i in estimated_enemy_moves[0][self.__id].keys():
                if current_owner == "n":
                    needed_cyborg[i] = abs((needed_cyborg[i] - 1) - estimated_enemy_moves[0][self.__id][i]) + 1
                else:
                    needed_cyborg[i] += estimated_enemy_moves[0][self.__id][i] + 1
                if needed_cyborg[i] > 0:
                    current_owner = considered_enemy
            if my_moves is not None and \
               self.__id in my_moves[0].keys() and \
               i in my_moves[0][self.__id].keys():
                needed_cyborg[i] -= my_moves[0][self.__id][i]
                if needed_cyborg[i] < 0:
                    current_owner = considered_owner
        # if estimated_enemy_moves is not None:
        #     print_err("needed_cy = ", needed_cyborg)
        return needed_cyborg

    # =========================
    def get_enemies_dist(self):
        """Get the list of distances to each enemy factory."""
        dists = {}
        for fi, [f, d] in self.__connections.items():
            if f.is_enemy():
                dists[fi] = d
        return dists

    def get_distance(self, fi):
        """..."""
        return self.__connections[fi][1]

    # ================================================
    def set_info(self, owner, nb_cyborg, prod, disabled_turn, coming_cyborg):
        """Set information of the factory."""
        self.__owner = owner
        self.__nb_cyborg = nb_cyborg
        self.__production = prod
        self.__turn_until_product_back = disabled_turn
        self.__coming_cyborgs = {'m': [], 'e': []}
        for cy in coming_cyborg['m']:
            self.__coming_cyborgs['m'].append([cy[0], cy[1]])
        for cy in coming_cyborg['e']:
            self.__coming_cyborgs['e'].append([cy[0], cy[1]])

    # ==============================
    def reset_closest_enemies(self):
        """Remove all known closest enemies."""
        self.__closest_enemies = []

    # ====================================
    def add_closest_enemy(self, fi_enemy):
        """Add a closest enemy (set by Game)."""
        if fi_enemy not in self.__closest_enemies:
            self.__closest_enemies.append(fi_enemy)

    # ===========================================
    def set_dist(self, factory_id, dist, factory):
        """Set distance between two factories."""
        self.__connections[factory_id] = [factory, dist]

    # ================
    def __str__(self):
        """str operator"""
        return "factory - " + self.__owner + " " + str(self.__nb_cyborg) + " " + str(self.__production)


# ========================
if __name__ == "__main__":

    ga = Game()

    # Auto-generated code below aims at helping you parse
    # the standard input according to the problem statement.
    factory_count = int(input())  # the number of factories
    link_count = int(input())  # the number of links between factories
    for _ in range(link_count):
        factory_1, factory_2, distance = [int(j) for j in input().split()]
        ga.add_factory(factory_1)
        ga.add_factory(factory_2)
        ga.set_factory_dist(factory_1, factory_2, distance)

    # game loop
    while True:
        factory_info = {}
        troops_info = {}
        cur_nb_enemy = 0
        cur_nb_mine = 0
        entity_count = int(input())  # the number of entities (e.g. factories and troops)
        for _ in range(entity_count):
            entity_id, entity_type, arg_1, arg_2, arg_3, arg_4, arg_5 = input().split()
            entity_id = int(entity_id)
            arg_1 = int(arg_1)
            arg_2 = int(arg_2)
            arg_3 = int(arg_3)
            arg_4 = int(arg_4)
            arg_5 = int(arg_5)
            cur_owner = "n"
            if arg_1 == 1:
                cur_owner = "m"
            elif arg_1 == -1:
                cur_owner = "e"

            if entity_type == "FACTORY":
                nb_cy = arg_2
                cur_prod = arg_3
                cur_disabled_turn = arg_4
                factory_info[entity_id] = [cur_owner, nb_cy, cur_prod, cur_disabled_turn]
                if cur_owner == "e":
                    cur_nb_enemy += nb_cy
                elif cur_owner == "m":
                    cur_nb_mine += nb_cy
            elif entity_type == "TROOP":
                if arg_3 not in troops_info.keys():
                    troops_info[arg_3] = {'m': [], 'e': []}
                if arg_1 == 1:
                    troops_info[arg_3]['m'].append([arg_4, arg_5])
                    cur_nb_mine += arg_4
                else:
                    troops_info[arg_3]['e'].append([arg_4, arg_5])
                    cur_nb_enemy += arg_4

        ga.next_turn(cur_nb_enemy, cur_nb_mine)
        # print_err(factory_info)

        for cur_factory_id, cur_factory_info in factory_info.items():
            troops_info_factory = {'e': [], 'm': []}
            if cur_factory_id in troops_info.keys():
                troops_info_factory = troops_info[cur_factory_id]
            ga.set_factory_info(cur_factory_id, cur_factory_info[0], cur_factory_info[1],
                                cur_factory_info[2], cur_factory_info[3], troops_info_factory)

        # ga.display()

        s = ga.get_orders()

        # Write an action using print
        # To debug: print("Debug messages...", file=sys.stderr)

        # Any valid action, such as "WAIT" or "MOVE source destination cyborgs"
        print(s)
