# -*- coding: utf-8 -*-
"""
Main file for ghost in the cell.
"""
from sys import stderr


def print_err(*args):
    """Print on error output."""
    print(*args, file=stderr)
    stderr.flush()


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
        # Get the list of enemy factory from which "self" is the closest
        closest_dict = {}  # {enemy_id:[mine_id, dist]}
        for fi, f in enumerate(self.__all_factory):
            f.reset_closest_enemies()
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
        for fi, f in enumerate(self.__all_factory):
            if f.is_mine():
                orders_per_factory[fi] = f.get_orders(self.__nb_enemy_cyborg,
                                                      self.__nb_mine_cyborg)
        orders = self.__post_treat_orders(orders_per_factory)
        return orders

    # ==============================================
    @staticmethod
    def __post_treat_orders(orders_per_factory):
        """Post treat orders, remove opposite moves between factories."""
        final_move_orders = {} # source, destination, nb
        final_bomb_order = [] # [source, destination]
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
                            if fi not in final_orders.keys():
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
            if orders != "":
                orders += ";BOMB " + str(src) + " " + str(destination)
            else: # TODO : pas envoyer une bombe deux fois au même endroit (avant 5 tours)
                orders = "BOMB " + str(src) + " " + str(destination)
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
    def get_orders(self, nb_enemy_cyborg, nb_mine_cyborg):
        """Get the orders for one given factory."""
        increase_order = False
        available_cyborg = self.__nb_cyborg
        if self.__increase_production_order(nb_enemy_cyborg, nb_mine_cyborg):
            increase_order = True
            available_cyborg -= 10

        move_orders = self.__get_moves_orders(nb_enemy_cyborg, nb_mine_cyborg, available_cyborg)

        bomb_orders = self.__get_bomb_orders()

        return move_orders, bomb_orders, increase_order

    # ==============================================================================
    def __get_moves_orders(self, nb_enemy_cyborg, nb_mine_cyborg, available_cyborg):
        """Compute best moves for the factory to first defend, then attack."""
        move_orders = []
        no_more_order = False
        treated_destinations = []
        # Look for all possible orders (while the factory can take control or help another)
        target_type = "defense"
        while not no_more_order or target_type == "defense":
            # print_err("-----------------", self.__id)
            if no_more_order:
                if available_cyborg > 10:
                    order = self.__look_for_factory_to_increase(nb_enemy_cyborg, nb_mine_cyborg)
                    if order is not None:
                        move_orders.append(order)
                        available_cyborg -= order[1]
                target_type = "attack"
            # no_more_target_factory = stop criteria -> while we have a move, we look for another
            target, no_more_target_factory = self.__get_target(target_type, treated_destinations)
            # print_err(target)
            # Target found, factory can attack or help
            if target[0] is not None:
                # Compute the number of cyborg necessary to take control or save
                f, nb_turn = self.__connections[target[0]]
                nb_cyborg_per_turn = f.get_needed_cyborg(nb_turn + 1)
                # print_err(target[0], nb_cyborg_per_turn, available_cyborg)
                # If not enough, we just give up for now (should be changed for defense...)
                # compute linear percent
                percent = 100
                if target_type == "attack":
                    MAX_DIST = 19
                    MIN_DIST = 4
                    a = 100 / (MIN_DIST - MAX_DIST)
                    b = -a * MAX_DIST
                    percent = min(100, a * nb_turn + b)
                check_available = available_cyborg + available_cyborg * percent / 100
                # print_err("check_available =", check_available, percent)
                nb_sent_cyborg = 0
                for nb_cyborg in nb_cyborg_per_turn.values():
                    # print_err(nb_cyborg)
                    if target[0] is not None and 0 < nb_cyborg < check_available:
                        percent_cyborg = int(nb_cyborg * percent / 100)
                        new_nb_sent_cyborg = max(min(available_cyborg, percent_cyborg), 1)
                        # print_err(percent_cyborg, new_nb_sent_cyborg)
                        # print_err("check danger ----", self.__id, nb_sent_cyborg)
                        if not self.is_in_danger(new_nb_sent_cyborg):
                            nb_sent_cyborg = new_nb_sent_cyborg
                # print_err(nb_sent_cyborg)
                if nb_sent_cyborg > 0:
                    # print_err(percent, nb_turn, available_cyborg, nb_cyborg,
                    # nb_sent_cyborg, check_available, percent_cyborg)
                    move_orders.append([target[0], nb_sent_cyborg])
                    available_cyborg -= nb_sent_cyborg
                # Factory treated! Don't forget that or infinite loop! ^.^
                treated_destinations.append(target[0])
                # print_err(available_cyborg, len(treated_destinations), move_orders)
            # Keep at least one cyborg just in case...
            no_more_order = available_cyborg < 2 or no_more_target_factory

        return move_orders

    # =====================================================================
    def __increase_production_order(self, nb_enemy_cyborg, nb_mine_cyborg):
        """Check if increase production is worth it."""
        order = False
        nb_cyborg_more = 10 * nb_mine_cyborg / 100
        if nb_enemy_cyborg <= (nb_mine_cyborg - nb_cyborg_more):
            if (self.__production == 0 and self.__nb_cyborg >= 20 or
                self.__production == 1 and self.__nb_cyborg >= 15 or
                self.__production == 2 and self.__nb_cyborg >= 10) and \
               not self.is_in_danger(10):
                order = True
        return order

    # ==========================
    def __get_bomb_orders(self):
        """Bomb order..."""
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
            if dist < 7:
                production = f.get_production()
                cyborg = f.get_nb_cyborg()
                if production == 0 and cyborg > 20 or \
                   production == 1 and cyborg > 15 or \
                   production == 2 and cyborg > 10 or \
                   production == 3:
                    nb_cyborg_per_turn = f.get_needed_cyborg(dist + 1)
                    if nb_cyborg_per_turn[dist + 1] > 0:
                        # print_err("BOMB", best_factory_enemy[1], nb_cyborg_per_turn)
                        orders.append(best_factory_enemy[1])
        return orders

    # ==============================================================
    def __get_target(self, target_type, treated_destinations):
        """Get the best target for the given factory"""
        # print_err("get_target", target_type, self.__id, treated_destinations)
        target = [None, -1, None]  # if of factory, production of factory, number of cyborg in it
        no_more_target_factory = True
        cur_dist = float("inf")

        for fi, [f, d] in self.__connections.items():
            # If factory already treated we don't test it (allows to find same type of factory but more far)
            if fi not in treated_destinations and \
               (target_type == "attack" and not f.is_mine() or target_type == "defense" and f.is_mine()):
                # Take the closest with better production
                if d <= cur_dist and f.get_production() >= target[1] and \
                   f.get_production() >= 0 and self.__id != fi:
                    cur_dist = d
                    target = [fi, f.get_production(), f.get_nb_cyborg()]
                    # print_err(target, d)
                    no_more_target_factory = False
        return target, no_more_target_factory

    # ==================================================================
    def is_in_danger(self, nb_less_cyborg=0):
        """Check if the factory is going to be taken."""
        enemy_factory_dist_cyborg = []
        for fi, [factory, dist] in self.__connections.items():
            if factory.is_enemy():
                enemy_factory_dist_cyborg.append([dist, factory.get_nb_cyborg()])
        # Check each time
        # print_err("in danger", self.__nb_cyborg, nb_less_cyborg)
        diff = {0: self.__nb_cyborg - nb_less_cyborg}  # per time
        for d, nb_cyborg in enemy_factory_dist_cyborg:
            if d in [1] and False:
                diff[d] = -nb_cyborg # - self.__production
        for n, t in self.__coming_cyborgs['m']:
            if t not in diff.keys():
                for i in range(t + 1):
                    if i not in diff.keys():
                        diff[i] = diff[i - 1]
                        if i >= self.__turn_until_product_back:
                            diff[i] += self.__production
            diff[t] += n
        for n, t in self.__coming_cyborgs['e']:
            if t not in diff.keys():
                for i in range(t + 1):
                    if i not in diff.keys():
                        diff[i] = diff[i - 1]
                        if i >= self.__turn_until_product_back:
                            diff[i] += self.__production
            diff[t] -= n
        # print_err(diff)
        for t, n in diff.items():
            if n <= 0:
                return True
        return False

    # ===================================================
    def __look_for_factory_to_increase(self, nb_enemy_cyborg, nb_mine_cyborg):
        # TODO : multiple increase?
        # TODO : envoyer que le nécessaire, pas "10" (vérifier si in_danger)
        target = [None, float("inf")]
        if nb_enemy_cyborg < (nb_mine_cyborg - 5) and not self.is_in_danger(10):
            for fi, [f, d] in self.__connections.items():
                if f.is_mine():
                    if 0 <= f.get_production() < 3:
                        if d < target[1]:
                            target = [fi, d]
        order = None
        if target[0] is not None:
            order = [target[0], 10]
        return order

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
    def get_needed_cyborg(self, nb_turn):
        """Get number of cyborg to take control or save the factory."""
        # print_err(self.__coming_cyborgs, nb_turn)
        needed_cyborg = {}
        if self.__owner == "m":
            needed_cyborg[0] = -self.__nb_cyborg
        else:
            needed_cyborg[0] = self.__nb_cyborg + 1
        current_owner = self.__owner
        for i in range(nb_turn+1):
            if i not in needed_cyborg.keys():
                needed_cyborg[i] = needed_cyborg[i-1]
            if current_owner == "m" and i >= self.__turn_until_product_back:
                needed_cyborg[i] -= self.__production
            elif current_owner == "e" and i >= self.__turn_until_product_back:
                needed_cyborg[i] += self.__production
            for n, t in self.__coming_cyborgs['m']:
                if t == i:
                    needed_cyborg[i] -= n
                    if needed_cyborg[i] < 0:
                        current_owner = "m"
            for n, t in self.__coming_cyborgs['e']:
                if t == i:
                    needed_cyborg[i] += n
                    if needed_cyborg[i] > 0:
                        current_owner = "e"
        return needed_cyborg

    # =========================
    def get_enemies_dist(self):
        """Get the list of distances to each enemy factory."""
        dists = {}
        for fi, [f, d] in self.__connections.items():
            if f.is_enemy():
                dists[fi] = d
        return dists

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
