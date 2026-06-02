rm -rf /tmp/gitops-artifact-root
mkdir -p /tmp/gitops-artifact-root

rsync -a \
  --exclude='.git' \
  --exclude='.github' \
  --exclude='.gitlab' \
  --exclude='node_modules' \
  --exclude='.venv' \
  --exclude='dist' \
  --exclude='build' \
  --exclude='.dvc' \
  --exclude='.pants.d' \
  --exclude='src' \
  --exclude='3rdparty' \
  --exclude='build-support' \
  clusters infrastructure apps \
  /tmp/gitops-artifact-root/
  