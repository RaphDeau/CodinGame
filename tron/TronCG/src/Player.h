#ifndef PLAYER_H
#define PLAYER_H

#include <string>
using namespace std;

class Player
{
 public:
  Player();
  virtual ~Player();

  inline void SetPos(int px, int py){this->px_=px; this->py_=py;}

  inline void SetInitPos(int x, int y){this->ipx_ = x; this->ipy_ = y;}

  inline int GetX(){return this->px_;}
  inline int GetY(){return this->py_;}

  inline int GetInitX() {return this->ipx_;}
  inline int GetInitY() {return this->ipy_;}

  void ComputeNewPos(string direction);
  
  virtual string GetDirection(int **map, int **players_info, int **players_pos, int my_id) = 0;

 private:
  
  int px_, py_, ipx_, ipy_;
};

#endif // PLAYER_H
