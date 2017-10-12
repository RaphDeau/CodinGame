#include "Player.h"

Player::Player()
{}

Player::~Player()
{}

void Player::ComputeNewPos(string direction)
{
  if (direction == "RIGHT")
    this->px_++;
  else if (direction == "LEFT")
    this->px_--;
  else if (direction == "DOWN")
    this->py_++;
  else if (direction == "UP")
    this->py_--;
}