#!/bin/sh

if [ $# -eq 0 ]; then
  echo "No script specified. Running default script."
  exec python /app/ami-client.py
else
  case $1 in
    *.sh)
      if [ -f "$1" ]; then
        echo "Run bash script $1"
        sh $1
      else
        echo "Script $1 not found"
        exit 1
      fi
      ;;
    *.py)
      if [ -f "$1" ]; then
        echo "Run python script $1"
        exec python $1
      else
        echo "Script $1 not found"
        exit 1
      fi
      ;;
    *)
      echo "No valid script specified. Running default script with args."
      exec python /app/ami-client.py $@
      ;;
  esac
fi
