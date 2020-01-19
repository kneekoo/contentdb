#!/bin/bash

docker exec -it contentdb_app_1 sh -c "FLASK_CONFIG=../config.cfg FLASK_APP=app/__init__.py python -m pytest app/tests/ --disable-warnings"
