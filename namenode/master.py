import rpyc
import uuid
import threading 
import math
import random
import signal
import pickle
import sys
import os
from collections import defaultdict

DATA_DIR="storage"
from rpyc.utils.server import ThreadedServer

def int_handler(signal, frame):
  file = open('fs.img','wb')
  pickle.dump(MasterService.exposed_Master.file_table, file)
  pickle.dump(MasterService.exposed_Master.tree, file)
  pickle.dump(MasterService.exposed_Master.metadata, file)
  pickle.dump(MasterService.exposed_Master.block_size, file)
  pickle.dump(MasterService.exposed_Master.replication_factor, file)
  pickle.dump(MasterService.exposed_Master.marked, file)
  pickle.dump(MasterService.exposed_Master.storages, file)
  file.close()
  sys.exit(0)

def load():
  if os.path.isfile('fs.img'):
    file = open('fs.img','rb')
    MasterService.exposed_Master.file_table = pickle.load(file)
    MasterService.exposed_Master.tree = pickle.load(file)
    MasterService.exposed_Master.metadata = pickle.load(file)
    MasterService.exposed_Master.block_size = pickle.load(file)
    MasterService.exposed_Master.replication_factor = pickle.load(file)
    MasterService.exposed_Master.marked = pickle.load(file)
    MasterService.exposed_Master.storages = pickle.load(file)
    file.close()

class MasterService(rpyc.Service):
  class exposed_Master():
    file_table = defaultdict(list)
    tree = defaultdict(list)
    metadata = dict()
    storages = {}
    marked = {}
    block_size = 0
    replication_factor = 0
    def isconnected(self,id):
      return (id in self.__class__.marked) and self.__class__.marked[id] == True
      
    def exposed_connected(self,id):
      return (id in self.__class__.marked) and self.__class__.marked[id] == True

    def exposed_connect_storage(self,host,port):
      print("Hello ",host,port)      
      id=0
      while self.isconnected(id):
        id=id+1
      print("Here is your id",id)
      self.__class__.storages[id] = (host,port)
      self.__class__.marked[id] = True
    
    def exposed_disconnect_storage(self,host,port): 
      print("Bye ",host,port)            
      id=0
      while (self.isconnected(id)&(self.__class__.storages[id] == (host,port)))==False:
        id=id+1
      self.__class__.marked[id] = False

    #DIRECTORY OPERATIONs
    def exposed_init(self,block_size,replication_factor):
      self.__class__.block_size = block_size
      self.__class__.replication_factor = replication_factor
	  
      self.__class__.file_table = defaultdict(list)
      self.__class__.tree = defaultdict(list)
      self.__class__.metadata = dict()
      self.__class__.tree[DATA_DIR].append('$')
      for storage in self.__class__.storages:
        if self.isconnected(storage):
          host,port = self.__class__.storages[storage]
          con = rpyc.connect(host,port=port)
          storage = con.root.storage()
          storage.init()
      return "OK"

    def exposed_mkdir(self,dir):
      dir_name = os.path.basename(dir)
      dir = DATA_DIR + dir
      par = os.path.dirname(dir)
      if(self.dir_exists(par) == False):
        return "Parent directory not exist"
      if(self.dir_exists(dir) == True):
        return "Directory already exist"
      self.__class__.tree[par].append(dir_name)
      self.__class__.tree[dir] = []
      self.__class__.tree[dir].append('$')
      return "OK"

    def exposed_rmdir(self,dir):
      dir_name = os.path.basename(dir)
      dir = DATA_DIR + dir
      par = os.path.dirname(dir)
      if(self.dir_exists(dir) == False):
        return "Directory not exist"
      if(len(self.__class__.tree[dir]) > 1):
        return "Directory not empty"
      self.__class__.tree[par].remove(dir_name)
      self.__class__.tree[dir] = []
      return "OK"

    def exposed_ls(self,dir):
      if(dir!='/'):
        dir = DATA_DIR + dir
      else:
        dir = DATA_DIR
      if(self.dir_exists(dir) == False):
        return "Directory not exist", []
      return "OK", self.__class__.tree[dir][1:]
    #END

    def exposed_write(self,dest,source,size):
      dest = DATA_DIR + dest
      if self.dir_exists(dest[:-1]) == False:
        return "Directory not exist", []
      if self.file_exists(dest+source):
        return "File already exist", []
      self.__class__.tree[dest[:-1]].append(source)
      self.__class__.file_table[dest+source]=[]
      num_blocks = self.numof_blocks(size)
      self.__class__.metadata[dest+source]=[size,num_blocks]
      blocks = self.alloc_blocks(dest+source,num_blocks)
      if(blocks == None):
        return "Storage servers less than replication factor", []
      return "OK", blocks

    def exposed_get_file_table_entry(self,fname):
      fname = DATA_DIR + fname
      if self.file_exists(fname):
        return self.__class__.file_table[fname]
      else:
        return None

    def exposed_get_metadata_entry(self,fname):
      fname = DATA_DIR + fname
      return self.__class__.metadata[fname]

    def exposed_rmv_file_table_entry(self,fname):
      fname = DATA_DIR + fname
      self.__class__.file_table[fname]=[]
      self.__class__.metadata[fname]=[]
      self.__class__.tree[os.path.dirname(fname)].remove(os.path.basename(fname))
    
    def exposed_get_block_size(self):
      return self.__class__.block_size

    def exposed_get_storages(self):
      return self.__class__.storages

    def numof_blocks(self,size):
      return int(math.ceil(float(size)/self.__class__.block_size))

    def file_exists(self,file):
      return (file in self.__class__.file_table)&(len(self.__class__.file_table[file])>0)

    def dir_exists(self,file):
      return len(self.__class__.tree[file]) > 0

    def alloc_blocks(self,dest,num):
      blocks,online = [],[]
      for storage in self.__class__.storages.keys():
        if self.isconnected(storage):
          online.append(storage)
      if(len(online) < self.__class__.replication_factor):
        return None
      for _ in range(num):
        block_uuid = uuid.uuid1()
        nodes_ids = random.sample(online,self.__class__.replication_factor)
        blocks.append((block_uuid,nodes_ids))
        self.__class__.file_table[dest].append((block_uuid,nodes_ids))

      return blocks


if __name__ == "__main__":
  load()
  signal.signal(signal.SIGINT,int_handler)
  t = ThreadedServer(MasterService, port = 2131)
  t.start()