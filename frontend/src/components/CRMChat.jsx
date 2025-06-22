import React, { useState, useRef, useEffect } from 'react';
import { Send, Upload, FileText, CheckCircle, AlertCircle, Bot, User } from 'lucide-react';
import API_BASE_URL from '../config';

const CRMChat = ({ onPipelineComplete }) => {
    const [messages, setMessages] = useState([]);
    const [inputMessage, setInputMessage] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [sessionId, setSessionId] = useState(null);
    const [pipelineComplete, setPipelineComplete] = useState(false);
    const [uploadedFiles, setUploadedFiles] = useState([]);

    const messagesEndRef = useRef(null);
    const fileInputRef = useRef(null);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    };

    // Only auto-scroll when there are multiple messages (not for the initial message)
    useEffect(() => {
        if (messages.length > 1) {
            scrollToBottom();
        }
    }, [messages]);

    // Add initial welcome message with a slight delay to prevent fast flash
    useEffect(() => {
        const timer = setTimeout(() => {
            if (messages.length === 0) {
                setMessages([{
                    id: 1,
                    type: 'agent',
                    content: 'Welcome! I\'m your AI CRM Builder.',
                    timestamp: new Date().toISOString()
                }]);
            }
        }, 500); // 500ms delay to prevent flash

        return () => clearTimeout(timer);
    }, []);

    useEffect(() => {
        if (messages.length > 0) {
            const lastMessage = messages[messages.length - 1];
            // Check if the last message is a system message with pipeline_payload
            if (lastMessage.type === 'system' && lastMessage.pipeline_payload) {
                console.log('🎉 Pipeline completed, notifying parent');
                if (onPipelineComplete) {
                    onPipelineComplete(lastMessage.pipeline_payload);
                }
            }
        }
    }, [messages, onPipelineComplete]);

    const handleSendMessage = async () => {
        if (!inputMessage.trim() || isLoading) return;

        const userMessage = {
            id: Date.now(),
            type: 'user',
            content: inputMessage,
            timestamp: new Date().toISOString()
        };

        setMessages(prev => [...prev, userMessage]);
        setInputMessage('');
        setIsLoading(true);

        try {
            const url = `${API_BASE_URL}/owner/chat`;
            const response = await fetch(url, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    content: inputMessage,
                    session_id: sessionId,
                    files: uploadedFiles.map(file => ({
                        name: file.name,
                        path: file.path
                    }))
                }),
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            console.log('📨 Backend response:', {
                pipeline_complete: data.pipeline_complete,
                has_payload: !!data.pipeline_payload,
                payload_keys: data.pipeline_payload ? Object.keys(data.pipeline_payload) : null,
                payload_sample: data.pipeline_payload ? {
                    biz_name: data.pipeline_payload.biz_name,
                    total_stages: data.pipeline_payload.total_stages,
                    stage_1_stage_name: data.pipeline_payload.stage_1_stage_name
                } : null
            });

            // Update session ID if this is the first message
            if (!sessionId && data.session_id) {
                setSessionId(data.session_id);
            }

            // Add agent response
            const agentMessage = {
                id: Date.now() + 1,
                type: 'agent',
                content: data.response,
                timestamp: data.timestamp
            };

            setMessages(prev => [...prev, agentMessage]);

            // Check if pipeline is complete
            if (data.pipeline_complete) {
                setPipelineComplete(true);

                // Add completion message with pipeline payload
                const completionMessage = {
                    id: Date.now() + 2,
                    type: 'system',
                    content: '🎉 Pipeline creation complete! Your custom CRM workflow has been generated and is ready to use.',
                    timestamp: new Date().toISOString(),
                    pipeline_payload: data.pipeline_payload
                };

                setMessages(prev => [...prev, completionMessage]);

                // Trigger onPipelineComplete when pipeline is complete (even without payload)
                if (onPipelineComplete) {
                    console.log('🎉 Pipeline completed, notifying parent immediately');
                    // If we have payload data, use it; otherwise, trigger with basic completion info
                    const completionData = data.pipeline_payload || { pipeline_complete: true };
                    onPipelineComplete(completionData);
                }
            }

            // Clear uploaded files after successful message
            setUploadedFiles([]);

        } catch (error) {
            console.error('Error sending message:', error);

            let errorContent = 'Sorry, there was an error processing your message. Please try again.';

            // Handle specific error types
            if (error.message.includes('status: 429')) {
                errorContent = '⏱️ Rate limit exceeded. Please wait a minute before sending another message. Google Cloud has a limit of 10 requests per minute.';
            } else if (error.message.includes('status: 500')) {
                errorContent = '🔧 Server error occurred. This might be due to rate limiting or a temporary issue. Please wait a moment and try again.';
            } else if (error.message.includes('status: 404')) {
                errorContent = '❓ Service not found. Please make sure the backend server is running.';
            }

            const errorMessage = {
                id: Date.now() + 1,
                type: 'error',
                content: errorContent,
                timestamp: new Date().toISOString()
            };

            setMessages(prev => [...prev, errorMessage]);
        } finally {
            setIsLoading(false);
        }
    };

    const handleFileUpload = async (event) => {
        const files = Array.from(event.target.files);

        for (const file of files) {
            const formData = new FormData();
            formData.append('file', file);
            if (sessionId) {
                formData.append('session_id', sessionId);
            }

            try {
                const url = `${API_BASE_URL}/owner/upload`;
                const response = await fetch(url, {
                    method: 'POST',
                    body: formData,
                });

                if (!response.ok) {
                    throw new Error(`Upload failed: ${response.status}`);
                }

                const uploadData = await response.json();

                setUploadedFiles(prev => [...prev, {
                    name: uploadData.filename,
                    path: uploadData.path,
                    size: uploadData.size,
                    type: uploadData.type
                }]);

                // Add file upload confirmation message
                const uploadMessage = {
                    id: Date.now(),
                    type: 'system',
                    content: `📁 File "${uploadData.filename}" uploaded successfully and added to your knowledge base.`,
                    timestamp: new Date().toISOString()
                };

                setMessages(prev => [...prev, uploadMessage]);

            } catch (error) {
                console.error('File upload error:', error);

                const errorMessage = {
                    id: Date.now(),
                    type: 'error',
                    content: `Failed to upload "${file.name}". Please try again.`,
                    timestamp: new Date().toISOString()
                };

                setMessages(prev => [...prev, errorMessage]);
            }
        }

        // Reset file input
        event.target.value = '';
    };

    const handleKeyPress = (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSendMessage();
        }
    };

    const formatTimestamp = (timestamp) => {
        return new Date(timestamp).toLocaleTimeString([], {
            hour: '2-digit',
            minute: '2-digit'
        });
    };

    return (
        <div className="flex flex-col h-full bg-gradient-to-br from-slate-50 via-white to-blue-50">
            {/* Header */}
            <div className="bg-white/80 backdrop-blur-xl shadow-sm border-b border-white/20 px-8 py-6">
                <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-4">
                        <div className="flex items-center justify-center w-10 h-10 bg-gradient-to-br from-blue-500 to-purple-600 rounded-xl shadow-md">
                            <Bot className="w-5 h-5 text-white" />
                        </div>
                        <div>
                            <h1 className="text-xl font-bold bg-gradient-to-r from-slate-800 to-slate-600 bg-clip-text text-transparent">
                                CRM Stage Builder Agent
                            </h1>
                            <p className="text-slate-600 font-medium">
                                Create your custom sales pipeline
                            </p>
                        </div>
                    </div>
                    <div className="flex items-center space-x-4">
                        {pipelineComplete && (
                            <div className="flex items-center bg-gradient-to-r from-emerald-50 to-green-50 text-emerald-700 px-4 py-2 rounded-xl border border-emerald-200/50 shadow-sm">
                                <CheckCircle className="w-4 h-4 mr-2" />
                                <span className="text-sm font-semibold">Pipeline Complete</span>
                            </div>
                        )}
                        {sessionId && (
                            <div className="bg-slate-100/60 backdrop-blur-sm text-slate-600 px-3 py-1.5 rounded-lg border border-slate-200/50">
                                <span className="text-xs font-mono">Session: {sessionId.slice(-8)}</span>
                            </div>
                        )}
                    </div>
                </div>
            </div>

            {/* Messages Area */}
            <div className="flex-1 overflow-y-auto px-8 py-6 space-y-6" style={{ minHeight: 0 }}>
                {messages.map((message) => (
                    <div
                        key={message.id}
                        className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}
                    >
                        <div className={`flex items-start space-x-3 max-w-4xl ${message.type === 'user' ? 'flex-row-reverse space-x-reverse' : ''}`}>
                            {/* Avatar */}
                            <div className={`flex-shrink-0 flex items-center justify-center w-8 h-8 rounded-xl shadow-sm ${message.type === 'user'
                                ? 'bg-gradient-to-br from-blue-500 to-blue-600'
                                : message.type === 'agent'
                                    ? 'bg-gradient-to-br from-purple-500 to-purple-600'
                                    : message.type === 'system'
                                        ? 'bg-gradient-to-br from-emerald-500 to-emerald-600'
                                        : 'bg-gradient-to-br from-red-500 to-red-600'
                                }`}>
                                {message.type === 'user' ? (
                                    <User className="w-4 h-4 text-white" />
                                ) : message.type === 'system' ? (
                                    <CheckCircle className="w-4 h-4 text-white" />
                                ) : message.type === 'error' ? (
                                    <AlertCircle className="w-4 h-4 text-white" />
                                ) : (
                                    <Bot className="w-4 h-4 text-white" />
                                )}
                            </div>

                            {/* Message Bubble */}
                            <div
                                className={`relative px-6 py-4 rounded-2xl shadow-sm border backdrop-blur-sm ${message.type === 'user'
                                    ? 'bg-gradient-to-br from-blue-600 to-blue-700 text-white border-blue-500/20'
                                    : message.type === 'agent'
                                        ? 'bg-white/80 border-slate-200/50 text-slate-800'
                                        : message.type === 'system'
                                            ? 'bg-gradient-to-br from-emerald-50 to-green-50 border-emerald-200/50 text-emerald-800'
                                            : 'bg-gradient-to-br from-red-50 to-pink-50 border-red-200/50 text-red-800'
                                    }`}
                            >
                                <div className="whitespace-pre-wrap leading-relaxed">{message.content}</div>
                                <div
                                    className={`text-xs mt-3 ${message.type === 'user'
                                        ? 'text-blue-100'
                                        : 'text-slate-500'
                                        }`}
                                >
                                    {formatTimestamp(message.timestamp)}
                                </div>
                            </div>
                        </div>
                    </div>
                ))}

                {isLoading && (
                    <div className="flex justify-start">
                        <div className="flex items-start space-x-3">
                            <div className="flex items-center justify-center w-8 h-8 bg-gradient-to-br from-purple-500 to-purple-600 rounded-xl shadow-sm">
                                <Bot className="w-4 h-4 text-white" />
                            </div>
                            <div className="bg-white/80 backdrop-blur-sm border border-slate-200/50 rounded-2xl px-6 py-4 shadow-sm">
                                <div className="flex items-center space-x-3">
                                    <div className="flex space-x-1">
                                        <div className="w-2 h-2 bg-gradient-to-r from-purple-500 to-blue-500 rounded-full animate-bounce"></div>
                                        <div className="w-2 h-2 bg-gradient-to-r from-purple-500 to-blue-500 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                                        <div className="w-2 h-2 bg-gradient-to-r from-purple-500 to-blue-500 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                                    </div>
                                    <span className="text-slate-600 font-medium">Agent is thinking...</span>
                                </div>
                            </div>
                        </div>
                    </div>
                )}

                <div ref={messagesEndRef} />
            </div>

            {/* Uploaded Files Display */}
            {uploadedFiles.length > 0 && (
                <div className="px-8 py-4 bg-blue-50/60 backdrop-blur-sm border-t border-blue-200/50">
                    <div className="flex flex-wrap gap-3">
                        {uploadedFiles.map((file, index) => (
                            <div
                                key={index}
                                className="flex items-center space-x-3 bg-white/80 backdrop-blur-sm rounded-xl px-4 py-3 border border-blue-200/50 shadow-sm"
                            >
                                <div className="flex items-center justify-center w-8 h-8 bg-gradient-to-br from-blue-500 to-blue-600 rounded-lg">
                                    <FileText className="w-4 h-4 text-white" />
                                </div>
                                <span className="text-sm font-medium text-blue-800">{file.name}</span>
                            </div>
                        ))}
                    </div>
                </div>
            )}

            {/* Input Area */}
            <div className="flex-shrink-0 bg-white/80 backdrop-blur-xl border-t border-white/20 px-8 py-6">
                <div className="flex items-end space-x-4">
                    <button
                        onClick={() => fileInputRef.current?.click()}
                        className="flex-shrink-0 flex items-center justify-center w-12 h-12 bg-gradient-to-br from-slate-100 to-slate-200 hover:from-slate-200 hover:to-slate-300 text-slate-600 hover:text-slate-800 rounded-xl transition-all duration-200 shadow-sm hover:shadow-md border border-slate-200/50"
                        title="Upload files (PDF, DOCX, CSV)"
                    >
                        <Upload className="w-5 h-5" />
                    </button>

                    <div className="flex-1 relative">
                        <textarea
                            value={inputMessage}
                            onChange={(e) => setInputMessage(e.target.value)}
                            onKeyPress={handleKeyPress}
                            placeholder="Describe your business, upload files, or ask questions about your sales pipeline..."
                            className="w-full px-6 py-4 bg-white/80 backdrop-blur-sm border border-slate-200/50 rounded-2xl resize-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500/50 outline-none transition-all duration-200 shadow-sm hover:shadow-md leading-relaxed"
                            rows="2"
                            disabled={isLoading}
                        />
                    </div>

                    <button
                        onClick={handleSendMessage}
                        disabled={!inputMessage.trim() || isLoading}
                        className="flex-shrink-0 flex items-center justify-center w-12 h-12 bg-gradient-to-br from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800 text-white rounded-xl disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 shadow-md hover:shadow-lg transform hover:scale-105 disabled:transform-none"
                    >
                        <Send className="w-5 h-5" />
                    </button>
                </div>

                <input
                    ref={fileInputRef}
                    type="file"
                    accept=".pdf,.docx,.csv"
                    multiple
                    onChange={handleFileUpload}
                    className="hidden"
                />

                <div className="mt-4 text-xs text-slate-500 bg-slate-50/60 backdrop-blur-sm px-4 py-2 rounded-xl border border-slate-200/50">
                    <span className="font-medium">Supported files:</span> PDF, DOCX, CSV • Press <kbd className="px-1.5 py-0.5 bg-slate-200/80 rounded text-xs">Enter</kbd> to send • <kbd className="px-1.5 py-0.5 bg-slate-200/80 rounded text-xs">Shift+Enter</kbd> for new line
                </div>
            </div>
        </div>
    );
};

export default CRMChat; 