#!/usr/bin/env python
#
# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.
#

from __future__ import print_function, unicode_literals
import optparse
import os
import time
import socket
from proton import Message
from proton.handlers import MessagingHandler
from proton.reactor import Container

class Send(MessagingHandler):
    def __init__(self, url, messages, total, payload):
        super(Send, self).__init__()
        self.url = url
        self.sent = 0
        self.confirmed = 0
        self.burst_sent = 0
        self.burst_count = int(messages)
        self.total = int(total)
        self.payload = payload
        self.hostname = socket.gethostname()


    def on_start(self, event):
        event.container.create_sender(self.url)

    def on_sendable(self, event):
        self.burst_sent = 0

        if self.sent >= self.total:
            print("-------- Send Complete! --------")
            event.connection.close()
            return

        while event.sender.credit and self.burst_sent < self.burst_count:
            bdy = {'sequence':(self.sent+1),'hostname':str(self.hostname), 'payload':str(payload)}
            print(f"Sending Message: {bdy}")

            msg = Message(id=(self.sent+1), body=bdy)
            event.sender.send(msg)
            self.sent += 1
            self.burst_sent += 1
        time.sleep(.5)


    def on_accepted(self, event):
        self.confirmed += 1
        
        print(f"Message accepted: {self.confirmed} total: {self.total}")
        if self.confirmed >= self.total:
            print("-------- All messages confirmed! --------")
            event.connection.close()

    def on_settled(self, event):
        #print("Settled")
        pass

    def on_session_error(self, event):
        print("Session Error")

    def on_rejected(self, event):
        print("Rejected")

    def on_disconnected(self, event):
        print("Disconnected")
        #self.sent = self.confirmed

parser = optparse.OptionParser(usage="usage: %prog [options]",
                               description="Send messages to the supplied address.")
parser.add_option("-a", "--address", help="address to which messages are sent (default %default)")
parser.add_option("-m", "--messages", type="int", default=10, help="number of messages to send at a time (default %default)")
parser.add_option("-t", "--total", type="int", default=100, help="Total Number of messages to send")
parser.add_option("-p", "--payload", type="string", default="", help="Payload string")

opts, args = parser.parse_args()

if __name__ == "__main__":

    # Create the Address
    addr = "localhost:5672/examples" # Default value
    if opts.address:
        addr = opts.address
    elif ("AMQP_BROKER" in os.environ and "AMQP_ADDRESS" in os.environ):
        addr = "{0}:5672/{1}".format(os.environ["AMQP_BROKER"], os.environ["AMQP_ADDRESS"])
    else:
        print("Warning: Using Default address")

    msgs = os.environ.get("MESSAGE_COUNT", default=opts.messages)
    total = os.environ.get("MESSAGE_TOTAL", default=opts.total)
    payload = os.environ.get("MESSAGE_PAYLOAD", default=opts.payload)

    try:
        Container(Send(addr, msgs, total, payload)).run()
        print("Sends complete sleeping!")
        while True:
            time.sleep(5)
    except KeyboardInterrupt: pass
