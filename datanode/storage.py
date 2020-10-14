import rpyc
import uuid
import sys
import signal
import os
import requests

from rpyc.utils.server import ThreadedServer

DATA_DIR="storage/"
def get_ip():
  response = requests.get('http://ipinfo.io').text
  l = response.find("ip")+6
  r = response.find(",")-1
  return response[l:r]

master_ip, master_port = "3.138.52.215", 2131
def int_handler(signal, frame):
  global master_ip, master_port
  con = rpyc.connect(master_ip,master_port,config={"allow_all_attrs": True})
  master = con.root.Master()  
  ip,port = get_ip(), 8888
  master.disconnect_storage(ip,port)
  print("Storage {}:{} disconnected".format(ip,port))
  sys.exit(0)

class StorageService(rpyc.Service):
  class exposed_storage():

    def exposed_init(self):
      if os.listdir(DATA_DIR):
        os.system("rm -r " + DATA_DIR + "*")

    def exposed_put(self,block_uuid,data,storages):
      with open(DATA_DIR+str(block_uuid),'w') as f:
        f.write(data)

    def exposed_get(self,block_uuid):
      block_addr=DATA_DIR+str(block_uuid)
      if not os.path.isfile(block_addr):
        return None
      with open(block_addr) as f:
        return f.read()   
        
    def exposed_rmv(self,block_uuid):
      block_addr=DATA_DIR+str(block_uuid)
      if not os.path.isfile(block_addr):
        return
      os.remove(block_addr)


def main():
  ip,port = get_ip(),8888
  con = rpyc.connect(master_ip,master_port,config={"allow_all_attrs": True})
  master = con.root.Master()   
  master.connect_storage(ip,port)
  print("Storage {}:{} connected".format(ip,port))

  signal.signal(signal.SIGINT,int_handler)
  if not os.path.isdir(DATA_DIR): 
    os.mkdir(DATA_DIR)
  t = ThreadedServer(StorageService, port = 8888)
  t.start()

if __name__ == "__main__":
  main()