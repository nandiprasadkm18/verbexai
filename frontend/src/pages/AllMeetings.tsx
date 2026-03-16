import React, { useState, useEffect } from 'react';
import { useFetch } from '../hooks/useFetch';
import { api } from '../utils/api';
import type { Meeting } from '../types.ts';
import { Filter, Calendar, User, Clock, ChevronRight, Trash2, AlertTriangle, BarChart3, ChevronDown, CheckCircle2, Circle, Loader2 } from 'lucide-react';

const AllMeetings: React.FC<{ onMeetingClick: (id: number) => void }> = ({ onMeetingClick }) => {
  const { data: meetings, loading, mutate } = useFetch<Meeting[]>('/meetings');
  const [deleteConfirm, setDeleteConfirm] = useState<string | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [updatingTaskId, setUpdatingTaskId] = useState<string | null>(null);
  const [syncingMeetingId, setSyncingMeetingId] = useState<string | null>(null);

  // Auto-sync ALL meetings on page load
  useEffect(() => {
    if (meetings && meetings.length > 0) {
      const syncAll = async () => {
        for (const meeting of meetings) {
          if (meeting.tasks && meeting.tasks.some((t: any) => t.github_issue_url || t.jira_issue_key)) {
            try {
              await api.get(`/meetings/${meeting.id}/sync`);
            } catch (e) {
              // silent - don't block the UI
            }
          }
        }
        await mutate(); // Refresh the data after all syncs complete
      };
      syncAll();
    }
  }, [meetings?.length]); // Only run when meetings count changes (initial load)

  // Auto-sync when expanding the intelligence box for a specific meeting
  useEffect(() => {
    if (expandedId) {
      handleSyncStatus(expandedId);
    }
  }, [expandedId]);

  const handleDelete = async (e: React.MouseEvent, id: string) => {
    e.stopPropagation();
    try {
      setIsDeleting(true);
      await api.delete(`/meetings/${id}`);
      setDeleteConfirm(null);
      mutate();
    } catch (err) {
      console.error('Failed to delete meeting:', err);
      alert('Failed to delete meeting');
    } finally {
      setIsDeleting(false);
    }
  };

  const handleStatusChange = async (taskId: string, newStatus: string) => {
    try {
      setUpdatingTaskId(taskId);
      await api.patch(`/tasks/${taskId}`, { status: newStatus });
      await mutate();
    } catch (err) {
      console.error('Failed to update status:', err);
      alert('Failed to update task status');
    } finally {
      setUpdatingTaskId(null);
    }
  };
  const handleSyncStatus = async (meetingId: string) => {
    try {
      setSyncingMeetingId(meetingId);
      await api.get(`/meetings/${meetingId}/sync`);
      await mutate();
    } catch (err) {
      console.error('Failed to sync statuses:', err);
    } finally {
      setSyncingMeetingId(null);
    }
  };

  return (
    <div className="page p-8 max-w-7xl mx-auto">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-6 mb-8">
        <div className="flex items-center gap-3">
          <button className="flex items-center gap-2 px-4 py-1.5 bg-white border border-slate-200 rounded-lg text-[13px] font-semibold text-slate-600 hover:bg-slate-50 transition-all shadow-xs">
            <Filter size={14} />
            Filters
          </button>
          <button className="flex items-center gap-2 px-4 py-1.5 bg-white border border-slate-200 rounded-lg text-[13px] font-semibold text-slate-600 hover:bg-slate-50 transition-all shadow-xs">
            <Calendar size={14} />
            Date Range
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-4">
        {loading && !meetings ? (
          <div className="h-64 flex items-center justify-center">
            <div className="w-6 h-6 border-2 border-slate-200 border-t-accent-teal rounded-full animate-spin"></div>
          </div>
        ) : (
          meetings?.map((meeting, i) => (
            <React.Fragment key={meeting.id}>
            <div 
              onClick={() => onMeetingClick(meeting.id as any)}
              className={`corporate-card group stagger-${(i % 5) + 1} flex flex-col hover:border-accent-teal/30 cursor-pointer overflow-hidden transition-all duration-300 ${
                expandedId === meeting.id ? 'ring-2 ring-accent-teal/20 border-accent-teal/30' : ''
              }`}
            >
              <div className="p-5 flex flex-col md:flex-row md:items-center gap-6">
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-2">
                    <span className={`px-1.5 py-0.5 rounded text-[10px] font-bold uppercase tracking-widest border ${
                      meeting.status === 'complete' ? 'bg-teal-50 text-teal-700 border-teal-100' : 'bg-slate-50 text-slate-500 border-slate-200'
                    }`}>
                      {meeting.status}
                    </span>
                    <p className="text-slate-400 text-[12px] font-semibold font-mono tracking-tight flex items-center gap-1.5">
                      <Clock size={12} />
                      {new Date(meeting.created_at).toLocaleString()}
                    </p>
                  </div>
                  <h3 className="text-lg font-bold text-primary group-hover:text-accent-teal transition-colors tracking-tight">{meeting.title}</h3>
                  <div className="flex items-center gap-4 mt-3">
                    <p className="text-slate-500 text-sm flex items-center gap-1.5">
                      <User size={14} className="text-slate-300" />
                      Hosted by <span className="text-primary font-semibold">{meeting.host_name}</span>
                    </p>
                    <div className="w-1 h-1 bg-slate-300 rounded-full"></div>
                    <span className="text-[10px] font-bold text-slate-400 uppercase tracking-tighter">
                      {meeting.input_type?.replace('_', ' ') || 'Manual'}
                    </span>
                  </div>
                </div>

                <div className="flex items-center gap-8 px-8 border-x border-slate-100 py-2">
                  <div className="text-center min-w-[60px]">
                    <p className="text-[10px] font-bold text-slate-400 uppercase mb-1">Tasks</p>
                    <p className="text-lg font-bold text-primary">{meeting.tasks?.length || 0}</p>
                  </div>
                  <div className="text-center min-w-[60px]">
                    <p className="text-[10px] font-bold text-slate-400 uppercase mb-1">Health</p>
                    {(() => {
                      const total = meeting.tasks?.length || 0;
                      const approved = meeting.tasks?.filter(t => t.status === 'approved' || t.status === 'completed').length || 0;
                      const health = total > 0 ? Math.round((approved / total) * 100) : 0;
                      return (
                        <p className={`text-lg font-bold ${health > 80 ? 'text-teal-600' : health > 40 ? 'text-amber-600' : 'text-rose-600'}`}>
                          {health}%
                        </p>
                      );
                    })()}
                  </div>
                </div>

                <div className="flex flex-wrap gap-2 md:w-32 justify-end">
                  {deleteConfirm === meeting.id ? (
                    <div className="flex items-center gap-2 animate-fadeIn">
                      <button
                        onClick={(e) => handleDelete(e, meeting.id)}
                        disabled={isDeleting}
                        className="px-3 py-1.5 bg-rose-500 text-white text-[10px] font-bold rounded uppercase tracking-widest hover:bg-rose-600 flex items-center gap-1.5"
                      >
                        {isDeleting ? <Loader2 size={12} className="animate-spin" /> : <Trash2 size={12} />}
                        Confirm
                      </button>
                      <button
                        onClick={(e) => { e.stopPropagation(); setDeleteConfirm(null); }}
                        className="px-3 py-1.5 bg-slate-100 text-slate-500 text-[10px] font-bold rounded uppercase tracking-widest hover:bg-slate-200"
                      >
                        X
                      </button>
                    </div>
                  ) : (
                    <button
                      onClick={(e) => { e.stopPropagation(); setDeleteConfirm(meeting.id); }}
                      className="p-2 text-slate-300 hover:text-rose-500 hover:bg-rose-50 rounded transition-all"
                    >
                      <Trash2 size={16} />
                    </button>
                  )}
                  <div 
                    className={`text-slate-300 transition-all ml-2 hidden md:block ${
                      expandedId === meeting.id ? 'rotate-90 text-accent-teal' : 'group-hover:text-accent-teal group-hover:translate-x-1'
                    }`}
                  >
                    <ChevronRight size={18} />
                  </div>
                </div>
              </div>

              {/* Prominent Action Button */}
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  setExpandedId(expandedId === meeting.id ? null : meeting.id);
                }}
                className={`w-full py-2.5 flex items-center justify-center gap-2 text-[11px] font-bold uppercase tracking-[0.1em] transition-all border-t ${
                  expandedId === meeting.id 
                    ? 'bg-slate-50 text-slate-400 border-slate-200' 
                    : 'bg-accent-teal/5 text-accent-teal border-accent-teal/10 hover:bg-accent-teal hover:text-white'
                }`}
              >
                {expandedId === meeting.id ? (
                  <>
                    <ChevronDown className="rotate-180" size={14} />
                    Collapse Intelligence Box
                  </>
                ) : (
                  <>
                    <BarChart3 size={14} />
                    View Task Intelligence & Real-time Tracking
                  </>
                )}
              </button>
            </div>

            {/* Collapsible Progress Tracking Box */}
            {expandedId === meeting.id && (
              <div 
                className="mx-4 mb-4 bg-white rounded-b-xl border-x border-b border-slate-200 p-6 animate-slideDown overflow-hidden shadow-xl z-10 relative"
              >
                <div className="flex flex-col gap-6">
                  {/* Progress Chart / Summary */}
                  <div className="flex flex-col gap-4 border-b border-slate-200 pb-6">
                    <div className="flex items-center justify-between">
                      <div>
                        <h4 className="text-xs font-bold text-slate-400 uppercase tracking-widest mb-1">Task Intelligence Overview</h4>
                        <p className="text-sm text-slate-600 font-medium tracking-tight">Monitoring {meeting.tasks?.length || 0} active work streams</p>
                      </div>
                      <div className="flex gap-4">
                        <div className="flex items-center gap-2">
                          <div className="w-2 h-2 rounded-full bg-emerald-500"></div>
                          <span className="text-[10px] font-bold text-slate-500 uppercase">Approved</span>
                        </div>
                        <div className="flex items-center gap-2">
                          <div className="w-2 h-2 rounded-full bg-blue-500"></div>
                          <span className="text-[10px] font-bold text-slate-500 uppercase">In Progress</span>
                        </div>
                        <div className="flex items-center gap-2">
                          <div className="w-2 h-2 rounded-full bg-amber-500"></div>
                          <span className="text-[10px] font-bold text-slate-500 uppercase">Pending</span>
                        </div>
                      </div>
                    </div>
                    
                    {/* Visual Progress Bar */}
                    <div className="w-full h-2 bg-slate-200 rounded-full overflow-hidden flex shadow-inner">
                      {(() => {
                        const total = meeting.tasks?.length || 0;
                        const approved = meeting.tasks?.filter(t => t.status === 'approved' || t.status === 'completed').length || 0;
                        const inProgress = meeting.tasks?.filter(t => t.status === 'in_progress').length || 0;
                        const pending = total - (approved + inProgress);
                        
                        const approvedPercent = total > 0 ? (approved / total) * 100 : 0;
                        const inProgressPercent = total > 0 ? (inProgress / total) * 100 : 0;
                        const pendingPercent = total > 0 ? (pending / total) * 100 : 0;
                        
                        return (
                          <>
                            <div className="h-full bg-emerald-500 transition-all duration-500" style={{ width: `${approvedPercent}%` }}></div>
                            <div className="h-full bg-blue-500 transition-all duration-500" style={{ width: `${inProgressPercent}%` }}></div>
                            <div className="h-full bg-amber-500 transition-all duration-500" style={{ width: `${pendingPercent}%` }}></div>
                          </>
                        );
                      })()}
                    </div>
                  </div>

                  {/* Detailed Task Table */}
                  <div className="overflow-x-auto">
                    <table className="w-full text-left">
                      <thead>
                        <tr className="border-b border-slate-200">
                          <th className="pb-3 text-[10px] font-bold text-slate-400 uppercase tracking-tighter w-16">ID</th>
                          <th className="pb-3 text-[10px] font-bold text-slate-400 uppercase tracking-tighter">Task Name</th>
                          <th className="pb-3 text-[10px] font-bold text-slate-400 uppercase tracking-tighter">Assignee</th>
                          <th className="pb-3 text-[10px] font-bold text-slate-400 uppercase tracking-tighter">Status Tracking</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-100">
                        {meeting.tasks && meeting.tasks.length > 0 ? (
                          meeting.tasks.map((task) => (
                            <tr key={task.id} className="hover:bg-slate-50 transition-colors">
                              <td className="py-4 text-[11px] font-mono text-slate-500 font-bold">#{task.id.slice(0, 5)}</td>
                              <td className="py-4 text-xs font-semibold text-primary">{task.title}</td>
                              <td className="py-4">
                                <span className="text-[11px] px-2 py-0.5 bg-slate-50 border border-slate-200 rounded font-bold text-slate-600 shadow-sm">
                                  {task.assignee_name || 'Unassigned'}
                                </span>
                              </td>
                              <td className="py-4">
                                <div className="flex items-center gap-3">
                                  {updatingTaskId === task.id ? (
                                    <Loader2 size={14} className="animate-spin text-accent-teal" />
                                  ) : (
                                    task.status === 'completed' || task.status === 'approved' ? <CheckCircle2 size={14} className="text-emerald-500" /> : <Circle size={14} className="text-slate-300" />
                                  )}
                                  <select 
                                    value={task.status}
                                    onChange={(e) => handleStatusChange(task.id, e.target.value)}
                                    className={`text-[10px] font-bold uppercase tracking-widest px-3 py-1.5 rounded-lg border transition-all cursor-pointer outline-none focus:ring-2 focus:ring-accent-teal/20 ${
                                      task.status === 'completed' || task.status === 'approved' ? 'bg-emerald-50 text-emerald-600 border-emerald-200' :
                                      task.status === 'in_progress' ? 'bg-blue-50 text-blue-600 border-blue-200' :
                                      task.status === 'failed' ? 'bg-rose-50 text-rose-600 border-rose-200' :
                                      'bg-amber-50 text-amber-600 border-amber-200'
                                    }`}
                                  >
                                    <option value="pending">Pending Review</option>
                                    <option value="approved">Approved</option>
                                    <option value="in_progress">In Progress</option>
                                    <option value="completed">Completed</option>
                                    <option value="failed">Failed</option>
                                  </select>
                                </div>
                              </td>
                            </tr>
                          ))
                        ) : (
                          <tr>
                            <td colSpan={4} className="py-8 text-center text-slate-400 text-xs font-medium italic">
                              No tasks derived from this meeting session.
                            </td>
                          </tr>
                        )}
                      </tbody>
                    </table>
                  </div>

                  <div className="pt-2 flex justify-between items-center text-[10px] font-bold text-slate-400 uppercase">
                    <span>Precision Engine: Groq LLaMA 3.3</span>
                    <button 
                      onClick={() => handleSyncStatus(meeting.id)}
                      disabled={syncingMeetingId === meeting.id}
                      className={`flex items-center gap-1.5 transition-all ${
                        syncingMeetingId === meeting.id 
                          ? 'text-accent-teal animate-pulse' 
                          : 'text-accent-teal hover:text-accent-teal/80 hover:underline cursor-pointer'
                      }`}
                    >
                      {syncingMeetingId === meeting.id ? (
                        <>
                          <Loader2 size={12} className="animate-spin" />
                          Syncing with Platforms...
                        </>
                      ) : (
                        <>
                          <BarChart3 size={12} />
                          Sync Platform Status
                        </>
                      )}
                    </button>
                  </div>
                </div>
              </div>
            )}
          </React.Fragment>
          ))
        )}
        {meetings?.length === 0 && !loading && (
          <div className="h-64 flex flex-col items-center justify-center gap-4 corporate-card bg-slate-50/50 border-dashed">
            <AlertTriangle className="text-slate-300 underline-offset-4" size={32} strokeWidth={1} />
            <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">No meeting history found</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default AllMeetings;
