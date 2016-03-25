from .message_media import MediaMessageProtocolEntity
from yowsup.common.tools import WATools
from yowsup.common.tools import MimeTools
import os
from Crypto.Cipher import AES
import urllib2
from axolotl.kdf.hkdfv3 import HKDFv3
from axolotl.util.byteutil import ByteUtil
import binascii
import base64
class DownloadableMediaMessageProtocolEntity(MediaMessageProtocolEntity):
    '''
    <message t="{{TIME_STAMP}}" from="{{CONTACT_JID}}" 
        offline="{{OFFLINE}}" type="text" id="{{MESSAGE_ID}}" notify="{{NOTIFY_NAME}}">
        <media type="{{DOWNLOADABLE_MEDIA_TYPE: (image | audio | video)}}"
            mimetype="{{MIME_TYPE}}" 
            filehash="{{FILE_HASH}}"
            url="{{DOWNLOAD_URL}}" 
            ip="{{IP}}"
            size="{{MEDIA SIZE}}"
            file="{{FILENAME}}" 

            > {{THUMBNAIL_RAWDATA (JPEG?)}}
        </media>
    </message>
    '''
    def __init__(self, mediaType,
            mimeType, fileHash, url, ip, size, fileName, 
            _id = None, _from = None, to = None, notify = None, timestamp = None, 
            participant = None, preview = None, offline = None, retry = None, refkey = None):

        super(DownloadableMediaMessageProtocolEntity, self).__init__(mediaType, _id, _from, to, notify, timestamp, participant, preview, offline, retry)
        self.setDownloadableMediaProps(mimeType, fileHash, url, ip, size, fileName, refkey)

    def __str__(self):
        out  = super(DownloadableMediaMessageProtocolEntity, self).__str__()
        out += "MimeType: %s\n" % self.mimeType
        out += "File Hash: %s\n" % self.fileHash
        out += "URL: %s\n" % self.url
        out += "IP: %s\n" % self.ip
        out += "File Size: %s\n" % self.size
        out += "File name: %s\n" % self.fileName
        out += "File %s encrypted\n" % "is" if self.refkey else "is NOT"
        return out

    def decrypt(self, encimg, refkey):
        derivative = HKDFv3().deriveSecrets(refkey, binascii.unhexlify('576861747341707020496d616765204b657973'), 112)
        parts = ByteUtil.split(derivative, 16, 32)
        iv = parts[0]
        cipherKey = parts[1]
        e_img = encimg[:-10]
        AES.key_size=128
        cr_obj = AES.new(key=cipherKey,mode=AES.MODE_CBC,IV=iv)
        return cr_obj.decrypt(e_img)

    def getMediaContent(self):
        data = urllib2.urlopen(self.url).read()
        if self.refkey:
            data = self.decrypt(data, self.refkey)
        return bytearray(data)

    def getMediaSize(self):
        return self.size

    def getMediaUrl(self):
        return self.url

    def getMimeType(self):
        return self.mimeType

    def setDownloadableMediaProps(self, mimeType, fileHash, url, ip, size, fileName, refkey):
        self.mimeType   = mimeType
        self.fileHash   = fileHash
        self.url        = url
        self.ip         = ip
        self.size       = int(size)
        self.fileName   = fileName
        self.refkey     = refkey

    def toProtocolTreeNode(self):
        node = super(DownloadableMediaMessageProtocolEntity, self).toProtocolTreeNode()
        mediaNode = node.getChild("media")
        mediaNode.setAttribute("mimetype",  self.mimeType)
        mediaNode.setAttribute("filehash",  self.fileHash)
        mediaNode.setAttribute("url",       self.url)
        if self.ip:
            mediaNode.setAttribute("ip",        self.ip)
        mediaNode.setAttribute("size",      str(self.size))
        mediaNode.setAttribute("file",      self.fileName)

        return node

    @staticmethod
    def fromProtocolTreeNode(node):
        entity = MediaMessageProtocolEntity.fromProtocolTreeNode(node)
        entity.__class__ = DownloadableMediaMessageProtocolEntity
        mediaNode = node.getChild("media")
        entity.setDownloadableMediaProps(
            mediaNode.getAttributeValue("mimetype"),
            mediaNode.getAttributeValue("filehash"),
            mediaNode.getAttributeValue("url"),
            mediaNode.getAttributeValue("ip"),
            mediaNode.getAttributeValue("size"),
            mediaNode.getAttributeValue("file"),
            base64.b64decode(mediaNode.getAttributeValue("refkey")) if mediaNode.getAttributeValue("refkey") else None
            )
        #f=open('/tmp/my2.jpg','wb')
        #f.write(entity.getMediaContent())
        #f.close()
        return entity

    @staticmethod
    def fromFilePath(fpath, url, mediaType, ip, to, mimeType = None, preview = None, filehash = None, filesize = None):
        mimeType = mimeType or MimeTools.getMIME(fpath)
        filehash = filehash or WATools.getFileHashForUpload(fpath)
        size = filesize or os.path.getsize(fpath)
        fileName = os.path.basename(fpath)

        return DownloadableMediaMessageProtocolEntity(mediaType, mimeType, filehash, url, ip, size, fileName, to = to, preview = preview)


