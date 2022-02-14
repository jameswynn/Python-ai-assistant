# MIT License

# Copyright (c) 2019 Georgios Papachristou

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import threading
import queue
import pyaudio
import urllib.request
import urllib.parse

from jarvis.engines.tts import TTSEngine
from jarvis.settings import REMOTE_TTS
class TTSEngineRemote(TTSEngine):
    """
    Text To Speech Engine (TTS)
    """

    def __init__(self):
        super().__init__()
        self.message_queue = queue.Queue(maxsize=9)  # Maxsize is the size of the queue / capacity of messages
        self.stop_speaking = False
        self.audio = pyaudio.PyAudio()
        self.is_playing = False

    def run_engine(self):
        pass

    def assistant_response(self, message, refresh_console=True):
        """
        Assistant response in voice.
        :param refresh_console: boolean
        :param message: string
        """
        self._insert_into_message_queue(message)
        try:
            speech_thread = threading.Thread(target=self._speech_and_console, args=(refresh_console,))
            speech_thread.start()
        except RuntimeError as e:
            self.logger.error('Error in assistant response thread with message {0}'.format(e))

    def _insert_into_message_queue(self, message):
        try:
            self.message_queue.put(message)
        except Exception as e:
            self.logger.error("Unable to insert message to queue with error message: {0}".format(e))

    def _speech_and_console(self, refresh_console):
        """
        Speech method translate text batches to speech and print them in the console.
        :param text: string (e.g 'tell me about google')
        """
        try:
            while not self.message_queue.empty() and self.is_playing == False:
                message = self.message_queue.get()
                if message:
                    self._say(message)
                    self.console_manager.console_output(message, refresh_console=refresh_console)
                    if self.stop_speaking:
                        self.logger.debug('Speech interruption triggered')
                        self.stop_speaking = False
                        break
        except Exception as e:
            self.logger.error("Speech and console error message: {0}".format(e))

    def _say(self, text):
        self.is_playing = True
        text = urllib.parse.quote(text)
        with urllib.request.urlopen('http://{}:{}/speech?text={}'.format(REMOTE_TTS['host'], REMOTE_TTS['port'], text)) as resp:
            stream = self.audio.open(format = pyaudio.paInt16,
                            channels = 1,
                            rate = 22050,
                            output = True)
            while True:
                data = resp.read(4096)
                stream.write(data)
                if not data:
                    break
            stream.close()
        self.is_playing = False

