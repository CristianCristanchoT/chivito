echo "### Docker Compose up"
docker-compose -f Docker/docker-compose.yaml up -d --build
echo "### Changing permissions "
sudo chmod -R go+w Data
sudo chmod -R go+w Models
sudo chmod -R go+w Notebooks
sudo chmod -R go+w Scripts
