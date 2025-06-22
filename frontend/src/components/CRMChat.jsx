import React, { useState, useRef, useEffect } from 'react';
import { Send, Upload, FileText, CheckCircle, AlertCircle } from 'lucide-react';

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
            const response = await fetch('http://localhost:8001/owner/chat', {
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
                const response = await fetch('http://localhost:8001/owner/upload', {
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
        <div className="flex flex-col h-full bg-gray-50">
            {/* Header */}
            <div className="bg-white shadow-sm border-b px-6 py-4">
                <div className="flex items-center justify-between">
                    <div>
                        <h1 className="text-xl font-semibold text-gray-900">
                            CRM Stage Builder Agent
                        </h1>
                        <p className="text-sm text-gray-500">
                            Create your custom sales pipeline
                        </p>
                    </div>
                    <div className="flex items-center space-x-2">
                        {pipelineComplete && (
                            <div className="flex items-center text-green-600">
                                <CheckCircle className="w-5 h-5 mr-1" />
                                <span className="text-sm font-medium">Pipeline Complete</span>
                            </div>
                        )}
                        {sessionId && (
                            <div className="text-xs text-gray-400">
                                Session: {sessionId.slice(-8)}
                            </div>
                        )}
                    </div>
                </div>
            </div>

            {/* Messages Area */}
            <div className="flex-1 overflow-y-auto px-6 py-4 space-y-4" style={{ minHeight: 0 }}>
                {messages.map((message) => (
                    <div
                        key={message.id}
                        className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'
                            }`}
                    >
                        <div
                            className={`max-w-3xl rounded-lg px-4 py-3 ${message.type === 'user'
                                ? 'bg-blue-600 text-white'
                                : message.type === 'agent'
                                    ? 'bg-white border shadow-sm text-gray-900'
                                    : message.type === 'system'
                                        ? 'bg-green-50 border border-green-200 text-green-800'
                                        : 'bg-red-50 border border-red-200 text-red-800'
                                }`}
                        >
                            <div className="whitespace-pre-wrap">{message.content}</div>
                            <div
                                className={`text-xs mt-2 ${message.type === 'user'
                                    ? 'text-blue-100'
                                    : 'text-gray-500'
                                    }`}
                            >
                                {formatTimestamp(message.timestamp)}
                            </div>
                        </div>
                    </div>
                ))}

                {isLoading && (
                    <div className="flex justify-start">
                        <div className="bg-white border shadow-sm rounded-lg px-4 py-3">
                            <div className="flex items-center space-x-2">
                                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600"></div>
                                <span className="text-gray-600">Agent is thinking...</span>
                            </div>
                        </div>
                    </div>
                )}

                <div ref={messagesEndRef} />
            </div>

            {/* Uploaded Files Display */}
            {uploadedFiles.length > 0 && (
                <div className="px-6 py-2 bg-blue-50 border-t border-blue-200">
                    <div className="flex flex-wrap gap-2">
                        {uploadedFiles.map((file, index) => (
                            <div
                                key={index}
                                className="flex items-center space-x-2 bg-blue-100 rounded-lg px-3 py-1"
                            >
                                <FileText className="w-4 h-4 text-blue-600" />
                                <span className="text-sm text-blue-800">{file.name}</span>
                            </div>
                        ))}
                    </div>
                </div>
            )}

            {/* Input Area */}
            <div className="flex-shrink-0 bg-white border-t px-6 py-4">
                <div className="flex items-end space-x-4">
                    <button
                        onClick={() => fileInputRef.current?.click()}
                        className="flex-shrink-0 p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
                        title="Upload files (PDF, DOCX, CSV)"
                    >
                        <Upload className="w-5 h-5" />
                    </button>

                    <div className="flex-1">
                        <textarea
                            value={inputMessage}
                            onChange={(e) => setInputMessage(e.target.value)}
                            onKeyPress={handleKeyPress}
                            placeholder="Describe your business, upload files, or ask questions about your sales pipeline..."
                            className="w-full px-4 py-3 border border-gray-300 rounded-lg resize-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
                            rows="2"
                            disabled={isLoading}
                        />
                    </div>

                    <button
                        onClick={handleSendMessage}
                        disabled={!inputMessage.trim() || isLoading}
                        className="flex-shrink-0 p-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
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

                <div className="mt-2 text-xs text-gray-500">
                    Supported files: PDF, DOCX, CSV • Press Enter to send • Shift+Enter for new line
                </div>
            </div>
        </div>
    );
};

export default CRMChat; 