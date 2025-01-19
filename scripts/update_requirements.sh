#! /bin/bash -e
pants pip-compile
pants generate-lockfiles
pants venv
