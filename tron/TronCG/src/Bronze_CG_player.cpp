#include "Bronze_CG_player.h"
#include <iostream>

using namespace std;

Bronze_CG_Player::Bronze_CG_Player(int map_width, int map_height)
{
  this->MAP_HEIGHT = map_height;
  this->MAP_WIDTH = map_width;
}

Bronze_CG_Player::~Bronze_CG_Player()
{}

string Bronze_CG_Player::GetDirection(int **map, int **players_info, int **players_pos, int my_id)
{
  string order = "LEFT";
  this->FindMostSpace(players_info[my_id][2], players_info[my_id][3], order, map, 1, order);
  order = this->AvoidDeath(players_info[my_id][2], players_info[my_id][3], order, map);
  return order;
}

int Bronze_CG_Player::GetNbAccessibleSquares(int **map, int X1, int Y1)
{
  int nb_squares = 0;
  for (int i = 0; i < 4; i++)
  {
    if (i == 0)
    {
      if (X1 > 0 and map[X1-1][Y1] == -1)
      {
        map[X1-1][Y1] = 0;
        nb_squares += 1 + this->GetNbAccessibleSquares(map, X1-1, Y1);
      }
    }
    else if (i == 1)
    {
      if (X1 < this->MAP_WIDTH-1 and map[X1+1][Y1] == -1)
      {
        map[X1+1][Y1] = 0;
        nb_squares += 1 + this->GetNbAccessibleSquares(map, X1+1, Y1);
      }
  }
    else if (i == 2)
    {
      if (Y1 > 0 and map[X1][Y1-1] == -1)
      {
        map[X1][Y1-1] = 0;
        nb_squares += 1 + this->GetNbAccessibleSquares(map, X1, Y1-1);
      }
    }
    else if (i == 3)
    {
      if (Y1 < this->MAP_HEIGHT-1 and map[X1][Y1+1] == -1)
      {
        map[X1][Y1+1] = 0;
        nb_squares += 1 + this->GetNbAccessibleSquares(map, X1, Y1+1);
      }
    }
  }
  return nb_squares;
}

int Bronze_CG_Player::FindMostSpace(int X1, int Y1, string current_order, int **map, int prevision_turn, string &order)
{
    int **cur_map;
    int nb_treated = 0;
    string treated_hash[4] = {"LEFT", "RIGHT", "UP", "DOWN"};
    int nb_squares[4] = {0, 0, 0, 0};
    string order_buffer = "NULL";
    while (nb_treated < 4)
    {
        cur_map = new int *[this->MAP_WIDTH];
        for (int i = 0; i < this->MAP_WIDTH; i++)
        {
            cur_map[i] = new int[this->MAP_HEIGHT];
            for (int j = 0; j < this->MAP_HEIGHT; j++)
            {
                cur_map[i][j] = map[i][j];
                //cerr << "init " << i << " " << j << endl;
            }
        }
        
        if (nb_treated == 0 and X1 > 0 and cur_map[X1-1][Y1] == -1)
        {
            cur_map[X1-1][Y1] = 0;
            if (prevision_turn == 0)
            {
                //clock_t start = clock();
                nb_squares[0] = max(nb_squares[0], this->GetNbAccessibleSquares(cur_map, X1-1, Y1));
                //cerr << "time to compute (left) " << ((clock() - start) / (double) CLOCKS_PER_SEC) * 1000 << endl;
            }
            else
                nb_squares[0] = this->FindMostSpace(X1-1, Y1, current_order, cur_map, prevision_turn-1, order_buffer);
        }
        else if (nb_treated == 1 and X1 < this->MAP_WIDTH-1 and cur_map[X1+1][Y1] == -1)
        {
            cur_map[X1+1][Y1] = 0;
            if (prevision_turn == 0)
                nb_squares[1] = max(nb_squares[1], this->GetNbAccessibleSquares(cur_map, X1+1, Y1));
            else
                nb_squares[1] = this->FindMostSpace(X1+1, Y1, current_order, cur_map, prevision_turn-1, order_buffer);
        }
        else if (nb_treated == 2 and Y1 > 0 and cur_map[X1][Y1-1] == -1)
        {
            cur_map[X1][Y1-1] = 0;
            if (prevision_turn == 0)
                nb_squares[2] = max(nb_squares[2], this->GetNbAccessibleSquares(cur_map, X1, Y1-1));
            else
                nb_squares[2] = this->FindMostSpace(X1, Y1-1, current_order, cur_map, prevision_turn-1, order_buffer);
        }
        else if (nb_treated == 3 and Y1 < this->MAP_HEIGHT-1 and cur_map[X1][Y1+1] == -1)
        {
            cur_map[X1][Y1+1] = 0;
            if (prevision_turn == 0)
                nb_squares[3] = max(nb_squares[3], this->GetNbAccessibleSquares(cur_map, X1, Y1+1));
            else
                nb_squares[3] = this->FindMostSpace(X1, Y1+1, current_order, cur_map, prevision_turn-1, order_buffer);
        }
        nb_treated++;
        for (int i = 0; i < this->MAP_WIDTH; i++)
            delete []cur_map[i];
        delete []cur_map;
    }
    /*
    cerr << "from " << X1 << ", " << Y1 << " - ";
    for (int i = 0; i < 4; i++)
    {
        cerr << nb_squares[i] << " ";
        switch (i)
        {
            case 0: cerr << "(left)" << " "; break;
            case 1: cerr << "(right)" << " "; break;
            case 2: cerr << "(up)" << " "; break;
            case 3: cerr << "(down)" << " "; break;
        }
    }
    cerr << endl;
    */
    string new_order = current_order;
    int current_max = 0;
    if (nb_squares[0] > current_max) {new_order = "LEFT"; current_max = nb_squares[0];}
    if (nb_squares[1] > current_max) {new_order = "RIGHT"; current_max = nb_squares[1];}
    if (nb_squares[2] > current_max) {new_order = "UP"; current_max = nb_squares[2];}
    if (nb_squares[3] > current_max) {new_order = "DOWN"; current_max = nb_squares[3];}
    if (order != "NULL") order = new_order;
    return current_max;
}


string Bronze_CG_Player::AvoidDeath(int X1, int Y1, string current_order, int **map)
{
  string order = current_order;
  if (current_order == "LEFT" and (X1 == 0 or map[X1-1][Y1] != -1))
  {
      order = "UP";
      if (Y1 == 0 or map[X1][Y1-1] == -1)
          order = "DOWN";
  }
  if (current_order == "RIGHT" and (X1 == this->MAP_WIDTH-1 or map[X1+1][Y1] != -1))
  {
      order = "UP";
      if (Y1 == 0 or map[X1][Y1-1] == -1)
          order = "DOWN";
  }
  
  if (current_order == "UP" and (Y1 == 0 or map[X1][Y1-1] != -1))
  {
      order = "LEFT";
      if (X1 == 0 or map[X1-1][Y1] == -1)
          order = "RIGHT";
  }
  
  if (current_order == "DOWN" and (Y1 == this->MAP_HEIGHT-1 or map[X1][Y1+1] != -1))
  {
      order = "LEFT";
      if (X1 == 0 or map[X1-1][Y1] == -1)
          order = "RIGHT";
  }
  return order;
}
