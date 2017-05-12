# -*- coding: utf-8 -*-

from math import sqrt, degrees, tan, radians, acos, cos, sin, atan
from sys import stderr
from random import randint, sample, random
from time import time


def printerr(*args):
    print(*args, file=stderr)
    stderr.flush()

WP_INFO = [[13576, 7617], [12440, 1339], [10532, 6000], [3563, 5203]]
NB_WP = 4
# nbLaps = int(input())
# NB_WP = int(input())
# WP_INFO = []
# for ic in range(NB_WP):
#     WP_INFO.append([int(coord) for coord in input().split()])

WP_RAYON = 600

# Race/Battle order ===================
MIN_THRUST = 20
MAX_THRUST = 100
maxAngle = 80
minAngle = 10
boostAndReduceAngle = 10
boostDist = 4500
# =====================================

# Battle order ========================
BATTLE_AHEAD_COEF = 0.2
# =====================================

# Race order ==========================
DELTA_REACHED_POINT = 400  # consider the point passed
# pre-turn ---
NEXT_POINT_INFL_DIST = 3000
ANGLE_FOR_PRE_TURN = 180
ANGLE_INFL_THRUST_IN_DIST = 19
# -------------
ANGLE_TO_SKIP = 1
# =====================================

# Colision ============================
CUR_TURN = 1
RACE_NO_TURN_SHIELD = 5
COLLIDE_DIST_BATTLE = 900
COLLIDE_DIST_RACE = 820
# =====================================

# Pre-compute trajectory ==============
NB_POINT_BETWEEN_WP = 20
NB_TOTAL_POINTS = NB_WP + NB_POINT_BETWEEN_WP * NB_WP
MEAN_X_BETWEEN_POINTS = []
MEAN_Y_BETWEEN_POINTS = []
for i, coord in enumerate(WP_INFO):
    if i == 0:
        prev_x, prev_y = WP_INFO[-1]
    else:
        prev_x, prev_y = WP_INFO[i - 1]
    x_diff = abs(prev_x - coord[0])
    y_diff = abs(prev_y - coord[1])
    MEAN_X_BETWEEN_POINTS.append(x_diff / NB_POINT_BETWEEN_WP)
    MEAN_Y_BETWEEN_POINTS.append(y_diff / NB_POINT_BETWEEN_WP)
# point line -
X_DIFF_FOR_Y_BASE = 3000
MAX_NEW_DIFF_POINT_SEARCH_TRY = 50
# -------------
RATIO_ANGLE_THRUST = [100 / (180 - 18), 0]  # to estimate new thrust according to angle
# Fitness ----
ACCEPTABLE_DELTA_THRUST = 10
ACCEPTABLE_ANGLE = 180 - (18 * 2)
# -------------
NB_MAX_GEN = 0
MAX_EVO_TIME = 0.9
CROSS_RATIO = 0.25
NB_SELECTION = 5
BEST_SELECTION_RATIO = 0.5
POP_SIZE = 25
MUTATION_THRUST = 10
MIN_CROSS_POINT = int(NB_TOTAL_POINTS / 5)
MAX_CROSS_POINT = int(4 * NB_TOTAL_POINTS / 5)
MAX_CROSS_ANGLE_FIND_TRY = 20
#MIN_MUTE_POINT = int(NB_TOTAL_POINTS / 3)
MAX_COEF_PUSH_FROM_WP = 0.025
MIN_COEF_PUSH_FROM_WP = 0.00001
# =====================================

# Opponent info =======================
HEAD_OPP_POD = 1
OPP_TURN = [1, 1]
OPP_PREV_WP = [0, 0]
# =====================================

# Prediction simulation ===============
COEF_X_THRUST_NEXT_POINT = 1.0
# =====================================

import pyqtgraph as pg
pg.mkQApp()
pg.setConfigOption('background', 'w')
PLOT_WIDGET = pg.PlotWidget()
from PyQt4.QtGui import QApplication


# ================================================
def getAngleBetweenPoints(ax, ay, bx, by, cx, cy):
    norm_v1 = sqrt((ax - bx) ** 2 + (ay - by) ** 2)
    norm_v2 = sqrt((cx - bx) ** 2 + (cy - by) ** 2)
    if norm_v1 != 0.0 and norm_v2 != 0.0:
        V1x = (ax - bx) / norm_v1
        V1y = (ay - by) / norm_v1
        V2x = (cx - bx) / norm_v2
        V2y = (cy - by) / norm_v2
        angle = degrees(acos(max(-1.0, min(1.0, V1x * V2x + V1y * V2y))))
    else:
        angle = 0
    return angle


# =============================
def getWpDist(podsInfo, podId):
    x, y, vx, vy, a, wp = podsInfo[podId]
    wpx, wpy = WP_INFO[wp]
    wpDist = sqrt((x - wpx) ** 2 + (y - wpy) ** 2)
    return wpDist

# ==============================================
def getNextPoint(x, y, vx, vy, a, tax, tay, th):
    if th == "SHIELD":
        th = 0
    elif th == "BOOST":
        th = 650
    m = tan(a)
    vthx = th * COEF_X_THRUST_NEXT_POINT
    if 90 < a < 180:
        vthx = -vthx
    vthy = m * vthx
    # printerr(vthx, vthy)
    vn1x = 1.0 * (vx + vthx)
    vn1y = 1.0 * (vy + vthy)

    new_x = x + vn1x
    new_y = y + vn1y
    return new_x, new_y


