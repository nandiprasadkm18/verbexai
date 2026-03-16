import React from 'react';
import { 
  LayoutDashboard, 
  Users, 
  CheckSquare, 
  MessageSquare, 
  UserCircle, 
  AlertCircle, 
  PlusCircle,
  ChevronRight
} from 'lucide-react';
import type { PageId } from '../types.ts';



interface SidebarProps {
  activePage: PageId;
  onPageChange: (id: PageId) => void;
  isCollapsed: boolean;
  onToggleCollapse: () => void;
  staleCount?: number;
}

const Sidebar: React.FC<SidebarProps> = ({ activePage, onPageChange, isCollapsed, onToggleCollapse, staleCount = 0 }) => {
  const navItems = [
    { id: 'manager' as PageId, label: 'Manager View', icon: <LayoutDashboard size={18} /> },
    { id: 'meetings' as PageId, label: 'All Meetings', icon: <Users size={18} /> },
    { id: 'tasks' as PageId, label: 'Task Board', icon: <CheckSquare size={18} /> },
    { id: 'decisions' as PageId, label: 'Decision Log', icon: <MessageSquare size={18} /> },
    { id: 'speakers' as PageId, label: 'Speaker Map', icon: <UserCircle size={18} /> },
    { id: 'stale' as PageId, label: 'Stale Tasks', icon: <AlertCircle size={18} />, badge: staleCount },
    { id: 'employees' as PageId, label: 'Employee Directory', icon: <Users size={18} /> },
    { id: 'ingest' as PageId, label: 'New Meeting', icon: <PlusCircle size={18} /> },
  ];

  return (
    <aside className={`fixed left-0 top-0 h-screen bg-white transition-all duration-300 flex flex-col z-50 shadow-[4px_0_24px_-12px_rgba(0,0,0,0.05)] border-r border-slate-200/60 ${isCollapsed ? 'w-20' : 'w-[240px]'}`}>
      <div className={`p-6 flex items-center justify-between transition-all ${isCollapsed ? 'flex-col gap-4 px-2' : ''}`}>
        <div className={`transition-opacity duration-300 ${isCollapsed ? 'opacity-0 h-0 overflow-hidden' : 'opacity-100'}`}>
          <h1 className="font-serif text-2xl text-primary leading-none font-bold">Verbex</h1>
          <p className="font-sans text-[10px] font-semibold uppercase tracking-widest text-slate-400 mt-1.5">Enterprise Data</p>
        </div>
        <button 
          onClick={onToggleCollapse}
          className={`p-1.5 rounded-lg border border-slate-100 bg-slate-50 text-slate-400 hover:text-primary hover:bg-white transition-all shadow-xs ${isCollapsed ? 'rotate-180' : ''}`}
        >
          <ChevronRight size={14} className={isCollapsed ? '' : 'rotate-180'} />
        </button>
      </div>

      <nav className="flex-1 space-y-1 px-3">
        {navItems.map((item) => (
          <button
            key={item.id}
            onClick={() => onPageChange(item.id)}
            className={`w-full flex items-center rounded-lg transition-all duration-200 group relative p-2 ${
              activePage === item.id 
                ? 'bg-accent-teal/5 text-accent-teal font-bold border border-accent-teal/10' 
                : 'text-slate-500 hover:text-primary hover:bg-slate-50'
            } ${isCollapsed ? 'justify-center' : 'gap-3 px-4'}`}
            title={isCollapsed ? item.label : ''}
          >
            {activePage === item.id && (
              <div className="absolute left-0 top-1/2 -translate-y-1/2 w-1 h-4 bg-accent-teal rounded-r shadow-[0_0_8px_rgba(17,94,89,0.3)]"></div>
            )}
            <span className={`${activePage === item.id ? 'text-accent-teal' : 'text-slate-400 group-hover:text-slate-600'}`}>
              {item.icon}
            </span>
            {!isCollapsed && (
              <span className="font-sans text-[13px] tracking-tight flex-1 text-left">
                {item.label}
              </span>
            )}
            {!isCollapsed && item.badge && (
              <span className="bg-rose-500 text-white text-[10px] font-bold px-1.5 py-0.5 rounded-full min-w-[18px] text-center">
                {item.badge}
              </span>
            )}
            {isCollapsed && item.badge && (
              <div className="absolute top-1.5 right-1.5 w-2 h-2 bg-rose-500 rounded-full border border-white"></div>
            )}
          </button>
        ))}
      </nav>

      <div className={`mt-auto p-4 transition-all ${isCollapsed ? 'px-2' : ''}`}>
        <div className={`flex items-center gap-3 p-2 rounded-xl border border-slate-100 bg-slate-50/50 ${isCollapsed ? 'justify-center' : ''}`}>
          <div className="w-9 h-9 shrink-0 rounded-full bg-white shadow-sm flex items-center justify-center font-sans font-bold text-xs text-primary border border-slate-100">
            SS
          </div>
          {!isCollapsed && (
            <div className="overflow-hidden">
              <p className="text-[13px] font-bold text-primary truncate">Suman S.</p>
              <p className="text-[11px] text-slate-500 font-medium tracking-tight">Admin</p>
            </div>
          )}
        </div>
      </div>
    </aside>
  );
};

export default Sidebar;
