#ifndef MAP_H
#define MAP_H

#include "Player.h"

class Map
{
 public:
  Map(int width, int heigth);
  ~Map();
  
  void Display();
  
  void InitPlayers(int nb_players, Player **p);
  void DeletePlayer(int player_id);

  int ApplyPlayerPos(int player_id, int px, int py);
  
 private:
  
  int height_;
  int width_;
  int **squares_;
};

#endif