# =================================================================
# =                              GA                               =
# =================================================================
CUR_ACCEPTABLE_DELTA_ANGLE = 0
class GA:
    # ===========================
    def __init__(self, pop_size):
        self.__pop_size = pop_size
        self.__pop = []
        self.__fit = []
        self.__curGen = 0
        self.__start_time = None

    # ============
    def run(self):
        t = time()

        # Test deterministe
        a = self.__random_indiv()
        new_ind = self.__mutate_indiv(a)
        while new_ind is not None:
            a = new_ind
            new_ind = self.__mutate_indiv(a)
            display_traj(0.0, new_ind)
            from time import sleep
            #sleep(200000)
        printerr("evo time", time() - t, self.__curGen, "gen")
        return new_ind
        # fin test

        self.__start_time = time()
        self.__init_pop()
        self.__evaluate()
        # printerr("init time", time() - t)
        while not (self.__stopCriteria()):
            # gt = time()
            # printerr(self.__curGen)
            self.__select()
            self.__reproduce()
            self.__evaluate()
            self.__curGen += 1
            # printerr("generation time", time() - gt)
        printerr("evo time", time() - t, self.__curGen, "gen")

    # ================
    def get_pop(self):
        return self.__pop, self.__fit

    # ======================
    def get_best_traj(self):
        max_fit_index = 0
        for i, f in enumerate(self.__fit):
            if f > self.__fit[max_fit_index]:
                max_fit_index = i
        return self.__pop[max_fit_index], self.__fit[max_fit_index]

    # ===================
    def __init_pop(self):
        self.__pop = []
        for i in range(self.__pop_size):
            self.__pop.append(self.__random_indiv())

    # ===================
    def __evaluate(self):
        self.__fit = []
        ideal_fit = 100 * NB_TOTAL_POINTS
        for indiv in self.__pop:
            # it = time()
            cur_point = 1
            thrust_sum = 0
            sum_da = 0
            sum_dt = 0
            accept = True
            nb_bad_angle = 0
            while accept and cur_point < len(indiv):
                # printerr("indiv format", indiv, indiv[cur_point])
                x, y, thrust = indiv[cur_point]
                thrust_sum += thrust
                # Compute angle
                if cur_point == 0:
                    xp, yp, tp = indiv[-1]
                else:
                    xp, yp, tp = indiv[cur_point - 1]
                if cur_point == len(indiv) - 1:
                    xn, yn, tn = indiv[0]
                else:
                    xn, yn, tn = indiv[cur_point + 1]
                angle = abs(getAngleBetweenPoints(xp, yp, x, y, xn, yn))
                # delta thrust
                estimated_t = int(RATIO_ANGLE_THRUST[0] * angle + RATIO_ANGLE_THRUST[1])
                estimated_t = min(100, max(0, estimated_t))
                dt = abs(estimated_t - thrust)
                accept = dt < ACCEPTABLE_DELTA_THRUST
                if accept:
                    sum_dt += dt
                # delta angle
                if angle < ACCEPTABLE_ANGLE:
                    nb_bad_angle += 1
                da = 180 - angle
                sum_da += da
                cur_point += 1
            fit = 0.0
            if accept:
                # printerr("fit", ideal_fit, (thrust_sum - sum_da - sum_dt))
                fit = max(0.0, (thrust_sum - sum_dt) / ideal_fit) / nb_bad_angle
                #fit = max(0.0, (thrust_sum - sum_da - sum_dt) / ideal_fit) / nb_bad_angle
            self.__fit.append(fit)
            # printerr("indiv time", time() - it)

    # =======================
    def __stopCriteria(self):
        stop = False
        # printerr(self.__fit)
        if 1.0 in self.__fit:
            stop = True
        if NB_MAX_GEN != 0 and self.__curGen == NB_MAX_GEN:
            stop = True
        if time() - self.__start_time > MAX_EVO_TIME:
            stop = True
        return stop

    # =================
    def __select(self):
        nb_best = int(NB_SELECTION * BEST_SELECTION_RATIO)
        fit_indexes = []
        for i, fit in enumerate(self.__fit):
            if len(fit_indexes) < nb_best:
                fit_indexes.append(i)
            else:
                min_fit_index = 0
                for ifi, fi in enumerate(fit_indexes):
                    if self.__fit[fit_indexes[min_fit_index]] < self.__fit[fi]:
                        min_fit_index = ifi
                if fit_indexes[min_fit_index] < fit:
                    fit_indexes[min_fit_index] = i
        while len(fit_indexes) < NB_SELECTION:
            i = randint(0, len(self.__fit)-1)
            while i in fit_indexes:
                i = randint(0, len(self.__fit)-1)
            fit_indexes.append(i)
        new_pop = []
        for i in fit_indexes:
            indiv = self.__pop[i]
            new_ind = []
            for p in indiv:
                new_ind.append([p[0], p[1], p[2]])
            new_pop.append(new_ind)
        self.__pop = new_pop
        # printerr("new_pop", self.__pop)

    # ====================
    def __reproduce(self):
        while len(self.__pop) < self.__pop_size:
            if random() < CROSS_RATIO:
                self.__pop.append(self.__cross())
            else:
                self.__pop.append(self.__mutate())

    # ================
    def __cross(self):
        a, b = sample(self.__pop, 2)
        point_to_cross = sample(list(range(NB_TOTAL_POINTS)),
                                randint(MIN_CROSS_POINT, MAX_CROSS_POINT))
        for i, cur_point in enumerate(point_to_cross):
            # Compute angle
            x, y, _ = b[cur_point]
            if cur_point == 0:
                xp, yp, tp = b[-1]
            else:
                xp, yp, tp = b[cur_point - 1]
            if cur_point == len(b) - 1:
                xn, yn, tn = b[0]
            else:
                xn, yn, tn = b[cur_point + 1]
            angle_b = abs(getAngleBetweenPoints(xp, yp, x, y, xn, yn))
            nbTry = 0
            while nbTry < MAX_CROSS_ANGLE_FIND_TRY and angle_b < ACCEPTABLE_ANGLE:
                cur_point = sample(list(range(NB_TOTAL_POINTS)), 1)[0]
                while cur_point in point_to_cross:
                    cur_point = sample(list(range(NB_TOTAL_POINTS)), 1)[0]
                x, y, _ = b[cur_point]
                if cur_point == 0:
                    xp, yp, tp = b[-1]
                else:
                    xp, yp, tp = b[cur_point - 1]
                if cur_point == len(b) - 1:
                    xn, yn, tn = b[0]
                else:
                    xn, yn, tn = b[cur_point + 1]
                angle_b = abs(getAngleBetweenPoints(xp, yp, x, y, xn, yn))
                nbTry += 1
            point_to_cross[i] = cur_point

        new_ind = []
        for i, p in enumerate(a):
            if i in point_to_cross:
                new_ind.append([b[i][0], b[i][1], b[i][2]])
            else:
                new_ind.append([p[0], p[1], p[2]])
        return new_ind

    # =================
    def __mutate(self):
        return self.__mutate_indiv(sample(self.__pop, 1)[0])

    def __mutate_indiv(self, indiv):
        new_ind = []
        # points_to_mute = sample(list(range(NB_TOTAL_POINTS)),
        #                         randint(MIN_MUTE_POINT, NB_TOTAL_POINTS))
        points_to_mute = []
        # choose best point to mute
        for cur_point in list(range(NB_TOTAL_POINTS)):
            x, y, _ = indiv[cur_point]
            if cur_point == 0:
                xp, yp, tp = indiv[-1]
                prev_point = len(indiv)
            else:
                xp, yp, tp = indiv[cur_point - 1]
                prev_point = cur_point - 1
            if cur_point == len(indiv) - 1:
                xn, yn, tn = indiv[0]
                next_point = 0
            else:
                xn, yn, tn = indiv[cur_point + 1]
                next_point = cur_point + 1
            angle_cur_point = abs(getAngleBetweenPoints(xp, yp, x, y, xn, yn))
            if angle_cur_point < ACCEPTABLE_ANGLE:
                if cur_point not in points_to_mute:
                    points_to_mute.append(cur_point)
                if prev_point not in points_to_mute:
                    points_to_mute.append(prev_point)
                if next_point not in points_to_mute:
                    points_to_mute.append(next_point)

        if len(points_to_mute) == 0:
            return None

        for i, p in enumerate(indiv):
            if i in points_to_mute:
                if i % (NB_POINT_BETWEEN_WP + 1) == 0:
                    prev_point = None
                    if i > 0:
                        prev_point = [new_ind[i - 1][0], new_ind[i - 1][1]]
                    new_ind.append(
                            self.__getRandomPointOnWP(prev_point,
                                                      int(i / (NB_POINT_BETWEEN_WP + 1))))
                else:
                    new_x, new_y, new_thrust = self.__mutate_push(indiv, i)
                    new_ind.append([new_x, new_y, new_thrust])
            else:
                new_ind.append([p[0], p[1], p[2]])
        return new_ind

    def __mutate_push(self, indiv, point_index):
        p = indiv[point_index]
        # Push near next waypoint in opposite from next wp + 1
        # push nexr current waypoint in opposite from previous wp
        cur_wp = (int(point_index / (NB_POINT_BETWEEN_WP + 1)))
        if point_index % NB_POINT_BETWEEN_WP > NB_POINT_BETWEEN_WP / 2:
            push_wp = (cur_wp + 2) % len(WP_INFO)
        else:
            if cur_wp == 0:
                push_wp = len(WP_INFO) - 1
            else:
                push_wp = cur_wp - 1
        push_wp_x, push_wp_y = WP_INFO[push_wp]
        if p[0] == push_wp_x:
            a = 0
        else:
            a = (p[1] - push_wp_y) / (p[0] - push_wp_x)
        b = push_wp_y - a * push_wp_x

        # x_dist = push_wp_x - p[0]
        # coef = MIN_COEF_PUSH_FROM_WP + random() * (MAX_COEF_PUSH_FROM_WP - MIN_COEF_PUSH_FROM_WP)
        #
        # nb_point_to_closest_wp = point_index % int((NB_POINT_BETWEEN_WP / 2))
        # nb_point_to_wp_coef = 1 + (nb_point_to_closest_wp / (NB_POINT_BETWEEN_WP / 2))
        # if random() < 0.55:
        #     new_x = int(p[0] - x_dist * coef * nb_point_to_wp_coef)
        # else:
        #     new_x = int(p[0] + x_dist * coef * nb_point_to_wp_coef)
        # new_y = int(a * new_x + b)
        if point_index != 0:
            xp, yp, _ = indiv[point_index - 1]
        else:
            xp, yp, _ = indiv[-1]
        if point_index > 1:
            xp2, yp2, _ = indiv[point_index - 2]
        else:
            xp2, yp2, _ = indiv[-(point_index+1)]
        if point_index < len(indiv) - 1:
            xn, yn, _ = indiv[point_index + 1]
        else:
            xn, yn, _ = indiv[0]

        cur_angle = getAngleBetweenPoints(xp2, yp2, xp, yp, p[0], p[1])
        new_angle = cur_angle + CUR_ACCEPTABLE_DELTA_ANGLE
        a2 = 0
        abs_new_angle = new_angle - abs(getAngleBetweenPoints(xp2, yp2, xp, yp, xp2, yp))
        if yp < yp2 < p[1]:
            abs_new_angle = new_angle + abs(getAngleBetweenPoints(xp2, yp2, xp, yp, xp2, yp))
        if xp2 < xp:
            abs_new_angle = 180 - abs_new_angle
        if abs_new_angle != 90:
            a2 = tan(abs_new_angle)
        b2 = xp - a2 * yp
        new_x = (b - b2) / (a2 - a)
        new_y = a*new_x + b
        print(point_index, abs_new_angle)
        print(p[0], p[1])
        print(new_x, new_y)
        angle = getAngleBetweenPoints(xp, yp, new_x, new_y, xn, yn)
        estimated_t = int(RATIO_ANGLE_THRUST[0] * angle + RATIO_ANGLE_THRUST[1])
        new_thrust = randint(estimated_t - MUTATION_THRUST,
                             estimated_t + MUTATION_THRUST)
        new_thrust = max(0, min(100, new_thrust))
        return new_x, new_y, new_thrust

    # =======================
    def __random_indiv(self):
        indiv = []
        next_wp = 0
        for i in range(NB_TOTAL_POINTS):
            if i % (NB_POINT_BETWEEN_WP + 1) == 0:
                prev_point = None
                if i > 0:
                    prev_point = [indiv[i - 1][0], indiv[i - 1][1]]
                indiv.append(self.__getRandomPointOnWP(prev_point, next_wp))
                next_wp += 1
                if next_wp == NB_WP:
                    next_wp = 0
            else:
                prev_point = [indiv[-1][0], indiv[-1][1]]
                indiv.append(self.__getPointOnNextWPLine(prev_point, next_wp))
        return indiv

    # =============================================
    def __getRandomPointOnWP(self, prev_point, wp):
        wp_x, wp_y = WP_INFO[wp]
        x = randint(wp_x - WP_RAYON / 2, wp_x + WP_RAYON / 2)
        y = randint(wp_y - WP_RAYON / 2, wp_y + WP_RAYON / 2)
        while sqrt((x - wp_x) ** 2 + (y - wp_y) ** 2) > WP_RAYON:
            x = randint(wp_x - WP_RAYON / 2, wp_x + WP_RAYON / 2)
            y = randint(wp_y - WP_RAYON / 2, wp_y + WP_RAYON / 2)
        new_thrust = 100
        if prev_point is not None:
            x1, y1 = prev_point
            if wp < len(WP_INFO) - 1:
                x2, y2 = WP_INFO[wp + 1]
            else:
                x2, y2 = WP_INFO[0]
            angle = getAngleBetweenPoints(x1, y1, x, y, x2, y2)
            estimated_t = int(RATIO_ANGLE_THRUST[0] * angle + RATIO_ANGLE_THRUST[1])
            new_thrust = randint(estimated_t - MUTATION_THRUST, estimated_t + MUTATION_THRUST)
            new_thrust = max(0, min(100, new_thrust))
        return [x, y, new_thrust]

    # ====================================================
    def __getPointOnNextWPLine(self, prev_point, next_wp):
        x1, y1 = prev_point
        x2, y2 = WP_INFO[next_wp]
        if x1 == x2:
            a = 0
        else:
            a = (y1 - y2) / (x1 - x2)
        b = y2 - a * x2
        if abs(x1 - x2) < X_DIFF_FOR_Y_BASE:
            base_compute = "y"
            if y1 < y2:
                min_y = y1 + MEAN_Y_BETWEEN_POINTS[next_wp] / 2
                max_y = y1 + MEAN_Y_BETWEEN_POINTS[next_wp] * 1.5
            else:
                min_y = y1 - MEAN_Y_BETWEEN_POINTS[next_wp] * 1.5
                max_y = y1 - MEAN_Y_BETWEEN_POINTS[next_wp] / 2
        else:
            base_compute = "x"
            if x1 < x2:
                min_x = x1 + MEAN_X_BETWEEN_POINTS[next_wp] / 2
                max_x = x1 + MEAN_X_BETWEEN_POINTS[next_wp] * 1.5
            else:
                min_x = x1 - MEAN_X_BETWEEN_POINTS[next_wp] * 1.5
                max_x = x1 - MEAN_X_BETWEEN_POINTS[next_wp] / 2
        x = x2
        y = y2
        nb_try = 0
        while nb_try < MAX_NEW_DIFF_POINT_SEARCH_TRY and \
                ((x == x2 and y == y2) or (x == x1 and y == y1)):
            nb_try += 1
            if base_compute == "x":
                x = randint(int(min_x), int(max_x))
                y = int(a * x + b)
            else:
                y = randint(int(min_y), int(max_y))
                if a == 0:
                    x = (y - b)
                else:
                    x = int((y - b) / a)
        angle = getAngleBetweenPoints(x1, y1, x, y, x2, y2)
        estimated_t = int(RATIO_ANGLE_THRUST[0] * angle + RATIO_ANGLE_THRUST[1])
        new_thrust = randint(estimated_t - MUTATION_THRUST, estimated_t + MUTATION_THRUST)
        new_thrust = max(0, min(100, new_thrust))
        return [x, y, new_thrust]


