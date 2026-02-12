from Crypto.Signature import PKCS1_PSS
from Crypto.PublicKey import RSA
import Crypto.Hash.SHA256 as SHA256
import base64
import hashlib
import os
import shutil
import logging

DefaultPath = "/etc/pwnagotchi/"


class KeyPair(object):
    def __init__(self, path=DefaultPath, view=None):
        self.path = path
        self.priv_path = os.path.join(path, "id_rsa")
        self.priv_key = None
        self.pub_path = "%s.pub" % self.priv_path
        self.pub_key = None
        self.fingerprint_path = os.path.join(path, "fingerprint")
        self._view = view

        if not os.path.exists(self.path):
            os.makedirs(self.path)

        max_retries = 3
        for attempt in range(max_retries):
            # first time, generate new keys
            if not os.path.exists(self.priv_path) or not os.path.exists(self.pub_path):
                self._view.on_keys_generation()
                logging.info("generating %s ..." % self.priv_path)
                # try pwngrid first, fall back to native Python key generation
                if shutil.which("pwngrid"):
                    ret = os.system("pwngrid -generate -keys '%s'" % self.path)
                    if ret != 0 or not os.path.exists(self.priv_path):
                        logging.warning("pwngrid failed, generating RSA keys with Python ...")
                        self._generate_keys_native()
                else:
                    logging.info("pwngrid not installed, generating RSA keys with Python ...")
                    self._generate_keys_native()

            # load keys: they might be corrupted if the unit has been turned off during the generation, in this case
            # the exception will remove the files and go back at the beginning of this loop.
            try:
                with open(self.priv_path) as fp:
                    self.priv_key = RSA.importKey(fp.read())

                with open(self.pub_path) as fp:
                    self.pub_key = RSA.importKey(fp.read())
                    self.pub_key_pem = self.pub_key.exportKey('PEM').decode("ascii")
                    # python is special
                    if 'RSA PUBLIC KEY' not in self.pub_key_pem:
                        self.pub_key_pem = self.pub_key_pem.replace('PUBLIC KEY', 'RSA PUBLIC KEY')

                pem_ascii = self.pub_key_pem.encode("ascii")

                self.pub_key_pem_b64 = base64.b64encode(pem_ascii).decode("ascii")
                self.fingerprint = hashlib.sha256(pem_ascii).hexdigest()

                with open(self.fingerprint_path, 'w+t') as fp:
                    fp.write(self.fingerprint)

                # no exception, keys loaded correctly.
                self._view.on_starting()
                return

            except Exception as e:
                # if we're here, loading the keys broke something ...
                logging.exception("error loading keys, maybe corrupted, deleting and regenerating (attempt %d/%d) ..." % (attempt + 1, max_retries))
                try:
                    os.remove(self.priv_path)
                except:
                    pass
                try:
                    os.remove(self.pub_path)
                except:
                    pass

        # exhausted retries — generate with Python as last resort
        logging.error("failed to load keys after %d attempts, generating fresh keys with Python ..." % max_retries)
        self._generate_keys_native()
        try:
            with open(self.priv_path) as fp:
                self.priv_key = RSA.importKey(fp.read())
            with open(self.pub_path) as fp:
                self.pub_key = RSA.importKey(fp.read())
                self.pub_key_pem = self.pub_key.exportKey('PEM').decode("ascii")
                if 'RSA PUBLIC KEY' not in self.pub_key_pem:
                    self.pub_key_pem = self.pub_key_pem.replace('PUBLIC KEY', 'RSA PUBLIC KEY')
            pem_ascii = self.pub_key_pem.encode("ascii")
            self.pub_key_pem_b64 = base64.b64encode(pem_ascii).decode("ascii")
            self.fingerprint = hashlib.sha256(pem_ascii).hexdigest()
            with open(self.fingerprint_path, 'w+t') as fp:
                fp.write(self.fingerprint)
            self._view.on_starting()
        except Exception as e:
            logging.exception("fatal: could not generate or load RSA keys")
            raise

    def _generate_keys_native(self):
        """Generate RSA key pair using PyCryptodome when pwngrid is not available."""
        key = RSA.generate(2048)
        with open(self.priv_path, 'wb') as fp:
            fp.write(key.exportKey('PEM'))
        os.chmod(self.priv_path, 0o600)
        with open(self.pub_path, 'wb') as fp:
            fp.write(key.publickey().exportKey('PEM'))
        logging.info("RSA keys generated natively at %s" % self.priv_path)

    def sign(self, message):
        hasher = SHA256.new(message.encode("ascii"))
        signer = PKCS1_PSS.new(self.priv_key, saltLen=16)
        signature = signer.sign(hasher)
        signature_b64 = base64.b64encode(signature).decode("ascii")
        return signature, signature_b64
