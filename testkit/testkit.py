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

import time, string, traceback
from brokertest import *
from qpid.messaging import *


try:
    import java.lang.System
    _cp = java.lang.System.getProperty("java.class.path"); 
except ImportError: 
    _cp = checkenv("QP_CP")

class Formatter:

  def __init__(self, message):
    self.message = message
    self.environ = {"M": self.message,
                    "P": self.message.properties,
                    "C": self.message.content}

  def __getitem__(self, st):
    return eval(st, self.environ)

# The base test case has support for launching the generic
# receiver and sender through the TestLauncher with all the options.
# 
class JavaClientTest(BrokerTest):
    """Base Case for Java Test cases"""

    client_class = "org.apache.qpid.testkit.TestLauncher" 

    # currently there is no transparent reconnection.
    # temp hack: just creating the queue here and closing it.
    def start_error_watcher(self,broker=None):
        ssn = broker.connect().session()
        err_watcher = ssn.receiver("control; {create:always}", capacity=1)
        ssn.close()  

    def client(self,**options):
        cmd =  ["java","-cp",_cp] 

        cmd += ["-Dtest_name=" + options.get("test_name", "UNKNOWN")]
        cmd += ["-Dhost=" + options.get("host","127.0.0.1")]
        cmd += ["-Dport=" + str(options.get("port",5672))]
        cmd += ["-Dcon_count=" + str(options.get("con_count",1))]
        cmd += ["-Dssn_per_con=" + str(options.get("ssn_per_con",1))]        
        cmd += ["-Duse_unique_dests=" + str(options.get("use_unique_dests",False))]
        cmd += ["-Dcheck_for_dups=" + str(options.get("check_for_dups",True))]
        cmd += ["-Ddurable=" + str(options.get("durable",False))]
        cmd += ["-Dtransacted=" + str(options.get("transacted",False))]
        cmd += ["-Dreceiver=" + str(options.get("receiver",False))]
        cmd += ["-Dsync_rcv=" + str(options.get("sync_rcv",False))]
        cmd += ["-Dsender=" + str(options.get("sender",False))]
        cmd += ["-Dmsg_size=" + str(options.get("msg_size",256))]
        cmd += ["-Dtx_size=" + str(options.get("tx_size",10))]
        cmd += ["-Dmsg_count=" + str(options.get("msg_count",10))]
        cmd += ["-Dsleep_time=" + str(options.get("sleep_time",1000))]
        cmd += ["-Dfailover=" + options.get("failover", "failover_exchange")]
        cmd += ["-Djms_durable_sub=" + str(options.get("jms_durable_sub", False))]  
        cmd += ["-Dlog.level=" + options.get("log.level", "warn")]  
        cmd += [self.client_class]
        cmd += [options.get("address", "my_queue; {create: always}")] 

        #print str(options.get("port",5672))  
        return cmd

    # currently there is no transparent reconnection.
    # temp hack: just creating a receiver and closing session soon after.
    def monitor_clients(self,broker=None,run_time=600,error_ck_freq=60):
        ssn = broker.connect().session()
        err_watcher = ssn.receiver("control; {create:always}", capacity=1)
        i = run_time/error_ck_freq
        for j in range(i):    
            not_empty = True
            while not_empty:            
                try:   
                    m = err_watcher.fetch(timeout=error_ck_freq)
                    ssn.acknowledge()
                    print "Java process notified of an error"
                    self.check_for_error(m) 
                except messaging.Empty, e: 
                    not_empty = False              
                    
        ssn.close()

    def check_for_error(self,msg):
        print msg.properties.get("exception-trace")

    def verify(self, receiver,sender):
        sender_running = receiver.is_running()
        receiver_running = sender.is_running()

        self.assertTrue(receiver_running,"Receiver has exited prematually")
        self.assertTrue(sender_running,"Sender has exited prematually")