# =================================================================
# =                              POD                              =
# =================================================================

class Pod:
    # ==============================
    def __init__(self, podId, mode):
        self.__id = podId
        self.__lastShiledTurn = -1
        self.__mode = mode
        self.__cur_target_point = 1

    # ===================================
    def getOptimisedOrder(self, podsInfo):
        if self.__mode == "race":
            orders = self.__getRaceOrders(podsInfo)
        if self.__mode == "battle":
            orders = self.__getBattleOrders(podsInfo)
        return orders

    # ======================================
    def __checkSkippedPoints(self, x, y, a):
        i = self.__cur_target_point
        closest = None
        done = False
        while not done:
            if i == len(POINTS):
                i = 0
            if i % (NB_POINT_BETWEEN_WP + 1) == 0:
                done = True
            if closest is None:
                closest = i
            else:
                xc, yc, _ = POINTS[closest]
                c_dist = sqrt((x - xc) ** 2 + (y - yc) ** 2)
                xi, yi, _ = POINTS[i]
                i_dist = sqrt((x - xi) ** 2 + (y - yi) ** 2)
                if c_dist > i_dist:
                    closest = i
            i += 1

        nb_to_skip = closest - self.__cur_target_point
        if closest % (NB_POINT_BETWEEN_WP + 1) != 0:
            cx, cy, _ = POINTS[closest]
            next_i = closest + 1
            if next_i == len(POINTS):
                next_i = 0
            nx, ny, _ = POINTS[next_i]
            angle = getAngleBetweenPoints(cx, cy, x, y, nx, ny)
            if angle > ANGLE_TO_SKIP:
                nb_to_skip += 1
        return nb_to_skip

    # ==================================
    def __getRaceOrders(self, podsInfo):
        x, y, vx, vy, a, wp = podsInfo[self.__id]
        self.__cur_target_point += (self.__checkSkippedPoints(x, y, a))
        self.__cur_target_point %= len(POINTS)
        targetX, targetY, thrust = POINTS[self.__cur_target_point]
        if abs(x - targetX) <= DELTA_REACHED_POINT and abs(y - targetY) < DELTA_REACHED_POINT:
            self.__cur_target_point += 1
            if self.__cur_target_point >= len(POINTS):
                self.__cur_target_point = 0

        dist = sqrt((x - targetX) ** 2 + (y - targetY) ** 2)
        angle = self.__computeTargetAngle(x, y, targetX, targetY, a, dist)
        b = MAX_THRUST * maxAngle / (maxAngle - minAngle)
        a = -b / maxAngle
        angle2 = None
        dist_to_turn = None
        one_turn = False
        cur_p1 = self.__cur_target_point
        cur_p2 = (self.__cur_target_point + 1) % len(POINTS)
        while angle2 is None or angle2 < ANGLE_INFL_THRUST_IN_DIST:
            x1, y1, _ = POINTS[cur_p1]
            x2, y2, _ = POINTS[cur_p2]
            angle2 = getAngleBetweenPoints(x, y, x1, y1, x2, y2)
            cur_p1 = (cur_p1 + 1) % len(POINTS)
            cur_p2 = (cur_p2 + 1) % len(POINTS)
            if cur_p1 == 0:
                one_turn = True
            dist_to_turn = sqrt((x - x1) ** 2 + (y - y1) ** 2)
        # printerr(angle, dist_to_turn, angle2)
        if abs(angle) < ANGLE_FOR_PRE_TURN and dist_to_turn < NEXT_POINT_INFL_DIST:
            # angle = angle2
            if one_turn:
                p = cur_p1 + len(POINTS)
            else:
                p = cur_p1
            diff = p - self.__cur_target_point
            new_target_p = (cur_p1 + int(diff / 2)) % len(POINTS)
            targetX, targetY, _ = POINTS[new_target_p]
        thrust = max(MIN_THRUST, min(MAX_THRUST, abs(int(a * angle + b))))
        thrust = self.__checkCollision(podsInfo, thrust)
        return targetX, targetY, thrust

    # ====================================
    def __getBattleOrders(self, podsInfo):
        target = "opp" + str(HEAD_OPP_POD)
        targetX, targetY, targetWp = self.__computeTrajectory(podsInfo, target)

        x, y, vx, vy, a, wp = podsInfo[self.__id]
        tDist = sqrt((x - targetX) ** 2 + (y - targetY) ** 2)
        if a == -1:
            targetAngle = 0
        else:
            targetAngle = self.__computeTargetAngle(x, y, targetX, targetY, a, tDist)
        b = MAX_THRUST * maxAngle / (maxAngle - minAngle)
        a = -b / maxAngle
        thrust = int(a * targetAngle + b)
        thrust = max(MIN_THRUST, min(MAX_THRUST, thrust))
        if targetAngle < boostAndReduceAngle:
            targetDist = sqrt((targetX - x) ** 2 + (targetY - y) ** 2)
            if targetDist > boostDist:
                thrust = "BOOST"
        thrust = self.__checkCollision(podsInfo, thrust)
        return targetX, targetY, thrust

    # ===========================================
    def __checkCollision(self, podsInfo, thrust):
        x, y, vx, vy, a, wp = podsInfo[self.__id]
        x1, y1, vx1, vy1, a1, _ = podsInfo[2]
        x2, y2, vx2, vy2, a2, _ = podsInfo[3]
        nx1 = x1 + vx1
        nx2 = x2 + vx2
        ny1 = y1 + vy1
        ny2 = y2 + vy2
        nx = x + vx
        ny = y + vy
        t1Dist = sqrt((nx - nx1) ** 2 + (ny - ny1) ** 2)
        t2Dist = sqrt((nx - nx2) ** 2 + (ny - ny2) ** 2)
        if self.__mode == "battle":
            collideDist = COLLIDE_DIST_BATTLE
        else:
            collideDist = COLLIDE_DIST_RACE
        if t1Dist < collideDist or t2Dist < collideDist:
            if self.__mode == "battle" or (
                    self.__mode == "race" and CUR_TURN > self.__lastShiledTurn + RACE_NO_TURN_SHIELD):
                thrust = "SHIELD"
                self.__lastShiledTurn = CUR_TURN
        return thrust

    # ==============================================
    def __computeTrajectory(self, podsInfo, target):
        x, y, vx, vy, a, wp = podsInfo[self.__id]
        # "target" is "opp1" or "opp2"
        oppId = eval(target.replace("opp", "")) + 1
        oppx, oppy, oppvx, oppvy, oppa, oppwp = podsInfo[oppId]
        oppDist = sqrt((oppx - x) ** 2 + (oppy - y) ** 2)
        if abs(oppa - a) > 90:
            coef = 1
            if oppvx != 0:
                coef = BATTLE_AHEAD_COEF * oppDist / oppvx
            targetX = int(oppx + coef * oppvx)
            targetY = int(oppy + coef * oppvy)
            wp = False
        else:
            wpx, wpy = WP_INFO[(oppwp + 1) % NB_WP]
            targetX = wpx - vx
            targetY = wpy - vy
            wp = True
        return targetX, targetY, wp

    # =====================================================
    def __computeTargetAngle(self, x, y, tx, ty, a, tDist):
        vtx = tx - x
        vty = ty - y
        nvtx = vtx / tDist
        nvty = vty / tDist
        m = tan(radians(360 - a))
        relativeDiry = 10
        if a < 180:
            relativeDiry = -10
        if m == 0:
            relativeDirx = 10
        else:
            relativeDirx = relativeDiry / m
        dirx = int(x + relativeDirx)
        diry = int(y - relativeDiry)
        vdirx = dirx - x
        vdiry = diry - y
        vDirDist = sqrt(vdirx ** 2 + vdiry ** 2)
        nvdirx = vdirx / vDirDist
        nvdiry = vdiry / vDirDist
        tAngle = degrees(acos(nvtx * nvdirx + nvty * nvdiry))
        return tAngle

