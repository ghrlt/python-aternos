import lxml.html
from typing import Union, List
from typing import TYPE_CHECKING

from .atfile import AternosFile, FileType
if TYPE_CHECKING:
	from .atserver import AternosServer

class FileManager:

	def __init__(self, atserv:'AternosServer') -> None:

		self.atserv = atserv

	def listdir(self, path:str='') -> List[AternosFile]:

		filesreq = self.atserv.atserver_request(
			f'https://aternos.org/files/{path}', 'GET'
		)
		filestree = lxml.html.fromstring(filesreq.content)
		fileslist = filestree.xpath(
			'//div[@class="files"]' + \
			'/div[@class="directory dropzone"]' + \
			'/div[@class="file clickable"]'
		)

		files = []
		for f in fileslist:

			ftype_raw = f.xpath('/@data-type')
			ftype = FileType.file \
				if ftype_raw == 'file' \
				else FileType.directory

			fsize_raw = f.xpath('/div[@class="filesize"]')
			fsize = 0
			if len(fsize_raw) > 0:

				fsize_text = fsize_raw[0].text.strip()
				fsize_num = fsize_text[:fsize_text.rfind(' ')]
				fsize_msr = fsize_text[fsize_text.rfind(' ')+1:]

				try:
					fsize = self.convert_size(float(fsize_num), fsize_msr)
				except ValueError:
					fsize = -1

			dlbutton = f.xpath('/div[contains(@class,"js-download-file ")]')
			dlallowed = False
			if len(dlbutton) > 0:
				dlallowed = True

			fullpath = f.xpath('/@data-path')
			filepath = fullpath[:fullpath.rfind('/')]
			filename = fullpath[fullpath.rfind('/'):]
			files.append(
				AternosFile(
					self.atserv,
					filepath, filename,
					ftype, fsize, dlallowed
				)
			)

		return files

	def convert_size(self, num:Union[int,float], measure:str) -> float:

		measure_match = {
			'B': 1,
			'kB': 1000,
			'MB': 1000000,
			'GB': 1000000000
		}
		try:
			result = num * measure_match[measure]
		except KeyError:
			result = -1
		return result

	def get_file(self, path:str) -> Union[AternosFile,None]:

		filepath = path[:path.rfind('/')]
		filename = path[path.rfind('/'):]

		filedir = self.listdir(filepath)
		for file in filedir:
			if file.name == filename:
				return file

		return None

	def dl_file(self, path:str) -> bytes:

		file = self.atserv.atserver_request(
			f'https://aternos.org/panel/ajax/files/download.php?' + \
			f'file={path.replace("/","%2F")}',
			'GET'
		)

		return file.content

	def dl_world(self, world:str='world') -> bytes:

		world = self.atserv.atserver_request(
			f'https://aternos.org/panel/ajax/worlds/download.php?' + \
			f'world={world.replace("/","%2F")}',
			'GET'
		)

		return world.content
