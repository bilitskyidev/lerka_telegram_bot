import dropbox
import os
import datetime

TOKEN_DROPBOX = os.environ.get("TOKEN_DROPBOX")


class TransferData:
    def __init__(self, file=None):
        self.dbx = dropbox.Dropbox(TOKEN_DROPBOX)
        self.file = file
        self.file_size = os.path.getsize(self.file) if self.file else None
        self.count = 0
        self.CHUNK_SIZE = 4 * (1024 ** 2)

    def upload_file(self):
        with open(self.file, 'rb') as f:
            if self.file_size <= 100 * (1024 ** 2):
                self.dbx.files_upload(f.read(), f'/{datetime.datetime.now().strftime("%Y_%m_%d")}/{self.file}')
            else:
                upload_session_start_result = self.dbx.files_upload_session_start(
                    f.read(self.CHUNK_SIZE))
                cursor = dropbox.files.UploadSessionCursor(session_id=upload_session_start_result.session_id,
                                                           offset=f.tell())
                commit = dropbox.files.CommitInfo(path=f'/{datetime.datetime.now().strftime("%Y_%m_%d")}/{self.file}')

                while f.tell() < self.file_size:
                    if (self.file_size - f.tell()) <= self.CHUNK_SIZE:
                        print(self.dbx.files_upload_session_finish(
                            f.read(self.CHUNK_SIZE), cursor, commit)
                        )
                    else:
                        self.dbx.files_upload_session_append_v2(
                            f.read(self.CHUNK_SIZE), cursor)
                        cursor.offset = f.tell()

    def check_dir_data(self, dir_name):
        if dir_name in [i.name for i in self.dbx.files_list_folder('').entries]:
            return f"{dir_name} exists"
        return f"{dir_name} not exists"

    def path_file(self):
        link = self.dbx.sharing_create_shared_link(f'/{datetime.datetime.now().strftime("%Y_%m_%d")}/{self.file}')
        return link.url
