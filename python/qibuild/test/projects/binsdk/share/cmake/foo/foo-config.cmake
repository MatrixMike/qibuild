## Copyright (c) 2012-2016 Aldebaran Robotics. All rights reserved.
## Use of this source code is governed by a BSD-style license that can be
## found in the COPYING file.
set(_root "${CMAKE_CURRENT_LIST_DIR}/../../..")
get_filename_component(_root ${_root} ABSOLUTE)

set(FOO_LIBRARIES
  ${_root}/lib/libfoo.so
  CACHE INTERNAL "" FORCE
)

set(FOO_INCLUDE_DIRS
  ${_root}/include
  CACHE INTERNAL "" FORCE
)

export_lib(FOO)
