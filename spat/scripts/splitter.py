from spat import seed
from spat.seed.formats import open_iqs, write_iqs_v1, to_IQSv1
import os
from copy import deepcopy
import click


dir_path = os.path.dirname(os.path.realpath(__file__))

def split_iqs_file(src : str, dest : str):
  if src.endswith(".iqs"):
    incoming = open_iqs(src)
    outgoing = to_IQSv1(incoming)
    write_iqs_v1(outgoing, dest)

@click.command()
@click.argument('filename', type=click.Path(exists=True, resolve_path=True))
def split_file(filename):
  split_iqs_file(filename, dir_path + "/test3.iqs")



def split_iqs_files(src_dir, dest_dir=None):
  if dest_dir is None:
    dest_dir = src_dir
  for file in os.listdir(src_dir):
    if file.endswith(".iqs"):
      split_iqs_file(os.path.join(src_dir, file), dest_dir)    


data_dir_new = "/bb2017035_new algorithms/2 µm"
data_dir_old = "/bb2045007_old algorithms/2 µm"

if __name__ == "__main__":
  split_file()

#a = open_iqs(dir_path + data_dir_new + '/2um_100e5-20210203-102759-A94.iqs')
#b = deepcopy(a)
#del b['data']['site1']
#write_iqs(b, os.path.join(dir_path, "site0.iqs"))
split_iqs_file(dir_path + "/2um_100e5-20210203-102759-A94.iqs", dir_path + "/test.iqs")