# install

```
ssh lazydockup-server

cd ~/docker
git clone https://github.com/Momro/LazyDockUp
cd LazyDockUp
docker compose up -d --build

exit

ssh some-other-server
cd ~/docker
git clone https://github.com/Momro/LazyDockUp
cd LazyDockUp/agent
docker build -t lazydockup-agent .

-> browser -> http://<lazydockup-server>:5000
``` 

# ideas / feature requests

* english
* update text / commit infos
* different icon (shows in browser tab), or different status code (201?) so the update status can be tracked in Kuma
