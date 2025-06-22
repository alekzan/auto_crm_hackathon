import React, { useState, useEffect, useRef } from 'react';
import { Send, User, Bot, CheckCircle, AlertCircle, ArrowRight, Building, Phone, Mail } from 'lucide-react';
import API_BASE_URL from '../config';

const LeadChat = ({ existingSession, existingMessages, onSessionCreated, onMessagesUpdate }) => {
    const [messages, setMessages] = useState(existingMessages || []);
    const [inputMessage, setInputMessage] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [sessionInfo, setSessionInfo] = useState(existingSession || null);
    const [leadData, setLeadData] = useState(null);
    const [isSessionCreated, setIsSessionCreated] = useState(!!existingSession);
    const messagesEndRef = useRef(null);

    // Initialize lead session on component mount only if no existing session
    useEffect(() => {
        if (existingSession) {
            console.log('🔄 Using existing lead session:', existingSession);
            setSessionInfo(existingSession);
            setIsSessionCreated(true);

            // Add welcome message only if no existing messages
            if (messages.length === 0 && (!existingMessages || existingMessages.length === 0)) {
                const welcomeMessage = {
                    id: Date.now(),
                    sender: 'agent',
                    content: `Welcome back to ${existingSession.business_name}! You're continuing in Stage ${existingSession.current_stage}: ${existingSession.current_stage_name}. How can I assist you today?`,
                    timestamp: new Date().toISOString(),
                    leadData: null
                };
                setMessages([welcomeMessage]);
            }
        } else {
            createLeadSession();
        }
    }, [existingSession]);

    // Update session info when existingSession changes
    useEffect(() => {
        if (existingSession && existingSession !== sessionInfo) {
            setSessionInfo(existingSession);
            setIsSessionCreated(true);
        }
    }, [existingSession]);

    // Update messages when existingMessages prop changes
    useEffect(() => {
        if (existingMessages && existingMessages.length > 0) {
            console.log('🔄 Loading existing messages:', existingMessages.length, 'messages');
            setMessages(existingMessages);
        }
    }, [existingMessages]);

    // Notify parent when messages change
    useEffect(() => {
        if (onMessagesUpdate && messages.length > 0) {
            onMessagesUpdate(messages);
        }
    }, [messages, onMessagesUpdate]);

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    };

    const createLeadSession = async () => {
        try {
            setIsLoading(true);

            const url = `${API_BASE_URL}/lead/create`;
            const response = await fetch(url, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                }
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Failed to create lead session');
            }

            const sessionData = await response.json();
            setSessionInfo(sessionData);
            setIsSessionCreated(true);

            // Notify parent component about session creation
            if (onSessionCreated) {
                onSessionCreated(sessionData);
            }

            // Add welcome message
            setMessages([{
                id: Date.now(),
                sender: 'agent',
                content: `Welcome to ${sessionData.business_name}! How can I assist you today?`,
                timestamp: new Date().toISOString(),
                leadData: null
            }]);

            console.log('✅ Lead session created:', sessionData);

        } catch (error) {
            console.error('❌ Error creating lead session:', error);
            setMessages([{
                id: Date.now(),
                sender: 'system',
                content: `Error: ${error.message}. Please make sure the CRM pipeline is set up first.`,
                timestamp: new Date().toISOString(),
                isError: true
            }]);
        } finally {
            setIsLoading(false);
        }
    };

    const handleSendMessage = async () => {
        if (!inputMessage.trim() || isLoading || !sessionInfo) return;

        const userMessage = {
            id: Date.now(),
            sender: 'user',
            content: inputMessage,
            timestamp: new Date().toISOString()
        };

        setMessages(prev => [...prev, userMessage]);
        setInputMessage('');
        setIsLoading(true);

        try {
            const url = `${API_BASE_URL}/lead/chat`;
            const response = await fetch(url, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    content: inputMessage,
                    session_id: sessionInfo.session_id,
                    timestamp: new Date().toISOString()
                })
            });

            if (!response.ok) {
                throw new Error('Failed to send message');
            }

            const data = await response.json();

            // Check if lead data was updated
            const updatedLeadData = data.pipeline_payload;
            if (updatedLeadData) {
                setLeadData(updatedLeadData);
                console.log('📊 Lead data updated:', updatedLeadData);
            }

            const agentMessage = {
                id: Date.now() + 1,
                sender: 'agent',
                content: data.response,
                timestamp: data.timestamp,
                leadData: updatedLeadData
            };

            setMessages(prev => [...prev, agentMessage]);

        } catch (error) {
            console.error('❌ Error sending message:', error);

            const errorMessage = {
                id: Date.now() + 1,
                sender: 'system',
                content: 'Sorry, there was an error processing your message. Please try again.',
                timestamp: new Date().toISOString(),
                isError: true
            };

            setMessages(prev => [...prev, errorMessage]);
        } finally {
            setIsLoading(false);
        }
    };

    const handleKeyPress = (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSendMessage();
        }
    };

    const formatLeadData = (data) => {
        if (!data) return null;

        const fields = [
            { label: 'Name', value: data.name, icon: User },
            { label: 'Type', value: data.type, icon: User },
            { label: 'Company', value: data.company, icon: Building },
            { label: 'Email', value: data.email, icon: Mail },
            { label: 'Phone', value: data.phone, icon: Phone },
            { label: 'Requirements', value: data.requirements, icon: CheckCircle },
        ].filter(field => field.value);

        return fields;
    };

    if (!isSessionCreated && isLoading) {
        return (
            <div className="flex items-center justify-center h-full bg-gray-50">
                <div className="text-center">
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
                    <h3 className="text-lg font-medium text-gray-900 mb-2">Initializing Lead Session</h3>
                    <p className="text-gray-500">Setting up your personalized experience...</p>
                </div>
            </div>
        );
    }

    return (
        <div className="h-full flex flex-col bg-gray-50">
            {/* Header */}
            <div className="bg-white shadow-sm border-b px-6 py-4">
                <div className="flex items-center justify-between">
                    <div>
                        <h1 className="text-xl font-semibold text-gray-900">
                            {sessionInfo ? `${sessionInfo.business_name} - Lead Chat` : 'Lead Chat'}
                        </h1>
                        <p className="text-sm text-gray-500">
                            {sessionInfo ?
                                `Stage ${sessionInfo.current_stage} of ${sessionInfo.total_stages}: ${sessionInfo.current_stage_name}` :
                                'Connecting...'
                            }
                        </p>
                    </div>

                    {leadData && (
                        <div className="flex items-center space-x-2">
                            <div className="flex items-center text-blue-600 bg-blue-50 px-3 py-2 rounded-lg">
                                <User className="w-4 h-4 mr-2" />
                                <span className="text-sm font-medium">
                                    {leadData.name || 'Lead'} - Stage {leadData.stage}
                                </span>
                            </div>
                        </div>
                    )}
                </div>
            </div>

            {/* Messages */}
            <div className="flex-1 overflow-y-auto p-6 space-y-4">
                {messages.map((message) => (
                    <div key={message.id} className={`flex ${message.sender === 'user' ? 'justify-end' : 'justify-start'}`}>
                        <div className={`max-w-xs lg:max-w-md px-4 py-2 rounded-lg ${message.sender === 'user'
                            ? 'bg-blue-600 text-white'
                            : message.isError
                                ? 'bg-red-100 text-red-800 border border-red-200'
                                : 'bg-white text-gray-800 shadow-sm border'
                            }`}>
                            <div className="flex items-start space-x-2">
                                {message.sender === 'agent' && (
                                    <Bot className="w-5 h-5 mt-0.5 text-blue-600 flex-shrink-0" />
                                )}
                                {message.sender === 'user' && (
                                    <User className="w-5 h-5 mt-0.5 text-white flex-shrink-0" />
                                )}
                                {message.sender === 'system' && (
                                    <AlertCircle className="w-5 h-5 mt-0.5 text-red-600 flex-shrink-0" />
                                )}

                                <div className="flex-1">
                                    <p className="text-sm whitespace-pre-wrap">{message.content}</p>

                                    {/* Show updated lead data */}
                                    {message.leadData && (
                                        <div className="mt-3 p-3 bg-green-50 border border-green-200 rounded-lg">
                                            <div className="flex items-center text-green-800 mb-2">
                                                <CheckCircle className="w-4 h-4 mr-2" />
                                                <span className="text-xs font-medium">Information Updated</span>
                                            </div>

                                            <div className="grid grid-cols-1 gap-2">
                                                {formatLeadData(message.leadData)?.map((field, index) => {
                                                    const Icon = field.icon;
                                                    return (
                                                        <div key={index} className="flex items-center text-xs text-green-700">
                                                            <Icon className="w-3 h-3 mr-2 flex-shrink-0" />
                                                            <span className="font-medium mr-2">{field.label}:</span>
                                                            <span className="truncate">{field.value}</span>
                                                        </div>
                                                    );
                                                })}

                                                {message.leadData.stage && (
                                                    <div className="flex items-center text-xs text-green-700 mt-1 pt-2 border-t border-green-200">
                                                        <ArrowRight className="w-3 h-3 mr-2 flex-shrink-0" />
                                                        <span className="font-medium">Moved to Stage {message.leadData.stage}</span>
                                                    </div>
                                                )}
                                            </div>
                                        </div>
                                    )}

                                    <p className="text-xs mt-1 opacity-70">
                                        {new Date(message.timestamp).toLocaleTimeString()}
                                    </p>
                                </div>
                            </div>
                        </div>
                    </div>
                ))}

                {isLoading && (
                    <div className="flex justify-start">
                        <div className="bg-white text-gray-800 shadow-sm border max-w-xs lg:max-w-md px-4 py-2 rounded-lg">
                            <div className="flex items-center space-x-2">
                                <Bot className="w-5 h-5 text-blue-600" />
                                <div className="flex space-x-1">
                                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                                </div>
                            </div>
                        </div>
                    </div>
                )}

                <div ref={messagesEndRef} />
            </div>

            {/* Input */}
            <div className="bg-white border-t px-6 py-4">
                <div className="flex space-x-4">
                    <div className="flex-1">
                        <textarea
                            value={inputMessage}
                            onChange={(e) => setInputMessage(e.target.value)}
                            onKeyPress={handleKeyPress}
                            placeholder={sessionInfo ? "Type your message..." : "Creating session..."}
                            disabled={isLoading || !sessionInfo}
                            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
                            rows="2"
                        />
                    </div>
                    <button
                        onClick={handleSendMessage}
                        disabled={!inputMessage.trim() || isLoading || !sessionInfo}
                        className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2"
                    >
                        <Send className="w-4 h-4" />
                        <span>Send</span>
                    </button>
                </div>

                {sessionInfo && (
                    <p className="text-xs text-gray-500 mt-2">
                        Session: {sessionInfo.session_id.substring(0, 8)}... |
                        Stage {sessionInfo.current_stage} of {sessionInfo.total_stages}
                    </p>
                )}
            </div>
        </div>
    );
};

export default LeadChat; 