from spat import seed
from spat.seed.formats import open_iqs, write_iqs_v1, to_IQSv1
import os
from copy import deepcopy
import click
from typing import Union, List


dir_path = os.path.dirname(os.path.realpath(__file__))

def add_site_to_path(path: str, site: int):
  return click.format_filename(path)+'/site'+str(site)+'.iqs'



def split_iqs_file(sites: List[int], src : str, dest: List[str]):
  """Splits an IQSv2 file"""
  # sites can be a single site or a list ([0, 1])
  # dest can be:
  #   None: put all files in folder containing src
  #   str: put all files in dest directory
  #   List[str]: put files in directories.
  assert(len(sites) == len(dest))

  if src.endswith(".iqs"):
    print(f'Opening .iqs file...')
    incoming = open_iqs(src)  
    for s, d in zip(sites, dest):
      print(f'Extracting site {s}...')
      inc_copy = deepcopy(incoming)
      outgoing = to_IQSv1(inc_copy, s)
      if write_iqs_v1(outgoing, add_site_to_path(d, s)):
        print(f'Site {s} extracted successfully!')
  else:
    print("Please supply a file with the .iqs extension!")

@click.command()
@click.argument('filename', type=click.Path(exists=True, resolve_path=True))
@click.option('--site', type=int)
def split_file(filename, site):
  if site not in (None, 0, 1):
    print("Site must be 0 or 1, if provided.")
    return
  split_iqs_file(site, filename)


# def split_iqs_files(src_dir, dest_dir=None):
#   if dest_dir is None:
#     dest_dir = src_dir
#   for file in os.listdir(src_dir):
#     if file.endswith(".iqs"):
#       split_iqs_file(os.path.join(src_dir, file), dest_dir)    



if __name__ == "__main__":
  split_file()
