#! /usr/bin/env bash

# newest versions of docker includes compose, if compose
# is included in docker, we don't need to check for docker-compose
doesDockerIncludeCompose=0

check () {
  # check if docker is installed
  if ! docker > /dev/null 2>&1 ; then
    echo -e "[ Error ] docker not found, aborting"
    exit 127
  fi

  # check if compose already is in docker executable
  if docker compose > /dev/null 2>&1 ; then
    doesDockerIncludeCompose=1
  fi

  # if compose is in the docker executable, we don't need to check for docker-compose
  # otherwise check that docker-compose is installed
  if [[ doesDockerIncludeCompose -eq 0 ]] && ! docker-compose > /dev/null 2>&1 ; then
    echo -e "[ Error ] docker-compose not found, aborting"
    exit 127
  fi

  if ! pidof dockerd > /dev/null; then
    echo -e "[ Error ] docker demon is not running, aborting"
    exit 127
  fi
}

printmenu() {
  echo -e "1) Create monitorapa-base image from Dockerfile-base"
  echo -e "2) Create monitor-base image from Dockerfile"
  echo -e "0) Quit"
}

mainloop () {
  while [[ 0 ]]; do
    read -n1 -p ": "
    echo
    case $REPLY in  
      1)
        docker build -t monitorapa-base -f Dockerfile-base . 
        break
      ;; 

      2)
        docker build -t monitor-base -f Dockerfile . 
        break
      ;;

      0) exit 0 ;;
    esac
  done
}

main () {
  echo
  check
  printmenu
  mainloop

  # implements a ternary operator
  [[ doesDockerIncludeCompose -eq 1 ]] && \
    docker compose up -d --build && docker attach monitorapa \
  || \
    docker-compose up -d --build && docker attach monitorapa
  exit 0
}

main