# ==================================
def display_traj(fit, p_list):
    PLOT_WIDGET.clear()
    PLOT_WIDGET.setTitle(fit)
    s = pg.ScatterPlotItem(pxMode=False)
    spots = []
    for cp in WP_INFO:
        spots.append({'pos': (cp[0], 9000-cp[1]),
                      'size': 600})
                      #'pen': fn.mkPen({'color': 'w', 'width': 2}),
                      #'symbol': "o"})
    s.addPoints(spots)
    PLOT_WIDGET.addItem(s)
    PLOT_WIDGET.setRange(xRange=[0, 16000], yRange=[0, 9000])

    all_x = []
    all_y = []
    for p in p_list:
        all_x.append(p[0])
        all_y.append(9000-p[1])
    PLOT_WIDGET.plot(all_x, all_y, symbol="x")
    QApplication.processEvents()

# =================================================================
# =                           START                               =
# =================================================================
if __name__ == "__main__":
    PLOT_WIDGET.show()
    # Get "perfect" path
    POINTS = []
    ga = GA(POP_SIZE)
    ga.run()
    # POINTS, fit = ga.get_best_traj()
    #
    # printerr(fit, POINTS)
    # all_x = []
    # all_y = []
    # i = 0
    # while i < len(POINTS):
    #     ax, ay, _ = POINTS[i]
    #     #bx, by, _ = POINTS[(i + 1) % len(POINTS)]
    #     #cx, cy, _ = POINTS[(i + 2) % len(POINTS)]
    #     #printerr(getAngleBetweenPoints(ax, ay, bx, by, cx, cy))
    #     all_x.append(ax)
    #     all_y.append(ay)
    #     i += 1
    #
    # cp_x = []
    # cp_y = []
    # for cp in WP_INFO:
    #     cp_x.append(cp[0])
    #     cp_y.append(cp[1])
    #
    # from pyqtgraph import functions as fn
    #
    # p_list, fits = ga.get_pop()
    # best_5 = []
    # fit_5 = []
    # for i, f in enumerate(fits):
    #     if len(fit_5) < 5:
    #         fit_5.append(f)
    #         best_5.append(p_list[i])
    #     else:
    #         done = False
    #         for j, f2 in enumerate(fit_5):
    #             if f2 < f and not done:
    #                 fit_5[j] = f
    #                 best_5[j] = p_list[i]
    #                 done = True
    #
    # print(fit_5)
    #
    # for i, p_list in enumerate(best_5):
    #     fit = fit_5[i]
    #     display_traj(fit, p_list)

    # for i, p_list in enumerate(best_5):
    #     fit = fit_5[i]
    #     w_cp = view.addPlot()
    #
    #     s = pg.ScatterPlotItem(pxMode=False)
    #     spots = []
    #     for cp in WP_INFO:
    #         spots.append({'pos': (cp[0], 9000-cp[1]),
    #                       'size': 600})
    #                       #'pen': fn.mkPen({'color': 'w', 'width': 2}),
    #                       #'symbol': "o"})
    #     s.addPoints(spots)
    #     w_cp.addItem(s)
    #     w_cp.setRange(xRange=[0, 16000], yRange=[0, 9000])
    #
    #     all_x = []
    #     all_y = []
    #     for p in p_list:
    #         all_x.append(p[0])
    #         all_y.append(9000-p[1])
    #     w_cp.plot(all_x, all_y, symbol="x")

    # app.exec_()

    # # game loop
    # cho = Pod(0, "race")
    # gall = Pod(1, "battle")
    # next_point = None
    # while True:
    #     st = time()
    #     podsInfo = []
    #     for i in range(4):
    #         podsInfo.append([int(info) for info in input().split()])
    #     # Update opponent info
    #     ho = HEAD_OPP_POD
    #     oo = 3 - ho
    #     if podsInfo[2][5] == 0 and OPP_PREV_WP[0] != 0:
    #         OPP_TURN[0] += 1
    #     if podsInfo[3][5] == 0 and OPP_PREV_WP[1] != 0:
    #         OPP_TURN[1] += 1
    #     if OPP_TURN[oo - 1] > OPP_TURN[ho - 1]:
    #         HEAD_OPP_POD = oo
    #     elif OPP_TURN[0] == OPP_TURN[1]:
    #         if podsInfo[ho + 1][5] < podsInfo[oo + 1][5]:
    #             HEAD_OPP_POD = oo
    #         elif podsInfo[ho + 1][5] == podsInfo[oo + 1][5]:
    #             hoWpDist = getWpDist(podsInfo, ho + 1)
    #             ooWpDist = getWpDist(podsInfo, oo + 1)
    #             if ooWpDist < hoWpDist:
    #                 HEAD_OPP_POD = oo
    #     OPP_PREV_WP = [podsInfo[2][5], podsInfo[3][5]]
    #
    #     # Compute target point/thrust
    #     x1, y1, t1 = cho.getOptimisedOrder(podsInfo)
    #     x2, y2, t2 = gall.getOptimisedOrder(podsInfo)
    #
    #     CUR_TURN += 1
    #
    #     # printerr("turn time", time() - st)
    #
    #     # Estimate next point
    #     # x, y, vx, vy, a, wp = podsInfo[0]
    #     # next_point = getNextPoint(x, y, vx, vy, a, x1, y1, t1)
    #
    #     print(x1, y1, t1)
    #     print(x2, y2, t2)

