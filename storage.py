import rpyc
import uuid
import sys
import socket
import signal
import os

from rpyc.utils.server import ThreadedServer

DATA_DIR="storage/"
master_ip, master_port = None, None
def int_handler(signal, frame):
  global master_ip, master_port
  con = rpyc.connect(master_ip,master_port,config={"allow_all_attrs": True})
  master = con.root.Master()
  hostname = socket.gethostname()     
  ip,port = socket.gethostbyname(hostname), 8888
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
      if len(storages)>0:
        self.forward(block_uuid,data,storages)

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

    def forward(self,block_uuid,data,storages):
      print ("8888: forwarding to:")
      print (block_uuid, storages)
      storage=storages[0]
      storages=storages[1:]
      host,port=storage

      con=rpyc.connect(host,port=port)
      storage = con.root.storage()
      storage.put(block_uuid,data,storages)

def main(args):
  global master_ip, master_port
  master_ip, master_port = args[0], int(args[1])

  hostname = socket.gethostname()  
  ip,port = socket.gethostbyname(hostname),8888
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
  main(sys.argv[1:])