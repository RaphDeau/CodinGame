#include "Map.h"

#include <iostream>
#include <stdlib.h>
#include <stdio.h>
#include <time.h>
using namespace std;

Map::Map(int width, int height) : height_(height), width_(width)
{
  srand(time(NULL));
  this->squares_ = new int*[width];
  for (int i = 0; i < width; i++)
  {
    this->squares_[i] = new int[height];
    for (int j = 0; j < height; j++)
      this->squares_[i][j] = 0;
  }
}

Map::~Map()
{
  for (int i = 0; i < this->width_; i++)
    delete [] this->squares_[i];
  delete [] this->squares_;
}

void Map::Display()
{
  for (int j = 0; j < this->height_; j++)
  {
    for (int i = 0; i < this->width_; i++)
    {
      int color = 30 + this->squares_[i][j];
      cout << "\033[1;" << color << "m" << this->squares_[i][j] << " \033[0m";
    }
    cout << endl;
  }
}


void Map::InitPlayers(int nb_players, Player **p)
{
  int nb_players_done = 0;
  while (nb_players_done < nb_players)
  {
    int px = rand() % 30;
    int py = rand() % 20;
    if (this->squares_[px][py] == 0)
    {
      this->squares_[px][py] = nb_players_done+1;
      p[nb_players_done]->SetPos(px, py);
      p[nb_players_done]->SetInitPos(px, py);
      nb_players_done++;
    }
  }
}

int Map::ApplyPlayerPos(int player_id, int px, int py)
{
  if (0 <= px && px < this->width_ and 0 <= py && py < this->height_)
  {
    if (this->squares_[px][py] == 0)
      this->squares_[px][py] = player_id;
    else
    {
      this->DeletePlayer(player_id);
      return 1;
    }
  }
  else
  {
    this->DeletePlayer(player_id);
    return 1;
  }
  return 0;
}

void Map::DeletePlayer(int player_id)
{
  for (int i = 0; i < this->width_; i++)
  {
    for (int j = 0; j < this->height_; j++)
    {
      if (this->squares_[i][j] == player_id)
        this->squares_[i][j] = 0;
    }
  }
}