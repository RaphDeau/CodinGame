#ifndef NN_PLAYER_H
#define NN_PLAYER_H

#include "Player.h"

class NN_Player : public Player
{
 public:
  NN_Player();
  virtual ~NN_Player();

  string GetDirection(int **map, int **players_info, int **players_pos, int my_id);

};

#endif // PLAYER_H
