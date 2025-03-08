#! /bin/bash -e

targets=$(pants --tag=pip-compile list ::)
for target in $targets; do
	pants run $target
done

pants generate-lockfiles
