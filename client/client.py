import rpyc
import sys
import os
import uuid
import logging

logging.basicConfig(level=logging.DEBUG)
LOG = logging.getLogger(__name__)

def write_to_storage(block_uuid,data,storage):
  LOG.info("sending: " + str(block_uuid) + str(storage))
  host,port=storage
  con=rpyc.connect(host,port=port)
  storage = con.root.storage()
  storage.put(block_uuid,data,storage)

def read_from_storage(block_uuid,storage):
  LOG.info("downloading block from: " + str(storage))
  host,port = storage
  con=rpyc.connect(host,port=port)
  storage = con.root.storage()
  return storage.get(block_uuid)

def put(master,source,dest,fname):
  fname = os.path.basename(fname)
  size = os.path.getsize(source)
  code, blocks = master.write(dest,fname,size)
  if(code != "OK"):
    print(code)
    return
  with open(source) as f:
    for block in blocks:
      data = f.read(master.get_block_size())
      block_uuid = block[0]
      for m in [master.get_storages()[_] for _ in block[1] if master.connected(_)]:
        write_to_storage(block_uuid, data, m)

def get(master,fname,dest):
  f = open(dest,"w")
  file_table = master.get_file_table_entry(fname)
  if not file_table:
    LOG.error("File not found")
    return
  for block in file_table:
    for m in [master.get_storages()[_] for _ in block[1] if master.connected(_)]:
      data = read_from_storage(block[0],m)
      if data:
        f.write(data)
        break
    else:
        LOG.error("No blocks found. Possibly a corrupt file")

def info(master,fname):
  file_table = master.get_file_table_entry(fname)
  if not file_table:
    LOG.error("File not found")
    return
  print("File:Size ",master.get_metadata_entry(fname)[0])
  print("File:NumberOfBlocks ",master.get_metadata_entry(fname)[1])

def remove_from_storage(block_uuid,storage):
  host,port = storage
  con=rpyc.connect(host,port=port)
  storage = con.root.storage()
  storage.rmv(block_uuid)

def rmv(master,fname):
  file_table = master.get_file_table_entry(fname)
  if not file_table:
    LOG.error("File not found")
    return
  for block in file_table:
    for m in [master.get_storages()[_] for _ in block[1] if master.connected(_)]:
      remove_from_storage(block[0], m)
  master.rmv_file_table_entry(fname)

def f(fname):
  fname = os.path.dirname(fname)
  if(fname == "/"):
    return fname
  return fname + "/"
  
def cp(master,source,dest):
  tmp = str(uuid.uuid1())
  get(master,source,tmp)
  put(master,tmp,f(dest), dest)
  os.system("rm "+tmp)

def mv(master,source,dest):
  cp(master,source,dest)
  rmv(master,source)

def crt(master,source,dest):
  code, blocks = master.write(dest,source,1)
  if(code != "OK"):
    LOG.error(code)
    return
  for b in blocks:
    block_uuid = b[0]
    storages = [master.get_storages()[_] for _ in b[1]]
    write_to_storage(block_uuid, '\n', storages)

def main(args):
  master_ip, master_port = None, None
  if args[0] == "connect":
    file = open('master.txt','w')
    master_ip, master_port = args[1], int(args[2])
    file.write(str(args[1])+":"+str(args[2]))
    file.close()
    return
  if os.path.isfile('master.txt'):
    file = open('master.txt','r')
    master_ip, master_port = file.read().split(":")
    file.close()
  else:
    print("Not connected to DFS namenode")
    print("Please follow this instruction to connect:")
    print("python3 client.py ip port")
    return
  con=rpyc.connect(master_ip,port=int(master_port),config={"allow_all_attrs": True})
  master=con.root.Master()
  #Directory operations
  if args[0] == "init":
	  #block_size - replication_factor
    code = master.init(int(args[1]),int(args[2]))
    if(code != "OK"):
      LOG.error(code)
  elif args[0] == "mkdir":
    code = master.mkdir(args[1])
    if(code != "OK"):
      LOG.error(code)
  elif args[0] == "rmdir":
    code = master.rmdir(args[1])
    if(code != "OK"):
      LOG.error(code)
  elif args[0] == "ls":
    code,res = master.ls(args[1])
    if(code != "OK"):
      LOG.error(code)
    else:
      print(res)

  #File operations
  elif args[0] == "read":
    get(master,args[1],args[2])
  elif args[0] == "write":
    put(master,args[1],args[2],args[1])
  elif args[0] == "create":
    crt(master,args[1],args[2])
  elif args[0] == "delete":
    rmv(master,args[1])
  elif args[0] == "cp":
    cp(master,args[1],args[2])
  elif args[0] == "mv":
    mv(master,args[1],args[2])
  elif args[0] == "info":
    info(master,args[1])
  else:
    LOG.error("command: not found")


if __name__ == "__main__":
  main(sys.argv[1:])