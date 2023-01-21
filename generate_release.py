import os
import shutil
import tarfile
import glob

temp_folder = 'c:\\temp\\frcvision'
temp_lib_folder = temp_folder + '\\python\\lib'
temp_etc_folder = temp_folder + '\\etc'
tar_file_name = temp_folder + '.tar.gz'

if os.path.exists(temp_folder):
    print('removing ', temp_folder)
    shutil.rmtree(temp_folder)
else:
    print(temp_folder, 'doesn\'t exist')

print ('Creating folder', temp_folder)
os.makedirs(temp_folder)

print ('Copying scripts')
for file in glob.glob('pi/scripts/*'):
    print('  ' + file)
    shutil.copy(file, temp_folder)

#print ('Creating python lib folder')
#os.makedirs(temp_lib_folder)

print ('Copying all lib files')
shutil.copytree('pi/python/lib', temp_lib_folder)

print ('Copying etc files')
shutil.copytree('pi/etc', temp_etc_folder)

def set_permissions(tarinfo):
    tarinfo.mode = 0o777
    return tarinfo

def make_tarfile(output_filename, source_dir):
    with tarfile.open(output_filename, "w:gz") as tar:
        for elem in glob.glob('*'):
            print('adding ', elem)
            tar.add(elem, filter=set_permissions)
        
print ('Tarball', temp_folder)
os.chdir(temp_folder)
make_tarfile(tar_file_name, '.')
