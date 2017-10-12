#ifndef BRONZE_CG_PLAYER_H
#define BRONZE_CG_PLAYER_H

#include "Player.h"

class Bronze_CG_Player : public Player
{
 public:
  Bronze_CG_Player(int map_width, int map_height);
  virtual ~Bronze_CG_Player();

  string GetDirection(int **map, int **players_info, int **players_pos, int my_id);
  
 private:
  string AvoidDeath(int X1, int Y1, string current_order, int **map);
  int FindMostSpace(int X1, int Y1, string current_order, int **map, int prevision_turn, string &order);
  int GetNbAccessibleSquares(int **map, int X1, int Y1);
  
  int MAP_WIDTH;
  int MAP_HEIGHT;
  
};

#endif // PLAYER_H
