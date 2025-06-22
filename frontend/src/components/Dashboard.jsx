import React, { useState, useEffect } from 'react';
import { MessageSquare, LayoutDashboard, RefreshCw, Users, RotateCcw, Target, Sparkles } from 'lucide-react';
import CRMChat from './CRMChat';
import KanbanBoard from './KanbanBoard';
import LeadChat from './LeadChat';
import { Button, Spin, Alert, message } from 'antd';
import API_BASE_URL from '../config';

const Dashboard = () => {
    const [activeTab, setActiveTab] = useState('chat');
    const [pipelineData, setPipelineData] = useState(null);
    const [isLoading, setIsLoading] = useState(false);
    const [leadSession, setLeadSession] = useState(null);
    const [leadMessages, setLeadMessages] = useState([]);
    const [resetting, setResetting] = useState(false);

    // Reset state function for MVP
    const resetState = async () => {
        if (window.confirm('Are you sure you want to reset the pipeline state? This will clear all current pipeline data.')) {
            console.log('🔄 Resetting pipeline state...');
            setPipelineData(null);
            setActiveTab('chat');

            // Optional: Call backend to clear state (if implemented)
            try {
                setResetting(true);
                const url = `${API_BASE_URL}/admin/reset-state`;
                const response = await fetch(url, { method: 'POST' });
                if (response.ok) {
                    message.success('Application state has been reset!');
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
            const url = `${API_BASE_URL}/state/pipeline`;
            const response = await fetch(url);

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
            description: 'Create your sales pipeline',
            gradient: 'from-blue-500 to-purple-600'
        },
        {
            id: 'kanban',
            name: 'Pipeline Board',
            icon: LayoutDashboard,
            description: 'Manage leads and opportunities',
            gradient: 'from-green-500 to-teal-600'
        },
        {
            id: 'leadchat',
            name: 'Lead Chat',
            icon: Users,
            description: 'Experience the lead journey',
            gradient: 'from-orange-500 to-red-600'
        }
    ];

    return (
        <div className="h-screen flex flex-col bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-100">
            {/* Navigation Header */}
            <div className="bg-white/90 backdrop-blur-xl shadow-lg border-b border-white/20">
                <div className="px-8 py-6">
                    <div className="flex items-center justify-between">
                        <div className="flex items-center space-x-4">
                            <div className="flex items-center justify-center w-12 h-12 bg-gradient-to-br from-blue-600 to-purple-700 rounded-xl shadow-lg">
                                <Sparkles className="w-6 h-6 text-white" />
                            </div>
                            <div>
                                <h1 className="text-3xl font-bold bg-gradient-to-r from-slate-800 to-slate-600 bg-clip-text text-transparent">
                                    AI-Powered CRM
                                </h1>
                                <p className="text-slate-600 font-medium">
                                    Build and manage your custom sales pipeline
                                </p>
                            </div>
                        </div>

                        <div className="flex items-center space-x-3">
                            {/* Refresh Button */}
                            <button
                                onClick={fetchPipelineData}
                                disabled={isLoading}
                                className="flex items-center px-4 py-2.5 text-sm font-medium text-slate-600 hover:text-slate-900 bg-white/60 hover:bg-white/80 backdrop-blur-sm rounded-xl border border-white/30 hover:border-white/50 transition-all duration-200 shadow-sm hover:shadow-md"
                            >
                                <RefreshCw className={`w-4 h-4 mr-2 ${isLoading ? 'animate-spin' : ''}`} />
                                Refresh
                            </button>

                            {/* Reset State Button */}
                            <button
                                onClick={resetState}
                                className="flex items-center px-4 py-2.5 text-sm font-medium text-red-600 hover:text-red-700 bg-red-50/60 hover:bg-red-50/80 backdrop-blur-sm rounded-xl border border-red-200/50 hover:border-red-300/70 transition-all duration-200 shadow-sm hover:shadow-md"
                            >
                                <RotateCcw className="w-4 h-4 mr-2" />
                                Reset State
                            </button>

                            {/* Pipeline Status */}
                            {pipelineData && (
                                <div className="flex items-center bg-gradient-to-r from-emerald-50 to-green-50 text-emerald-700 px-4 py-2.5 rounded-xl border border-emerald-200/50 shadow-sm">
                                    <div className="w-2 h-2 bg-emerald-500 rounded-full mr-3 animate-pulse"></div>
                                    <span className="text-sm font-semibold">Pipeline Active</span>
                                </div>
                            )}
                        </div>
                    </div>

                    {/* Tab Navigation */}
                    <div className="mt-8">
                        <nav className="flex space-x-2 bg-white/40 backdrop-blur-sm rounded-2xl p-2 border border-white/30">
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
                                        className={`flex items-center flex-1 px-6 py-4 rounded-xl font-medium text-sm transition-all duration-300 ${isActive
                                            ? `bg-gradient-to-r ${tab.gradient} text-white shadow-lg transform scale-105`
                                            : isDisabled
                                                ? 'text-slate-400 cursor-not-allowed opacity-50'
                                                : 'text-slate-600 hover:text-slate-800 hover:bg-white/60 hover:shadow-md'
                                            }`}
                                    >
                                        <Icon className={`w-5 h-5 mr-3 ${isActive ? 'text-white' : ''}`} />
                                        <div className="text-left">
                                            <div className="font-semibold">{tab.name}</div>
                                            <div className={`text-xs mt-0.5 ${isActive ? 'text-white/80' : 'text-slate-500'}`}>
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