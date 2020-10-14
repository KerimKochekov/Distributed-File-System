### User guide

---
# Contribution to the projects

**Kerim Kochekov** namenode implementation, maintained communication between datanodes, client and namenode on AWS and docker configuration

**Temurbek Khujaev** storage side implementation and system testing

**Farhod Khakimiyon** Corrected formats of commands, helped to debug code and populated report with images and testing.

# DFS
Distributed file system like HDFS. It consists of one Master (NameNode) and multiple Storages (DataNode). And a client for interaction. It will dump namespace information(dir_tree and file_tree) when given SIGINT and reload it when fired up next time(fs.img). Replicate data the way HDFS does(random). It will send data to 1st storage and that storage will send it to next one and so on. Reading done in similar manner. Will contact first storage for block, if fails then second and so on.  Uses RPyC library in Python for RPC. 



### Running it:
- Install requirements
* run in namenode server

```
docker pull 33123998/namenode
docker run --rm -i -t -p 2131:2131 33123998/namenode
```
* run in datanode server

```
docker pull 33123998/datanode
docker run --rm -i -t -p 8888:8888 33123998/datanode
``` 
  
### Here avaiable commands with examples:
```sh
1) Initialize the DFS
$ python3 client.py init block_size replication_Factor
Creates storage directory in all storages and clean the dir_tree,metadata,storages and file_Tree in storage

2) Make new directory in DFS
$ python3 client.py mkdir /dir1/dir2
To run this command parent /dir1 should be avaiable and child /dir1/dir2 should not avaible

3) Remove directory in DFS
$ python3 client.py rmdir /dir1/dir2
To run this command /dir1/dir2 should be empty(without any file and dirs)

4) List directory in DFS
$ python3 client.py ls /dir1/dir2
To run this command /dir1/dir2 should be avaiable, so it lists us the files and dirs avaiable in /dir1/dir2

5) Download file from DFS to destination file in local machine(-copytoLocal in HDFS)
$ python3 client.py read /dir1/file1 dest
To run this command /dir1/file1 should be avaiable in DFS

6) Upload file from local machine to DFS(-copyfromLocal in HDFS)
$ python3 client.py write source /dir1/dir2/
To run this command /dir1/dir2/ should be avaiable in DFS 
Do not forget last '/' in the command, so it will upload source file as form /dir1/dir2/source in DFS

7) Create empty file in DFS with one block size
$ python3 client.py create file /dir1/dir2/
To run this command /dir1/dir2/ should be avaiable in DFS 

8) Delete file from DFS
$ python3 client.py delete /dir1/file1
To run this command /dir1/file1 should be avaiable in DFS

9) Copy file from one directory to other directory in DFS
$ python3 client.py cp /dir1/file1 /dir1/dir2/file2
Copies file1 to /dir1/dir2 and saving with name files2
If file2 already exist in /dir1/dir2 then program returns error

10) Copy file from one directory to other directory in DFS
$ python3 client.py mv /dir1/file1 /dir1/dir2/file2
Same as cp command, the only difference is that it deletes file1 from /dir1 after copying to /dir1/dir2

11) Metadata of files in DFS(file size and number of blocks it occupy)
$ python3 client.py info /dir1/file1
To run this command /dir1/file1 should be avaiable in DFS


```
##### Stop it using Ctll + C so that it will end the namespace.
### Architecture Diagramm
![](/res/pic1.png)
### Architecture Diagramm
![](/res/pic2.png)
