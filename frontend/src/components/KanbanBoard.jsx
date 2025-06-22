import React, { useState, useEffect } from 'react';
import { Plus, Users, Target, ArrowRight, RefreshCw } from 'lucide-react';

const KanbanBoard = ({ pipelineData }) => {
    const [stages, setStages] = useState([]);
    const [businessName, setBusinessName] = useState('');
    const [leads, setLeads] = useState([]);
    const [isLoadingLeads, setIsLoadingLeads] = useState(false);
    const [error, setError] = useState(null);

    useEffect(() => {
        console.log('🔍 KanbanBoard received pipelineData:', pipelineData);

        if (pipelineData && pipelineData.total_stages) {
            // Extract business name
            setBusinessName(pipelineData.biz_name || 'Business Pipeline');

            // Build stages from flattened ready state
            const totalStages = pipelineData.total_stages || 0;
            const stageList = [];

            for (let i = 1; i <= totalStages; i++) {
                const stage = {
                    id: i,
                    name: pipelineData[`stage_${i}_stage_name`] || `Stage ${i}`,
                    goal: pipelineData[`stage_${i}_brief_stage_goal`] || 'No goal specified',
                    entry_condition: pipelineData[`stage_${i}_entry_condition`] || '',
                    fields: pipelineData[`stage_${i}_fields`] || [],
                    // Add default user_tags if not present
                    user_tags: pipelineData[`stage_${i}_user_tags`] || [`stage_${i}`, 'active'],
                    leads: [] // Will be populated with actual leads
                };
                stageList.push(stage);
                console.log(`📋 Built stage ${i}:`, stage);
            }

            setStages(stageList);

            // Fetch real lead data instead of using demo data
            fetchLeads();
        } else {
            console.log('⚠️ No valid pipeline data received');
            setStages([]);
            setLeads([]);
        }
    }, [pipelineData]);

    // Fetch leads when component mounts
    useEffect(() => {
        if (pipelineData && pipelineData.total_stages) {
            fetchLeads();
        }
    }, []);

    // Fetch real lead data from backend
    const fetchLeads = async () => {
        try {
            setIsLoadingLeads(true);
            setError(null);
            console.log('🔄 Fetching leads from backend...');

            const response = await fetch('http://localhost:8001/state/leads');
            if (response.ok) {
                const leadsData = await response.json();
                console.log('📊 Leads data loaded:', leadsData);

                // Validate and sanitize leads data
                const sanitizedLeads = leadsData.map(lead => ({
                    id: lead.session_id || lead.id || `lead-${Date.now()}`,
                    name: lead.name || 'Unnamed Lead',
                    type: lead.type || 'Lead',
                    email: lead.email || '',
                    stage: lead.stage || 1,
                    user_tags: Array.isArray(lead.user_tags) ? lead.user_tags : [],
                    created_at: lead.created_at || new Date().toISOString(),
                    ...lead
                }));

                setLeads(sanitizedLeads);
            } else {
                console.log('⚠️ No leads data available yet');
                setLeads([]);
            }
        } catch (error) {
            console.error('❌ Error fetching leads:', error);
            setError('Failed to load leads data');
            setLeads([]);
        } finally {
            setIsLoadingLeads(false);
        }
    };

    const getLeadsForStage = (stageId) => {
        return leads.filter(lead => lead.stage === stageId);
    };

    const moveLeadToStage = (leadId, newStage) => {
        setLeads(prevLeads =>
            prevLeads.map(lead =>
                (lead.id === leadId || lead.session_id === leadId) ? { ...lead, stage: newStage } : lead
            )
        );
    };

    const addNewLead = (stageId) => {
        const newLead = {
            id: `lead-${Date.now()}`,
            name: `New Patient #${Date.now().toString().slice(-4)}`,
            type: 'New Patient',
            email: `patient${Date.now()}@demo.com`,
            stage: stageId,
            tags: ['new_patient', 'manual_add'],
            created_at: new Date().toISOString()
        };
        setLeads(prevLeads => [...prevLeads, newLead]);
    };

    if (!pipelineData || !pipelineData.total_stages || stages.length === 0) {
        return (
            <div className="flex items-center justify-center h-64 bg-gray-50 rounded-lg">
                <div className="text-center">
                    <Target className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                    <h3 className="text-lg font-medium text-gray-900 mb-2">No Pipeline Available</h3>
                    <p className="text-gray-500">Create a CRM pipeline first to see the Kanban board.</p>
                    {error && (
                        <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-lg">
                            <p className="text-sm text-red-700">Error: {error}</p>
                        </div>
                    )}
                    {pipelineData && (
                        <div className="mt-4 p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
                            <p className="text-sm text-yellow-700">
                                Debug: Pipeline data received but missing total_stages
                            </p>
                        </div>
                    )}
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
                            {businessName} - Sales Pipeline
                        </h1>
                        <p className="text-sm text-gray-500">
                            {stages.length} stages • {leads.length} total leads
                            {isLoadingLeads && <span className="ml-2 text-blue-600">• Loading...</span>}
                        </p>
                    </div>
                    <div className="flex items-center space-x-2">
                        {/* Refresh Button */}
                        <button
                            onClick={fetchLeads}
                            disabled={isLoadingLeads}
                            className="flex items-center text-gray-600 hover:text-gray-900 bg-gray-100 hover:bg-gray-200 px-3 py-2 rounded-lg transition-colors disabled:opacity-50"
                        >
                            <RefreshCw className={`w-4 h-4 mr-2 ${isLoadingLeads ? 'animate-spin' : ''}`} />
                            <span className="text-sm font-medium">Refresh</span>
                        </button>

                        <div className="flex items-center text-green-600 bg-green-50 px-3 py-2 rounded-lg">
                            <div className="w-2 h-2 bg-green-600 rounded-full mr-2"></div>
                            <span className="text-sm font-medium">Pipeline Active</span>
                        </div>
                        <div className="flex items-center text-blue-600">
                            <Users className="w-5 h-5 mr-1" />
                            <span className="text-sm font-medium">{leads.length} Leads</span>
                        </div>
                    </div>
                </div>
            </div>

            {/* Kanban Board */}
            <div className="flex-1 overflow-x-auto p-6">
                <div className="flex space-x-6 min-w-max">
                    {stages.map((stage, index) => {
                        const stageLeads = getLeadsForStage(stage.id);

                        return (
                            <div key={stage.id} className="flex-shrink-0 w-80">
                                {/* Stage Header */}
                                <div className="bg-white rounded-lg shadow-sm border mb-4">
                                    <div className="p-4 border-b">
                                        <div className="flex items-center justify-between mb-2">
                                            <h3 className="font-semibold text-gray-900">
                                                {stage.id}. {stage.name}
                                            </h3>
                                            <span className="bg-blue-100 text-blue-800 text-xs font-medium px-2 py-1 rounded-full">
                                                {stageLeads.length}
                                            </span>
                                        </div>
                                        <p className="text-sm text-gray-600 mb-3">{stage.goal}</p>

                                        {/* Entry Condition */}
                                        {stage.entry_condition && (
                                            <div className="text-xs text-gray-500 bg-gray-50 p-2 rounded">
                                                <strong>Entry:</strong> {stage.entry_condition}
                                            </div>
                                        )}

                                        {/* Stage Tags */}
                                        {stage.user_tags && Array.isArray(stage.user_tags) && stage.user_tags.length > 0 && (
                                            <div className="flex flex-wrap gap-1 mt-2">
                                                {stage.user_tags.map((tag, tagIndex) => (
                                                    <span
                                                        key={tagIndex}
                                                        className="inline-block bg-gray-200 text-gray-700 text-xs px-2 py-1 rounded"
                                                    >
                                                        {tag}
                                                    </span>
                                                ))}
                                            </div>
                                        )}
                                    </div>

                                    {/* Add Lead Button */}
                                    <div className="p-3 border-b bg-gray-50">
                                        <button
                                            onClick={() => addNewLead(stage.id)}
                                            className="w-full flex items-center justify-center text-sm text-gray-600 hover:text-gray-900 hover:bg-gray-100 p-2 rounded transition-colors"
                                        >
                                            <Plus className="w-4 h-4 mr-1" />
                                            Add Lead
                                        </button>
                                    </div>
                                </div>

                                {/* Lead Cards */}
                                <div className="space-y-3 min-h-[200px]">
                                    {stageLeads.map((lead) => (
                                        <div
                                            key={lead.id}
                                            className="bg-white rounded-lg shadow-sm border p-4 hover:shadow-md transition-shadow cursor-pointer"
                                        >
                                            <div className="flex items-start justify-between mb-2">
                                                <h4 className="font-medium text-gray-900">{lead.name || 'Unnamed Lead'}</h4>
                                                <span className="text-xs text-gray-500">{lead.type || 'Lead'}</span>
                                            </div>

                                            <p className="text-sm text-gray-600 mb-3">{lead.email || 'No email provided'}</p>

                                            {/* Lead Tags */}
                                            <div className="flex flex-wrap gap-1 mb-3">
                                                {(lead.user_tags || []).map((tag, tagIndex) => (
                                                    <span
                                                        key={tagIndex}
                                                        className="inline-block bg-blue-100 text-blue-800 text-xs px-2 py-1 rounded"
                                                    >
                                                        {tag}
                                                    </span>
                                                ))}
                                            </div>

                                            {/* Move Actions */}
                                            <div className="flex justify-between items-center">
                                                <span className="text-xs text-gray-400">
                                                    {lead.created_at ? new Date(lead.created_at).toLocaleDateString() : 'No date'}
                                                </span>

                                                <div className="flex space-x-1">
                                                    {stage.id > 1 && (
                                                        <button
                                                            onClick={() => moveLeadToStage(lead.id, stage.id - 1)}
                                                            className="text-xs text-gray-500 hover:text-gray-700 px-2 py-1 rounded hover:bg-gray-100"
                                                            title="Move to previous stage"
                                                        >
                                                            ←
                                                        </button>
                                                    )}
                                                    {stage.id < stages.length && (
                                                        <button
                                                            onClick={() => moveLeadToStage(lead.id, stage.id + 1)}
                                                            className="text-xs text-blue-600 hover:text-blue-800 px-2 py-1 rounded hover:bg-blue-50 flex items-center"
                                                            title="Move to next stage"
                                                        >
                                                            <ArrowRight className="w-3 h-3" />
                                                        </button>
                                                    )}
                                                </div>
                                            </div>
                                        </div>
                                    ))}

                                    {stageLeads.length === 0 && (
                                        <div className="text-center py-8 text-gray-400">
                                            <Users className="w-8 h-8 mx-auto mb-2 opacity-50" />
                                            <p className="text-sm">No leads in this stage</p>
                                        </div>
                                    )}
                                </div>
                            </div>
                        );
                    })}
                </div>
            </div>
        </div>
    );
};

export default KanbanBoard; 