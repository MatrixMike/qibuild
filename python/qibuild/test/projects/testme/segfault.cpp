/*
 * Copyright (c) 2012-2015 Aldebaran Robotics. All rights reserved.
 * Use of this source code is governed by a BSD-style license that can be
 * found in the COPYING file.
 */
#include <iostream>
int main()
{
  std::cout << "segfault" << std::endl;
  int* p = 0;
  *p = 42;
}