class ConcurrencyTest(JavaClientTest):
    """A concurrency test suite for the JMS client"""

    def test_multiplexing_con(self):
        """Tests multiple sessions on a single connection""" 

        cluster = Cluster(self, 2)
        p = cluster[0].port()
     
        self.start_error_watcher(broker=cluster[0])

        receiver = self.popen(self.client(receiver=True,
                                          ssn_per_con=25,
                                          port=p,
                                          address="amq.topic", 
                                          use_unique_dests=True,
                                          test_name=self.id()),
                              expect=EXPECT_RUNNING) 

        sender = self.popen(self.client(sender=True,
                                        ssn_per_con=25,
                                        port=p,
                                        address="amq.topic", 
                                        use_unique_dests=True,
                                        test_name=self.id()),
                              expect=EXPECT_RUNNING) 

        self.monitor_clients(broker=cluster[0],run_time=180)
        self.verify(receiver,sender)


    def test_multiplexing_con_tx(self):
        """Tests multiple transacted sessions on a single connection""" 

        cluster = Cluster(self,2)
        ssn = cluster[0].connect().session()
        p = cluster[0].port()
     
        self.start_error_watcher(broker=cluster[0])

        receiver = self.popen(self.client(receiver=True,
                                          ssn_per_con=25,
                                          port=p,
                                          transacted=True,
                                          address="amq.topic",
                                          use_unique_dests=True,  
                                          test_name=self.id()),
                              expect=EXPECT_RUNNING) 

        sender = self.popen(self.client(sender=True,
                                        ssn_per_con=25,
                                        port=p,
                                        transacted=True,
                                        address="amq.topic",
                                        use_unique_dests=True, 
                                        test_name=self.id()),
                              expect=EXPECT_RUNNING) 

        self.monitor_clients(broker=cluster[0],run_time=60)
        ssn.close(); 
        self.verify(receiver,sender)

class SoakTest(JavaClientTest):
    """A soak test suite for the JMS client"""

    def test_failover(self):
        cluster = self.cluster(4, expect=EXPECT_EXIT_FAIL)
        p = cluster[0].port()
        self.start_error_watcher(broker=cluster[0])
        receiver = self.popen(self.client(receiver=True,
                                          ssn_per_con=1,
                                          port=p,
                                          test_name=self.id()),
                              expect=EXPECT_RUNNING) 

        sender = self.popen(self.client(sender=True,
                                        ssn_per_con=1,
                                        port=p,
                                        test_name=self.id()),
                              expect=EXPECT_RUNNING) 
      
        # grace period for java clients to get the failover properly setup.
        time.sleep(30) 
        error_msg= None
        # Kill original brokers, start new ones.
        try:
            for i in range(8):
                cluster[i].kill()
                b=cluster.start()
                self.monitor_clients(broker=b,run_time=30,error_ck_freq=30)
                print "iteration : " + str(i)
        except ConnectError, e1:
            error_msg = "Unable to connect to new cluster node : " + traceback.format_exc(e1)

        except SessionError, e2:
            error_msg = "Session error while connected to new cluster node : " + traceback.format_exc(e2)

        self.verify(receiver,sender)
        if error_msg:      
            raise Exception(error_msg)            
     
    def test_failover_with_durablesub(self):
        cluster = self.cluster(4, expect=EXPECT_EXIT_FAIL)
        p = cluster[0].port()
        self.start_error_watcher(broker=cluster[0])
        receiver = self.popen(self.client(receiver=True,
                                          ssn_per_con=1,
                                          port=p,
                                          jms_durable_sub=True,
                                          test_name=self.id()),
                              expect=EXPECT_RUNNING) 

        sender = self.popen(self.client(sender=True,
                                        ssn_per_con=1,
                                        port=p,
                                        test_name=self.id()),
                              expect=EXPECT_RUNNING) 
      
        # grace period for java clients to get the failover properly setup.
        time.sleep(30) 
        error_msg=None
        # Kill original brokers, start new ones.
        try:
            for i in range(8):
                cluster[i].kill()
                b=cluster.start()
                self.monitor_clients(broker=b,run_time=30,error_ck_freq=30)
        except ConnectError, e1:
            error_msg = "Unable to connect to new cluster node : " + traceback.format_exc(e1)

        except SessionError, e2:
            error_msg = "Session error while connected to new cluster node : " + traceback.format_exc(e2)

        self.verify(receiver,sender)
        if error_msg:      
            raise Exception(error_msg)            
