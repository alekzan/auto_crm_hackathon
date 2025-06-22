import React, { useState, useEffect } from 'react';
import { MessageSquare, LayoutDashboard, RefreshCw, Users, RotateCcw, Target } from 'lucide-react';
import CRMChat from './CRMChat';
import KanbanBoard from './KanbanBoard';
import LeadChat from './LeadChat';

const Dashboard = () => {
    const [activeTab, setActiveTab] = useState('chat');
    const [pipelineData, setPipelineData] = useState(null);
    const [isLoading, setIsLoading] = useState(false);
    const [leadSession, setLeadSession] = useState(null);
    const [leadMessages, setLeadMessages] = useState([]);

    // Reset state function for MVP
    const resetState = async () => {
        if (window.confirm('Are you sure you want to reset the pipeline state? This will clear all current pipeline data.')) {
            console.log('🔄 Resetting pipeline state...');
            setPipelineData(null);
            setActiveTab('chat');

            // Optional: Call backend to clear state (if implemented)
            try {
                const response = await fetch('http://localhost:8001/admin/reset-state', {
                    method: 'POST'
                });
                if (response.ok) {
                    console.log('✅ Backend state reset successfully');
                } else {
                    console.log('⚠️ Backend state reset failed, but frontend state cleared');
                }
            } catch (error) {
                console.log('⚠️ Could not reset backend state:', error.message);
            }
        }
    };

    // Debug functions removed - pipeline completion and extraction is now automatic

    // Fetch pipeline data from backend
    const fetchPipelineData = async () => {
        setIsLoading(true);
        try {
            console.log('🔄 Fetching pipeline data from backend...');
            const response = await fetch('http://localhost:8001/state/pipeline');

            if (response.ok) {
                const data = await response.json();
                console.log('📊 Pipeline data loaded successfully:', data);
                setPipelineData(data);

                // Verify the data has required fields
                if (data.total_stages && data.biz_name) {
                    console.log(`✅ Valid pipeline data: ${data.biz_name} with ${data.total_stages} stages`);
                } else {
                    console.warn('⚠️ Pipeline data missing required fields:', {
                        has_total_stages: !!data.total_stages,
                        has_biz_name: !!data.biz_name,
                        data_keys: Object.keys(data)
                    });
                }
            } else {
                console.log(`⚠️ No pipeline data available yet (HTTP ${response.status})`);
                const errorText = await response.text();
                console.log('Error details:', errorText);
                setPipelineData(null);
            }
        } catch (error) {
            console.error('❌ Error fetching pipeline data:', error);
            setPipelineData(null);
        } finally {
            setIsLoading(false);
        }
    };

    // Load pipeline data on component mount
    useEffect(() => {
        fetchPipelineData();
    }, []);

    // Handle pipeline completion from CRM chat
    const handlePipelineComplete = async (payload) => {
        console.log('🎉 Pipeline completed:', payload);

        // If we have full payload data, use it directly
        if (payload && payload.biz_name && payload.total_stages) {
            setPipelineData(payload);
        } else {
            // If we only have completion notification, set a minimal pipeline data to unlock tabs
            console.log('🔄 Pipeline complete but no full payload - setting minimal data and fetching from backend');
            setPipelineData({ pipeline_complete: true, loading: true });

            // Fetch the actual pipeline data from backend
            await fetchPipelineData();
        }

        // Automatically switch to Kanban view when pipeline is complete
        setActiveTab('kanban');
    };

    // Handle lead session creation and persistence
    const handleLeadSessionCreated = (sessionData) => {
        console.log('💾 Storing lead session for persistence:', sessionData);
        setLeadSession(sessionData);
    };

    // Handle lead messages updates
    const handleLeadMessagesUpdate = (messages) => {
        console.log('💬 Storing lead messages for persistence:', messages.length, 'messages');
        setLeadMessages(messages);
    };

    const tabs = [
        {
            id: 'chat',
            name: 'CRM Builder',
            icon: MessageSquare,
            description: 'Create your sales pipeline'
        },
        {
            id: 'kanban',
            name: 'Pipeline Board',
            icon: LayoutDashboard,
            description: 'Manage leads and opportunities'
        },
        {
            id: 'leadchat',
            name: 'Lead Chat',
            icon: Users,
            description: 'Experience the lead journey'
        }
    ];

    return (
        <div className="h-screen flex flex-col bg-gray-50">
            {/* Navigation Header */}
            <div className="bg-white shadow-sm border-b">
                <div className="px-6 py-4">
                    <div className="flex items-center justify-between">
                        <div>
                            <h1 className="text-2xl font-bold text-gray-900">AI-Powered CRM</h1>
                            <p className="text-sm text-gray-500">
                                Build and manage your custom sales pipeline
                            </p>
                        </div>

                        <div className="flex items-center space-x-4">
                            {/* Refresh Button */}
                            <button
                                onClick={fetchPipelineData}
                                disabled={isLoading}
                                className="flex items-center px-3 py-2 text-sm text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition-colors"
                            >
                                <RefreshCw className={`w-4 h-4 mr-2 ${isLoading ? 'animate-spin' : ''}`} />
                                Refresh
                            </button>

                            {/* Reset State Button */}
                            <button
                                onClick={resetState}
                                className="flex items-center px-3 py-2 text-sm text-red-600 hover:text-red-800 hover:bg-red-50 rounded-lg transition-colors"
                            >
                                <RotateCcw className="w-4 h-4 mr-2" />
                                Reset State
                            </button>

                            {/* Debug buttons removed - functionality is now automatic */}

                            {/* Pipeline Status */}
                            {pipelineData && (
                                <div className="flex items-center text-green-600 bg-green-50 px-3 py-2 rounded-lg">
                                    <div className="w-2 h-2 bg-green-600 rounded-full mr-2"></div>
                                    <span className="text-sm font-medium">Pipeline Active</span>
                                </div>
                            )}
                        </div>
                    </div>

                    {/* Tab Navigation */}
                    <div className="mt-6">
                        <nav className="flex space-x-8">
                            {tabs.map((tab) => {
                                const Icon = tab.icon;
                                const isActive = activeTab === tab.id;
                                // Tabs are enabled when we have pipeline data OR when pipeline is marked as complete
                                const isPipelineReady = pipelineData && (pipelineData.total_stages || pipelineData.pipeline_complete);
                                const isDisabled = (tab.id === 'kanban' || tab.id === 'leadchat') && !isPipelineReady;

                                return (
                                    <button
                                        key={tab.id}
                                        onClick={() => !isDisabled && setActiveTab(tab.id)}
                                        disabled={isDisabled}
                                        className={`flex items-center py-2 px-1 border-b-2 font-medium text-sm transition-colors ${isActive
                                            ? 'border-blue-500 text-blue-600'
                                            : isDisabled
                                                ? 'border-transparent text-gray-400 cursor-not-allowed'
                                                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                                            }`}
                                    >
                                        <Icon className="w-5 h-5 mr-2" />
                                        <div className="text-left">
                                            <div>{tab.name}</div>
                                            <div className="text-xs font-normal opacity-75">
                                                {tab.description}
                                            </div>
                                        </div>
                                    </button>
                                );
                            })}
                        </nav>
                    </div>
                </div>
            </div>

            {/* Main Content */}
            <div className="flex-1 overflow-hidden">
                {activeTab === 'chat' && (
                    <CRMChat onPipelineComplete={handlePipelineComplete} />
                )}
                {activeTab === 'kanban' && (
                    <KanbanBoard pipelineData={pipelineData} />
                )}
                {activeTab === 'leadchat' && (
                    <LeadChat
                        existingSession={leadSession}
                        existingMessages={leadMessages}
                        onSessionCreated={handleLeadSessionCreated}
                        onMessagesUpdate={handleLeadMessagesUpdate}
                    />
                )}
            </div>
        </div>
    );
};

export default Dashboard; 