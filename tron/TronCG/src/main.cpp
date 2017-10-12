
#include "Map.h"
#include "Bronze_CG_player.h"

#include <unistd.h>
#include <iostream>
using namespace std;

void RemovePlayer(int player_id, int **map)
{
  for (int i = 0; i < 30; i++)
  {
    for (int j = 0; j < 20; j++)
    {
      if (map[i][j] == player_id)
        map[i][j] = -1;
    }
  }
}


int main()
{
  Map *m = new Map(30, 20);
  int **map = new int*[30];
  int i, j;
  for (i = 0; i < 30; i++)
  {
    map[i] = new int[20];
    for (j = 0; j < 20; j++)
      map[i][j] = -1;
  }
  
  int nb_players = 2;
  
  Player **players = new Player *[nb_players];
  players[0] = new Bronze_CG_Player(30, 20);
  players[1] = new Bronze_CG_Player(30, 20);
  //for (int i = 0; i < nb_players; i++)
  //  players[i] = new Player();
  
  m->InitPlayers(nb_players, players);
  
  int **players_info;
  int **players_pos;
  players_info = new int*[nb_players];
  players_pos = new int*[nb_players];
  for (i = 0; i < nb_players; i++) 
  {
    int X0 = players[i]->GetInitX(); // starting X coordinate of lightcycle (or -1)
    int Y0 = players[i]->GetInitY(); // starting Y coordinate of lightcycle (or -1)
    int X1 = players[i]->GetX(); // starting X coordinate of lightcycle (can be the same as X0 if you play before this player)
    int Y1 = players[i]->GetY(); // starting Y coordinate of lightcycle (can be the same as Y0 if you play before this player)
    
    //cerr << X0 << " " << Y0 << " " << X1 << " " << Y1 << endl;
    players_info[i] = new int[4];
    players_info[i][0] = X0;
    players_info[i][1] = Y0;
    players_info[i][2] = X1;
    players_info[i][3] = Y1;
    players_pos[i] = new int[2];
    players_pos[i][0] = X1;
    players_pos[i][1] = Y1;
    if (X1 == -1)
      RemovePlayer(i, map);
    else
    {
      map[X0][Y0] = i;
      map[X1][Y1] = i;
    }
  }
  
  m->Display();
  int is_dead = 0;
  int nb_players_alive = nb_players;
  while (nb_players_alive > 1)
  {
    usleep(100000);
    for (int j = 0; j < nb_players; j++)
    {
      if (players[j] != NULL)
      {
        string direction = players[j]->GetDirection(map, players_info, players_pos, j);
        cout << "player " << j+1 << " direction: " << direction << " (" << players[j]->GetX() << ", " << players[j]->GetY() << ")" << endl;
        players[j]->ComputeNewPos(direction);
        is_dead = m->ApplyPlayerPos(j+1, players[j]->GetX(), players[j]->GetY());
        if (is_dead == 1)
        {
          delete players[j];
          players[j] = NULL;
          nb_players_alive--;
        }
        else
        {
          int x = players[j]->GetX();
          int y = players[j]->GetY();
          players_info[j][2] = x;
          players_info[j][3] = y;
          map[x][y] = j;
        }
      }
    }
    cout << "-------------------------" << endl;
    m->Display();
  }
}