#         # LOG OF PREVIOUS CODES BELOW
#         """
#         # Write an action using print
#         # To debug: print("Debug messages...", file=sys.stderr)
#
#         # You have to output the target position
#         # followed by the power (0 <= thrust <= 100)
#         # i.e.: "x y thrust"
#         #thrust = 100
#         maxDist = 2000
#         minDist = 0
#         minSpeed = 10
#         maxSpeed = 100
#         maxAngle = 110 # 90 -> 10 / 100 -> 10 / 110 -> 5
#         minAngle = 20
#         deltaMax = 900 # 1200 -> 5
#         boostDist = 4500
#         boostAndReduceAngle = 10
#         collideDist = 815
#         nbNoShieldTurn = 3
#         angle = abs(next_checkpoint_angle)
#         # linéaire
#         b = maxSpeed * maxAngle / (maxAngle - minAngle)
#         a = -b/maxAngle
#         thrust = int(a*angle + b)
#         # log
#         #a = 1 / (minAngle - maxAngle)
#         #b = -a*maxAngle
#         #thrust = int((1+log(max(0.000001, a*angle+b)))*100)
#         thrust = max(minSpeed, min(maxSpeed, thrust))
#         newPointx = next_checkpoint_x + Vx
#         newPointy = next_checkpoint_y + Vy
#         delta_x = min(deltaMax, abs(next_checkpoint_x-x))
#         delta_y = min(deltaMax, abs(next_checkpoint_y-y))
#         opponent_dist = sqrt((opponent_y - y)**2 + (opponent_x - x)**2)
#         if opponent_dist < 2*collideDist:
#             if x < next_checkpoint_x and opponent_x > x:
#                 newPointx += delta_x
#             elif x > next_checkpoint_x and opponent_x < x:
#                 newPointx -= delta_x
#             if y < next_checkpoint_y and opponent_y > y:
#                 newPointy += delta_y
#             elif y > next_checkpoint_y and opponent_y < y:
#                 newPointy -= delta_y
#         if angle < boostAndReduceAngle:
#             if next_checkpoint_dist > boostDist:
#                 thrust = "BOOST"
#             if next_checkpoint_dist < maxDist:
#                 a = (maxSpeed - minSpeed) / (2 * (maxDist - minDist))
#                 b = minSpeed - a*minDist
#                 thrust = min(maxSpeed, max(minSpeed, int(a*next_checkpoint_dist + b)))
#                 print("Ralenti", thrust, file=stderr)
#         if opponent_dist < collideDist and turn > 5 and shiledLastTurn < turn - nbNoShieldTurn:
#             thrust = "SHIELD"
#             shieldLastTurn = turn
#         turn += 1
#         """
#
# """
# # Calcul des équations des droites perpendiculaire divisants les segments en n points
# EQU_PER_POINT = []
# for iWp, wp_info in enumerate(WP_INFO):
#     next_wp = iWp+1
#     if next_wp == len(WP_INFO):
#         next_wp = 0
#     x1, y1 = wp_info
#     x2, y2 = WP_INFO[next_wp]
#     a = (y2 - y1) / (x2 - x1)
#     b = y1 - a * x1
#     a1 = -1/a
#     x_diff = abs(x2 - x1)
#     EQU_PER_POINT.append([x1, x2]) # WP
#     for ip in range(NB_POINT_BETWEEN_WP):
#         x = x1 + x_diff*ip
#         if x2 < x1:
#             x = x1 - x_diff*ip
#         y = a*x + b
#         b1 = y - a1*x
#         EQU_PER_POINT.append([a1, b1])
# """
#
# """
# ANGLE_LIST = []
# for a in range(18, 90):
#     ANGLE_LIST.append(a)
#     ANGLE_LIST.append(-a)
#
# def compute_traj(cur_point, cur_angle, prev_wp, next_wp, change_angle=False):
#     if cur_point < NB_TOTAL_POINTS:
#         ok = True
#         if cur_point % NB_POINT_BETWEEN_WP == 0:
#             POINTS.append(WP_INFO[next_wp])
#             # Calculer l'angle et revenir en arriere si ça passe pas
#             prev_wp += 1
#             next_wp += 1
#             if next_wp == NB_WP:
#                 next_wp = 0
#             if prev_wp == NB_WP:
#                 prev_wp = 0
#         else:
#             if len(POINTS) > 2:
#                 x_prev = POINTS[cur_point - 1][0]
#                 y_prev = POINTS[cur_point - 1][1]
#                 x_prev2 = POINTS[cur_point - 2][0]
#                 y_prev2 = POINTS[cur_point - 2][1]
#                 a = (y_prev2 - y_prev) / (x_prev2 - x_prev)
#                 b = y_prev - a*x_prev
#             else:
#                 x_prev, y_prev = WP_INFO[prev_wp]
#                 x_next, y_next = WP_INFO[next_wp]
#                 a = (y_next - y_prev) / (x_next - x_prev)
#                 b = y_prev - a * x_prev
#
#             a0 = (tan(cur_angle) - a) / (1 - a*tan(cur_angle))
#             b0 = y_prev - a0*x_prev
#             a_perp, b_perp = EQU_PER_POINT[cur_point]
#
#             x = (b_perp - b0) / (a0 - a_perp)
#             y = a0 * x + b0
#             POINTS.append([int(x), int(y)])
#         if ok:
#             compute_traj(cur_point+1, -cur_angle, prev_wp, next_wp)
#
# cur_angle = 0
# while len(POINTS) < NB_TOTAL_POINTS:
#     compute_traj(0, ANGLE_LIST[cur_angle], 0, 1)
#     cur_angle += 1
#     print(POINTS, file=stderr)
# """
#
# """
# POD GET_RACE_ORDER:
# wpx, wpy = wpInfo[wp]
# targetX = wpx
# targetY = wpy
#
# wpDist = sqrt((x - wpx)**2 + (y - wpy)**2)
# wpAngle = self.__computeTargetAngle(x, y, wpx, wpy, a, wpDist) if a != -1 else 0
#
# alpha = atan((wpy - y)/(wpx - x))
# dy = int(WP_RAYON * sin(alpha))
# dx = int(WP_RAYON * cos(alpha))
# if x < wpx:
#     targetX = int(targetX - WP_DIST_COEF*dx)
# elif x > wpx:
#     targetX = int(targetX + WP_DIST_COEF*dx)
# if y < wpy:
#     targetY = int(targetY - WP_DIST_COEF*dy)
# elif y > wpy:
#     targetY = int(targetY + WP_DIST_COEF*dy)
#
# b = maxSpeed * maxAngle / (maxAngle - minAngle)
# a = -b/maxAngle
# thrust = int(a*wpAngle + b)
# if wpAngle < boostAndReduceAngle:
#     if wpDist > boostDist:
#         thrust = "BOOST"
#     if wpDist < maxDist:
#         a = (maxSpeed - minSpeed) / (2 * (maxDist - minDist))
#         b = minSpeed - a*minDist
#         thrust = int(a*wpDist + b)
# if thrust != "BOOST":
#     thrust = max(minSpeed, min(maxSpeed, thrust))
# thrust = self.__checkCollision(podsInfo, thrust)
# """
#
# """
# POD COMPUTE_TARGET_ANGLE
# vdirx = 1000 * cos(radians(a))
# vdiry = 1000 * sin(radians(a))
# dirDist = sqrt(vdirx**2 + vdiry**2)
# vect_pod_direction_x = vdirx / dirDist
# vect_pod_direction_y = vdiry / dirDist
# scalar_product = int((nvtx * vect_pod_direction_x) + (nvty * vect_pod_direction_y))
# tAngle = degrees(acos(scalar_product))
# """