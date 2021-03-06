/*
 * Licensed to the Apache Software Foundation (ASF) under one
 * or more contributor license agreements.  See the NOTICE file
 * distributed with this work for additional information
 * regarding copyright ownership.  The ASF licenses this file
 * to you under the Apache License, Version 2.0 (the
 * "License"); you may not use this file except in compliance
 * with the License.  You may obtain a copy of the License at
 *
 *   http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing,
 * software distributed under the License is distributed on an
 * "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
 * KIND, either express or implied.  See the License for the
 * specific language governing permissions and limitations
 * under the License.
 */

package org.apache.qpid.systests.jms_1_1.extensions.queue;

import static org.junit.Assert.assertFalse;
import static org.junit.Assert.assertTrue;

import java.util.Collections;

import javax.jms.Connection;
import javax.jms.Session;
import javax.jms.TemporaryQueue;

import org.junit.Test;

import org.apache.qpid.server.virtualhost.QueueManagingVirtualHost;
import org.apache.qpid.systests.JmsTestBase;

public class TemporaryQueuePrefixTest extends JmsTestBase
{

    @Test
    public void testNoPrefixSet() throws Exception
    {
        Connection connection = getConnection();
        try
        {
            Session session = connection.createSession(false, Session.AUTO_ACKNOWLEDGE);
            TemporaryQueue queue = session.createTemporaryQueue();

            assertTrue(queue.getQueueName() + " does not start with \"TempQueue\".",
                       queue.getQueueName().startsWith("TempQueue"));
        }
        finally
        {
            connection.close();
        }
    }

    @Test
    public void testEmptyPrefix() throws Exception
    {
        updateGlobalAddressDomains("[]");

        Connection connection = getConnection();
        try
        {
            Session session = connection.createSession(false, Session.AUTO_ACKNOWLEDGE);
            TemporaryQueue queue = session.createTemporaryQueue();

            assertTrue(queue.getQueueName() + " does not start with \"TempQueue\".",
                       queue.getQueueName().startsWith("TempQueue"));
        }
        finally
        {
            connection.close();
        }
    }

    @Test
    public void testTwoDomains() throws Exception
    {
        final String primaryPrefix = "/testPrefix";
        updateGlobalAddressDomains("[\"" + primaryPrefix + "\", \"/foo\" ]");

        Connection connection = getConnection();
        try
        {
            Session session = connection.createSession(false, Session.AUTO_ACKNOWLEDGE);
            TemporaryQueue queue = session.createTemporaryQueue();

            assertFalse(queue.getQueueName() + " has superfluous slash in prefix.",
                        queue.getQueueName().startsWith(("[\"" + primaryPrefix + "\", \"/foo\" ]") + "/"));
            assertTrue(queue.getQueueName() + " does not start with expected prefix \"" + primaryPrefix + "\".",
                       queue.getQueueName().startsWith(primaryPrefix));
        }
        finally
        {
            connection.close();
        }
    }

    @Test
    public void testPrefix() throws Exception
    {
        String prefix = "/testPrefix";
        updateGlobalAddressDomains("[ \"" + prefix + "\" ]");

        Connection connection = getConnection();
        try
        {
            Session session = connection.createSession(false, Session.AUTO_ACKNOWLEDGE);
            TemporaryQueue queue = session.createTemporaryQueue();

            assertTrue(queue.getQueueName() + " does not start with expected prefix \"" + prefix + "/\".",
                       queue.getQueueName().startsWith(prefix + "/"));
        }
        finally
        {
            connection.close();
        }
    }

    private void updateGlobalAddressDomains(String globalDomains) throws Exception
    {
        updateEntityUsingAmqpManagement(getVirtualHostName(),
                                        "org.apache.qpid.VirtualHost",
                                        Collections.singletonMap(QueueManagingVirtualHost.GLOBAL_ADDRESS_DOMAINS,
                                                                 globalDomains));
    }
}
