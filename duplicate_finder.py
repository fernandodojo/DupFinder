import hashlib
from os import walk, stat
from os.path import join, getsize
from send2trash import send2trash
import json
from file import File


class DuplicateFinder:
    dict_by_size = {}
    dict_by_hash = {}
    log = {'unique_files_by_size_log': {"Qtd": 0, 'Files': []},
           'unique_files_by_hash_log': {"Qtd": 0, 'Files': []},
           'duplicates_log': {"Qtd": 0, 'Files': []},
           'empty_folders_log': {"Qtd": 0, 'Files': []}}

    def __init__(self, directory):
        self._hash_algorithm = hashlib.sha512()
        self._directory = directory

    @property
    def directory(self):
        return self._directory

    @directory.setter
    def directory(self, value):
        self._directory = value

    @property
    def hash_algorithm(self):
        return self._hash_algorithm

    @hash_algorithm.setter
    def hash_algorithm(self, value):
        self._hash_algorithm = value

    def get_hash(self, file_path):
        self._hash_algorithm = hashlib.sha512()
        with open(file_path, "rb") as f:
            file = f.read()
            self._hash_algorithm.update(file)
        return self._hash_algorithm.hexdigest()

    def find_duplicate_by_size(self):
        total = []
        for path, dirs, files in walk(self._directory):
            for file in files:
                try:
                    file_name = file
                    file_path = path
                    file_full_path = join(path, file)
                    file_size = getsize(file_full_path)
                    file_time = stat(file_full_path).st_mtime
                    file_obj = File(file_name, file_path, file_full_path, file_size, file_time)
                    total.append(file_obj)
                    if file_size not in self.dict_by_size:
                        self.dict_by_size[file_size] = [file_obj]
                    else:
                        self.dict_by_size[file_size].append(file_obj)
                except Exception as e:
                    print(e)

        unique_file_per_size = []
        for i in self.dict_by_size:
            if len(self.dict_by_size[i]) < 2:
                unique_file_per_size.append(i)
        for i in unique_file_per_size:
            self.log['unique_files_by_size_log']['Files'].append(str(self.dict_by_size[i]))
            del (self.dict_by_size[i])

        self.log['unique_files_by_size_log']['Qtd'] = len(unique_file_per_size)
        print("Qtd. Unique File Size:{}".format(len(unique_file_per_size)))
        print("Qtd. Size Dict:{}".format(len(self.dict_by_size)))

    def find_duplicate_by_full_hash(self):
        for key, obj_list in self.dict_by_size.items():
            for obj in obj_list:
                hash_id = self.get_hash(obj.full_path)
                obj.hash_id = hash_id
                if hash_id not in self.dict_by_hash:
                    self.dict_by_hash[hash_id] = [obj]
                else:
                    self.dict_by_hash[hash_id].append(obj)

        unique_file_per_hash = []
        for i in self.dict_by_hash:
            if len(self.dict_by_hash[i]) < 2:
                unique_file_per_hash.append(i)
        for i in unique_file_per_hash:
            self.log['unique_files_by_hash_log']['Files'].append(str(self.dict_by_hash[i]))
            del (self.dict_by_hash[i])

        self.log['unique_files_by_hash_log']['Qtd'] = len(unique_file_per_hash)
        print("Qtd. Unique File Hash:{}".format(len(unique_file_per_hash)))
        print("Qtd. Hash Dict:{}".format(len(self.dict_by_hash)))

    def send_duplicate_to_trash(self):
        duplicates = []
        for key, obj_list in self.dict_by_hash.items():
            original = obj_list[0]
            for obj in obj_list:
                if len(obj.name) < len(original.name):
                    original = obj
            obj_list.remove(original)
            for obj in obj_list:
                duplicates.append(obj.full_path)
                self.log['duplicates_log']['Files'].append(str(obj))

        self.log['duplicates_log']['Qtd'] = len(duplicates)
        print("Qtd. Duplicates:{}".format(len(duplicates)))

        for i in duplicates:
            try:
                send2trash(i)
            except Exception as e:
                print(e)
                continue

    def remove_empty_folder(self):
        empty_folders = []
        for path, dirs, files in walk(self._directory):
            if not dirs and not files:
                empty_folders.append(path)
                self.log['empty_folders_log']['Files'].append(path)
        self.log['empty_folders_log']['Qtd'] = len(empty_folders)
        for i in empty_folders:
            send2trash(i)

    def export_log(self):
        out_file = open("log.json", "w")
        json.dump(self.log, out_file, indent=6)
        out_file.close()
